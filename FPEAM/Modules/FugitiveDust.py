from Module import Module

from FPEAM import (Data, utils)

LOGGER = utils.logger(name=__name__)


class FugitiveDust(Module):
    """Base class to manage execution of on-farm fugitive dust calculations"""

    def __init__(self, config, production,
                 fugitive_dust_emission_factors,
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
        self.fugitivedust = fugitive_dust_emission_factors

    def get_fugitivedust(self):
        """
        Calculate all total PM10 and PM2.5 emissions from fugitive dust by
        feedstock, region and tillage type.

        :return: _df: DataFrame containing PM10 and PM2.5 amounts
        """

        _idx = ['feedstock', 'tillage_type']
