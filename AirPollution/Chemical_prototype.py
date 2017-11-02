# -*- coding: utf-8 -*-
"""

"""
import pandas as pd
# remove os once csv files are no longer needed
import os

# Nitro fertilizer emissions factors, Units: percent volatilized
nfert_ef = (1./100.) * pd.DataFrame({'nox': [0.79, 3.8, 3.5, 0.9, 0.79], 
                                     'nh3': [4.0, 1.91, 9.53, 15.8, 8.0]}, 
                                     index = ['aa', 'an', 'as', 'ur', 'ns'])

# Nitro fertilizer allocation, Units: kg specific fertilizer per kg total fertilizer
nfert_app = pd.DataFrame({'Corn': [0.3404, 0.0247, 0.0279, 0.2542, 0.3528],
                          'Corn stover': [0.3404, 0.0247, 0.0279, 0.2542, 0.3528],
                          'Wheat straw': [0.3404, 0.0247, 0.0279, 0.2542, 0.3528],
                          'Switchgrass': [0., 0., 0., 0., 1.],
                          'Sorghum stubble': [0.3404, 0.0247, 0.0279, 0.2542, 0.3528],
                          'Miscanthus': [0., 0., 0., 0., 1.],
                          'Residues': [0., 0., 0., 0., 1.],
                          'Whole tree': [0., 0., 0., 0., 1.]},
                            index = ['aa', 'an', 'as', 'ur', 'ns'])

# calculate NOx and NH3 emissions factors for each feedstock
# Units: kg pollutant per kg total N fertilizer
nfert_ems = pd.DataFrame({"nox_ef": nfert_app.multiply(nfert_ef['nox'],
                                                       axis = 'index').sum(axis = 'index'),
                          "nh3_ef": nfert_app.multiply(nfert_ef['nh3'],
                                                       axis = 'index').sum(axis = 'index')})
nfert_ems['crop'] = nfert_ems.index

# read in budget data for energy crops
budg_en = pd.read_csv(os.getcwd() + '\\input_data\\' +
                        'equip_budgets\\bdgtengy_20160114.csv')

# budget has CT, NT
budg_conv = pd.read_csv(os.getcwd() + '\\input_data\\' +
                        'equip_budgets\\bdgtconv_20151215.csv')

# pull out CT budget entries to create proxy entries for RT
budg_conv_append = budg_conv[budg_conv.till == 'CT']
# Re-label these entries as RT
budg_conv_append.loc[:,'till'] = 'RT'

# attach RT budget entries to original df containing CT and NT
budg_conv = budg_conv.append(budg_conv_append)
del(budg_conv_append)

# create master budget df with all crops
budg = budg_conv.append(budg_en)
del(budg_conv, budg_en)

# read in complete production data set
prod_dat = pd.read_csv(os.getcwd() + '\\input_data\\' +
                    'current_ag\\bc10602040prod_20160126.csv')
                    
# rename the prod column b/c prod is a built-in method for data frames
# prod calculates the product, btw
prod_dat = prod_dat.rename(columns = {"prod": "production"})

# join together the production and budget dfs for easier calculating
dat = budg.merge(prod_dat, on = ['crop', 'till', 'polyfrr'], how = 'outer')

# add columns: NOx and NH3 emission factors
dat = dat.merge(nfert_ems, on = 'crop', how = 'outer')

# add column: total N fertilizer by FIPS and feedstock
dat['nfert'] = dat.n_lbac.multiply(dat.harv, fill_value = 0) + \
                dat.n_lbdt.multiply(dat.production, fill_value = 0)

# add column: total VOC emissions from insecticide and herbicide application by FIPS
dat['voc'] = (0.9 * 0.835 * 0.907018474 / 2000.0) * \
               (dat.insc_lbac.multiply(dat.harv, fill_value = 0) + \
               dat.herb_lbac.multiply(dat.harv, fill_value = 0))

# add column: total NOx emissions from N fertilizer application by FIPS
dat['nox'] = dat.nfert.multiply(dat.nox_ef, fill_value = 0)

# add column: total NH3 emissions from N fertilizer application by FIPS
dat['nh3'] = dat.nfert.multiply(dat.nh3_ef, fill_value = 0)

# add in column for activity
dat['activity'] = 'Chem'

# clean up data table by keeping only relevant columns
dat = dat[['crop', 'till', 'bdgtyr', 'year', 'fips', 'harv', 'production', 'opertype', 'nox', 'nh3', 'voc']]

dat = dat[dat.crop.isin(list(nfert_app.columns))]