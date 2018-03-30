# Introduction
FPEAM calculates air pollutants from agricultural activities and transportation associated with production of biomass for renewable energy.

Pollutants included are: CH<sub>4</sub>, NH<sub>3</sub>, NO<sub>x</sub>, SO<sub>2</sub>, VOC, PM2.5, PM10

## Code structure
FPEAM is organized into modules that calculate pollutant emissions from a particular activity category. Each module is described further in its own section.

* MOVES: Off-farm, on-road transportation of biomass to biorefineries.
* NONROAD: On-farm use of agricultural equipment.  Includes emissions from fuel combustion and equipment operation.
* Chemical: Emissions from volatilization of nitrogenous fertilizers, herbicides and insecticides.
* FugitiveDust: Fugitive dust (PM2.5 and PM10) emissions from on-farm activities.

Config files are used for each module. Within each config file section, GUI user options list the FPEAM parameters and options that can be controlled via the built-in GUI. These are considered basic options necessary for the average user to construct FPEAM scenarios. Advanced user options cannot be controlled via the GUI; they must be changed manually by editing the .ini files for FPEAM and for each module. Advanced user options are not considered to be necessary for the average user to define and run FPEAM scenarios, but may be useful in defining custom scenarios that explore alternative supply chain options.

## Input data and formatting

A default for each data set described in this section is provided with the FPEAM code base and can be used to run basic scenarios.  Any or all of these data sets can be altered or replaced by users to run custom scenarios.  Any changes to the format (column names, column data types, etc) of any data set will break FPEAM.

This section describes the basic crop production data on which every FPEAM module runs. Several modules require additional input data, which can also be revised or replaced by users. These additional input data are discussed in the section for each module.

### Crop equipment and activity budget

Columns and data types

Typical source of budget data 

Changes to make to the default budget data to model different scenarios

Sample / small subset of budget data demonstrating format

### Crop production

Columns and data types

Typical source of production data (POLYSYS and forSEAM)

Sample / small subset of data demonstrating format

## Output

### Structure of csv file

### Figures generated within the GUI

# MOVES Module

## GUI user options

TABLE: User options that determine if MOVES is run and at what level of detail.

| Parameter | Data Type | Default Value | Description |
|-----------|-----------|---------------|-------------|
| run_moves | Boolean | True | Flag that determines whether the MOVES module is run for a given scenario. If the MOVES module is not run, no emissions from off-farm biomass transportation will be included. |
| state_level_moves | Boolean | True | Flag that determines whether the MOVES module is run for a given scenario. If the MOVES module is not run, no emissions from off-farm biomass transportation will be included. |
| moves_by_crop | Boolean | False | Flag that determines for how many FIPS MOVES is run. If True, MOVES is run for the set of FIPS in each state with the highest crop production for each single crop in the budget - for instance, MOVES will run for the FIPS with the most corn production, with the most switchgrass production, and so on. If False, MOVES is run for a single FIPS in each state, with the FIPS determined by highest total crop production across all crops. |

TABLE: MOVES database connection parameters.

| Parameter | Data Type | Default Value | Description |
|-----------|-----------|---------------|-------------|
| moves_database | string | movesdb20151028 | The name of the default MOVES database created when MOVES is first installed on a computer. This value will vary depending on when MOVES was installed. |
| moves_output_db | string | movesoutputdb | The name of the database to which MOVES saves results. This name is invariable and can be left at its default value. |
| moves_db_user | string | moves | User name to access the MOVES databases. This value should be set by each user based on what was entered during MOVES installation. |
| moves_db_pass | string | moves | Password to access the MOVES databases. This value should be set by each user based on what was entered during MOVES installation. |
| moves_db_host | string | localhost | Name of the machine on which MOVES is installed. Provided a user is running MOVES on the same machine running FPEAM, this should remain at its default value.|

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

| Crop code | Capacity (dry short tons/load) |
|-----------|--------------------------------|
| CS | 17.28 |
| WS | 17.28 |
| SG | 17.28 |
| CG | 17.28 |
| SS | 21.10 |
| FR | 16.68 |
| FW | 16.68 |

TABLE: Default values of vmt_fraction dictionary. Calculated from Federal Highway Administration data on total vehicle miles traveled nationwide by combination trucks in 2006. Raw data available at https://www.fhwa.dot.gov/policy/ohim/hs06/metric_tables.cfm in the table "Vehicle distance of travel in kilometers and related data, by highway category and vehicle type." Vehicle idling was assumed to be 0 due to lack of data.

| Road type | Road type description | vmt_fraction |
|-----------|-----------------------|--------------|
| 1 | Vehicle idling | 0 |
| 2 | Rural restricted | 0.30 |
| 3 | Rural unrestricted | 0.28 |
| 4 | Urban restricted | 0.21 |
| 5 | Urban unrestricted | 0.21 |

TABLE: Default moves_timespan dictionary. This timespan represents a typical harvest day for most crops.

| Key | Key description | Value | Value description |
|-----|-----------------|-------|-------------------|
| mo  | Month: can take values from 1 - 12 | 10 | October |
| bhr | Beginning hour: can take values from 1 - 24 | 7 | 7:00 (7am) |
| ehr | Ending hour: can take values from 1 - 24 | 18 | 18:00 (6pm) |
| d   | Day type: 5 indicates weekday, 2 indicates weekend | 5 | Weekday |

## Module structure and function



## Output

Table of emission factors

Postprocessing

## Additional development

Currently, emissions from biomass transportation must be calculated via MOVES. It would be possible to implement an option within FPEAM that allows users to input their own set of emissions factors for transportation and use those factors in place of running MOVES.

vmt_fraction could be updated to reflect 2015 or 2016 data.


# NONROAD Module

Calculate emissions from on-farm fuel combustion and equipment operation. Equipment types include tractors, combines, and trucks.

## GUI user options

The only NONROAD options available through the GUI is the run_nonroad flag that controls whether NONROAD is run.

## Advanced user options

TABLE: NONROAD temperature range.

| Temperature |             |
| ------------|-------------|
| Minimum     | 50.0 &deg;F |
| Mean        | 60.0 &deg;F |
| Maximum     | 68.8 &deg;F |

TABLE: Matching generic equipment types from the budget to specific NONROAD equipment and fuel types.

| Budget equipment names | NONROAD equipment types |
| ---------------------- | ----------------------- |
| tractor | Dsl - Agricultural Tractors |
| combine | Dsl - Combines |
| chipper | Dsl - Chippers/Stump Grinders (com) |
| loader | Dsl - Forest Eqp - Feller/Bunch/Skidder |
| other_forest_eqp | Dsl - Forest Eqp - Feller/Bunch/Skidder |
| chain_saw | Lawn & Garden Equipment Chain Saws |
| crawler | Dsl - Crawler Tractors |

## Module structure and function

## Output
Table of total emissions for off-road equipment operation

## Additional development

# Chemical Module

## GUI user options

The only GUI option for the chemical module is the run_chemical flag that controls whether the module is run.

## Advanced user options

There are no advanced user options for the chemical module within the chemical.ini file, but users may edit the input data files described below.

TABLE: NO (used as proxy for NO<sub>x</sub>) and NH<sub>3</sub> emission factors for application of nitrogenous fertilizers. NO emission factors obtained from FOA (2001) and GREET (ANL 2010); NH<sub>3</sub> factors obtained from Goebes et al. 2003 and Davidson et al. 2004.  See [Zhang et al. (2015)](https://onlinelibrary.wiley.com/doi/full/10.1002/bbb.1620) for additional information.
 
| N Fertilizer               | Pollutant      | Emission Factor | Units                             |
| -------------------------- | -------------- | --------------- | --------------------------------- |
| Anhydrous Ammonia          | NO             | 0.79            | % of N in fertilizer              |
| Anhydrous Ammonia          | NH<sub>3</sub> | 4.00            | % N volatilized as NH<sub>3</sub> |
| Ammonium Nitrate (33.5% N) | NO             | 3.80            | % of N in fertilizer              |
| Ammonium Nitrate (33.5% N) | NH<sub>3</sub> | 1.91            | % N volatilized as NH<sub>3</sub> |
| Ammonium Sulfate           | NO             | 3.50            | % of N in fertilizer              |
| Ammonium Sulfate           | NH<sub>3</sub> | 9.53            | % N volatilized as NH<sub>3</sub> |
| Urea (44 - 46% N)          | NO             | 0.90            | % of N in fertilizer              |
| Urea (44 - 46% N)          | NH<sub>3</sub> | 15.8            | % N volatilized as NH<sub>3</sub> |
| Nitrogen Solutions         | NO             | 0.79            | % of N in fertilizer              |
| Nitrogen Solutions         | NH<sub>3</sub> | 8.00            | % N volatilized as NH<sub>3</sub> |

TABLE: Distribution of nitrogenous fertilizers. The national average distribution from 2010 [(USDA)](https://www.ers.usda.gov/data-products/fertilizer-use-and-price.aspx#26720) is used for corn grain and stover, sorghum stubble, and wheat straw. The perennial crop distribution which consists of nitrogen solutions only is used for switchgrass, miscanthus and all forest products. (Turhollow, 2011, personal communication)

| N Fertilizer       | 2010 National Average Distribution | Perennial Crop Distribution |
|--------------------|------------------------------------|-----------------------------|
| Anhydrous Ammonia  | 0.3404                             | 0                           |
| Ammonium Nitrate   | 0.0247                             | 0                           |
| Ammonium Sulfate   | 0.0279                             | 0                           |
| Urea               | 0.2542                             | 0                           |
| Nitrogen Solutions | 0.3528                             | 1                           |

## Output

# Fugitive Dust Module

The fugitive dust module calculates PM2.5 and PM10 emissions from on-farm (harvest and non-harvest) activities. On-road fugitive dust from biomass transportation is not calculated.

## GUI user options

The only GUI option for the fugitive dust module is the run_fugdust flat that controls whether the module is run.

## Advanced user options

TABLE: Parameters controlling how biomass is transported on-farm from field to roadside.

| Parameter | Data Type | Default Value | Units | Description |
|-----------|-----------|---------------|-------|-------------|
| onfarm_truck_capacity | float | 15 | dry short tons/load | Amount of biomass that can be transported on-farm by one truck in one trip. |
| onfarm_default_distance | float | 1 | miles | Average distance that biomass is transported on-farm, from the field to the roadside. |

## Data and Calculations

## Output
