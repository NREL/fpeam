scenario_name = string

moves_by_state = boolean
moves_by_crop = boolean

feedstock_measure_type = string(default='harvested')


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


vmt_short_haul = float

pop_short_haul = integer

hpmsv_type_id = integer
source_type_id = integer


# fuel fraction
avft = string(default='../data/inputs/avft.csv')


# fraction of VMT by road type
[vmt_fraction]
#2 = float
#3 = float
#4 = float
#5 = float

# Timespan for MOVES runs
#[moves_timespan]
#mo = option(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
#bhr = option(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24)
#ehr = option(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24)
#d = option(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31)

#[pollutant_dict]
#NH3 = integer
#CO = integer
#NOX = integer
#PM10 = integer
#PM25 = integer
#SO2 = integer
#VOC = integer
