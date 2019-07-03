
## run identifier
scenario_name = string

## project output directory
project_path = filepath

## modules to run
modules = force_list(default=list('emissionfactors', 'MOVES', 'NONROAD', 'fugitivedust'))

## logging verbosity level (CRITICAL, ERROR, WARNING, INFO, DEBUG, UNSET)
logger_level = option(CRITICAL, ERROR, WARNING, INFO, DEBUG, UNSET, default=INFO)

## use the router engine to calculate vmt by county
use_router_engine = boolean(default=True)

## data paths
equipment = filepath(default='data/equipment/bts16_equipment.csv')
production = filepath(default='data/production/production_2017_bc1060.csv')
feedstock_loss_factors = filepath(default='data/inputs/feedstock_loss_factors.csv')

## MOVES routing graph
transportation_graph = filepath(default='data/inputs/transportation_graph.csv')

## graph node locations
node_locations = filepath(default='data/inputs/node_locations.csv')

## data backfill flag
backfill = boolean(default=True)
