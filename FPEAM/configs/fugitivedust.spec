

## production table identifier (feedstock_measure in production data)
feedstock_measure_type = string

## on-farm truck capacity (dry short tons/load)
onfarm_truck_capacity = float(min=0.01, default=15)

## on-farm default distance to transport feedstock from field to roadside (miles)
onfarm_default_distance = float(min=0.01, default=1)

## pollutant emission factors for resources
emission_factors = filepath(default='../data/inputs/fugitive_dust_emission_factors.csv')
