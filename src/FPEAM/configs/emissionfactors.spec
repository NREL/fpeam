# production table identifier (feedstock_measure in production data)
feedstock_measure_type = string(default='harvested')

# emission factors as lb pollutant per lb resource subtype
emission_factors = filepath(default='data/inputs/emission_factors.csv')

# resource subtype distribution for all resources
resource_distribution = filepath(default='data/inputs/resource_distribution.csv')
