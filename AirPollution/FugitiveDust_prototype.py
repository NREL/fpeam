import pandas as pd

# remove when csv no longer needed
import os

# conversion factor for converting pounds to metric tons - since the fugdust emission factor data input is in
# lbs/acre by default
convert_lb_to_mt = 0.907 / 2000.0

# read in table of fugdust emission factor input data for harvest and non-harvest activities.
# this is the default data to be used, which will be stored in the database and can be updated by users
fugdust_ef = pd.read_csv(os.getcwd() + '\\fugdust_input.csv')

# read in silt data table (stored in fpeam.state_road_data)
silt_table = pd.read_csv(os.getcwd() + '\\state_road_data.csv')

# read in complete production data set
prod_dat = pd.read_csv(os.getcwd() + '\\input_data\\' + 'current_ag\\bc10602040prod_20160126.csv')
# rename the prod column
prod_dat = prod_dat.rename(columns = {"prod": "production"})

# read in complete budget data set
budg_dat = pd.read_csv(os.getcwd() + '\\input_data\\equip_budgets\\bdgtconv_20151215.csv')

# create column containing the last letter of opertype code to classify each budget entry as either
# a crop ("C") or a residue ("R") operation - this will be used in allocating fugdust emissions between crops and
# residues for sorghum (stubble), corn (stover) and wheat (straw)
budg_dat['croptype'] = budg_dat.opertype.str[3]

# calculate horsepower-hours for each opertype
# fillna replaces all missing values with zeros - otherwise the entire calculation is filled with NaNs
budg_dat['hp_hrs'] = budg_dat.powr01_hpac.fillna(0) * budg_dat.time01_hrac.fillna(0) + \
                     budg_dat.powr02_hpac.fillna(0) * budg_dat.time02_hrac.fillna(0) + \
                     budg_dat.powr03_hpac.fillna(0) * budg_dat.time03_hrac.fillna(0)

# this sums the hp_hrs values within each group defined by the budget id, then calculates the PM10 allocation factor
# by dividing each individual hp_hrs value by the budget id group total
# tested calculation using BA.CT.01, math checked out
budg_dat['hp_hrs_alloc'] = budg_dat.groupby('bdgt_id').hp_hrs.apply(lambda x: x / float(x.sum()))

# factors for equation.
onfarm_truck_capacity = 15.0  # dt / load
weight = 32.01  # short tons - should this be in lbs? cf conversion factor
k25 = 0.15
k10 = 1.5
a25 = 0.9
a10 = 0.9
b25 = 0.45
b10 = 0.45
D = 1.0  # default value for on-farm distance traveled (in vehicle miles traveled)


# add in leading zeros to state FIPS codes where necessary
# it's either for loops or add redundant columns
prod_dat['lead_zeros'] = [len(str(fips)) for fips in prod_dat.fips]
prod_dat['st_fips'] = [str(fips)[0:2] for fips in prod_dat.fips]
prod_dat.st_fips[prod_dat.lead_zeros == 4] = [('0' + str(fips)[0]) for fips in prod_dat.fips[prod_dat.lead_zeros == 4]]
prod_dat.st_fips = prod_dat.st_fips.astype('int64')

dat = prod_dat.merge(fugdust_ef, on = ['crop', 'till'], how = 'outer').merge(silt_table, on = 'st_fips', how = 'outer')

# calculate pm10 by summing harvest + non-harvest + lime app
# harvest = crop x till x year x fips
# non-harvest = f(production, truck capacity, pct silt) + lime app
dat['pm10'] = dat.harv.multiply(dat.pm10_ef_mtac, fill_value = 0) + \
                dat.production / onfarm_truck_capacity * k10*D*(dat.uprsm_pct_silt/12.0)**a10 * (weight/3.0)**b10 * \
                convert_lb_to_mt

# calculate pm25 by crop x till x year x fips
dat['pm25'] = dat.harv.multiply(dat.pm25_ef_mtac, fill_value = 0) + \
                dat.production / onfarm_truck_capacity * k25*D*(dat.uprsm_pct_silt/12.0)**a25 * (weight/3.0)**b25 * \
                convert_lb_to_mt