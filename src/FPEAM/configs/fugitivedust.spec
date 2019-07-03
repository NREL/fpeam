

## production table identifier (feedstock_measure in production data)
feedstock_measure_type = string(default='harvested')

## particulate matter emission factors by acreage
fugitive_dust_factors = filepath(default='data/inputs/fugitive_dust_emission_factors.csv')

## road silt content by state
silt_content = filepath(default='data/inputs/fugitive_dust_silt_content.csv')

## constants for calculating onroad fugitive dust
fugitive_dust_onroad_constants = filepath(default='data/inputs/fugitive_dust_onroad_constants.csv')
