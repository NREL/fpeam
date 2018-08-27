
scenario_name = string(default='')

# modules to run
modules = force_list

# logging verbosity level
logger_level = option(CRITICAL, ERROR, WARNING, INFO, DEBUG, UNSET)

# file paths
project_path = string

# data paths
equipment = string
production = string
emission_factor = string(default='../data/inputs/emission_factor.csv')
fertilizer_distribution = string(default='../data/inputs/resource_distribution.csv')
fugitive_dust_emission_factor = string(default='../data/inputs/fugitive_dust_emission_factor.csv')
moisture_content = string(default='../data/inputs/moisture_content.csv')
nonroad_equipment = string(default='../data/inputs/nonroad_equipment.csv')
scc_code = string(default='../data/inputs/scc_code.csv')
transportation_graph = string(default='../data/inputs/transportation_graph.csv')
county_node = string(default='../data/inputs/county_node.csv')
