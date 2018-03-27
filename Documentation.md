# Introduction
FPEAM calculates air pollutants from agricultural activities and transportation associated with production of biomass for renewable energy.

Pollutants included are: CH<sub>4</sub>, NH<sub>3</sub>, NO<sub>x</sub>, SO<sub>x</sub>, VOC, PM2.5, PM10

## Code structure
FPEAM is organized into modules that calculate pollutant emissions from a particular activity category. Each module is described further in its own section.

* MOVES: Off-farm, on-road transportation of biomass to biorefineries.
* NONROAD: On-farm use of agricultural equipment.  Includes emissions from fuel combustion and equipment operation.
* Chemical: Emissions from volatilization of nitrogenous fertilizers, herbicides and insecticides.
* FugitiveDust: Fugitive dust (PM2.5 and PM10) emissions from on-farm transportation.

Config files are used for each module. Values in config files with sources


# MOVES Module

## User options (basic)
These are user options accessible with the built-in FPEAM GUI.

## User options (advanced)
These are user options that must be set directly in the moves.ini config file.

## Data and Calculations

## Output
Table of emission factors


# NONROAD Module
Calculate emissions from on-farm fuel combustion and equipment operation. Equipment types include tractors, combines, and trucks.

## User options (basic)

## User options (advanced)

## Data and Calculations

## Output
Table of total emissions for off-road equipment operation

# Chemical Module

## User options (basic)

## User options (advanced)

## Data and Calculations

Data sources for NOX:
 ANL. 2012. Green House Gases, Regulated Emissions, and Energy Use in Transportation (GREET) Model version 1 2012 revision 2. Lemont, IL: Argonne National Laboratory. Available at: http://greet.es.anl.gov/.
	In 2017 model, see sheet EtOH cell D489 for possible source of 0.79 number
	Cannot find other NOx numbers in 2017, 2012 or GREET publications
	
 EPA. 2011a. NEI Technical Support Documentation. U.S. Environmental Protection Agency. Available at https://www.epa.gov/air-emissions-inventories/2011-national-emissions-inventory-nei-technical-support-document.
	See table 2-2: NEI does not estimate NOX emissions from fertilizer application, only NH3.
	
Data source for NH3:
 EPA. 2015. 2011 National Emissions Inventory, version 2 Technical Support Document. Emissions Inventory and Analysis Group.  Research Triangle Park, NC: EPA. Available at: https://www.epa.gov/air-emissions-inventories/2011-national-emissions-inventory-nei-technical-support-document.

 TABLE: NO<sub>x</sub> and NH<sub>3</sub> emission factors for application of nitrogenous fertilizers.
 
| N Fertilizer       | Pollutant      | % Fertilizer Volatilized as Pollutant |
| ------------------ | -------------- | ------------------------------------- |
| Anhydrous Ammonia  | NO<sub>x</sub> | 0.79                                  |
| Anhydrous Ammonia  | NH<sub>3</sub> | 4.00                                  |
| Ammonium Nitrate   | NO<sub>x</sub> | 3.80                                  |
| Ammonium Nitrate   | NH<sub>3</sub> | 1.91                                  |
| Ammonium Sulfate   | NO<sub>x</sub> | 3.50                                  |
| Ammonium Sulfate   | NH<sub>3</sub> | 9.53                                  |
| Urea               | NO<sub>x</sub> | 0.90                                  |
| Urea               | NH<sub>3</sub> | 15.8                                  |
| Nitrogen Solutions | NO<sub>x</sub> | 0.79                                  |
| Nitrogen Solutions | NH<sub>3</sub> | 8.00                                  |

@TODO add in source, table for fertilizer SCC codes

@TODO find and add source for n fertilizer allocation (BTS)

TABLE: Distribution of nitrogenous fertilizers. The national average distribution is used for corn grain and stover, sorghum stubble, and wheat straw. The perennial crop distribution is used for switchgrass, miscanthus and all forest products.

| N Fertilizer       | National Average Distribution | Perennial Crop Distribution |
|--------------------|-------------------------------|-----------------------------|
| Anhydrous Ammonia  | 0.3404                        | 0                           |
| Ammonium Nitrate   | 0.0247                        | 0                           |
| Ammonium Sulfate   | 0.0279                        | 0                           |
| Urea               | 0.2542                        | 0                           |
| Nitrogen Solutions | 0.3528                        | 1                           |

## Output

# Fugitive Dust Module

## User options (basic)

## User options (advanced)

## Data and Calculations

## Output