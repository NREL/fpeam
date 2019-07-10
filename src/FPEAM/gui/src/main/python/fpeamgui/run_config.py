import os, tempfile, self


def runConfigCreation(tmpFolder, attributeValueObj):

    ini_template_string = """[run_config]
## run identifier
scenario_name = '{scenario_name}'
    
## project output directory
project_path = '{project_path}'

## modules to run
modules = {modules}

## logging verbosity level (CRITICAL, ERROR, WARNING, INFO, DEBUG, UNSET)
logger_level = {logger_level}

## data paths
equipment = '{equipment}'
production = '{production}'
feedstock_loss_factors = '{feedstock_loss_factors}'

## MOVES routing graph
transportation_graph = '{transportation_graph}'


## data backfill flag
backfill = {backfill}

## use the router engine to calculate vmt by county
use_router_engine = {use_router_engine} """


    my_ini_config = ini_template_string.format(scenario_name=attributeValueObj.scenarioName,
                                               project_path=attributeValueObj.projectPath,
                                               modules = attributeValueObj.module ,
                                               logger_level = attributeValueObj.loggerLevel ,
                                               equipment = attributeValueObj.equipment,
                                               production = attributeValueObj.production,
                                               feedstock_loss_factors = attributeValueObj.feedstockLossFactors,
                                               transportation_graph = attributeValueObj.transportationGraph,
                                               backfill = attributeValueObj.backfill,
                                               use_router_engine = attributeValueObj.useRouterEngine)

    print(tmpFolder)

    my_ini_file_path = os.path.join(tmpFolder,"run_config.ini")
    with open(my_ini_file_path, 'w') as f:
        f.write(my_ini_config)



    ##########################

    #
    # with open(my_ini_file_path) as f:
    #     print(my_ini_file_path)
    #     #print(f.read())
    #     pass

    return my_ini_file_path