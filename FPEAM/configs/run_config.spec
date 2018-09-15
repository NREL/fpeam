
## run identifier
scenario_name = string

## project output directory
project_path = filepath

## start year (equipment year #1)
year = integer

## modules to run
modules = force_list(default=list('emissionfactors', 'MOVES', 'NONROAD', 'fugitivedust'))

## logging verbosity level (CRITICAL, ERROR, WARNING, INFO, DEBUG, UNSET)
logger_level = option(CRITICAL, ERROR, WARNING, INFO, DEBUG, UNSET, default=INFO)


## data paths
equipment = filepath(default='../data/equipment/bts16_equipment.csv')
production = filepath(default='../data/production/prod_2015_bc1060.csv')
