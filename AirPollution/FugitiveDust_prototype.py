# -*- coding: utf-8 -*-
"""
Created November 2 2017

Code snippet for calculating fugitive dust (PM10 and PM2.5) from harvest,
non-harvest and lime application.  Dust from on-farm transportation of
feedstock is not calculated.

"""

import pandas as pd

# @TODO remove when csv no longer needed
import os

# conversion factor for converting pounds to metric tons - since the fugdust
# emission factor data input is in lbs/acre by default
convert_lb_to_mt = 0.907 / 2000.0

# read in table of fugdust emission factor input data for harvest and
# non-harvest activities.  this is the default data to be used, which will be
# stored in the database and can be updated by users
fugdust_ef = pd.read_csv(os.getcwd() + '\\fugdust_input.csv')

# corn stover, wheat straw and sorghum stubble use the same fugdust emission
#  factors as do corn grain, wheat and sorghum respectively.  By default the
#  input data does not include those as separate entries.
# Duplicate the corn, wheat and sorghum entries and append them to fugdust_ef
# corn stover
fugdust_ef_stover = fugdust_ef[fugdust_ef['crop'] == 'Corn']
fugdust_ef_stover.crop = 'Corn stover'

# wheat straw
fugdust_ef_straw = fugdust_ef[fugdust_ef['crop'] == 'Wheat']
fugdust_ef_straw.crop = 'Wheat straw'

# sorghum stubble
fugdust_ef_stubble = fugdust_ef[fugdust_ef['crop'] == 'Sorghum']
fugdust_ef_stubble.crop = 'Sorghum stubble'

# stitch together original data frame and the three crop residue data frames
#  for one master emission factor df
fugdust_ef = fugdust_ef.append(fugdust_ef_stover).append(
    fugdust_ef_straw).append(fugdust_ef_stubble)

# read in silt data table (stored in fpeam.state_road_data)
silt_table = pd.read_csv(os.getcwd() + '\\state_road_data.csv')

# read in complete production data set
prod_dat = pd.read_csv(os.getcwd() + '\\input_data\\' +
                       'current_ag\\bc10602040prod_20160126.csv')
# rename the prod column
prod_dat = prod_dat.rename(columns = {"prod": "production"})

## generate state FIPS in prod_dat
# some county FIPS codes are four-digit, some are five
# to generate the state FIPS codes, pull out the first two digits of the
# five-digit FIPS codes and just the first digit of the four-digit codes
# it's either for loops or add redundant columns
prod_dat['fips_digits'] = [len(str(fips)) for fips in prod_dat.fips]
prod_dat['st_fips'] = [str(fips)[0:2] for fips in prod_dat.fips]
prod_dat.loc[(prod_dat['fips_digits'] == 4), 'st_fips'] = [str(fips)[0] \
                                               for fips in prod_dat.fips[
                                                   prod_dat.fips_digits == 4]]
prod_dat.st_fips = prod_dat.st_fips.astype('int64')

# read in complete budget data set
# eventually this df will need budget data for all crops of interest
budg_dat = pd.read_csv(os.getcwd() +
                       '\\input_data\\equip_budgets\\bdgtconv_20151215.csv')

# create column containing the last letter of opertype code to classify each
# budget entry as either a crop ("C") or a residue ("R") operation.
# this will be used in allocating fugdust emissions between crops and
# residues for sorghum (stubble), corn (stover) and wheat (straw)
budg_dat['croptype'] = budg_dat.opertype.str[3]

# use the croptype column to rename budget entries that correspond to corn
# stover, sorghum stubble and wheat straw
budg_dat.loc[(budg_dat['croptype'] == 'R') & (budg_dat['crop'] == 'Corn'),
             'crop'] = 'Corn stover'

budg_dat.loc[(budg_dat['croptype'] == 'R') & (budg_dat['crop'] == 'Sorghum'),
              'crop'] = 'Sorghum stubble'

budg_dat.loc[(budg_dat['croptype'] == 'R') & (budg_dat['crop'] == 'Wheat'),
             'crop'] = 'Wheat straw'

# calculate horsepower-hours for each opertype
# fillna replaces all missing values with zeros
# otherwise the entire calculation is filled with NaNs
budg_dat['hp_hrs'] = budg_dat.powr01_hpac.fillna(0) * \
                       budg_dat.time01_hrac.fillna(0) + \
                     budg_dat.powr02_hpac.fillna(0) * \
                       budg_dat.time02_hrac.fillna(0) + \
                     budg_dat.powr03_hpac.fillna(0) * \
                       budg_dat.time03_hrac.fillna(0)

# this sums the hp_hrs values within each group defined by the budget id, then
# calculates the PM10 allocation factor by dividing each individual hp_hrs
# value by the budget id group total.
# tested calculation using BA.CT.01, math checked out
budg_dat['hp_hrs_alloc'] = \
    budg_dat.groupby('bdgt_id').hp_hrs.apply(lambda x: x / float(x.sum()))

# merge the emission factors from fugdust_ef into budg_dat
# cheat a bit by dividing the budget into one budget for harvest activities
# and another for non-harvest activities
budg_dat_harv = budg_dat.loc[budg_dat.opertype.isin(('HRVR', 'HRVC'))]
budg_dat_nonharv = budg_dat.loc[budg_dat.opertype.isin(('ESTC', 'MNTR',
                                                        'MNTC'))]

# similarly divide the fugdust_ef into harvest and non-harvest data frames
fugdust_ef_harv = fugdust_ef.loc[fugdust_ef.source_category == 'Harvest']
fugdust_ef_nonharv = fugdust_ef.loc[fugdust_ef.source_category ==
                                    'Non-Harvest']

# merge by matching crop, till and budget year - ignore polyfrr
budg_dat_harv = budg_dat_harv.merge(fugdust_ef_harv, on = ['crop', 'till',
                                                           'bdgtyr'],
                                    how = 'outer')

# calculate pm10 emissions (lb per acre) from each opertype
# these values do NOT include pm10 from on-farm travel, which is calculated
# for each state after the production data is merged in
budg_dat_harv['pm10_lbac_alloc'] = budg_dat_harv.pm10_ef_lbac * \
                         budg_dat_harv.hp_hrs_alloc

# merge non-harvest dfs by matching crop, till and budget year
budg_dat_nonharv = budg_dat_nonharv.merge(fugdust_ef_nonharv, on = ['crop',
                                                                    'till',
                                                                    'bdgtyr'],
                                          how = 'outer')

# calculate pm10 emissions (lb per acre) from each opertype
# these values do NOT include pm10 from on-farm travel, which is calculated
# for each state after the production data is merged in
budg_dat_nonharv['pm10_lbac_alloc'] = budg_dat_nonharv.pm10_ef_lbac * \
                           budg_dat_nonharv.hp_hrs_alloc

# stitch together the harvest and non-harvest expanded budgets with pm10
budg_dat_fugdust = budg_dat_harv.append(budg_dat_nonharv)

# calculate PM2.5 emissions (lb per acre) as 20% by mass of PM10 emissions
budg_dat_fugdust['pm25_lbac_alloc'] = 0.20 * budg_dat_fugdust.pm10_lbac_alloc

# merge together the production data with state FIPS, the budget data with
# harvest and non-harvest PM10 and PM2.5 emissions (pounds per acre) and the
#  silt table with the silt information necessary to calculate PM10 and
# PM2.5 from on-farm travel
dat = prod_dat.merge(budg_dat_fugdust, on = ['crop', 'till', 'polyfrr'],
                     how = 'outer').merge(silt_table, on = 'st_fips',
                                          how = 'outer')

# calculate pm10 by multiplying the PM10 emissions factors (which include
# emissions from harvest, non-harvest and lime application activities) by
# harvested acres and adding PM10 from on-farm travel (also allocated between
# opertypes by horsepower-hours), then converting the sum to metric tons
dat['pm10'] = (dat.harv * dat.pm10_lbac_alloc) * convert_lb_to_mt

# calculate PM2.5 by multiplying the PM2.5 emissions (including emissions
# from harvest, non-harvest and lime application activities) by harvested
# acres and adding the PM2.5 from on-farm travel (also allocated between
# opertypes by horsepower-hours), then converting the sum to metric tons
dat['pm25'] = (dat.harv * dat.pm25_lbac_alloc) * convert_lb_to_mt