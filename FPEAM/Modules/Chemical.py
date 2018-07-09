# -*- coding: utf-8 -*-
from os import path
from Module import Module
from FPEAM import (utils, IO)
LOGGER = utils.logger(name=__name__)


class Chemical(Module):
    """Base class to manage execution of chemical emissions"""

    # @TODO: remove _inputs
    _inputs = """- equipment: equipment budgets
                 - production: crop production data
                 - emission_factors (previously nfert_ef): NOx and NH3 emission factors by N fertilizer type
                 - fertilizer_distribution (previously nfert_app): N fertilizer allocations by crop"""

    def __init__(self, config, equipment, production, fertilizer_distribution, emission_factors,
                 **kvals):
        """
        :param config [ConfigObj] configuration options
        :param equipment: [DataFrame] equipment group
        :param production: [DataFrame] production values
        :param fertilizer_distribution: [DataFrame] Nitrogen fertilizer allocation in units
                                        kg specific fertilizer per kg
        :param emission_factors: [DataFrame] Nitrogen fertilizer emissions factors in units
                                             percent volatilized
        """

        # init parent
        super(Chemical, self).__init__(config=config)

        # init properties
        self.emissions = []
        self.equipment = equipment
        self.production = production

        # Nitro fertilizer emissions factors, Units: percent volatilized
        self.emission_factors = emission_factors

        # Nitro fertilizer allocation, Units: kg specific fertilizer per kg
        #  total fertilizer
        self.fertilizer_distribution = fertilizer_distribution

    def get_emissions(self, resource, factors):
        """
        Calculate evaporative VOC emissions for <resource>.

        :param resource: [string] equipment resource value
        :param factors: [list] factors
        :return: [dict] {<resource>_voc: DataFrame[production row_id x voc}
        """

        # expand factors
        _final_factor = 1
        for _factor in factors:
            _final_factor *= _factor

        # create column selectors
        _idx = ['feedstock', 'tillage_type', 'equipment_group']
        _prod_columns = ['row_id', ] + _idx + ['crop_amount']
        _equip_columns = _idx + ['rate', ]

        # create row selectors
        _equip_rows = self.equipment.resource == resource

        # combine production and equipment  # @TODO: filtered by crop_measure == 'harvested'
        _df = self.production[_prod_columns].merge(self.equipment[_equip_rows][_equip_columns],
                                                   on=_idx)

        # calculate VOCs
        _df.eval('voc = @_final_factor * crop_amount * rate',
                 inplace=True)

        # clean up DataFrame
        _df = _df[['row_id', 'voc']].set_index('row_id', drop=True)

        return {'%s' % resource: _df}

    def run(self):
        """
        Execute all calculations.

        :return: [bool] True on success
        """

        _voc_content_percent = self.config.as_float('voc_content_percent')
        _voc_evaporation_rate = self.config.as_float('voc_evaporation_rate')

        for _resource in ['insecticide', 'herbicide']:
            self.emissions.append(self.get_emissions(resource=_resource, factors=[_voc_evaporation_rate,
                                                                                  _voc_content_percent]))

        self.status = 'complete'

    def summarize(self):
        pass
