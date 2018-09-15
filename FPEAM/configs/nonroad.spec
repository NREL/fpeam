
## run identifier; defaults to FPEAM scenario name
scenario_name = string(default='')


### input data options

## production table row identifier (feedstock_measure in production data)
feedstock_measure_type = string

## equipment table row identifier (resource in equipment data)
time_resource_name = string(default='time')

## forest feedstocks have different allocation indicators
forestry_feedstock_names = str_list(default=list())


### input data files

## production region to NONROAD FIPS mapping
#region_fips_map = string(default='../data/inputs/region_fips_map.csv')

## state abbreviation to FIPS mapping
state_fips_map = filepath(default='../data/inputs/state_fips_map.csv')

## equipment name to NONROAD equipment name and SCC mapping
nonroad_equipment = string(default='../data/inputs/nonroad_equipment.csv')



### NONROAD database connection options
nonroad_database = string
nonroad_db_user = string
nonroad_db_pass = string
nonroad_db_host = string


### NONROAD application options
nonroad_path = filepath
nonroad_project_path = filepath
nonroad_exe = string(default='NONROAD.exe')


### NONROAD input options

## temperature range
nonroad_temp_min = float(default=50.0)
nonroad_temp_max = float(default=68.8)
nonroad_temp_mean = float(default=60.0)

## lower heating value for diesel fuel (mmBTU/gallon) (DOE)
diesel_lhv = float(default=0.12845)

## nh3 emission factor for diesel fuel (grams NH3/mmBTU diesel) (SF2 impact analysis)
diesel_nh3_ef = float(default=0.68)

## VOC conversion factor (EPA NONROAD Conversion Factors for Hydrocarbon Emission Components)
diesel_thc_voc_conversion = float(default=1.053)

## pm10 to PM2.5 conversion factor
diesel_pm10topm25 = float(default=0.97)
