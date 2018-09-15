

# production table identifier (feedstock_measure in production data)
feedstock_measure_type = string

# percent VOC content (%)
voc_content_percent = float(0, 1, default=0.834)

# VOC evaporation rate (%)
voc_evaporation_rate = float(default=0.9)

# emission factors as lb pollutant per lb resource subtype
emission_factors = filepath(default='../data/inputs/emission_factors.csv')

# resource subtype distribution for all resources
resource_distribution = filepath(default='../data/inputs/resource_distribution.csv')
