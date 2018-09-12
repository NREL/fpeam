# Introduction

The Feedstock Production Emissions to Air Model (FPEAM) calculates spatially explicit inventories of criteria air pollutants and precursors generated from agricultural and transportation activities associated with the production and supply of biomass feedstocks for renewable energy generation. FPEAM was originally developed to calculate air pollutants as part of the 2016 update to the Billion Ton Study (BTS). For this version of FPEAM, the code base has been substantially refactored and streamlined to provide increased flexibility around biomass production scenario definitions, including what activities and pollutants are included in the calculations and at what spatial scale. This document describes the FPEAM code base and default input files bundled with the beta model release.

FPEAM calculations are organized into semi-independent modules, listed in the first table below along with the activities and pollutants included by default in each module. The EmissionFactors module is unique in that it can be used to calculate any pollutant from any activity, if sufficient input data is provided. In particular, users have the option of using the EmissionFactors module to replace the MOVES and/or NONROAD modules with emissions factors for agricultural equipment and on-road vehicle use. The EmissionFactors module can also be used to calculate pollutants from additional activities, such as non-nitrogen fertilizer application.

A full list of the default pollutants calculated by FPEAM is listed in the second table below. Additional pollutants may also be calculated from user-provided input data using the EmissionFactors module. At this stage of development calculating additional pollutants from either the NONROAD or MOVES modules is not allowed for in the model but this functionality can be added in the future if there is demand.

The structure and function of each module, and the module-specific input data required to run each module, is described further in subsequent sections.

TABLE: Available FPEAM modules.

| Module | Default pollutants calculated | Default activities included |
| :----- | :-------------------: | :------------------ |
| MOVES | All | Off-farm, on-road transportation of biomass to biorefineries |
| NONROAD | All | On-farm use of agricultural equipment |
| EmissionFactors | VOC, NH<sub>3</sub>, NO<sub>x</sub>, others | Nitrogen fertilizer application; pesticide and herbicide application; other activities as data is available |
| FugitiveDust | PM<sub>2.5</sub>, PM<sub>10</sub> | On-farm use of agricultural equipment |

TABLE: Default list of pollutants calculated by FPEAM.

| Pollutant name | Description |
| :------------: | :---------- |
| CO | Criteria air pollutant |
| NH<sub>3</sub> | Criteria air pollutant precursor|
| NO<sub>x</sub> | Criteria air pollutant |
| SO<sub>2</sub> | Criteria air pollutant |
| VOC |  Criteria air pollutant precursor |
| PM<sub>2.5</sub> | Criteria air pollutant |
| PM<sub>10</sub> | Criteria air pollutant | 

# Input and Output Data

The equipment and feedstock production input datasets described in the next sections are used by all FPEAM modules and provide the basic format and identification variables for the FPEAM outputs. A default for each dataset described in this section is provided with the FPEAM code base and can be used to run feedstock production scenarios from the 2016 BTS update. Provided the data format is preserved, these datasets may be altered, expanded or replaced to run custom model scenarios. Additional input datasets are discussed in the following sections as well, and defaults are packaged with the FPEAM code.

## Equipment use

The equipment dataset defines the agricultural activities involved in feedstock production; columns in this dataset are defined in the table below. The equipment dataset defines the equipment used for each agricultural activity (in the default equipment dataset, activities consist of establishment, maintenance, harvest and loading, but additional or alternate activities may be specified as needed) as well as the resources consumed, such as fuel, time, fertilizer, and other agricultural chemicals. Resource rate (amount) units in the equipment dataset must correspond with the units in the feedstock production dataset discussed below, or an error will be given when the data is read into FPEAM. For each activity that involves agricultural equipment, the equipment name must be provided. These are user-defined names that can be matched to NONROAD equipment types with a provided CSV file discussed further in the NONROAD module section.

TABLE: List of columns and data types in equipment dataset.

| Column name | Data type | Description |
| :---------- | :-------: | :---------- |
| feedstock | string | Feedstock being grown |
| tillage_type | string | Tillage practice |
| equipment_group | string | Region identifier |
| rotation_year | integer | Year of crop rotation |
| activity | string | Activity category |
| equipment_name | string | Description of equipment used, if any |
| equipment_horsepower | integer | Horsepower (if applicable to equipment) |
| resource | string | Resource used (each activity may have multiple resources associated with it) |
| rate | float | Quantity of resource used |
| unit_numerator | string | Numerator of resource rate unit |
| unit_denominator | string | Denominator of resource rate unit |

Equipment data must be specified at a regional level of resolution, but the exact bounds of each region can be user-defined and at any scale. In the default equipment data, some region identifiers are numbered (with the numbers stored as characters rather than integers) and some are named. Numbered regions correspond to U.S. Farm Resource Regions (FRRs), while named regions correspond to forestry regions. Regions in the equipment dataset must correspond with the regions defined in the feedstock production dataset, to allow feedstock production data to be merged with the equipment data. Feedstocks and tillage types in the equipment dataset must also match those in the feedstock production dataset; any equipment data without matching feedstock production data (or vice versa) will be excluded from FPEAM calculations.

<!-- TABLE: Equipment data examples

| feedstock | tillage_type | equipment_group | rotation_year | activity | equipment_name | equipment_horsepower | resource | rate | unit_numerator | unit_denominator |
| :--- | :------ | :-------------: | :---------: | :-------------: | :------- | :------------- | :------------------: | :------- | :--: | :--------: | :--------: |
| willow | conventional tillage | 6	| 2 | maintenance | tractor 2wd 55 hp | 55 | herbicide | 0.75 | pound | acre |
| corn | conventional tillage | 1 | 1 | establishment | tractor 2wd 100 hp | 100 | time | 0.087 | hour | acre |
| corn stover | no tillage | 9 | 1 | maintenance | nitrogen | 12.8 | pound | dry short ton |
| switchgrass | no tillage | 12 | 8 | harvest | tractor 2wd 160 hp | 160 | diesel | 0.742 | gallon | acre |
| forest residues | no tillage | northeast | 1 | harvest | whole tree chipper (large) | 750 | time | 0.0245 | hour | dry short ton | -->

The equipment data provided with the FPEAM release was obtained from the Policy Analysis System (POLYSYS) model, "a national, interregional, agricultural model" [(Ugarte and Ray, 2000)](https://www.sciencedirect.com/science/article/pii/S0961953499000951 ). From the [University of Tennessee's Bio-Based Energy Analysis Group](https://ag.tennessee.edu/arec/Pages/beag.aspx ), POLYSYS 

> is a dynamic stochastic (in yields) model of the US agricultural sector, capable of estimating the competitive allocation of agricultural land and feedstock prices associated with changes in yield and management practices. Input requirements include a baseline solution typically from USDA, and policy or resource changes desired for a particular scenario. Output includes economic variables such as County-level feedstock supply, national feedstock demands and prices, National livestock supply and demand, farm income, and land use including forest harvest, afforestation, and pasture conversion. In addition, through the environmental module, estimates of changes in carbon emission and sequestration, soil erosion and sediment, fertilizer use, and chemical use are provided.

Equipment data for whole trees and forest residues was obtained from the Forest Sustainable and Economic Analysis Model (ForSEAM), "a national forest optimization model." Also from the [University of Tennessee's Bio-Based Energy Analysis Group](https://ag.tennessee.edu/arec/Pages/beag.aspx ):

> the Forest Sustainable and Economic Analysis Model (ForSEAM) was originally constructed to estimate forest land production over time and its ability to produce not only traditional forest products, but also products to meet biomass feedstock demands through a cost minimization algorithm (He et al., 2014). The model has three components. The supply component includes general forest production activities for 305 production regions based on USDA’s agricultural supply districts. Each region has a set of production activities defined by the USFS. The Forest Product Demand Component is based on six USFS Scenarios with estimates developed by the US Forest Products Model. The sustainability component ensures that harvest in each region does not exceed annual growth, forest tracts are located within one-half mile of existing roads, and that current year forest attributes reflect previous years’ harvests and fuel removals. The model incorporates dynamic tracking of forest growth.

The default equipment dataset did not originally include loading equipment; rates for this equipment were incorporated into the dataset separately and are shown in the table below.

TABLE: Loading equipment information source from BTS 2016. This data was added to the default equipment dataset packaged with the FPEAM code.
 
| feedstock | equipment type | equipment horsepower | resource | rate | unit |
| :-------- | :------------: | :------------------: | :------: | :--- | :--- |
| corn stover | tractor | 143 | time | 0.017361 | hour/dry short ton |
| wheat straw | tractor | 143 | time | 0.017361 | hour/dry short ton | 
| switchgrass | tractor | 143 | time | 0.017361 | hour/dry short ton |
| sorghum stubble | tractor | 450 | time | 0.050226017 | hour/dry short ton
| corn grain | tractor | 143 | time | 0.017361 | hour/dry short ton |
| miscanthus | tractor | 143 | time | 0.017361 | hour/dry short ton |

## Feedstock production

The feedstock production dataset defines what feedstocks were produced where, in what amounts, and by what agricultural practices. Columns and data within this dataset are described in the table below. This dataset contains two region identifiers, equipment_group (values must match those in the equipment dataset) and region_production, that indicate where feedstocks were produced. Region_production values in the default feedstock production dataset correspond to the [Federal Information Processing Standards](https://www.nrcs.usda.gov/wps/portal/nrcs/detail/national/home/?cid=nrcs143_013697) (FIPS) codes which identify U.S. counties. If values in the region_production column are not FIPS codes, an additional input file giving the mapping of the region_production values to FIPS values must be provided in order for MOVES and NONROAD to run successfully; this file is discussed further in the Additional input datasets section.

TABLE: List of columns in feedstock production data set with data types and descriptions

| Column name | Data type | Description |
| :---------- | :-------: | :---------- |
| feedstock | string | Feedstock being grown; may be food crop, energy feedstock or residue |
| tillage_type | string | Type of tillage practice |
| region_production | string | Identifies the region where the feedstock is grown |
| region_destination | string | Identifies the region to which the harvested feedstock from this region_production is transported |
| equipment_group | string | Region identifier; must match equipment_group values in equipment data set |
| feedstock_measure | string | Identifies the value in the feedstock_amount column | 
| feedstock_amount | float | Feedstock amount defined by feedstock_measure, with units given by unit_numerator and unit_denominator |
| unit_numerator | string | Numerator of feedstock_amount unit |
| unit_denominator | string | Denominator of feedstock_amount unit, if any |

<!--TABLE: Feedstock production data examples

| feedstock | tillage_type | region_production | region_destination | equipment_group | feedstock_measure | feedstock_amount | unit_numerator | unit_denominator |
| :--- | :------ | :----: | :------------: | :----------- | :---------: | ---- |
| poplar | conventional tillage | 12067 | 12039 | 13 | yield | 61.6 | dry short ton | acre |
| poplar | conventional tillage | 12067 | 12039 | 13 | produced | 113.7 | dry short ton  |  |
| poplar | conventional tillage | 12067 | 12039 | 13 | harvested | 1.87 | acre |  |
| poplar | conventional tillage | 12067 | 12039 | 13 | planted | 14.8 | acre |  |-->

<!-- Feedstock production datasets corresponding to the BTS can be downloaded from the [Bioenergy Knowledge Discovery Framework](https://bioenergykdf.net/bt16-download-tool/county?f%5B0%5D=year%3A%222030%22&f%5B1%5D=type%3A%22Energy%22); some rearranging is necessary to transform the dataset into the format required by FPEAM. -->

Any feedstock amounts in mass units should be in dry short tons in the input data. Thus the amounts of any feedstocks traditionally measured in other units such as bushels must be converted before the data is supplied to FPEAM. While this conversion is not done internally, the following tables of average feedstock moisture contents and bushel sizes are provided to users to assist in the units conversion.

TABLE: Moisture content (mass fraction) at time of transport.

| feedstock | moisture content | source |
| :--- | :--------------: | :----- |
| barley straw |  0.069 | Mani et al. (2004) |
| biomass sorghum | 0.650 | Estimated from Rocateli et al. (2012) |
| corn stover |  0.15 | McAloon et al. (2000) |
| energy cane | 0.1 | Estimated from Miao et al. (2011) |
| eucalyptus | 0.1 | Assumed equal to willow |
| forest residues | 0.5 | Bouchard et al. (2012) |
| hay | 0.069 | Assumed equal to barley straw |
| miscanthus | 0.1 | Estimated from Miao et al. (2011) |
| oats straw | 0.069 | Assumed equal to barley straw |
| pine | 0.1 | Assumed equal to willow |
| poplar | 0.1 | Assumed equal to willow |
| sorghum stubble | 0.650 | Assumed equal to biomass sorghum |
| switchgrass | 0.052 | Mani et al. (2004) |
| wheat straw | 0.083 | Mani et al. (2004) |
| whole tree | 0.5 | Bouchard et al. (2012) |
| willow | 0.1 | Estimated from Miao et al. (2011) |

TABLE: Bushel weight in dry short tons by feedstock.

| feedstock | dry short tons per bushel | source |
| :--- | :-----------------------: | :----: | 
| barley | 0.020 | 1. |
| corn | 0.024 | 1. |
| cotton | 0.015 | 1. |
| oats | 0.014 | 1. |
| rice | 0.019 | 2. |
| sorghum | 0.020 | 1. | 
| soybeans | 0.026 | 1. |
| wheat | 0.026 | 1. |

1. Murphy, William J. Tables for Weights and Measurements: Crops. University of Missouri Extension. Available at https://extension2.missouri.edu/G4020. Accessed May 25, 2018.
2. U.S. Department of Agriculture, Office of Weights and Measures. Standard weight per bushel for agricultural commodities. Available at ftp://www.ilga.gov/JCAR/AdminCode/008/00800600ZZ9998bR.html Accessed May 25, 2018.

## Additional input datasets

Region_production and region_destination values in the feedstock production dataset must be mapped to FIPS codes for use in MOVES and NONROAD (region_production) and in the router module (region_production and region_destination). Only one mapping is provided, thus the region column in the mapping should contain all region_production and region_destination values found in the feedstock production dataset. Any production or destination regions for which a FIPS mapping is not provided will be excluded from FPEAM calculations and results. Currently the region-to-FIPS mapping must be one-to-one, meaning that each unique region_production and region_destination code must map to one unique FIPS. Mappings which are not one-to-one will produce an error when the data is read in and must be corrected before FPEAM is run. Further development can allow for many-to-one and one-to-many mappings, if there is demand. 

TABLE: List of columns, data types and descriptions in the map of region_production and region_destination values to FIPS codes

| Column name | Data type | Description |
| :---------- | :-------- | :---------- |
| region | string | Contains all unique region_production and region_destination values from the feedstock production dataset |
| fips | string (5 characters) | FIPS code uniquely corresponding to the region_production or region_destination value |

A map of state FIPS codes (the first two characters of the five-digit county FIPS codes) to two-letter state abbreviations is also packaged with the FPEAM code. This mapping is used in the NONROAD module to create NONROAD input files corresponding to each state. Unlike other input data files provided with FPEAM, this file should not be altered by users.

TABLE: Map of state FIPS codes to two-letter state abbreviations

| Column name | Data type | Description |
| :---------- | :-------- | :---------- |
| state_abbreviation | string | Two-character state name abbreviation |
| state_fips | string | Two-digit state FIPS code, stored as string |

## FPEAM Output

Raw output calculated by FPEAM is a data frame containing several identifier columns as well as pollutant names and amounts. The columns in this data frame are described in the table below. Not every module produces values for every identifier column - MOVES, for instance, does not work with resource subtypes, and Fugitive Dust does not have an activity associated with it - and so some identifier columns may be partially empty. However, every entry in the output data frame will have a feedstock, region_production, region_destination, tillage_type, module, pollutant and pollutant_amount.

TABLE: Columns in main FPEAM output

| Column name | Data type | Description |
| ----------- | --------- | ----------- |
| feedstock | string | Name of feedstock produced or transported |
| region_production | string | Region identifier where feedstock was harvested |
| region_destination | string | Region identifier where feedstock was transported |
| tillage_type | string | Type of tillage used to grow feedstock |
| activity | string | Name of activity that produced the pollutant, if any |
| module | string | Name of module that calculated the pollutant amount in each row |
| resource | string | Resource that caused pollutant emissions (for instance, time, fertilizer or diesel) |
| resource_subtype | string | Resource subtype that caused pollutant emissions (for instance, specific fertilizer types) |
| pollutant | string | Chemical abbreviation of pollutant produced |
| region_transportation | string | Region identifier through which feedstock was transported (route) |
| pollutant_amount | float | Amount of pollutant generated in pounds |

Once generated, the raw output data frame may be saved as a CSV file or stored in a SQL database for further postprocessing or visualization. 

# MOVES Module

Emissions from feedstock transportation are by default calculated using version 2014a of the EPA's Motor Vehicle Emission Simulator (MOVES) model. FPEAM creates all required input files and runs MOVES in batch mode, using a set of parameters listed below to determine at what level of detail MOVES is run. Following the MOVES run(s), emission rates for vehicle operation and start and hotelling are postprocessed with feedstock production data, truck capacity data and feedstock transportation routes to calculate total pollutant amounts.

Currently the FPEAM MOVES module can only run MOVES at the FIPS (county) level, although development is planned to allow users to run MOVES on a project level, where a project may encompass part of a county or parts of several counties. The FIPS for which MOVES is run are determined from region_production values in the feedstock production set, which are mapped to FIPS using the user-provided region-to-FIPS map discussed in the previous section.

MOVES can be run for all FIPS for which a mapping from region_production to FIPS was provided, or at two levels of aggregation: one FIPS per state based on which FIPS had the highest total feedstock production, or multiple FIPS per states based on which FIPS had the highest production of each feedstock. By default, MOVES is run once per state with FIPS selected based on highest total feedstock production. This aggregation is done by default to keep FPEAM run times reasonable; MOVES requires between 10 and 15 minutes to run each FIPS and can easily extend model run times into days.

MOVES aggregation levels are set using the moves_by_state and moves_by_state_and_feedstock parameters, both Booleans that can be set either via the FPEAM GUI or in the MOVES config file. These parameters are mutually exclusive: at most one of them can be True. If neither moves_by_state nor moves_by_state_and_feedstock are True, then MOVES automatically runs every FIPS for which sufficient data is provided.

TABLE: MOVES module user options

| Parameter | Data Type | Default Value | Description |
| :-------- | :-------- | :-----------  | :---------- |
| moves_by_state | Boolean | True | Determines if MOVES is run once per state, based on the FIPS with the highest total feedstock production |
| moves_by_state_and_feedstock | Boolean | False | Determines if MOVES is run for multiple FIPS in each state, based on which FIPS have the highest production of each feedstock type |
| feedstock_measure_type | string | production | Determines which feedstock measure in the feedstock production dataset is used to calculate transportation emissions |

Additional parameters are required by the MOVES module to establish a connection to the MOVES database and allow for the use of SQL statements. These parameters are listed in the table below.

TABLE: MOVES database connection and software parameters.

| Parameter | Data Type | Default Value | Description |
| :-------- | :-------- | :------------ | :---------- |
| moves_database | string | movesdb20161117 | The name of the default MOVES database created when MOVES is first installed on a computer. This value will vary depending on when MOVES was installed. |
| moves_output_db | string | moves_output_db | The name of the database to which MOVES saves results. |
| moves_db_user | string | moves | User name to access the MOVES databases. This value should be set by each user based on what was entered during MOVES installation. |
| moves_db_pass | string | moves | Password to access the MOVES databases. This value should be set by each user based on what was entered during MOVES installation. |
| moves_db_host | string | localhost | Name of the machine on which MOVES is installed. Provided a user is running MOVES on the same machine running FPEAM, this should remain at its default value.|
| moves_version | string | MOVES2014a-20161117 | Version of MOVES software with database version appended |
| moves_path | string | C:\MOVES2014a | Path to primary MOVES2014a directory |
| moves_datafiles_path | string | C:\MOVESdata | Path to MOVESdata directory |
| mysql_binary | string | C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe | Path to mysql executable |
| mysqldump_binary | string | C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe | Path to mysqldump executable |

Before using FPEAM to run MOVES for the first time, the user must create the MOVES output database (moves_output_db in the table above)  using the MOVES GUI. To complete this step, open the MOVES2014a Master software and go to the "General Output" screen, under "Output." Enter the desired MOVES output database name in the Database field under Output Database and click Create Database. A database will be initialized with all tables required to run MOVES in batch mode. Once the database has been created, the MOVES software can be closed without saving the run specification and the user can proceed to using FPEAM.

## User options

These options can be changed manually using the FPEAM GUI or directly in the MOVES config file. The vmt_short_haul parameter is only used if the Router module is either unavailable or if the user specifies that the router should not be used. In this case vmt_short_haul specifies the number of vehicle miles used to calculate transportation emissions within each FIPS where a feedstock is produced.

TABLE: Transportation distance and transportation mode parameters.

| Parameter | Data Type | Default Value | Units | Description |
| :-------- | :-------- | :------------ | :---: |  :--------- |
| vmt_short_haul | float | 100 | miles | Vehicle miles traveled by one truck, in one FIPS, on one feedstock transportation trip. |
| pop_short_haul | int | 1 | trucks | Number of trucks for which MOVES is run. |
| hpmsv_type_id | int | 60 | - | Identifies the class of vehicle used for feedstock transportation as combination trucks |
| source_type_id | int | 61 | - | Identifies the specific type of vehicle used for feedstock transportation as short-haul combination trucks |
| vmt_fraction | dictionary of floats | See VMT fraction table below | unitless | Fraction of vehicle miles traveled on each of four types of roads. |
| moves_timespan | dictionary of ints | See MOVES timespan table below | unitless | Set of values defining the day and hours for which MOVES is run. | 

TABLE: Default truck capacities by feedstock. Source: BTS.

| Feedstock | Vehicle capacity (dry short tons/load) |
| :-------: | :----------------------------: |
| corn stover | 17.28 |
| wheat straw | 17.28 |
| switchgrass | 17.28 |
| corn grain | 17.28 |
| sorghum stubble | 21.10 |
| forest residues | 16.68 |
| whole trees | 16.68 |

Default vehicle miles traveled (VMT) fractions were calculated from Federal Highway Administration data on total vehicle miles traveled nationwide by combination trucks in 2006. The raw data is available from the [Federal Highway Administration](https://www.fhwa.dot.gov/policy/ohim/hs06/metric_tables.cfm) in the table "Vehicle distance of travel in kilometers and related data, by highway category and vehicle type." The VMT fraction representing vehicle idling (road type = 1) was assumed to be 0 due to lack of data.

TABLE: Default VMT fraction values. 

| Road type | Road type description | VMT fraction value |
| :--------: | :--------------------- | :-----------: |
| 1 | Vehicle idling | 0 |
| 2 | Rural restricted | 0.30 |
| 3 | Rural unrestricted | 0.28 |
| 4 | Urban restricted | 0.21 |
| 5 | Urban unrestricted | 0.21 |

TABLE: Default MOVES timespan specification. This timespan represents a typical post-harvest day for most feedstocks.

| Key | Key description | Allowed values | Default value | Default value description |
| :-: | :-------------- | :------------: | :-----------: | :------------------------ |
| mo  | Month | integers 1 - 12 | 10 | October |
| bhr | Beginning hour | integers 1 - 24 | 7 | 7:00 (7am) |
| ehr | Ending hour | integers 1 - 24 | 18 | 18:00 (6pm) |
| d   | Day type | 5 or 2 | 5 | Weekday |

## Module structure and function

The MOVES module creates all necessary input files to run MOVES and executes system commands to run MOVES. Raw output is saved to the MOVES output database specified by the user, and the postprocessing method within the MOVES module fetches the raw output and transforms the emission rates into total pollutant amounts.

## Additional development

Allow for multiple vehicle, fuel and engine type selections, with selections possibly varying by feedstock or by region.

Allow for users to select which pollutants to calculate from the full list of pollutants and pollutant processes included in MOVES.

# Router Module

The Router module is used within the MOVES module to obtain the routes taken by feedstock transportation vehicles and calculate the vehicle miles traveled by FIPS over each route. This information is used with the emission factors obtained from MOVES to calculate emissions within each FIPS where biomass is produced, transported and delivered. Due to MOVES' long run time, emission factors are not obtained for every FIPS through which biomass is transported; however, this functionality can be added in the future if there is demand. Because the Router module is only used internally to FPEAM, there are no user options for running the router and no config file needs to be provided.

Currently the Router module uses a graph of all known, publicly accessible roads in the contiguous U.S., obtained from the [Global Roads Open Access Data Sets](http://sedac.ciesin.columbia.edu/data/set/groads-global-roads-open-access-v1) (gROADS) v1. This graph does not contain transportation pathways such as rivers, canals and train tracks, and therefore limits the transportation modes that can be used in FPEAM to on-road vehicles such as trucks. Future FPEAM development will expand the available routes to include multiple route types and transportation modes. Dijkstra's algorithm is applied to find the shortest path from the biomass production region to the destination region (both mapped to FIPS as discussed previously), and the shortest path is used to obtain a list of FIPS through which the biomass is transported as well as the vehicle miles traveled within each FIPS.

# NONROAD Module

NONROAD is a model for calculating emissions from off-road sources including logging, agricultural and other types of equipment. Although NONROAD is contained within MOVES 2014a, the required inputs, interface and outputs are sufficiently different from MOVES that a separate FPEAM module for setting up and running NONROAD was created. Unlike MOVES, NONROAD run times are on the order of seconds, and so NONROAD is run entirely at a FIPS level rather than at an aggregated level.

There are a variety of input files required to run NONROAD, many of which are nested several sub-directories deep. NONROAD requires that the complete file paths to all input files be 60 characters or less (although some file paths may extend to 80 characters, developers have chosen to limit input file paths to 60 characters for simplicity), and so to avoid file path length errors, NONROAD input files have coded names that indicate feedstock type, tillage type and activity. CSV files recording the encoded feedstock, tillage and activity names are saved automatically to the main FPEAM directory when the names are encoded, to allow users to review the input files if necessary.

## User options and input data

User options within the NONROAD config file (also accessible via the GUI) consist of identifiers used to select which entries in the feedstock production and equipment datasets should be used in NONROAD runs, NONROAD temperature specifications and a set of multipliers used to calculate criteria air pollutants of interest from those returned by NONROAD. These options are listed in the table below with default values and descriptions.

TABLE: NONROAD module user options

| Parameter | Data Type | Default Value | Units | Description |
| :-------- | :-------- | :------------ | :---: |  :--------- |
| feedstock_measure_type | string | harvested | Unitless | Type of feedstock measure used in NONROAD calculations - the units of this feedstock measure should be acreage |
| time_resource_name | string | time | Unitless | Name used in equipment dataset to identify time spent running agricultural equipment |
| forestry_feedstock_names | list of strings | forest whole trees, forest residues | Unitless | Names of forestry feedstocks in feedstock production and equipment datasets, if any |
| nonroad_temp_min | float | 50.0 | &deg;F | Minimum temperature used by NONROAD |
| nonroad_temp_mean | float | 60.0 | &deg;F | Mean temperature used by NONROAD |
| nonroad_temp_max | float | 68.8 | &deg;F | Maximum temperature used by NONROAD |
| diesel_lhv | float | 0.012845 | mmBTU/gallon | Lower heating value of diesel fuel |
| diesel_nh3_ef | float | 0.68 | grams NH3/mmBTU diesel | NH3 emission factor for diesel fuel [1.] |
| diesel_thc_voc_conversion | float | 1.053 | Unitless | Default total hydrocarbon (THC) to VOC conversion factor for diesel fuel [2.] |
| diesel_pm10topm25 | float | 0.97 | Unitless | Default PM10 to PM2.5 conversion factor for diesel fuel [2.] |

1. “Co-Benefits Risk Assessment (COBRA) Screening Model.” EPA, Climate and Energy
Resources for State, Local, and Tribal Governments. https://www.epa.gov/statelocalclimate/co-benefits-risk-assessment-cobra-screening-model.
2. EPA NONROAD Conversion Factors for Hydrocarbon Emission Components

NONROAD identifies equipment based on Source Characterization Codes (SCCs) and equipment horsepower. In the default equipment data set, SCCs were not provided, so an additional input file mapping equipment names from the equipment dataset to equipment SCCs is supplied as well. A portion of this input file is given in the table below. SCCs for equipment types included in NONROAD but not used in the default equipment dataset may be found in Appendix B of the [NONROAD User Guide](https://www.epa.gov/moves/nonroad-model-nonroad-engines-equipment-and-vehicles#user%20guide).

TABLE: Sample entries from the nonroad_equipment input dataset. Equipment descriptions in this file are added to NONROAD input files but are not necessary for NONROAD to run, thus the descriptions may be left blank if desired. 

| Equipment name | Equipment description | Source Characterization Code (SCC) |
| :------------- | :-------------------- | :--------------------------------: |
| whole tree chipper (large) | Dsl - Chippers/Stump Grinders (com) | 2270004066 |
| loader (2 row) | Dsl - Forest Eqp - Feller/Bunch/Skidder | 2270007015 |
| combine (2wd) | Dsl - Combines | 2270005020 |
| tractor 2wd 150 hp | Dsl - Agricultural Tractors | 2270005015 |

## Module structure and function

The NONROAD module has very similar functionality to the MOVES module; input files for running the model are created and saved, and system commands (saved as batch files in the NONROAD module) are used to call the external models. A separate postprocessing method for raw NONROAD output reads in the NONROAD output files, concatenates the output from various NONROAD runs together, and adds identifier columns.

## Additional development

# EmissionFactors Module

Input files: equipment, production, resource_distribution, emission_factors

Other inputs: feedstock_measure_type

Output files: None; calculates pollutants in each region-feedstock combination from resources and resource subtypes as defined by resource_distribution and emission_factors inputs

## Input file format

The emission factors input files 

## Default input data and sources

TABLE: Default emissions factors for NO (used as a proxy for NO<sub>x</sub>) and NH<sub>3</sub> from nitrogen fertilizers and VOC from herbicides and insecticides. NO emission factors were obtained from FOA (2001) and GREET (ANL 2010). NH<sub>3</sub> factors were obtained from Goebes et al. 2003, Davidson et al. 2004 and the 17/14 ratio of NH<sub>3</sub> to N. See [Zhang et al. (2015)](https://onlinelibrary.wiley.com/doi/full/10.1002/bbb.1620) for additional information. Note that as of July 2, 2018 the Davidson et al. reference, the CMU Ammonia Model, Version 3.6 from The Environmental Institute at Carnegie Mellon University was not available online and source data could not be verified. 
 
| resource | resource subtype           | pollutant      | emission_factor | unit_numerator | unit_denominator |
| :------- | :------------------------- | :------------: | :-------------: | :--------: | :--------: |
| nitrogen | anhydrous ammonia          | no<sub>x</sub> | 0.79            | pound      | pound |
| nitrogen | anhydrous ammonia          | nh<sub>3</sub> | 4.86            | pound      | pound |
| nitrogen | ammonium nitrate (33.5% N) | no<sub>x</sub> | 3.80            | pound      | pound |
| nitrogen | ammonium nitrate (33.5% N) | nh<sub>3</sub> | 2.32            | pound      | pound |
| nitrogen | ammonium sulfate           | no<sub>x</sub> | 3.50            | pound      | pound |
| nitrogen | ammonium sulfate           | nh<sub>3</sub> | 11.6            | pound      | pound |
| nitrogen | urea (44 - 46% N)          | no<sub>x</sub> | 0.90            | pound      | pound |
| nitrogen | urea (44 - 46% N)          | nh<sub>3</sub> | 19.2            | pound      | pound |
| nitrogen | nitrogen solutions         | no<sub>x</sub> | 0.79            | pound      | pound |
| nitrogen | nitrogen solutions         | nh<sub>3</sub> | 9.71            | pound      | pound |
| herbicide | generic herbicide         | voc            | 0.75            | pound      | pound |
| insecticide | generic insecticide     | voc            | 0.75            | pound      | pound |

VOC emission factors from application of herbicides and insecticides were calculated from the following equation: (Zhang et al., 2015):

VOC (lb/acre/year) = R * I * ER * C<sub>VOC</sub>

where R is the pesticide or herbicide application rate (lb/harvested acre/year), I is the amount of active ingredient per pound of pesticide or herbicide (lb active ingredient/lb chemical, assumed to be 1), ER is the evaporation rate (assumed to be 0.9 per EPA recommendations from emissions inventory improvement program guidance) and C<sub>VOC</sub> is the VOC content in the active ingredient (lb VOC/lb active ingredient, assumed to be 0.835 per Huntley 2015 revision of 2011 NEI technical support document).

TABLE: The default resource subtype distribution data file defines the nitrogen fertilizer distribution among five common nitrogenous fertilizers and the distribution of herbicide and insecticide to generics. The nitrogen fertilizer distribution varies between feedstocks. The national average distribution from 2010 [(USDA)](https://www.ers.usda.gov/data-products/fertilizer-use-and-price.aspx#26720) is used for corn grain and stover, sorghum stubble, and wheat straw. The perennial feedstock distribution which consists of nitrogen solutions only is used for switchgrass, miscanthus and all forest products. (Turhollow, 2011, personal communication). Two example distributions are shown in the table.

| feedstock | resource | resource_subtype | distribution |
| :-------- | :------- | :--------------- | :----------: |
| corn grain | nitrogen | anhydrous ammonia | 0.3404 |
| corn grain | nitrogen | ammonium nitrate | 0.0247 |
| corn grain | nitrogen | ammonium sulfate | 0.0179 |
| corn grain | nitrogen | urea | 0.2542 |
| corn grain | nitrogen | nitrogen solutions | 0.3528 |
| switchgrass | nitrogen | anhydrous ammonia |  0 |
| switchgrass | nitrogen | ammonium nitrate |  0 |
| switchgrass | nitrogen | ammonium sulfate |  0 |
| switchgrass | nitrogen | urea | 0 |
| switchgrass | nitrogen | nitrogen solutions | 1 |
| eucalyptus | herbicide | generic herbicide | 1 |
| wheat | insecticide | generic insecticide | 1 |

# Fugitive Dust Module

The fugitive dust module calculates PM<sub>2.5</sub> and PM<sub>10</sub> emissions from on-farm (harvest and non-harvest) activities. On-road fugitive dust from feedstock transportation is not calculated.

PM<sub>10</sub> emissions are calculated using feedstock-specific emissions factors developed by the [California Air Resources Board](http://www.arb.ca.gov/ei/areasrc/fullpdf/full7-5.pdf) , which are available in Chapter 9 of the Billion Ton Study 2016 Update and packaged with the FPEAM code base in the default input data files. PM<sub>2.5</sub> emission factors, which are also included in the default FPEAM input data files, are calculated by multiplying the PM<sub>10</sub> emission factors by 0.2. This fraction represents agricultural tilling and was developed by the [Midwest Research Institute](http://www.epa.gov/ttnchie1/ap42/ch13/bgdocs/b13s02.pdf) . Users are able to use a different PM<sub>2.5</sub> fraction or alternative emissions factors by editing the input data.

TABLE: List of columns and data types in fugitive dust emissions factors dataset.

| Column name | Data type | Description |
| :---------- | :-------: | :---------- |
| feedstock	| string | Feedstock being grown |
| tillage_type | string | Type of tillage practice | 
| pollutant | string | Identifies if the rate is for PM10 or PM2.5 |
| rate | float | Amount of fugitive dust generated per acre for the feedstock specified in an average year |
| unit_numerator | string | Numerator of rate unit |
| unit_denominator | string | Denominator of rate unit |

TABLE: Fugitive dust input file example

| feedstock | tillage_type | source_category | pollutant | rate | unit_numerator | unit_denominator |
| :-------- | :----------- | :-------------- | :-------: | :--: | :--------- | :--------- |
| sorghum stubble | conventional tillage | harvest | PM10 | 1.7 | pound | acre |
| sorghum stubble | conventional tillage | harvest | PM25 | 0.34 | pound | acre |
| sorghum stubble | conventional tillage | non-harvest | PM10 | 0 | pound | acre |
| sorghum stubble | conventional tillage | non-harvest | PM25 | 0 | pound | acre |



## Advanced user options

TABLE: Parameters controlling how biomass is transported on-farm from field to roadside.

| Parameter | Data Type | Default Value | Units | Description |
|-----------|-----------|---------------|-------|-------------|
| onfarm_truck_capacity | float | 15 | dry short tons/load | Amount of biomass that can be transported on-farm by one truck in one trip. |
| onfarm_default_distance | float | 1 | miles | Average distance that biomass is transported on-farm, from the field to the roadside. |

## Output