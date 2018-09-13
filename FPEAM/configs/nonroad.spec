scenario_name = string

nonroad_path = string
nonroad_project_path = string
nonroad_exe = string(default='NONROAD.exe')

nonroad_temp_min = float
nonroad_temp_max = float
nonroad_temp_mean = float

nonroad_database = string
nonroad_db_user = string
nonroad_db_pass = string
nonroad_db_host = string

feedstock_measure_type = string
time_resource_name = string

forestry_feedstock_names = force_list

# DOE lower heating value for diesel fuel
# also part of GREET Argonne model for conversion.
# units = mmBTU/gallon
diesel_lhv = float(default=0.12845)

# SF2 impact analysis nh3 emission factor for diesel fuel
# units = grams NH3/mmBTU diesel
diesel_nh3_ef = float(default=0.68)

# From EPA NONROAD Conversion Factors for Hydrocarbon Emission Components.
# default for diesel fuel
# Convert mass of thc to mass of voc
diesel_thc_voc_conversion = float(default=1.053)

# Convert pm10 to PM2.5
diesel_pm10topm25 = float(default=0.97)
