# -*- coding: utf-8 -*-
"""

"""
import pandas as pd

# @todo remove os once csv files are no longer needed
import os

class Chemical:

    def __init__(self):

        # Nitro fertilizer emissions factors, Units: percent volatilized
        # @todo read in default or user-defined data
        self.nfert_ef = (1./100.) * pd.DataFrame({'nox': [0.79, 3.8, 3.5,
                                                          0.9, 0.79],
                                                  'nh3': [4.0, 1.91, 9.53,
                                                          15.8, 8.0]},
                                                 index = ['aa', 'an', 'as',
                                                          'ur', 'ns'])

        # Nitro fertilizer allocation,  Units: kg specific fertilizer per kg
        #  total fertilizer
        # @todo read in default or user-defined data
        self.nfert_app = pd.DataFrame({'Corn': [0.3404, 0.0247, 0.0279,
                                                0.2542, 0.3528],
                                       'Corn stover': [0.3404, 0.0247, 0.0279,
                                                       0.2542, 0.3528],
                                       'Wheat straw': [0.3404, 0.0247, 0.0279,
                                                       0.2542, 0.3528],
                                       'Switchgrass': [0., 0., 0.,
                                                       0., 1.],
                                       'Sorghum stubble': [0.3404, 0.0247,
                                                           0.0279,
                                                           0.2542, 0.3528],
                                       'Miscanthus': [0., 0., 0.,
                                                      0., 1.],
                                       'Residues': [0., 0., 0.,
                                                    0., 1.],
                                       'Whole tree': [0., 0., 0.,
                                                      0., 1.]},
                                      index = ['aa', 'an', 'as',
                                               'ur', 'ns'])

        # calculate NOx and NH3 emissions factors for each feedstock
        # Units: kg pollutant per kg total N fertilizer
        self.nfert_ems = pd.DataFrame({"nox_ef":
                                           self.nfert_app.multiply(
                                               self.nfert_ef['nox'],
                                               axis = 'index').sum(axis =
                                                                     'index'),
                                       "nh3_ef": self.nfert_app.multiply(
                                           self.nfert_ef['nh3'],
                                           axis = 'index').sum(axis =
                                                                'index')})
        self.nfert_ems['crop'] = self.nfert_ems.index

        # read in budget data for energy crops
        # @todo read in default or user-defined data
        budg_en = pd.read_csv(os.getcwd() + '\\input_data\\' +
                                'equip_budgets\\bdgtengy_20160114.csv')

        # budget has CT, NT
        # @todo read in default or user-defined data
        budg_conv = pd.read_csv(os.getcwd() + '\\input_data\\' +
                                'equip_budgets\\bdgtconv_20151215.csv')

        # pull out CT budget entries to create proxy entries for RT
        budg_conv_append = budg_conv[budg_conv.till == 'CT']
        # Re-label these entries as RT
        budg_conv_append.loc[:,'till'] = 'RT'

        # attach RT budget entries to original df containing CT and NT
        self.budg_conv = budg_conv.append(budg_conv_append)

        # create master budget df with all crops
        self.budg = budg_conv.append(budg_en)

        # read in complete production data set
        # @todo read in default or user-defined data
        self.prod_dat = pd.read_csv(os.getcwd() + '\\input_data\\' +
                                    'current_ag\\bc10602040prod_20160126.csv')

        # rename the prod column b/c prod is a built-in method for data frames
        # prod calculates the product, btw
        self.prod_dat = self.prod_dat.rename(columns = {"prod": "production"})

    def get_chemical_emissions(self):

        # join together the production and budget dfs for easier calculating
        output_df = self.budg.merge(self.prod_dat,
                                    on = ['crop', 'till', 'polyfrr'],
                                    how = 'outer').merge(self.nfert_ems,
                                                         on = 'crop',
                                                         how = 'outer')

        # add column: total N fertilizer by FIPS and feedstock
        output_df['nfert'] = output_df.n_lbac.multiply(output_df.harv,
                                                       fill_value = 0) + \
                             output_df.n_lbdt.multiply(output_df.production,
                                                       fill_value = 0)

        # add column: total VOC emissions from insecticide and herbicide
        # application by FIPS
        output_df['voc'] = (0.9 * 0.835 * 0.907018474 / 2000.0) * \
                       (output_df.insc_lbac.multiply(output_df.harv,
                                                     fill_value = 0) + \
                       output_df.herb_lbac.multiply(output_df.harv,
                                                    fill_value = 0))

        # add column: total NOx emissions from N fertilizer application by FIPS
        output_df['nox'] = output_df.nfert.multiply(output_df.nox_ef,
                                                    fill_value = 0)

        # add column: total NH3 emissions from N fertilizer application by FIPS
        output_df['nh3'] = output_df.nfert.multiply(output_df.nh3_ef,
                                                    fill_value = 0)

        # add in column for activity
        output_df['source_category'] = 'Chem'

        return output_df