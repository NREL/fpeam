
# run identifier; defaults to FPEAM scenario name
scenario_name = string()


### MOVES execution options

## use a single representative county for all counties in each state
moves_by_state = boolean(default=True)

## use a single representative county for each crop for all counties in each state
moves_by_state_and_feedstock = boolean(default=False)

## use existing results in MOVES output database or run MOVES for all counties
use_cached_results = boolean(default=True)

## production table identifier (feedstock_measure in production data)
feedstock_measure_type = string(default='production')

## if router is not used, assume 20 vmt per biomass production county
vmt_short_haul = float(default=20)

## population of combination short-haul trucks per trip
pop_short_haul = integer(default=1)

## vehicle category: combination trucks
hpmsv_type_id = integer(default=60)

## specific vehicle type: short-haul combination truck
source_type_id = integer(default=61)

## start year (equipment year #1)
year = integer(default='2017')

## feedstock loss factor dataset
feedstock_loss_factors = filepath(default='data/inputs/feedstock_loss_factors.csv')


### MOVES database connection options
moves_db_host = string(default='localhost')
moves_db_user = string(default='root')
moves_db_pass = string(default='root')
moves_database = string(default='movesdb20161117')
moves_output_db = string(default='moves_output_db')


### MOVES application options

## the moves version used only for human reference; it's ignored by MOVES
moves_version = string(default='MOVES2014b-20151028')

## this directory contains all input files created for MOVES runs
moves_datafiles_path = filepath(default='C:\MOVESdata', max_length=30)

## use this path to specify which version of MOVES should be run
moves_path = filepath(default='C:\MOVES2014b')


### MySQL options
mysql_binary = string(default='C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe')
mysqldump_binary = string(default='C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe')


### input files

## truck capacities for feedstock transportation
truck_capacity = filepath(default='data/inputs/truck_capacity.csv')

## fuel fraction by engine type
avft = filepath(default='data/inputs/avft.csv')

## production region to MOVES FIPS mapping
region_fips_map = filepath(default='data/inputs/region_fips_map.csv')


### Moves input options

## fraction of VMT by road type (must sum to 1)
[vmt_fraction]
rural_restricted = float(min=0, max=1, default=0.30)
rural_unrestricted = float(min=0, max=1, default=0.28)
urban_restricted = float(min=0, max=1, default=0.21)
urban_unrestricted = float(min=0, max=1, default=0.21)

## timespan(s)
[moves_timespan]
month = integer(1, 12, default=10)
day = integer(1, 31, default=5)
beginning_hour = integer(1, 24, default=7)
ending_hour = integer(1, 24, default=18)

# MOVES pollutant dictionary (pollutant name to pollutant ID)
[pollutant_dict]
NH3 = integer(default=30)
CO = integer(default=2)
NOX = integer(default=3)
PM10 = integer(default=100)
PM25 = integer(default=110)
SO2 = integer(default=31)
VOC = integer(default=87)
