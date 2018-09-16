
# run identifier; defaults to FPEAM scenario name
scenario_name = string(default='')


### MOVES execution options

## use a single representative county for all counties in each state
moves_by_state = boolean

## use a single representative county for each crop for all counties in each state
moves_by_state_and_feedstock = boolean

## production table identifier (feedstock_measure in production data)
feedstock_measure_type = string

## annual vehicle miles traveled by combination short-haul trucks
vmt_short_haul = float(default=100)

## population of combination short-haul trucks per trip
pop_short_haul = integer(default=1)

## vehicle category: combination trucks
hpmsv_type_id = integer(default=60)

## specific vehicle type: short-haul combination truck
source_type_id = integer(default=61)

## start year (equipment year #1)
year = integer


### MOVES database connection options
moves_db_host = string
moves_db_user = string
moves_db_pass = string
moves_database = string
moves_output_db = string


### MOVES application options
moves_version = string
moves_path = filepath
moves_datafiles_path = filepath


### MySQL options
mysql_binary = string
mysqldump_binary = string


### input files

## MOVES routing graph
transportation_graph = filepath(default='../data/inputs/transportation_graph.csv')

## graph nodes representing each county
county_nodes = filepath(default='../data/inputs/county_nodes.csv')

## truck capacities for feedstock transportation
truck_capacity = filepath(default='../data/inputs/truck_capacity.csv')

## fuel fraction by engine type
avft = filepath(default='../data/inputs/avft.csv')

## production region to MOVES FIPS mapping
region_fips_map = filepath(default='../data/inputs/region_fips_map.csv')


### Moves input options

## fraction of VMT by road type (must sum to 1)
[vmt_fraction]
rural_restricted = float(min=0, max=1, default=0.30)
rural_unrestricted = float(min=0, max=1, default=0.28)
urban_restricted = float(min=0, max=1, default=0.21)
urban_unrestricted = float(min=0, max=1, default=0.21)

## timespan(s)
[moves_timespan]
months = int_list(1, 12, default=list(10, ))
days = int_list(1, 31, default=list(5, ))
beginning_hours = int_list(1, 24, default=list(7, ))
ending_hours = int_list(1, 24, default=list(18, ))

# MOVES pollutant dictionary (pollutant name to pollutant ID)
[pollutant_dict]
NH3 = integer(default=30)
CO = integer(default=2)
NOX = integer(default=3)
PM10 = integer(default=100)
PM25 = integer(default=110)
SO2 = integer(default=31)
VOC = integer(default=87)
