import os, tempfile

#Create Fugitve Dust config file
def fugitiveDustConfigCreation(tmpFolder, attributeValueObj):
    ini_template_string = """[fugitivedust]

## production table identifier (feedstock_measure in production data)
feedstock_measure_type = '{feedstock_measure_type}'

## pollutant emission factors for resources
emission_factors ='{emission_factors}'"""


    my_ini_config = ini_template_string.format(feedstock_measure_type=attributeValueObj.feedMeasureTypeFD,
                                               emission_factors=attributeValueObj.emissionFactorsFD)


    my_ini_file_path = os.path.join(tmpFolder, "fugitivedust.ini")
    with open(my_ini_file_path, 'w') as f:
        f.write(my_ini_config)

    return my_ini_file_path
