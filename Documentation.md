# Introduction

The Feedstock Production Emissions to Air Model (FPEAM) calculates spatially explicit inventories of criteria air pollutants and precursors generated from agricultural and tranportation activities associated with the production and supply of biomass feedstocks for renewable energy generation. FPEAM was originally developed to calculate air pollutants as part of the 2016 update to the Billion Ton Study (BTS). For this version of FPEAM, the code base has been substantially refactored and streamlined to provide increased flexibility around biomass production scenario definitions, including what activities and pollutants are included in the calculations and at what spatial scale. This document describes the FPEAM code base and default input files bundled with the beta model release.

FPEAM calculations are organized into independent modules, listed in the first table below along with the activities and pollutants included by default in each module. The EmissionFactors module is unique in that it can be used to calculate any pollutant from any activity, if sufficient input data is provided. In particular, users have the option of using the EmissionFactors module to replace the MOVES and/or NONROAD modules with emissions factors for agricultural equipment and on-road vehicle use. The EmissionFactors module can also be used to calculate pollutants from additional activities, such as non-nitrogen fertilizer application.

A full list of the default pollutants calculated by FPEAM is listed in the second table below. Additional pollutants may also be calculated from user-provided input data using the EmissionFactors module.

The structure and function of each module, and the module-specific input data required to run each module, is described further in subsequent sections.

TABLE: Available FPEAM modules.

| Module | Default pollutants calculated | Default activities included |
| :----- | :-------------------: | :------------------ |
| MOVES | All | Off-farm, on-road transportation of biomass to biorefineries |
| NONROAD | All | On-farm use of agricultural equipment |
| EmissionFactors | VOC, NH<sub>3</sub>, NO<sub>x</sub> | Nitrogen fertilizer application; pesticide and herbicide application |
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

## General input data: Equipment use and agricultural activities

The two input datasets described in this section are used by all FPEAM modules and provide the basic format for the FPEAM outputs. A default for each dataset described in this section is provided with the FPEAM code base and can be used to run the BTS feedstock production scenarios. Provided the data format is preserved, these datasets may be altered, expanded or replaced to run custom feedstock production scenarios.

The equipment dataset defines the agricultural activities involved in feedstock production. In this dataset, 

TABLE: List of columns and data types in equipment dataset.

| Column name | Data type | Description |
| :---------- | :-------: | :---------- |
| feedstock | string | Feedstock being grown |
| tillage_type | string | Tillage practice |
| equipment_group | string | Region identifier |
| rotation_year | integer | Year of crop rotation |
| activity | string | Activity category |
| equipment_name | string | Description of equipment used |
| equipment_horsepower | integer | Horsepower (if applicable to equipment) |
| resource | string | Resource used (each activity may have multiple resources associated with it) |
| rate | float | Quantity of resource used |
| unit_numerator | string | Numerator of resource rate unit |
| unit_denominator | string | Denominator of resource rate unit |


Budgets must be at a regional level of resolution, but the exact bounds of each region can be user-defined and at any scale. In the default equipment data, some region identifiers are numbered (with the numbers stored as characters rather than integers) and some are named. Numbered regions correspond to U.S. Farm Resource Regions (FRRs), while named regions correspond to forestry regions.

For each activity that involves agricultural equipment, the equipment name must be provided. These are user-defined names that can be matched to NONROAD equipment types during scenario definition or with a provided CSV file for batch runs.

Columns with restricted values are: tillage_type, activity, resource and unit. The allowed values are listed in the table below. If input data is provided that contains non-allowed values in these columns, FPEAM will produce an error and the input data must be corrected before a scenario can be run.

TABLE: Equipment data examples

| feedstock | tillage_type | equipment_group | rotation_year | activity | equipment_name | equipment_horsepower | resource | rate | unit_numerator | unit_denominator |
| :--- | :------ | :-------------: | :---------: | :-------------: | :------- | :------------- | :------------------: | :------- | :--: | :--------: | :--------: |
| willow | conventional tillage | 6	| 2 | maintenance | tractor 2wd 55 hp | 55 | herbicide | 0.75 | pound | acre |
| corn | conventional tillage | 1 | 1 | establishment | tractor 2wd 100 hp | 100 | time | 0.087 | hour | acre |
| corn stover | no tillage | 9 | 1 | maintenance | nitrogen | 12.8 | pound | dry short ton |
| switchgrass | no tillage | 12 | 8 | harvest | tractor 2wd 160 hp | 160 | diesel | 0.742 | gallon | acre |
| forest residues | no tillage | northeast | 1 | harvest | whole tree chipper (large) | 750 | time | 0.0245 | hour | dry short ton |

The equipment data provided with the FPEAM release was obtained from the Policy Analysis System (POLYSYS) model, "a national, interregional, agricultural model" [(Ugarte and Ray, 2000)](https://www.sciencedirect.com/science/article/pii/S0961953499000951 ). From the [University of Tennessee's Bio-Based Energy Analysis Group](https://ag.tennessee.edu/arec/Pages/beag.aspx ), POLYSYS 

> is a dynamic stochastic (in yields) model of the US agricultural sector, capable of estimating the competitive allocation of agricultural land and feedstock prices associated with changes in yield and management practices. Input requirements include a baseline solution typically from USDA, and policy or resource changes desired for a particular scenario. Output includes economic variables such as County-level feedstock supply, national feedstock demands and prices, National livestock supply and demand, farm income, and land use including forest harvest, afforestation, and pasture conversion. In addition, through the environmental module, estimates of changes in carbon emission and sequestration, soil erosion and sediment, fertilizer use, and chemical use are provided.

Equipment data for whole trees and forest residues was obtained from the Forest Sustainable and Economic Analysis Model (ForSEAM), "a national forest optimization model." Also from the [University of Tennessee's Bio-Based Energy Analysis Group](https://ag.tennessee.edu/arec/Pages/beag.aspx ):

> the Forest Sustainable and Economic Analysis Model (ForSEAM) was originally constructed to estimate forest land production over time and its ability to produce not only traditional forest products, but also products to meet biomass feedstock demands through a cost minimization algorithm (He et al., 2014). The model has three components. The supply component includes general forest production activities for 305 production regions based on USDA’s agricultural supply districts. Each region has a set of production activities defined by the USFS. The Forest Product Demand Component is based on six USFS Scenarios with estimates developed by the US Forest Products Model. The sustainability component ensures that harvest in each region does not exceed annual growth, forest tracts are located within one-half mile of existing roads, and that current year forest attributes reflect previous years’ harvests and fuel removals. The model incorporates dynamic tracking of forest growth."

Users may develop alternate feedstock production scenarios using POLYSYS and ForSEAM, or by directly making edits to the provided equipment data sets.

Values in the feedstock, tillage and equipment_group column must match to those provided in the equipment data file. Any production values without matching budgets, or vice versa, will not be included in FPEAM calculations.

If values in the region column do not correspond to the Federal Information Processing Standards (FIPS) code (county identifiers) used in MOVES and NONROAD, an additional file giving the mapping of the region values to FIPS values must be provided. When running FPEAM interactively via the GUI, the user will be prompted to provide this file if necessary.

*** Scenario name, year no longer in production dataset ***

TABLE: List of columns in production data set with data types and descriptions

| Column name | Data type | Description |
| :---------- | :-------: | :---------- |
| feedstock | string | Feedstock being grown; may be food crop, energy feedstock or residue |
| tillage_type | string | Type of tillage pracice |
| region_production | string | Identifies the region where the feedstock is grown |
| region_destination | string | Identifies the region to which the harvested feedstock from this region_production is transported |
| equipment_group | string | Region identifier; must match equipment_group values in equipment data set |
| feedstock_measure | string | Identifies the value in the feedstock_amount column | 
| feedstock_amount | float | Feedstock amount defined by feedstock_measure, with units given by unit_numerator and unit_denominator |
| unit_numerator | string | Numerator of feedstock_amount unit |
| unit_denominator | string | Denominator of feedstock_amount unit |

TABLE: Production data examples

| feedstock | tillage_type | region_production | region_destination | equipment_group | feedstock_measure | feedstock_amount | unit_numerator | unit_denominator |
| :--- | :------ | :----: | :------------: | :----------- | :---------: | ---- |
| poplar | conventional tillage | 12067 | - | 13 | yield | 61.6 | dry short ton | acre |
| poplar | conventional tillage | 12067 | - | 13 | produced | 113.7 | dry short ton  | - |
| poplar | conventional tillage | 12067 | - | 13 | harvested | 1.87 | acre | - |
| poplar | conventional tillage | 12067 | - | 13 | planted | 14.8 | acre | - |


Typical source of production data (POLYSYS and forSEAM)

### Additional input data

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

## Output

### Structure of csv file

### Figures generated within the GUI

# MOVES Module

TABLE: User options that determine if MOVES is run and at what level of detail.

| Parameter | Data Type | Default Value | Description |
|-----------|-----------|---------------|-------------|
| run_moves | Boolean | True | Flag that determines whether the MOVES module is run for a given scenario. If the MOVES module is not run, no emissions from off-farm biomass transportation will be included. |
| state_level_moves | Boolean | True | Flag that determines whether the MOVES module is run for a given scenario. If the MOVES module is not run, no emissions from off-farm biomass transportation will be included. |
| moves_by_crop | Boolean | False | Flag that determines for how many FIPS MOVES is run. If True, MOVES is run for the set of FIPS in each state with the highest feedstock production for each single feedstock in the equipment - for instance, MOVES will run for the FIPS with the most corn production, with the most switchgrass production, and so on. If False, MOVES is run for a single FIPS in each state, with the FIPS determined by highest total feedstock production across all feedstocks. |

TABLE: MOVES database connection parameters.

| Parameter | Data Type | Default Value | Description |
|-----------|-----------|---------------|-------------|
| moves_database | string | movesdb20151028 | The name of the default MOVES database created when MOVES is first installed on a computer. This value will vary depending on when MOVES was installed. |
| moves_output_db | string | movesoutputdb | The name of the database to which MOVES saves results. This name is invariable and can be left at its default value. |
| moves_db_user | string | moves | User name to access the MOVES databases. This value should be set by each user based on what was entered during MOVES installation. |
| moves_db_pass | string | moves | Password to access the MOVES databases. This value should be set by each user based on what was entered during MOVES installation. |
| moves_db_host | string | localhost | Name of the machine on which MOVES is installed. Provided a user is running MOVES on the same machine running FPEAM, this should remain at its default value.|

MOVES can be run for one FIPS per state, for multiple FIPS per state, or for all FIPS for which a mapping from region_production to FIPS was provided. These are mutually exclusive options set by Booleans in the moves.ini file; at most one of these parameters can be true. If neither moves_by_state nor moves_by_state_and_feedstock are True, then MOVES automatically runs for every FIPS available. Caution: MOVES is time-consuming to run and can easily extend FPEAM run times to multiple days. Developers recommend that the number of FPIS for which MOVES is run during a scenario be kept in the low hundreds at most.

The feedstock_measure_type argument fed into the MOVES module defines the crop measure used to determine which FIPS are run - if either moves_by_state or moves_by_state_and_feedstock are true.

## Advanced user options

These options can be changed manually within the moves.ini file.

TABLE: Transportation distance and transportation mode parameters.

| Parameter | Data Type | Default Value | Units | Description |
|-----------|-----------|---------------|-------|-------------|
| vmt_short_haul | float | 100 | miles | Vehicle miles traveled by one truck on one biomass delivery trip. |
| pop_short_haul | int | 1 | trucks | Number of trucks for which MOVES is run. |
| truck_capacity | dictionary of floats | See table below | dry short tons/load | Amount of biomass that can be transported off-farm by one truck in one trip. |
| vmt_fraction | dictionary of floats | See table below | unitless | Fraction of vehicle miles traveled spent on each of four types of roads. |
| moves_timespan | dictionary of ints | See table below | unitless | Set of values defining the day and hours for which MOVES is run. | 

TABLE: Default values of truck_capacity dictionary. Source: No source in BTS.

| Feedstock | Vehicle capacity (dry short tons/load) |
| :-------: | :----------------------------: |
| corn stover | 17.28 |
| wheat straw | 17.28 |
| switchgrass | 17.28 |
| corn grain | 17.28 |
| sorghum stubble | 21.10 |
| forest residues | 16.68 |
| whole trees | 16.68 |

Default VMT fraction values were calculated from Federal Highway Administration data on total vehicle miles traveled nationwide by combination trucks in 2006. The raw data is available from the [Federal Highway Administration](https://www.fhwa.dot.gov/policy/ohim/hs06/metric_tables.cfm) in the table "Vehicle distance of travel in kilometers and related data, by highway category and vehicle type." The VMT fraction representing vehicle idling (road type = 1) was assumed to be 0 due to lack of data.

TABLE: Default VMT fraction values. 

| Road type | Road type description | VMT fraction value |
| :--------: | :--------------------- | :-----------: |
| 1 | Vehicle idling | 0 |
| 2 | Rural restricted | 0.30 |
| 3 | Rural unrestricted | 0.28 |
| 4 | Urban restricted | 0.21 |
| 5 | Urban unrestricted | 0.21 |

TABLE: Default specification for MOVES timespan. This timespan represents a typical harvest day for most feedstocks.

| Key | Key description | Allowed values | Default value | Default value description |
| :-: | :-------------- | :------------: | :-----------: | :------------------------ |
| mo  | Month | integers 1 - 12 | 10 | October |
| bhr | Beginning hour | integers 1 - 24 | 7 | 7:00 (7am) |
| ehr | Ending hour | integers 1 - 24 | 18 | 18:00 (6pm) |
| d   | Day type | 5 or 2 | 5 | Weekday |

## Module structure and function



## Output

Table of emission factors

Postprocessing

## Additional development

Currently, emissions from biomass transportation must be calculated via MOVES. It would be possible to implement an option within FPEAM that allows users to input their own set of emissions factors for transportation and use those factors in place of running MOVES.

vmt_fraction could be updated to reflect 2015 or 2016 data.

# NONROAD Module

Calculate emissions from on-farm fuel combustion and equipment operation. Equipment types include tractors, combines, and trucks.

## Advanced user options

TABLE: NONROAD temperature range.

|             | Temperature |
| :---------- | :---------: |
| Minimum     | 50.0 &deg;F |
| Mean        | 60.0 &deg;F |
| Maximum     | 68.8 &deg;F |

TABLE: Matching generic equipment types from the equipment to specific NONROAD equipment and fuel types.

| Equipment names | NONROAD equipment types | Source Characterization Code |
| ---------------------- | ----------------------- | :------------------------ |
| tractor | Dsl - Agricultural Tractors | |
| combine | Dsl - Combines | |
| chipper | Dsl - Chippers/Stump Grinders (com) | |
| loader | Dsl - Forest Eqp - Feller/Bunch/Skidder | |
| other_forest_eqp | Dsl - Forest Eqp - Feller/Bunch/Skidder | |
| chain_saw | Lawn & Garden Equipment Chain Saws | |
| crawler | Dsl - Crawler Tractors | |

## Module structure and function

## Output
Table of total emissions for off-road equipment operation

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
| nitrogen | anhydrous ammonia          | NO<sub>x</sub> | 0.79            | pound      | pound |
| nitrogen | anhydrous ammonia          | NH<sub>3</sub> | 4.86            | pound      | pound |
| nitrogen | ammonium nitrate (33.5% N) | NO<sub>x</sub> | 3.80            | pound      | pound |
| nitrogen | ammonium nitrate (33.5% N) | NH<sub>3</sub> | 2.32            | pound      | pound |
| nitrogen | ammonium sulfate           | NO<sub>x</sub> | 3.50            | pound      | pound |
| nitrogen | ammonium sulfate           | NH<sub>3</sub> | 11.6            | pound      | pound |
| nitrogen | urea (44 - 46% N)          | NO<sub>x</sub> | 0.90            | pound      | pound |
| nitrogen | urea (44 - 46% N)          | NH<sub>3</sub> | 19.2            | pound      | pound |
| nitrogen | nitrogen solutions         | NO<sub>x</sub> | 0.79            | pound      | pound |
| nitrogen | nitrogen solutions         | NH<sub>3</sub> | 9.71            | pound      | pound |
| herbicide | generic herbicide         | VOC            | 0.75            | pound      | pound |
| insecticide | generic insecticide     | VOC            | 0.75            | pound      | pound |

VOC emission factors from application of herbicides and insecticides were calculated from the following equation: (Zhang et al., 2015):

VOC (lb/acre/year) = R * I * ER * C<sub>VOC</sub>

where R is the pesticide or herbicide application rate (lb/harvested acre/year), I is the amount of active ingredient per pound of pesticide or herbicide (lb active ingredient/lb chemical, assumed to be 1), ER is the evaporation rate (assumed to be 0.9 per EPA reccomendations from emmissions inventory improvement program guidance) and C<sub>VOC</sub> is the VOC content in the active ingredient (lb VOC/lb active ingredient, assumed to be 0.835 per Huntley 2015 revision of 2011 NEI technical support document).

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

## Output

# Fugitive Dust Module

The fugitive dust module calculates PM<sub>2.5</sub> and PM<sub>10</sub> emissions from on-farm (harvest and non-harvest) activities. On-road fugitive dust from biomass transportation is not calculated.

PM<sub>10</sub> emissions are calculated using feedstock-specific emissions factors developed by the [California Air Resources Board](http://www.arb.ca.gov/ei/areasrc/fullpdf/full7-5.pdf) , which are available in Chapter 9 of the Billion Ton Study 2016 Update and packaged with the FPEAM code base in the default input data files. PM<sub>2.5</sub> emission factors, which are also included in the default FPEAM input data files, are calculated by multiplying the PM<sub>10</sub> emission factors by 0.2. This fraction represents agricultural tilling and was developed by the [Midwest Research Institute](http://www.epa.gov/ttnchie1/ap42/ch13/bgdocs/b13s02.pdf) . Users are able to use a different PM<sub>2.5</sub> fraction or alternative emissions factors by editing the input data.

TABLE: List of columns and data types in equipment dataset.

| Column name | Data type | Description |
| :---------- | :-------: | :---------- |
| feedstock	| string | Feedstock being grown |
| tillage_type | string | Type of tillage practice |
| source_category | string | Identifies harvest or non-harvest fugitive dust | 
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