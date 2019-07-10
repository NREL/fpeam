import os, tempfile


def emissionFactorsConfigCreation(tmpFolder, attributeValueObj):


    my_ini_config = "[emissionfactors] \n"

    if attributeValueObj.feedMeasureTypeEF:

        temp_string = "## production table identifier (feedstock_measure in production data) \n" \
                        + "feedstock_measure_type = '{feedstock_measure_type}' \n"
        my_ini_config += temp_string.format(feedstock_measure_type=attributeValueObj.feedMeasureTypeEF)

    if attributeValueObj.emissionFactorsEF:

        temp_string = "## emission factors as lb pollutant per lb resource subtype \n" \
                        + "emission_factors = '{emission_factors}' \n"

        my_ini_config += temp_string.format(emission_factors = attributeValueObj.emissionFactorsEF)

    if attributeValueObj.resourceDistributionEF:

        temp_string = "## resource subtype distribution for all resources \n" \
                + "resource_distribution = '{resource_distribution}' \n"

        my_ini_config += temp_string.format(resource_distribution = attributeValueObj.resourceDistributionEF)

    # my_ini_config = ini_template_string.format(feedstock_measure_type=attributeValueObj.feedMeasureTypeEF,
    #                                            emission_factors = attributeValueObj.emissionFactorsEF,
    #                                            resource_distribution = attributeValueObj.resourceDistributionEF)


    my_ini_file_path = os.path.join(tmpFolder,"emissionfactors.ini")
    with open(my_ini_file_path, 'w') as f:
        f.write(my_ini_config)

    return my_ini_file_path

    ##########################
    #
    #
    # with open(my_ini_file_path) as f:
    #     print(my_ini_file_path)
    #     #print(f.read())
    #     pass
    #
    #
    #os.system("fpim "+my_ini_file_path)
