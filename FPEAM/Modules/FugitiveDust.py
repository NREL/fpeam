from Module import Module
from FPEAM import (Data, utils)

LOGGER = utils.logger(name=__name__)


class FugitiveDust(Module):
    """Base class to manage execution of on-farm fugitive dust calculations"""

    def __init__(self, config, production, fugitive_dust_emission_factors,
                 crop_measure_type,
                 **kvals):
        """
        :param config [ConfigObj] configuration options
        :param production: [DataFrame] production values
        :param fugitive_dust_emission_factors: [DataFrame] fugitive dust
        generation per acre
        """

        # init parent
        super(FugitiveDust, self).__init__(config = config)

        # init properties
        self.production = production
        self.crop_measure_type = crop_measure_type

        # pre-process fugitive dust input file to calculate
        # fugitive dust generation per acre for one average year

        # average fugitive dust emission factors over rotation_year within
        # each feedstock-tillage-pollutant combo
        # these average numbers get multiplied by acreages to calculate
        # fugitive dust by feedstock, tillage type, source category and region
        self.fugitive_dust = fugitive_dust_emission_factors.groupby([
            'feedstock', 'tillage_type', 'source_category',
            'pollutant'], as_index = False).mean()

        # remove rotation_year column which no longer has usefule
        # information in it
        self.fugitive_dust.drop('rotation_year', axis = 1, inplace = True)

    def get_fugitivedust(self):
        """
        Calculate total PM10 and PM2.5 emissions from fugitive dust by
        feedstock, tillage type, source category and region.

        :return: _df: DataFrame containing PM10 and PM2.5 amounts by
        feedstock, tillage type, source category and region
        """

        # define columns used to merge production with fugitive_dust
        _idx = ['feedstock', 'tillage_type']

        # define list of columns of interest in production
        _prod_columns = ['row_id'] + _idx + ['region_production',
                                             'crop_amount']

        # select only production rows corresponding to the user-defined crop
        #  measure
        _prod_rows = self.production.crop_measure == self.crop_measure_type

        # merge production with fugitive dust
        _df = self.production[_prod_rows][_prod_columns].merge(
            self.fugitive_dust, on = _idx)

        # calculate fugitive dust
        _df.eval('pollutant_amount = crop_amount * rate',
                 inplace = True)

        # clean up DataFrame
        # @TODO verify that these are the columns to return
        _df = _df[['row_id', 'feedstock', 'source_category', 'tillage_type',
                   'source_category', 'region_production', 'pollutant',
                   'pollutant_amount']].set_index('row_id', drop = True)

        return _df

    def run(self):
        """
        Execute all calculations.

        :return: _results DataFrame containing fugitive dust amounts
        """

        _results = None
        _status = self.status

        try:
            _results = self.get_fugitivedust()
        except Exception as e:
            LOGGER.exception(e)
            _status = 'failed'
        else:
            _status = 'complete'
        finally:
            self.status = _status
            return _results

    def summarize(self):
        pass
