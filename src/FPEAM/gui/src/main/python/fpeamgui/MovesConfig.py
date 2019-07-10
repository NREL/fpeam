import os, tempfile


def movesConfigCreation(tmpFolder, attributeValueObj):
    ini_template_string = """[moves]

    ### MOVES execution options

    ## Aggregation Level
    #aggregation_level = '{aggregation_level}'

    ## use existing results in MOVES output database or run MOVES for all counties
    #use_cached_results = {use_cached_results}

    ## production table identifier (feedstock_measure in production data)
    #feedstock_measure_type = '{feedstock_measure_type}'

    ## VMT per truck
    #VMT_per_truck = '{VMT_per_truck}'

    ## Number of trucks used
    #No_of_trucks_used = '{No_of_trucks_used}'

    ## start year (equipment year #1)
    #year = {year}

    #moves_path = '{moves_path}'
    #moves_datafiles_path = '{moves_datafiles_path}'


    ### input files

    ## truck capacities for feedstock transportation
    #truck_capacity = '{truck_capacity}'

    ## fuel fraction by engine type
    #avft = '{avft}'

    ## production region to MOVES FIPS mapping
    #region_fips_map = '{region_fips_map}'


    ### MOVES input options

    ## fraction of VMT by road type (must sum to 1)
    #[vmt_fraction]
    #rural_restricted = {rural_restricted}
    #rural_unrestricted = {rural_unrestricted}
    #urban_restricted = {urban_restricted}
    #urban_unrestricted = {urban_unrestricted}

    ## timespan(s)
    #[moves_timespan]
    #month = {month}
    #date = {date}
    #beginning_hour = {beginning_hour}
    #ending_hour = {ending_hour}
    #day_type = {day_type} """

    my_ini_config = ini_template_string.format(aggregation_level=attributeValueObj.aggegationLevel,
                                               use_cached_results=attributeValueObj.cachedResults,
                                               feedstock_measure_type=attributeValueObj.feedstockMeasureTypeMoves,
                                               VMT_per_truck=attributeValueObj.vMTPerTruck,
                                               No_of_trucks_used=attributeValueObj.noOfTrucksUsed,
                                               year=attributeValueObj.yearMoves,
                                               moves_path=attributeValueObj.movesPath,
                                               moves_datafiles_path=attributeValueObj.movesDatafilesPath,
                                               truck_capacity=attributeValueObj.truckCapacity,
                                               avft=attributeValueObj.avft,
                                               region_fips_map=attributeValueObj.regionFipsMapMoves,
                                               rural_restricted=attributeValueObj.ruralRestricted,
                                               rural_unrestricted=attributeValueObj.ruralUnrestricted,
                                               urban_restricted=attributeValueObj.urbanRestricted,
                                               urban_unrestricted=attributeValueObj.urbanUnrestricted,
                                               month=attributeValueObj.month, date=attributeValueObj.date,
                                               beginning_hour=attributeValueObj.beginningHr,
                                               ending_hour=attributeValueObj.endingHr,
                                               day_type=attributeValueObj.dayType)

    print(tmpFolder)

    my_ini_file_path = os.path.join(tmpFolder, "moves.ini")
    with open(my_ini_file_path, 'w') as f:
        f.write(my_ini_config)

    return my_ini_file_path
