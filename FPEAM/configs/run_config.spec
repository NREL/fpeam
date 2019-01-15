
## run identifier
scenario_name = string

## project output directory
project_path = filepath

## modules to run
modules = force_list(default=list('emissionfactors', 'MOVES', 'NONROAD', 'fugitivedust'))

## logging verbosity level (CRITICAL, ERROR, WARNING, INFO, DEBUG, UNSET)
logger_level = option(CRITICAL, ERROR, WARNING, INFO, DEBUG, UNSET, default=INFO)


## data paths
equipment = filepath(default='')
production = filepath(default='')
feedstock_loss_factors = filepath(default='')
