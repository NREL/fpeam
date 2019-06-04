from FPEAM import utils
from .Module import Module
from ..Data import FugitiveDustFactors

LOGGER = utils.logger(name=__name__)


class FugitiveDust(Module):
    """Base class to manage execution of on-farm fugitive dust calculations"""

    def __init__(self, config, production, backfill=True, **kvals):
        """
        :param config [ConfigObj] configuration options
        :param production: [DataFrame] production values
        :param backfill: [boolean] backfill missing data values with 0
        """

        # init parent
        super(FugitiveDust, self).__init__(config=config)

        self.production = production

        self.fugitive_dust = FugitiveDustFactors(fpath=self.config.get('emission_factors'),
                                          backfill=backfill)

        self.feedstock_measure_type = self.config.get('feedstock_measure_type')
        
    def get_onfarm_fugitivedust(self):
        """
        Calculate total PM10 and PM2.5 emissions from fugitive dust by
        feedstock, tillage type, source category and region.

        :return: [DataFrame] containing PM10 and PM2.5 amounts by feedstock,
                 tillage type, source category and region
        """

        # define columns used to merge production with fugitive_dust
        _idx = ['feedstock', 'tillage_type']

        # define list of columns of interest in production
        _prod_columns = ['row_id'] + _idx + ['region_production', 'feedstock_amount']

        # select only production rows corresponding to the user-defined crop measure
        _prod_rows = self.production.feedstock_measure == self.feedstock_measure_type

        # merge production with fugitive dust
        _df = self.production[_prod_rows][_prod_columns].merge(self.fugitive_dust, on=_idx)

        # calculate fugitive dust
        _df.eval('pollutant_amount = feedstock_amount * rate', inplace=True)

        # add column to identify module
        _df['module'] = 'fugitive dust'

        # clean up DataFrame
        _df = _df[['region_production', 'feedstock',
                   'tillage_type', 'module', 'pollutant',
                   'pollutant_amount']]

        return _df

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
