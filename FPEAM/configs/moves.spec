state_level_moves = boolean
moves_by_crop = boolean

feedstock_measure_type = string(default='harvested')


moves_database = string
moves_output_db = string
moves_db_user = string
moves_db_pass = string
moves_db_host = string

moves_path = string
moves_datafiles_path = string
mysql_binary = string
mysqldump_binary = string

transportation_graph = string(default='../data/inputs/transportation_graph.csv')
county_node = string(default='../data/inputs/county_nodes.csv')

vmt_short_haul = float

pop_short_haul = int


# fuel fraction
fuel_fraction = float_list()


# truck capacity
# C = conventional, A = Advanced
# Units = dry short tons/load
[truck_capacity]
[[CS]]
C = float
A = float

[[WS]]
C = float
A = float

[[SG]]
C = float
A = float

[[MS]]
C = float
A = float

[[CG]]
C = float
A = float

[[SS]]
C = float
A = float

[[FR]]
C = float
A = float

[[FW]]
C = float
A = float

# vehicle age distribution for MOVES runs
[age_distribution]
2015 = float_list()
2017 = float_list()
2022 = float_list()
2040 = float_list()

# fraction of VMT by road type
[vmt_fraction]
2 = float
3 = float
4 = float
5 = float

# Timespan for MOVES runs
[moves_timespan]
mo = option(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
bhr = option(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24)
ehr = option(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24)
d = option(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31)

[pollutant_dict]
NH3 = int
CO = int
NOX = int
PM10 = int
PM25 = int
SO2 = int
VOC = int
