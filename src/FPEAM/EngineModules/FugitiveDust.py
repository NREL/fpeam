import numpy as np
from FPEAM import utils
from .Module import Module
from ..Data import FugitiveDustFactors, TruckCapacity, SiltContent,\
    FugitiveDustOnroadConstants


LOGGER = utils.logger(name=__name__)


class FugitiveDust(Module):
    """Base class to manage execution of on-farm fugitive dust calculations"""

    def __init__(self, config, production, feedstock_loss_factors, router=None,
                 backfill=True, **kvals):
        """
        :param config [ConfigObj] configuration options
        :param production: [DataFrame] production values
        :param backfill: [boolean] backfill missing data values with 0
        """

        # init parent
        super(FugitiveDust, self).__init__(config=config)

        self.production = production

        self._router = router
        self.vmt_short_haul = self.config.as_int('vmt_short_haul')

        self.onfarm_feedstock_measure_type = self.config.get('onfarm_feedstock_measure_type')
        self.onroad_feedstock_measure_type = self.config.get('onroad_feedstock_measure_type')

        self.forestry_feedstock_names = self.config.get('forestry_feedstock_names')

        self.region_fips_map = self.config.get('region_fips_map')

        # define columns used to merge production with fugitive_dust
        self.prod_idx = ['feedstock', 'tillage_type']

        # define list of columns of interest in production
        _prod_columns = ['row_id'] + self.prod_idx + ['region_production', 'feedstock_amount']

        # select only production rows corresponding to the user-defined crop measure
        _prod_rows_onfarm = self.production.feedstock_measure == self.onfarm_feedstock_measure_type
        _prod_rows_onroad = self.production.feedstock_measure == self.onroad_feedstock_measure_type

        # pull out relevant subset of production data
        self.prod_onfarm = self.production[_prod_rows_onfarm][_prod_columns]
        self.prod_onroad = self.production[_prod_rows_onroad][_prod_columns]

        self.feedstock_loss_factors = feedstock_loss_factors

        # these inputs are datasets read in from csv files
        self.truck_capacity = TruckCapacity(fpath=self.config.get('truck_capacity'),
                                            backfill=backfill)
        self.fugitive_dust_factors = FugitiveDustFactors(fpath=self.config.get('fugitive_dust_factors'),
                                          backfill=backfill)
        self.silt_content = SiltContent(fpath=self.config.get('silt_content'),
                                        backfill=backfill)
        self.fugitive_dust_onroad_constants = FugitiveDustOnroadConstants(fpath=self.config.get('fugitive_dust_onroad_constants'),
                                                                          backfill=backfill)

    @property
    def router(self):
        return self._router

    @router.setter
    def router(self, value):
        try:
            getattr(value, 'get_route')
        except AttributeError:
            LOGGER.error('%s is NOT a valid routing engine. '
                         'Method .get_route(FIPS, FIPS) is required' % value)
        else:
            self._router = value

    def get_onfarm_fugitivedust(self):
        """
        Calculate total PM10 and PM2.5 emissions from fugitive dust by
        feedstock, tillage type, source category and region.

        :return: [DataFrame] containing PM10 and PM2.5 amounts by feedstock,
                 tillage type, source category and region
        """

        # merge production subset with fugitive dust
        _df = self.prod_onfarm.merge(self.fugitive_dust_factors, on=self.prod_idx)

        # calculate fugitive dust
        _df.eval('pollutant_amount = feedstock_amount * rate', inplace=True)

        # add column to identify module
        _df['module'] = 'fugitive dust'

        # clean up DataFrame
        _df = _df[['region_production', 'feedstock',
                   'tillage_type', 'module', 'pollutant',
                   'pollutant_amount']]

        return _df

    def get_onroad_fugitivedust(self):
        """
        Calculate PM10 and PM2.5 from on-road biomass transportation, using
        silt factors from the EPA and equations documented in the Billion Ton
        Study.

        Only equations and parameters for primary roads are used because the
        definitions of primary and secondary roads are unclear and may vary
        from data source to data source
        :return: None
        """


        # apply feedstock loss factors for on-farm dry matter losses, since
        # trips should be calculated based on farm-gate feedstock amounts
        self.feedstock_loss_factors.eval('dry_matter_remaining = '
                                         '1 - dry_matter_loss',
                                         inplace=True)

        # pull out only on-farm feedstock losses
        _loss_factors_farmgate = self.feedstock_loss_factors[
            self.feedstock_loss_factors.supply_chain_stage.isin(['farm gate'])]

        # calculate total losses on farm, remove unnecessary columns
        _loss_factors_farmgate = _loss_factors_farmgate.groupby(['feedstock'],
                                                                as_index=False)
        _loss_factors_farmgate = _loss_factors_farmgate.prod()[['feedstock',
                                                                'dry_matter_remaining']]

        # grab relevant prod data frame - preprocessed in init
        _prod = self.prod_onroad

        # merge loss factors with prod df
        _df = _prod.merge(_loss_factors_farmgate, on='feedstock')

        # calculate farmgate feedstock amount by applying loss factors
        _df['feedstock_amount'] = _df['feedstock_amount'] * _df['dry_matter_remaining']

        # remove loss factor column
        del _df['dry_matter_remaining']

        # merge with truck capacity so trips can be calculated
        _df.merge(self.truck_capacity, on='feedstock')

        # trips calculation accounting for dry matter loss (calc'd above),
        # feedstock-specific truck capacity, and backhauling
        _df.eval('trips = (2 * feedstock_amount / truck_capacity - 1)',
                 inplace=True)

        # find rows where the trips calculation works out to be less than 1 and
        # # set these trip values to 1 (can't have less than one trip)
        _df.loc[_df['trips'] < 1, 'trips'] = 1

        # remove truck capacity column that's not needed further
        del _df['truck_capacity']

        # create column containing state FIPS identifier for merging with silt content
        # data frame
        _df['st_fips'] = _df.region_production.astype('str').str[0:2]

        # don't need the state name, it's only in the input data for human readability
        del self.silt_content['st_name']

        # convert the state fips column to string to match the new column in _df
        self.silt_content['st_fips'] = self.silt_content.st_fips.astype('str')

        # merge silt content with production etc. data frame
        _df = _df.merge(self.silt_content, on='st_fips')

        # to implement the onroad fugdust calculations it'll be easier
        # to store the onroad constants as a dictionary and access them by
        # name
        # what's going on below - first fugitive_dust_onroad_constants is being subsetted by
        # road type and pollutant type, then just the columns with the constant name and
        # value are kept. following that, the index for this smaller df is set to the
        # column with the constant name to make it easier to convert to a dictionary
        # then the df is converted to a dictionary with one key, 'value', containing
        # essentially the same structure as the small df. pulling out just this 'value'
        # creates a dictionary where you can access constants values using the
        # constant name, ie _unp_pm25['k']
        # @NOTE based on the road database the router engine pulls from, we
        # aren't using the paved secondary road type constants, only the paved primary
        _unp_pm25 = self.fugitive_dust_onroad_constants[(self.fugitive_dust_onroad_constants['road_type'] == 'unpaved') &
                                                        (self.fugitive_dust_onroad_constants['pollutant'] == 'pm2.5')][['constant', 'value']].set_index('constant').to_dict()['value']
        _unp_pm10 = self.fugitive_dust_onroad_constants[(self.fugitive_dust_onroad_constants['road_type'] == 'unpaved') &
                                                        (self.fugitive_dust_onroad_constants['pollutant'] == 'pm10')][['constant', 'value']].set_index('constant').to_dict()['value']
        _pav_pm25 = self.fugitive_dust_onroad_constants[(self.fugitive_dust_onroad_constants['road_type'] == 'paved primary') &
                                                        (self.fugitive_dust_onroad_constants['pollutant'] == 'pm2.5')][['constant', 'value']].set_index('constant').to_dict()['value']
        _pav_pm10 = self.fugitive_dust_onroad_constants[(self.fugitive_dust_onroad_constants['road_type'] == 'paved primary') &
                                                        (self.fugitive_dust_onroad_constants['pollutant'] == 'pm10')][['constant', 'value']].set_index('constant').to_dict()['value']

        # mileage per feedstock-county combination on unpaved roads is
        # assumed to be 2 miles for ag feedstocks and 10 miles for forestry
        # feedstocks, per BTS16 Ch 9

        # create column in _df filled with 2.0 to hold the unpaved vmt values
        # overwrite with 10.0 for forestry feedstocks only
        _df['unp_vmt'] = 2.0
        _df.loc[_df.feedstock.isin(self.forestry_feedstock_names), 'unp_vmt'] = 10.0

        # calculate pm25 and pm10 emissions from transpo over unpaved roads in
        # production regions
        _df.eval('unp_pm25 = trips * unp_vmt * @k * (uprsm_pct_silt/12)**@A * (@W/3)**@B',
                 global_dict=_unp_pm25, inplace=True)
        _df.eval('unp_pm10 = trips * unp_vmt * @k * (uprsm_pct_silt/12)**@A * (@W/3)**@B',
                 global_dict=_unp_pm10, inplace=True)

        # the router engine must be used to calculate the onroad, paved fugdust
        # since we need vmt by county *for every county along the route* in
        # order to do the calculations properly

        # get routing information between each unique region_production and
        # region_destination pair
        _routes = _df[['region_production',
                       'region_destination']].drop_duplicates()

        # use the region-fips map to generate fips_production and
        # fips_destination columns - in case any of the regions aren't fips
        _routes = _routes.merge(self.region_fips_map, how='left',
                                left_on='region_production',
                                right_on='region')
        _routes.rename(index=str, columns={'fips': 'fips_production'},
                       inplace=True)

        _routes = _routes.merge(self.region_fips_map, how='left',
                                left_on='region_destination',
                                right_on='region')[['region_production',
                                                    'region_destination',
                                                    'fips_production',
                                                    'fips']]
        _routes.rename(index=str, columns={'fips': 'fips_destination'},
                       inplace=True)

        # if routing engine is specified, use it to get the route (fips and
        # vmt) for each unique region_production and region_destination pair
        if self.router is not None:

            # initialize holder for all routes
            _vmt_by_county_all_routes = pd.DataFrame()

            # loop through all routes
            for i in np.arange(_routes.shape[0]):

                # use the routing engine to get a route
                _vmt_by_county = self.router.get_route(
                    from_fips=_routes.fips_production.iloc[i],
                    to_fips=_routes.fips_destination.iloc[i])

                # add identifier columns for later merging with _run_emissions
                _vmt_by_county['region_production'] = \
                _routes.region_production.iloc[i]
                _vmt_by_county['region_destination'] = \
                _routes.region_destination.iloc[i]

                # either create the data frame to store all routes,
                # or append the current route
                if _vmt_by_county_all_routes.empty:
                    _vmt_by_county_all_routes = _vmt_by_county

                else:
                    _vmt_by_county_all_routes = \
                        _vmt_by_county_all_routes.append(_vmt_by_county,
                                                         ignore_index=True,
                                                         sort=True)

            # after the loop through all routes is complete, merge the data
            # frame containing all routes with _run_emissions
            _df = _df.merge(_vmt_by_county_all_routes,
                            how='left', on=['region_production',
                                            'region_destination'])

        else:
            # if user has specified NOT to use the router engine, use the
            # user-specified vmt and fill the region_transportation column
            # with values from the region_production column
            _df['region_transportation'] = _df['region_production']
            _df['vmt'] = self.vmt_short_haul




    def run(self):
        """
        Execute all calculations.

        :return:
        """

        _results = None
        _status = self.status
        _e = None

        try:
            _results = self.get_onfarm_fugitivedust()
        except Exception as e:
            _e = e
            LOGGER.exception(e)
            _status = 'failed'
        else:
            _status = 'complete'
        finally:
            self.status = _status
            self.results = _results
            if _e:
                raise _e

    def summarize(self):
        pass
