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

    def get_voc(self, resource, voc_content_percent, voc_evaporation_rate):
        """
        Calculate evaporative VOC emissions for <resource>.

        :param resource: [string] equipment resource value
        :param voc_content_percent: [float] Percent VOC (lbs VOC / lb active ingredient)
        :param voc_evaporation_rate: [float] Rate of VOC evaporation
        :return: [dict] {<resource>_voc: DataFrame[production row_id x voc}
        """

        # create column selectors
        _idx = ['feedstock', 'tillage_type', 'equipment_group']
        _prod_columns = ['row_id', ] + _idx + ['crop_amount']
        _equip_columns = _idx + ['rate', ]

        # create row selectors
        _equip_rows = self.equipment.resource == resource

        # combine production and equipment
        _df = self.production[_prod_columns].merge(self.equipment[_equip_rows][_equip_columns],
                                                   on=_idx)

        # calculate VOCs
        _df.eval('voc = @voc_evaporation_rate * @voc_content_percent * crop_amount * rate',
                 inplace=True)

        # clean up DataFrame
        _df = _df[['row_id', 'voc']].set_index('row_id', drop=True)

        return {'%s_voc' % resource: _df}

    def other(self):
        """
        Calculate non-VOC chemical emissions.

        :return: [DataFrame]
        """

        raise NotImplementedError

        #
        # #
        #
        # # combine budget and production data
        # _output_df = self.equipment.merge(self.production,
        #                                   on=['feedstock', 'tillage_type', 'equipment_group'],
        #                                   how='outer')
        #
        # # add emission factors
        # _output_df.merge(self.fertilizer_distribution, on='feedstock', how='outer')
        #
        # # add column: total N fertilizer by FIPS and feedstock
        # #   (n lb/acre * harvest)
        # # + (n lb/dt   * production)
        #
        # assert 1
        #
        # _output_df['nfert'] = _output_df.n_lbac.multiply(_output_df.harv, fill_value=0) + _output_df.n_lbdt.multiply(_output_df.production, fill_value=0)
        #
        # # add column: total VOC emissions from insecticide and herbicide
        # # application by FIPS
        #
        # # huntley
        # _output_df['voc'] = (voc_evaporation_rate
        #                      * voc_content_percent
        #                      * self.conversions['tonne']['ton']
        #                      * self.conversions['ton']['pound'])\
        #     * (_output_df.insc_lbac.multiply(_output_df.harv, fill_value=0)
        #         + _output_df.herb_lbac.multiply(_output_df.harv, fill_value=0))
        # #   (lbs VOC/acre)
        # # * (lbs active/lbs VOC)
        # # * (lbs VOC/lbs active)
        # # * (mt/lbs)
        # # = mt VOC
        #
        # # emissions = harvested acres * lbs/acre * Evaporation rate * VOC content (lbs VOC / lb active ingridient) * conversion from lbs to mt.
        # # emissions = total VOC emissions (lbs VOC).
        # # total_harv_ac = total harvested acres. (acres)
        # # pest.EF = lbs VOC/acre.
        # # .9 =  evaporation rate. (lbs active/lbs VOC)
        # # .835 = voc content. lbs VOC / lb active ingridient.
        # # (acres) * (lbs VOC/acre) * (lbs active/lbs VOC) * (lbs VOC/lbs active) * (mt/lbs) = mt VOC
        #
        # # calculate NOx and NH3 emissions factors for each feedstock
        # # Units: kg pollutant per kg total N fertilizer
        # self.nfert_ems = pd.DataFrame({"nox_ef":
        #                                self.fertilizers.multiply(self.emission_factors['nox'],
        #                                                          axis='index').sum(axis='index'),
        #                                "nh3_ef":
        #                                self.fertilizers.multiply(self.emission_factors['nh3'],
        #                                                          axis='index').sum(axis='index')})
        # self.nfert_ems['crop'] = self.nfert_ems.index
        #
        # # add column: total NOx emissions from N fertilizer application by FIPS
        # _output_df['nox'] = _output_df.nfert.multiply(_output_df.nox_ef, fill_value=0)
        #
        # # add column: total NH3 emissions from N fertilizer application by FIPS
        # _output_df['nh3'] = _output_df.nfert.multiply(_output_df.nh3_ef, fill_value=0)
        #
        # # add in column for activity
        # _output_df['source_category'] = 'Chem'
        #
        # return _output_df

    def run(self):
        """
        Execute all calculations.

        :return: [bool] True on success
        """

        _voc_content_percent = self.config.as_float('voc_content_percent')
        _voc_evaporation_rate = self.config.as_float('voc_evaporation_rate')

        for _resource in ['insecticide', 'herbacide']:
            self.emissions.append(self.get_voc(resource=_resource,
                                               voc_evaporation_rate=_voc_evaporation_rate,
                                               voc_content_percent=_voc_content_percent))

        self.status = 'complete'

    def summarize(self):
        pass
