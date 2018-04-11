# -*- coding: utf-8 -*-

from Module import Module


class Chemical(Module):
    """Base class to manage execution of chemical emissions"""

    _inputs = """- equipment budgets
                 - crop production data
                 - nfert_ef (table of NOx and NH3 emission factors by N fertilizer type)
                 - nfert_app (table of N fertilizer allocations by crop)"""

    def __init__(self, budget, production, fertilizers, emission_factors):
        """
        :param budget: [DataFrame]
        :param production: [DataFrame]
        :param fertilizers: [DataFrame] Nitrogen fertilizer allocation in units kg specific
                                        fertilizer per kg
        :param emission_factors: [DataFrame] Nitrogen fertilizer emissions factors in units
                                             percent volatilized
        """
        # init parent
        super(Module, self).__init__()

        # init properties
        self.budget = budget
        self.production = production

        # Nitro fertilizer emissions factors, Units: percent volatilized
        self.emission_factors = emission_factors

        # Nitro fertilizer allocation,  Units: kg specific fertilizer per kg
        #  total fertilizer
        self.fertilizers = fertilizers

        # calculate NOx and NH3 emissions factors for each feedstock
        # Units: kg pollutant per kg total N fertilizer
        self.nfert_ems = pd.DataFrame({"nox_ef":
                                       self.fertilizers.multiply(self.emission_factors['nox'],
                                                                 axis='index').sum(axis='index'),
                                       "nh3_ef":
                                       self.fertilizers.multiply(self.emission_factors['nh3'],
                                                                 axis='index').sum(axis='index')})
        self.nfert_ems['crop'] = self.nfert_ems.index

    def insecticide_voc(self, x, voc_content_percent=0.834, voc_evaporation_rate=0.9):
        """
        Calculate evaporative VOC emissions for applied insectides.

        :param x: [DataFrame]
        :param voc_content_percent: [float] Percent VOC (lbs VOC / lb active ingredient)
        :param voc_evaporation_rate: [float] Rate of VOC evaporation
        :return: [DataFrame]
        """

        raise NotImplementedError

    def fertilizer_voc(self, x, ):
        return x.n_lbac.multiply(x.harv, fill_value=0) +\
               x.n_lbdt.multiply(x.production, fill_value=0)

    def get_chemical_emissions(self, voc_content_percent=0.834, voc_evaporation_rate=0.9):
        """
        Calculate chemical emissions for applied insectides.

        :param voc_content_percent: [float] percent lbs VOC/lb active ingredient; default 0.834 from
                                            Huntley 2015 revision of 2011 NEI technical support
                                            document @TODO: add specific reference
        :param voc_evaporation_rate: [float] percent lbs active/lbs VOC; default 0.9 (EPA
                                             reccomendations from emmissions inventory improvement
                                              program guidance @TODO: add specific reference
        :return: [DataFrame]
        """

        # join together the production and budget dfs for easier calculating
        _output_df = self.budget.merge(self.production,
                                       on=['crop', 'till', 'polyfrr'],
                                       how='outer').merge(self.nfert_ems, on='crop', how='outer')

        # add column: total N fertilizer by FIPS and feedstock
        _output_df['nfert'] = _output_df.n_lbac.multiply(_output_df.harv, fill_value=0)\
            + _output_df.n_lbdt.multiply(_output_df.production, fill_value=0)

        # add column: total VOC emissions from insecticide and herbicide
        # application by FIPS

        # huntley
        _output_df['voc'] = (voc_evaporation_rate
                             * voc_content_percent
                             * self.conversions['tonne']['ton']
                             * self.conversions['ton']['pound'])\
            * (_output_df.insc_lbac.multiply(_output_df.harv, fill_value=0)
                + _output_df.herb_lbac.multiply(_output_df.harv, fill_value=0))
        #   (lbs VOC/acre)
        # * (lbs active/lbs VOC)
        # * (lbs VOC/lbs active)
        # * (mt/lbs)
        # = mt VOC

        # emissions = harvested acres * lbs/acre * Evaporation rate
        # * VOC content (lbs VOC / lb active ingridient) * conversion from lbs to mt.
        # emissions = total VOC emissions (lbs VOC).
        # total_harv_ac = total harvested acres. (acres)
        # pest.EF = lbs VOC/acre.
        # .9 =  evaporation rate. (lbs active/lbs VOC)
        # .835 = voc content. lbs VOC / lb active ingridient.
        # (acres) * (lbs VOC/acre) * (lbs active/lbs VOC) * (lbs VOC/lbs active) * (mt/lbs) = mt VOC

        # add column: total NOx emissions from N fertilizer application by FIPS
        _output_df['nox'] = _output_df.nfert.multiply(_output_df.nox_ef, fill_value=0)

        # add column: total NH3 emissions from N fertilizer application by FIPS
        _output_df['nh3'] = _output_df.nfert.multiply(_output_df.nh3_ef, fill_value=0)

        # add in column for activity
        _output_df['source_category'] = 'Chem'

        return _output_df

    def __str__(self):
        return self


if __name__ == '__main__':
    import os

    import pandas as pd

    emission_factors = (1. / 100.) * pd.DataFrame({'nox': [0.79, 3.8, 3.5, 0.9, 0.79],
                                                   'nh3': [4.0, 1.91, 9.53, 15.8, 8.0]},
                                                  index=['aa', 'an', 'as', 'ur', 'ns'])

    fertilizers = pd.DataFrame({'Corn': [0.3404, 0.0247, 0.0279, 0.2542, 0.3528],
                                'Corn stover': [0.3404, 0.0247, 0.0279, 0.2542, 0.3528],
                                'Wheat straw': [0.3404, 0.0247, 0.0279, 0.2542, 0.3528],
                                'Switchgrass': [0., 0., 0., 0., 1.],
                                'Sorghum stubble': [0.3404, 0.0247, 0.0279, 0.2542, 0.3528],
                                'Miscanthus': [0., 0., 0., 0., 1.],
                                'Residues': [0., 0., 0., 0., 1.],
                                'Whole tree': [0., 0., 0., 0., 1.]},
                               index=['aa', 'an', 'as', 'ur', 'ns'])

    # set fpaths
    fpath_budget_energy = os.path.join(os.getcwd(),
                                       'input_data',
                                       'equip_budgets',
                                       'bdgtengy_20160114.csv')
    fpath_budget_conventional = os.path.join(os.getcwd(),
                                             'input_data',
                                             'equip_budgets',
                                             'bdgtconv_20151215.csv')

    # load crop budgets
    budg_en = pd.read_csv(fpath_budget_energy)
    budg_conv = pd.read_csv(fpath_budget_conventional)

    # budget has CT, NT
    # @todo read in default or user-defined data

    # backfill RT with CT budget entries to create proxy entries for RT
    budg_conv_append = budg_conv[budg_conv.till == 'CT']
    # Re-label these entries as RT
    budg_conv_append.loc[:, 'till'] = 'RT'

    # attach RT budget entries to original df containing CT and NT
    budg_conv = budg_conv.append(budg_conv_append)

    # create master budget df with all crops
    budget = budg_conv.append(budg_en)

    # read in complete production data set
    # @todo read in default or user-defined data
    production_fpath = os.path.join(os.getcwd(),
                                    'input_data',
                                    'current_ag',
                                    'bc10602040prod_20160126.csv')
    production = pd.read_csv(production_fpath)
    # rename the prod column b/c prod is a built-in method for data frames
    production = production.rename(columns={"prod": "production"})

    C = Chemical(budget=budget,
                 production=production,
                 fertilizers=fertilizers,
                 emission_factors=emission_factors)

    C.get_chemical_emissions()
