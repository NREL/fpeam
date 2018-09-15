# run MOVES by state
moves_by_state = boolean

moves_by_state_and_feedstock = boolean

feedstock_measure_type = string

# database connection
moves_database = string
moves_output_db = string
moves_db_user = string
moves_db_pass = string
moves_db_host = string

moves_version = string

moves_path = string
moves_datafiles_path = string
mysql_binary = string
mysqldump_binary = string

transportation_graph = string(default='../data/inputs/transportation_graph.csv')
county_nodes = string(default='../data/inputs/county_nodes.csv')
truck_capacity = string(default='../data/inputs/truck_capacity.csv')

# fuel fraction
avft = string(default='../data/inputs/avft.csv')

vmt_short_haul = float(default=100)
pop_short_haul = integer(default=1)
hpmsv_type_id = integer(default=60)
source_type_id = integer(default=61)

# fraction of VMT by road type
[vmt_fraction]
rural_restricted = float(min=0, max=1, default=0.30)
rural_unrestricted = float(min=0, max=1, default=0.28)
urban_restricted = float(min=0, max=1, default=0.21)
urban_unrestricted = float(min=0, max=1, default=0.21)

# Timespan for MOVES runs
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
