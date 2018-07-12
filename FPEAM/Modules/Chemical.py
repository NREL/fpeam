# -*- coding: utf-8 -*-
from os import path
from Module import Module
from FPEAM import (utils, IO)
LOGGER = utils.logger(name=__name__)


class Chemical(Module):
    """Base class to manage execution of pollutants calculated from
    emission factors"""

    # @TODO: remove _inputs
    _inputs = """- equipment: equipment budgets
                 - production: crop production data
                 - resource_distribution: defines the distribution of resource 
                 subtypes (specific chemicals) for each resource
                 - emission_factors: all pollutant emission factors by 
                 resource type and subtype (lb pollutant/lb resource)"""

    def __init__(self, config, equipment, production, resource_distribution,
                 emission_factors,
                 **kvals):
        """
        :param config [ConfigObj] configuration options
        :param equipment: [DataFrame] equipment group
        :param production: [DataFrame] production values
        :param resource_distribution: [DataFrame] Resource subtype
        distribution (fraction, unitless) by feedstock
        :param emission_factors: [DataFrame] Emission factors for each
        resource and resource subtype (lb pollutant/lb resource)
        """

        # init parent
        super(Chemical, self).__init__(config=config)

        # init properties
        self.emissions = []
        self.equipment = equipment
        self.production = production

        # Emissions factors, Units: lb pollutant/lb resource
        self.emission_factors = emission_factors

        # Resource subtype distribution, Units: unitless fraction
        self.resource_distribution = resource_distribution

        # merge emissions factors and resource subtype distribution
        # dataframes by matching resource and resource subtype
        _factors_merge = self.resource_distribution.merge(
            self.emission_factors, on = ['resource',
                                         'resource_subtype'])

        # calculate overall rate as the product of the resource subtype
        # distributions and the subtype-specific emission factors
        _factors_merge.eval('overall_rate = distribution * rate',
                            inplace = True)

        # sum emissions factors within unique combinations of
        # feedstock-resource-pollutant to generate overall factors that will
        #  convert resource mass to pollutant mass
        self.overall_factors = _factors_merge.groupby(['feedstock',
                                                       'resource',
                                                       'pollutant']).sum()

        # convert the indexes created by groupby back into regular columns
        # for further merging with equipment, production
        self.overall_factors.reset_index(level = ['feedstock',
                                                  'resource',
                                                  'pollutant'],
                                         inplace = True)


    def get_emissions(self, resource):
        """
        Calculate all emissions from <resource> for which a subtype
        distribution and emissions factors are provided.

        :param resource: [string] resource value from equipment
        :return: [dict] {<resource>_voc: DataFrame[production row_id x voc}
        """

        # create column selectors
        _idx = ['feedstock', 'tillage_type', 'equipment_group']
        _prod_columns = ['row_id', 'region'] + _idx + ['crop_amount']
        _equip_columns = _idx + ['rate', ]
        _factors_columns = ['feedstock', 'resource', 'overall_rate',
                            'pollutant']

        # create row selectors
        _equip_rows = self.equipment.resource == resource & \
                      self.equipment.crop_measure == 'harvested'
        _factors_rows = self.overall_factors.resource == resource

        # combine production and equipment and overall factors
        _df = self.production[_prod_columns].merge(self.equipment[
                                                       _equip_rows][
                                                       _equip_columns],
                                                   on = _idx).merge(
            self.overall_factors[_factors_columns][_factors_rows],
            on = ['feedstock', 'resource'])

        # calculate emissions
        _df.eval('pollutant_amount = overall_factor * crop_amount * rate',
                 inplace = True)

        # clean up DataFrame
        _df = _df[['row_id', 'pollutant_amount']].set_index('row_id',
                                                            drop = True)

        # @TODO add column with source category - maybe defined from
        # user-provided argument

        return {'%s' % resource: _df}

    def run(self):
        """
        Execute all calculations.

        :return: [bool] True on success
        """

        # generate resource list from unique entries in equipment,
        # resource_distribution and emission_factors
        _resource_list = set(self.equipment.resource.unique()) & \
                         set(self.emission_factors.resource.unique()) & \
                         set(self.resource_distribution.resource.unique())

        for _resource in _resource_list:
            self.emissions.append(self.get_emissions(resource = _resource))

        self.status = 'complete'

    def summarize(self):
        pass
