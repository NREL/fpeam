from FPEAM import utils
from .Module import Module
from ..Data import FugitiveDustFactors, TruckCapacity, SiltContent,\
    FugitiveDustOnroadConstants


LOGGER = utils.logger(name=__name__)


class FugitiveDust(Module):
    """Base class to manage execution of on-farm fugitive dust calculations"""

    def __init__(self, config, production, feedstock_loss_factors,
                 backfill=True, **kvals):
        """
        :param config [ConfigObj] configuration options
        :param production: [DataFrame] production values
        :param backfill: [boolean] backfill missing data values with 0
        """

        # init parent
        super(FugitiveDust, self).__init__(config=config)

        self.production = production

        # define columns used to merge production with fugitive_dust
        self.prod_idx = ['feedstock', 'tillage_type']

        # define list of columns of interest in production
        _prod_columns = ['row_id'] + self.prod_idx + ['region_production', 'feedstock_amount']

        # select only production rows corresponding to the user-defined crop measure
        _prod_rows = self.production.feedstock_measure == self.feedstock_measure_type

        # pull out relevant subset of production data
        self.production = self.production[_prod_rows][_prod_columns]

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

        self.feedstock_measure_type = self.config.get('feedstock_measure_type')
        
    def get_onfarm_fugitivedust(self):
        """
        Calculate total PM10 and PM2.5 emissions from fugitive dust by
        feedstock, tillage type, source category and region.

        :return: [DataFrame] containing PM10 and PM2.5 amounts by feedstock,
                 tillage type, source category and region
        """

        # merge production subset with fugitive dust
        _df = self.production.merge(self.fugitive_dust_factors, on=self.prod_idx)

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

        # merge loss factors with prod df
        _df = self.production.merge(_loss_factors_farmgate, on='feedstock')

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

        # remove truck capacity column that's not needed further
        del _df['truck_capacity']



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
