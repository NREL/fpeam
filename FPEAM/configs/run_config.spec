
scenario_name = string

# modules to run
modules = force_list

# logging verbosity level
logger_level = option(CRITICAL, ERROR, WARNING, INFO, DEBUG, UNSET)

# file paths
project_path = string

# data paths
equipment = string
production = string
emission_factors = string(default='../data/inputs/emission_factors.csv')
resource_distribution = string(default='../data/inputs/resource_distribution.csv')
fugitive_dust_emission_factors = string(default='../data/inputs/fugitive_dust_emission_factors.csv')
moisture_content = string(default='../data/inputs/moisture_content.csv')
nonroad_equipment = string(default='../data/inputs/nonroad_equipment.csv')
scc_codes = string(default='../data/inputs/scc_codes.csv')
region_fips_maps = string(default='../data/inputs/region_fips_map.csv')
truck_capacity = string(default='../data/inputs/truck_capacity.csv')
