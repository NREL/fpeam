# -*- coding: utf-8 -*-

from .Module import Module
from .. import utils
LOGGER = utils.logger(name=__name__)


class EmissionFactors(Module):
    """Base class to manage execution of pollutants calculated from emission factors"""

    def __init__(self, config, equipment, production, resource_distribution,
                 emission_factors, **kvals):
        """
        :param config [ConfigObj] configuration options
        :param equipment: [DataFrame] equipment group
        :param production: [DataFrame] production values
        :param resource_distribution: [DataFrame] Resource subtype distribution
                                      (fraction, unit-less) by feedstock
        :param emission_factors: [DataFrame] Emission factors for each
                                 resource and resource subtype (lb pollutant/lb resource)
        """

        # init parent
        super(EmissionFactors, self).__init__(config=config)

        # init properties
        self.emissions = []
        self.equipment = equipment
        self.production = production

        # Emissions factors, Units: lb pollutant/lb resource
        self.emission_factors = emission_factors

        # Resource subtype distribution, Units: unit-less fraction
        self.resource_distribution = resource_distribution

        # Selector for the crop amount that scales emission factors
        self.feedstock_measure_type = config.get('feedstock_measure_type')

        # merge emissions factors and resource subtype distribution
        # dataframes by matching resource and resource subtype
        _factors_merge = self.resource_distribution.merge(self.emission_factors,
                                                          on=['resource', 'resource_subtype'])

        # calculate overall rate as the product of the resource subtype
        # distributions and the subtype-specific emission factors
        _factors_merge.eval('overall_rate = distribution * rate', inplace=True)

        # sum emissions factors within unique combinations of
        # feedstock-resource-pollutant to generate overall factors that will
        #  convert resource mass to pollutant mass
        self.overall_factors = _factors_merge.groupby(['feedstock',
                                                       'resource',
                                                       'pollutant'],
                                                      as_index=False).sum()

    def get_emissions(self):
        """
        Calculate all emissions from <resource> for which a subtype
        distribution and emissions factors are provided.

        :return: [DataFrame] pollutant amounts
        """

        # create column selectors
        _idx = ['feedstock', 'tillage_type', 'equipment_group']
        _prod_columns = ['row_id'] + _idx + ['feedstock_amount']
        _equip_columns = ['row_id'] + _idx + ['rate']
        _factors_columns = ['feedstock', 'resource', 'overall_rate',
                            'pollutant']

        # create row selectors
        _prod_rows = self.production.feedstock_measure == self.feedstock_measure_type

        # combine production and equipment and overall factors
        _df = self.production[_prod_rows][_prod_columns]\
            .merge(self.equipment[_equip_columns], on=_idx, suffixes=['_prod', '_equip'])\
            .merge(self.overall_factors[_factors_columns], on=['feedstock', 'resource'])

        # calculate emissions
        _df.eval('pollutant_amount = overall_factor * feedstock_amount * rate', inplace=True)

        # clean up DataFrame
        _df = _df[['row_id_prod', 'row_id_equip', 'resource',
                   'resource_subtype', 'pollutant_amount']].set_index('row_id_prod', drop=True)

        return _df

    def run(self):
        """
        Execute all calculations.

        :return: [DataFrame] pollutant amounts
        """

        _results = None
        _status = self.status

        try:
            _results = self.get_emissions()
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
