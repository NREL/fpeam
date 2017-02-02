# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 15:07:58 2016

Imports production data into database

@author: aeberle
"""
# import pymysql
import os
import csv
from src.AirPollution.utils import config, logger
from model.Database import Database

INCLUDE_OAT_BARLEY_STRAW = config.get('include_oat_barley_straw')


class LoadData:
    """
    Loads data for FPEAM feedstocks
    Includes production data (e.g., harvested acreage, dry tons produced)
             transportation data (e.g., mileage traveled from field to depot)
             chemical data (e.g., pesticide and fertilizer usage)
             equipment data (e.g., power and activity rate of tractors)
    Also includes load_scenario_data function to load data for specific scenario into {feed}_data tables (if desired)
    """

    def __init__(self, scenario_year, scenario_yield):

        # get database object
        title = config.get('title')
        self.db = Database(model_run_title=title)

        # specify year and case for this scenario
        self.scenario_year = scenario_year
        self.scenario_case = scenario_yield

        # set production and constants schema
        self.production_schema = config.get('production_schema')
        self.constants_schema = config.get('constants_schema')

        # file paths for input data
        self.filepath_equip = './development/input_data/equip_budgets/'
        self.filepath_prod = './development/input_data/current_ag/'
        self.filepath_prod_fr = './development/input_data/forestry_prod_data/'

        # file names for equipment budgets
        self.equipfiles = {'cg': 'bdgtconv_20151215.csv',
                           'sg': 'bdgtengy_20160114.csv',
                           'ws': 'bdgtconv_20151215.csv',
                           'cs': 'bdgtconv_20151215.csv',
                           'ms': 'bdgtengy_20160114.csv',
                           'fr': 'bdgtfrst_20151229.csv',
                           'fw': 'bdgtfrst_20151229.csv',
                           'ss': 'bdgtconv_20151215.csv'}

        # create new schema for production data
        # @TODO: this should probably include a backup
        query_create_schema = """DROP SCHEMA IF EXISTS {s}; CREATE SCHEMA {s};""".format(s=self.production_schema)
        self.db.execute_sql(query_create_schema)

        # get list of all years, feedstocks, and (yield) cases for production data
        self.year_list = ['2017', '2040']  # years of production data for agricultural crops
        self.fr_year_list = ['2017', '2040'] # years of production data for forestry
        self.feedstock_list = ['cg', 'cs', 'sg', 'ws', 'ms', 'ss']  # shorthand for feedstocks
        self.case_list = ['bc', 'hh']  # yield case for production data (bc: base case, hh: high yield)

        # dictionaries for production data
        self.crop_dict_production_data = {'cg': 'Corn', 'cs': 'Corn stover', 'sg': 'Switchgrass', 'ws': 'Wheat straw', 'ms': 'Miscanthus', 'fr': 'Forest residue', 'fw': 'Forest whole', 'ss': 'Sorghum stubble'}  # names of feedstocks in production data
        self.filename_dict = {'bc': 'bc1060', 'hh': 'hh3060'}  # changes to production file names for base case and high yield

        # dictionaries for equipment data
        self.oper_type = {'Harvest': 'HRV', 'Establish': 'EST', 'Maintain': 'MNT'}
        self.act_dict = {'HRV': 'Harvest', 'EST': 'Nonharvest', 'MNT': 'Nonharvest', 'HARV': 'Harvest', 'ESTC': 'Nonharvest'}
        self.feeddict_read = {'cg': {'Crop_name': 'Corn', 'Oper_type': 'C'},  # oper_type 'R' = residue, 'C' = crop
                              'sg': {'Crop_name': 'Switchgrass', 'Oper_type': 'C'},
                              'ws': {'Crop_name': 'Wheat', 'Oper_type': 'R'},
                              'cs': {'Crop_name': 'Corn', 'Oper_type': 'R'},
                              'ms': {'Crop_name': 'Miscanthus', 'Oper_type': 'C'},
                              'ss': {'Crop_name': 'Sorghum', 'Oper_type': 'R'}}
        self.feeddict_out = {'cg': 'Corn Grain', 'sg': 'Switchgrass', 'ws': 'Wheat Straw', 'cs': 'Corn Stover', 'ms': 'Miscanthus', 'fr': 'Forest residue', 'fw': 'Forest whole', 'ss': 'Sorghum stubble'}  # feedstock names for output
        self.db_table_names = {'cg': 'cg_equip', 'sg': 'sg_equip', 'ws': 'ws_equip', 'cs': 'cs_equip', 'ms': 'ms_equip', 'fr': 'fr_equip', 'fw': 'fw_equip', 'ss': 'ss_equip'}  # database table names
        self.equipdic = {'Tractor': 'Dsl - Agricultural Tractors',
                         'Combine': 'Dsl - Combines',
                         'Single-axle Truck': 'Dsl - Agricultural Tractors',
                         'Aerial': 'Aerial',
                         'Planting - Miscanthus': 'Dsl - Agricultural Tractors'}  # equipment dictionary for nonroad
        self.equip_type_dict = {'Tractor': 'tractor',
                                'Combine': 'combine',
                                'Single-axle Truck': 'tractor',
                                'Aerial': 'aerial',
                                'Planting - Miscanthus': 'tractor'}
        self.loading_equip = config.get('loading_equip')

        # dictionaries for chemical data (pesticides and fertilizers)
        self.crop_type_chem = {'cg': 'conv', 'cs': 'conv', 'ws': 'conv', 'sg': 'energy', 'ms': 'energy', 'ss': 'conv'}  # crop type: either conventional (conv) or energy (energy)
        # @TODO: need to make sure other modules are using these same values automatically
        self.col_dict_chem = {'cg': ['n_lbac', 'p2o5_lbac', 'k2o_lbac', 'lime_lbac', 'herb_lbac', 'insc_lbac'],
                              'cs': ['n_lbdt', 'p2o5_lbdt', 'k2o_lbdt', 'lime_lbdt', 'herb_lbac', 'insc_lbac'],
                              'ws': ['n_lbdt', 'p2o5_lbdt', 'k2o_lbdt', 'lime_lbdt', 'herb_lbac', 'insc_lbac'],
                              'ss': ['n_lbdt', 'p2o5_lbdt', 'k2o_lbdt', 'lime_lbdt', 'herb_lbac', 'insc_lbac'],
                              'sg_yr1': ['n_lbac', 'p2o5_lbac', 'k2o_lbac', 'lime_lbac', 'herb_lbac', 'insc_lbac'],
                              'sg_yr2to10': ['n_lbdt', 'p2o5_lbdt', 'k2o_lbdt', 'lime_lbdt', 'herb_lbac', 'insc_lbac'],
                              'ms_yr1': ['n_lbac', 'p2o5_lbac', 'k2o_lbac', 'lime_lbac', 'herb_lbac', 'insc_lbac'],
                              'ms_yr2to10': ['n_lbdt', 'p2o5_lbdt', 'k2o_lbdt', 'lime_lbdt', 'herb_lbac', 'insc_lbac']}  # column names for chemicals used for each crop

        # variables for joining fips_region
        self.fipsregion_table_name = 'fips_region'
        self.table_list = ['chem', 'equip']  # list for tables that require fips-region join (both chemical (chem) and equipment (equip) need to be joined with fips)

        # variables for transportation data
        self.crop_type_list = ['herb', 'woody']  # crop types (herbaceous or woody)
        self.system_list = {'2017': {'conv'}, '2040': {'adv'}}  # type of logistics system used by scenario year
        self.trans_case_list = {'2017': {'bc'}, '2040': {'bc', 'hh'}}  # list of yield types for scenario years
        self.year_sub = {'2017': '2017', '2040': '2040'}  # substitution value for 2017 transport data (2022 was previously used for 2017)
        # list of columns in transportation table
        self.column_dict = {'conv': 'feed_id char(55), sply_fips char(5), used_qnty float(15,5), avg_total_cost float(15,5), avg_dist int',
                            'adv': 'feed_id char(55), sply_fips char(5), used_qnty float(15,5), avg_flddep_dist float(15,5), avg_depref_dist float(15,5), avg_total_cost float(15,5), avg_dist int'}

        # variables for forestry equipment
        self.forestry_feed_list = ['fr', 'fw', ]  # list of forestry types (forest residues (fr) and whole trees (fw))
        # dictionary for identifying crop budgets for each forestry type
        self.bdgt_dict = {'fw': 'TREE', 'fr': 'RESD', }

    def load_production_data(self):
        # create and populate tables for production data
        # loop through years and crops, load raw data, pivot tables, insert into new FPEAM data table for production
        for year in self.year_list:
            for case in self.case_list:
                # specify path for raw data file
                fname = "{filename_change}{year}prod_20160126.csv".format(filename_change=self.filename_dict[case], year=year)
                fpath = os.path.join(self.filepath_prod, fname)

                kvals = {'prod': self.production_schema,
                         'case': case,
                         'year': year,
                         'filename': fpath}

                # logger.debug('Dropping {prod}.herb_{case}_{year};'.format(**kvals))
                #
                # # create query for generating raw data table
                sql = "DROP TABLE IF EXISTS {prod}.herb_{case}_{year};".format(**kvals)
                self.db.execute_sql(sql)

                # create table for raw data
                logger.debug('Creating {prod}.herb_{case}_{year};'.format(**kvals))
                query_create_rawtable = """
                CREATE TABLE {prod}.herb_{case}_{year}
                (scenario varchar(10),
                 year	  char(4),
                 crop	  char(25),
                 till	  char(2),
                 fips	  char(5),
                 polyfrr  char(2),
                 plnt	  float(15, 5),
                 harv	  float(15, 5),
                 prod	  float(15, 5),
                 yield	  float(15, 5),
                 produnit text,
                 yldunit text
                );""".format(**kvals)
                # execute query
                self.db.execute_sql(query_create_rawtable)

                # create query for loading raw data file
                logger.debug('Loading raw data into {prod}.herb_{case}_{year}'.format(**kvals))
                query_load_rawdata = """
                LOAD DATA LOCAL INFILE "{filename}"
                INTO TABLE {prod}.herb_{case}_{year}
                COLUMNS TERMINATED BY ','
                OPTIONALLY ENCLOSED BY '"'
                ESCAPED BY '"'
                LINES TERMINATED BY '\n'
                IGNORE 1 LINES
                (scenario, year, crop, till, @fips, polyfrr, @plnt, @harv, @prod, @yield, produnit, yldunit)
                SET
                 fips = LPAD(@fips, 5, '0'),
                 plnt = nullif(@plnt, ''),
                 harv = nullif(@harv, ''),
                 prod = nullif(@prod, ''),
                 yield = nullif(@yield, '')
                ;""".format(**kvals)
                # execute query
                self.db.execute_sql(query_load_rawdata)

                # create indices
                for col in ('year', 'crop', 'till', 'fips', 'polyfrr', 'plnt', 'harv', 'prod', 'yield'):
                    sql = """CREATE INDEX idx_herb_{case}_{year}_{col} ON {prod}.herb_{case}_{year} ({col});""".format(col=col, **kvals)
                    self.db.execute_sql(sql)

                for crop in self.feedstock_list:
                    # update kvals dictionary with crop names
                    kvals.update({'crop': crop, 'cropname': self.crop_dict_production_data[crop]})

                    logger.info("Loading data for crop: {crop}, year: {year}, case: {case}".format(**kvals))

                    # check to see if other straws should be included with wheat straw
                    if crop == 'ws' and INCLUDE_OAT_BARLEY_STRAW is True:
                        kvals['selection'] = """crop = 'Oats straw' OR crop = 'Wheat straw' OR crop = 'Barley straw'"""
                    else:
                        kvals['selection'] = """crop = '{cropname}'""".format(**kvals)

                    # drop view
                    sql = """DROP VIEW IF EXISTS {prod}.{crop}_extended;""".format(**kvals)
                    self.db.execute_sql(sql)

                    # create query to generate extended table view
                    logger.debug('Creating extended view {prod}.{crop}_extended'.format(**kvals))
                    query_view_extend = """
                    CREATE VIEW {prod}.{crop}_extended AS (
                      SELECT
                            fips,
                            CASE WHEN till = 'CT' THEN (IF(harv > 0, SUM(IFNULL(prod, 0)) / SUM(IFNULL(harv, 0)), 0)) END AS convtill_yield,
                            CASE WHEN till = 'RT' THEN (IF(harv > 0, SUM(IFNULL(prod, 0)) / SUM(IFNULL(harv, 0)), 0)) END AS reducedtill_yield,
                            CASE WHEN till = 'NT' THEN (IF(harv > 0, SUM(IFNULL(prod, 0)) / SUM(IFNULL(harv, 0)), 0)) END AS notill_yield,
                            CASE WHEN till = 'CT' THEN SUM(IFNULL(prod, 0))                                           END AS convtill_prod,
                            CASE WHEN till = 'RT' THEN SUM(IFNULL(prod, 0))                                           END AS reducedtill_prod,
                            CASE WHEN till = 'NT' THEN SUM(IFNULL(prod, 0))                                           END AS notill_prod,
                            CASE WHEN till = 'CT' THEN SUM(IFNULL(harv, 0))                                           END AS convtill_harv_ac,
                            CASE WHEN till = 'RT' THEN SUM(IFNULL(harv, 0))                                           END AS reducedtill_harv_ac,
                            CASE WHEN till = 'NT' THEN SUM(IFNULL(harv, 0))                                           END AS notill_harv_ac,
                            CASE WHEN till = 'CT' THEN SUM(IFNULL(plnt, 0))                                           END AS convtill_planted_ac,
                            CASE WHEN till = 'RT' THEN SUM(IFNULL(plnt, 0))                                           END AS reducedtill_planted_ac,
                            CASE WHEN till = 'NT' THEN SUM(IFNULL(plnt, 0))                                           END AS notill_planted_ac
                      FROM {prod}.herb_{case}_{year}
                      WHERE {selection}
                      GROUP BY fips, till
                    );""".format(**kvals)
                    # execute query
                    self.db.execute_sql(query_view_extend)

                    # drop view
                    sql = """DROP VIEW IF EXISTS {prod}.{crop}_extended_pivot;""".format(**kvals)
                    self.db.execute_sql(sql)

                    # create query to pivot extended table view
                    logger.debug('Creating pivot table {prod}.{crop}_extended_pivot'.format(**kvals))
                    query_pivot = """
                    CREATE VIEW {prod}.{crop}_extended_pivot AS
                     (SELECT
                            fips,
                            SUM(convtill_yield)         AS convtill_yield,
                            SUM(reducedtill_yield)      AS reducedtill_yield,
                            SUM(notill_yield)           AS notill_yield,
                            SUM(convtill_prod)          AS convtill_prod,
                            SUM(reducedtill_prod)       AS reducedtill_prod,
                            SUM(notill_prod)            AS notill_prod,
                            SUM(convtill_harv_ac)       AS convtill_harv_ac,
                            SUM(reducedtill_harv_ac)    AS reducedtill_harv_ac,
                            SUM(notill_harv_ac)         AS notill_harv_ac,
                            SUM(convtill_planted_ac)    AS convtill_planted_ac,
                            SUM(reducedtill_planted_ac) AS reducedtill_planted_ac,
                            SUM(notill_planted_ac)      AS notill_planted_ac
                      FROM {prod}.{crop}_extended
                      GROUP BY fips
                     )
                    ;""".format(**kvals)
                    # execute query
                    self.db.execute_sql(query_pivot)

                    # drop view
                    sql = """DROP VIEW IF EXISTS {prod}.{crop}_extended_pivot_pretty;""".format(**kvals)
                    self.db.execute_sql(sql)

                    # create query to get rid of extra rows
                    logger.debug('Creating pretty pivot {prod}.{crop}_extended_pivot_pretty'.format(**kvals))
                    query_pretty = """
                    CREATE VIEW {prod}.{crop}_extended_pivot_pretty AS
                     (SELECT
                            fips,
                            COALESCE(convtill_yield,         0) AS convtill_yield,
                            COALESCE(reducedtill_yield,      0) AS reducedtill_yield,
                            COALESCE(notill_yield,           0) AS notill_yield,
                            COALESCE(convtill_prod,          0) AS convtill_prod,
                            COALESCE(reducedtill_prod,       0) AS reducedtill_prod,
                            COALESCE(notill_prod,            0) AS notill_prod,
                            COALESCE(convtill_harv_ac,       0) AS convtill_harv_ac,
                            COALESCE(reducedtill_harv_ac,    0) AS reducedtill_harv_ac,
                            COALESCE(notill_harv_ac,         0) AS notill_harv_ac,
                            COALESCE(convtill_planted_ac,    0) AS convtill_planted_ac,
                            COALESCE(reducedtill_planted_ac, 0) AS reducedtill_planted_ac,
                            COALESCE(notill_planted_ac,      0) AS notill_planted_ac
                      FROM {prod}.{crop}_extended_pivot
                     )
                    ;""".format(**kvals)
                    # execute query
                    self.db.execute_sql(query_pretty)

                    # drop table
                    sql = """DROP TABLE IF EXISTS {prod}.{crop}_data_{case}_{year};""".format(**kvals)
                    self.db.execute_sql(sql)

                    # create query to create table for FPEAM production data
                    logger.debug('Creating {prod}.{crop}_data_{case}_{year}'.format(**kvals))
                    query_create_table = """
                    CREATE TABLE           {prod}.{crop}_data_{case}_{year}
                     (fips	                char(5),
                      convtill_yield         float(15, 5),
                      convtill_planted_ac    float(15, 5),
                      convtill_harv_ac       float(15, 5),
                      convtill_prod          float(15, 5),
                      reducedtill_yield      float(15, 5),
                      reducedtill_planted_ac float(15, 5),
                      reducedtill_harv_ac    float(15, 5),
                      reducedtill_prod       float(15, 5),
                      notill_yield           float(15, 5),
                      notill_planted_ac      float(15, 5),
                      notill_harv_ac         float(15, 5),
                      notill_prod            float(15, 5),
                      total_prod             float(15, 5),
                      total_harv_ac          float(15, 5)
                     )
                    ;""".format(**kvals)
                    # execute query
                    self.db.execute_sql(query_create_table)

                    # create query for inserting data into production table
                    logger.debug('Inserting cleaned data into {prod}.{crop}_data_{case}_{year}'.format(**kvals))
                    query_insert_data = """
                    INSERT INTO {prod}.{crop}_data_{case}_{year} (fips, convtill_yield, convtill_planted_ac, convtill_harv_ac, convtill_prod, reducedtill_harv_ac,
                                                                  reducedtill_planted_ac, reducedtill_prod, reducedtill_yield, notill_harv_ac, notill_planted_ac,
                                                                  notill_prod, notill_yield, total_prod, total_harv_ac)
                    SELECT  LPAD(fips, 5, '0'),
                            convtill_yield,
                            convtill_planted_ac,
                            convtill_harv_ac,
                            convtill_prod,
                            reducedtill_harv_ac,
                            reducedtill_planted_ac,
                            reducedtill_prod,
                            reducedtill_yield,
                            notill_harv_ac,
                            notill_planted_ac,
                            notill_prod,
                            notill_yield,
                            convtill_prod + reducedtill_prod + notill_prod,
                            convtill_harv_ac + reducedtill_harv_ac + notill_harv_ac
                    FROM {prod}.{crop}_extended_pivot_pretty""".format(**kvals)
                    # execute query
                    # logger.info("Inserting data into {crop}_data_{case}_{year} table".format(**kvals))
                    self.db.execute_sql(query_insert_data)

                    # create indicies
                    for col in ('fips', 'convtill_yield', 'convtill_planted_ac', 'convtill_harv_ac', 'convtill_prod', 'reducedtill_yield', 'reducedtill_planted_ac', 'reducedtill_harv_ac', 'reducedtill_prod', 'notill_yield', 'notill_planted_ac', 'notill_harv_ac', 'notill_prod', 'total_prod', 'total_harv_ac'):
                        sql = """CREATE INDEX idx_{crop}_data_{case}_{year}_{col} ON {prod}.{crop}_data_{case}_{year} ({col});""".format(col=col, **kvals)
                        self.db.execute_sql(sql)

    def load_scenario_data(self):
        # once all data are loaded, select correct data for scenario

        # loop through crops in feedstock list
        list_total = [j for i in [self.feedstock_list, self.forestry_feed_list] for j in i]
        for scenario_crop in list_total:
            # create kvals dictionary for sql queries
            kvals = {'prod': self.production_schema,
                     'scenario_year': self.scenario_year,
                     'scenario_case': self.scenario_case,
                     'scenario_crop': scenario_crop,
                     }

            # drop table
            sql = """DROP TABLE IF EXISTS {prod}.{scenario_crop}_data;""".format(**kvals)
            self.db.execute_sql(sql)

            # create scenario data table for scenario_crop
            query_scenario_table = """
                    CREATE TABLE {prod}.{scenario_crop}_data(fips	char(5),
                            convtill_yield float(15,5),
                            convtill_planted_ac float(15,5),
                            convtill_harv_ac float(15,5),
                            convtill_prod float(15,5),
                            reducedtill_yield float(15,5),
                            reducedtill_planted_ac float(15,5),
                            reducedtill_harv_ac float(15,5),
                            reducedtill_prod float(15,5),
                            notill_yield float(15,5),
                            notill_planted_ac float(15,5),
                            notill_harv_ac float(15,5),
                            notill_prod float(15,5),
                            total_prod float(15,5),
                            total_harv_ac float(15,5),
                            bdgt char(25)
                            );""".format(**kvals)
            # execute query
            self.db.execute_sql(query_scenario_table)

            # create query for inserting data for scenario_crop
            if scenario_crop == 'fr' or scenario_crop == 'fw':
                query_scenario_data = """
                        INSERT INTO {prod}.{scenario_crop}_data (fips, convtill_yield, convtill_planted_ac, convtill_harv_ac, convtill_prod, reducedtill_harv_ac,
                                                                 reducedtill_planted_ac, reducedtill_prod, reducedtill_yield, notill_harv_ac, notill_planted_ac, notill_prod,
                                                                 notill_yield, total_prod, total_harv_ac, bdgt)
                        SELECT  fips,
                                convtill_yield,
                                convtill_planted_ac,
                                convtill_harv_ac,
                                convtill_prod,
                                reducedtill_harv_ac,
                                reducedtill_planted_ac,
                                reducedtill_prod,
                                reducedtill_yield,
                                notill_harv_ac,
                                notill_planted_ac,
                                notill_prod,
                                notill_yield,
                                total_prod,
                                total_harv_ac,
                                bdgt
                        FROM {prod}.{scenario_crop}_data_{scenario_case}_{scenario_year}""".format(**kvals)
                # execute query
                self.db.execute_sql(query_scenario_data)
            else:
                query_scenario_data = """
                        INSERT INTO {prod}.{scenario_crop}_data (fips, convtill_yield, convtill_planted_ac, convtill_harv_ac, convtill_prod, reducedtill_harv_ac,
                                                                 reducedtill_planted_ac, reducedtill_prod, reducedtill_yield, notill_harv_ac, notill_planted_ac, notill_prod,
                                                                 notill_yield, total_prod, total_harv_ac, bdgt)
                        SELECT  fips,
                                convtill_yield,
                                convtill_planted_ac,
                                convtill_harv_ac,
                                convtill_prod,
                                reducedtill_harv_ac,
                                reducedtill_planted_ac,
                                reducedtill_prod,
                                reducedtill_yield,
                                notill_harv_ac,
                                notill_planted_ac,
                                notill_prod,
                                notill_yield,
                                total_prod,
                                total_harv_ac,
                                'NULL'
                        FROM {prod}.{scenario_crop}_data_{scenario_case}_{scenario_year}""".format(**kvals)
                # execute query
                self.db.execute_sql(query_scenario_data)

            # create indices
            for col in ('fips', 'convtill_yield', 'convtill_planted_ac', 'convtill_harv_ac', 'convtill_prod', 'reducedtill_harv_ac',
             'reducedtill_planted_ac', 'reducedtill_prod', 'reducedtill_yield', 'notill_harv_ac', 'notill_planted_ac',
             'notill_prod',
             'notill_yield', 'total_prod', 'total_harv_ac', 'bdgt'):
                sql = """CREATE INDEX idx_{scenario_crop}_data_{col} ON {prod}.{scenario_crop}_data ({col});""".format(col=col, **kvals)
                self.db.execute_sql(sql)

    def execute_equip_query(self, kvals):
        # execute query for equipment data
        # param: kvals = dictionary of values for string formatting of sql query
        # param: feed = feedstock name

        # create query for inserting data into equipment table
        query = ("""
                    INSERT INTO {prod}.{table}
                    (bdgt_id, region, feedstock, bdgtyr,
                     tillage, oper_type,
                     machinery, equip_type,
                     hp, fuel_consump,
                     activity, activity_rate_hrperac,
                     n_lbac, p2o5_lbac,
                     k2o_lbac, lime_lbac,
                     n_lbdt, p2o5_lbdt,
                     k2o_lbdt, lime_lbdt,
                     herb_lbac, insc_lbac)
                    VALUES
                    ('NULL',
                     '{region}',
                     '{feedstock}',
                     '{bdgtyr}',
                     '{tillage}',
                     '{oper_type}',
                     '{machinery}',
                     '{equip_type}',
                     {hp},
                     {fuel_consump},
                     '{activity}',
                     {activity_rate},
                     {n_lbac},
                     {p2o5_lbac},
                     {k2o_lbac},
                     {lime_lbac},
                     {n_lbdt},
                     {p2o5_lbdt},
                     {k2o_lbdt},
                     {lime_lbdt},
                     {herb_lbac},
                     {insc_lbac})
                    ;""").format(**kvals)
        # execute query and insert data into database
        self.db.execute_sql(query)

    def execute_equip_query_fr(self, kvals):
        # execute query for equipment data
        # param: kvals = dictionary of values for string formatting of sql query
        # param: feed = feedstock name

        # create query for inserting data into equipment table
        query = ("""
                    INSERT INTO {prod}.{table}
                    (bdgt_id, feedstock, bdgtyr, tillage, machinery, equip_type, hp, fuel_consump, activity, activity_rate_hrperdt,
                     activity_rate_hrperac, n_lbac, p2o5_lbac, k2o_lbac, lime_lbac, n_lbdt, p2o5_lbdt, k2o_lbdt, lime_lbdt, herb_lbac, insc_lbac)
                    VALUES
                    ('{bdgt_id}',
                     '{feedstock}',
                     '{bdgtyr}',
                     '{tillage}',
                     '{machinery}',
                     '{equip_type}',
                     {hp},
                     {fuel_consump},
                     '{activity}',
                     {activity_rate_hrperdt},
                     {activity_rate_hrperac},
                     {n_lbac},
                     {p2o5_lbac},
                     {k2o_lbac},
                     {lime_lbac},
                     {n_lbdt},
                     {p2o5_lbdt},
                     {k2o_lbdt},
                     {lime_lbdt},
                     {herb_lbac},
                     {insc_lbac})
                    ;""").format(**kvals)
        # execute query and insert data into database
        self.db.execute_sql(query)

    def load_equip_data(self):
        # load equipment data for all feedstocks

        for feed in self.feedstock_list:
            logger.info('Loading equipment data for feedstock: %s' % (feed, ))
            crop = self.feeddict_out[feed]
            # drop table
            sql = """DROP   TABLE IF EXISTS {prod}.{table};""".format(table=self.db_table_names[feed], prod=self.production_schema)
            self.db.execute_sql(sql)

            query = """
                    CREATE TABLE           {prod}.{table}
                     (bdgt_id               char(25),
                      region                char(2),
                      feedstock             char(55),
                      bdgtyr                char(2),
                      tillage               char(55),
                      oper_type             char(55),
                      machinery             char(55),
                      equip_type            char(30),
                      hp                    float(15, 5),
                      fuel_consump          float(15, 5),
                      activity              char(55),
                      activity_rate_hrperac float(15, 5),
                      activity_rate_hrperdt float(15, 5),
                      n_lbac                float(15, 5),
                      p2o5_lbac             float(15, 5),
                      k2o_lbac              float(15, 5),
                      lime_lbac             float(15, 5),
                      n_lbdt                float(15, 5),
                      p2o5_lbdt             float(15, 5),
                      k2o_lbdt              float(15, 5),
                      lime_lbdt             float(15, 5),
                      herb_lbac             float(15, 5),
                      insc_lbac             float(15, 5)
                     )
                    ;""".format(table=self.db_table_names[feed], prod=self.production_schema)

            # execute query to create new table in production database
            self.db.execute_sql(query)

            # set filename to the correct value using equipfiles dictionary
            filename = os.path.join(self.filepath_equip, self.equipfiles[feed])
            # read csv file for feedstock equipment
            reader = csv.reader(open(filename, 'rU'))

            # loop through rows in csv reader
            header_dict = dict()
            for i, row in enumerate(reader):
                # if first row, set values in header dictionary
                if i == 0:
                    headers = row
                    for j in range(0, len(headers)):
                        header_dict[headers[j]] = j
                # otherwise, get data from row, manipulate it, and then insert into database
                else:
                    # if the crop type in the csv file corresponds with the feedstock in the feedstock loop, get data and create query
                    if row[header_dict['crop']] == self.feeddict_read[feed]['Crop_name']:
                        # loop through operation types in oper_type dictionary (e.g., harvest, maintain, establish)
                        for operation in self.oper_type:
                            opertype = self.oper_type[operation] + self.feeddict_read[feed]['Oper_type']  # set operation type by crop (corn grain = HRVC vs. corn stover = HRVR)
                            if row[header_dict['opertype']] == opertype:
                                activity = self.act_dict[opertype[0:3]]
                                # pre-set values to null
                                equip = 'NULL'
                                equip_type = 'NULL'
                                time = 'NULL'
                                hp = 'NULL'
                                fuel_consump = 'NULL'
                                # check if power is not empty
                                if row[header_dict['powr01_hpac']] != '':
                                    # set activity, hp, and time (activity_rate) for the first operation in the row
                                    hp = row[header_dict['powr01_hpac']]
                                    time = row[header_dict['time01_hrac']]
                                    fuel_consump = row[header_dict['fuel01_galac']]
                                # loop through keys in equipment dictionary
                                for key in self.equipdic:
                                    # if equipment string starts with dictionary key
                                    if row[header_dict['oper01ac']].startswith(key):
                                        # set equipment type to dictionary key
                                        equip = self.equipdic[key]
                                        equip_type = self.equip_type_dict[key]
                                        # if equipment starts with aerial or planting, set the power and time manually
                                        if equip == 'Aerial':
                                            hp = 0
                                            time = 0
                                        if key.startswith('Planting'):
                                            hp = 60
                                            time = 0.5059

                                # set kvals dictionary for string formatting
                                kvals = {'region': row[header_dict['polyfrr']],
                                         'feedstock': crop,
                                         'tillage': row[header_dict['till']],
                                         'oper_type': opertype,
                                         'machinery': equip,
                                         'equip_type': equip_type,
                                         'hp': hp,
                                         'fuel_consump': fuel_consump,
                                         'activity': activity,
                                         'activity_rate': time,
                                         'prod': self.production_schema,
                                         'table': self.db_table_names[feed],
                                         'bdgtyr': row[header_dict['bdgtyr']]}

                                chemical_list = ['n_lbac',
                                                 'p2o5_lbac',
                                                 'k2o_lbac',
                                                 'lime_lbac',
                                                 'n_lbdt',
                                                 'p2o5_lbdt',
                                                 'k2o_lbdt',
                                                 'lime_lbdt',
                                                 'herb_lbac',
                                                 'insc_lbac']

                                # loop through list of chemicals and check data for empty values
                                for value in chemical_list:
                                    # set string to value of chemical in csv file
                                    string = row[header_dict[value]]
                                    # if the string is empty, set the value to zero
                                    kvals[value] = string if string else 0

                                # execute equip query to insert data for first equipment operation
                                self.execute_equip_query(kvals)

                                # check to see if another operation occurs in the same row (oper02ac)
                                if row[header_dict['oper02ac']] != '':
                                    # if so, set the hp and time (activity_rate) for the second operation
                                    hp = row[header_dict['powr02_hpac']]
                                    time = row[header_dict['time01_hrac']]

                                    # loop through keys in equipment dictionary
                                    for key in self.equipdic:
                                        # if equipment string starts with dictionary key
                                        if row[header_dict['oper02ac']].startswith(key):
                                            # set equipment type to dictionary key
                                            equip = self.equipdic[key]
                                            # if equipment starts with aerial, set the power and time manually
                                            equip_type = self.equip_type_dict[key]
                                            if equip == 'Aerial':
                                                hp = 0
                                                time = 0

                                    # set kvals dictionary for string formatting
                                    kvals = {'region': row[header_dict['polyfrr']],
                                             'feedstock': crop,
                                             'tillage': row[header_dict['till']],
                                             'oper_type': opertype,
                                             'machinery': equip,
                                             'equip_type': equip_type,
                                             'hp': hp,
                                             'fuel_consump': row[header_dict['fuel02_galac']],
                                             'activity': activity,
                                             'activity_rate': time,
                                             'prod': self.production_schema,
                                             'table': self.db_table_names[feed],
                                             'bdgtyr': row[header_dict['bdgtyr']]}

                                    # loop through list of chemicals and check data for empty values
                                    for value in chemical_list:
                                        # set string to value of chemical in csv file
                                        string = row[header_dict[value]]
                                        # if the string is empty, set the value to zero
                                        kvals[value] = string if string else 0

                                    # execute equip query to insert data for first equipment operation
                                    self.execute_equip_query(kvals)

            # load loading equipment data (not included in crop budgets so defined in config)
            kvals = {'prod': self.production_schema,
                     'table': self.db_table_names[feed],
                     'crop': crop,
                     'activity': 'Loading',
                     'oper_type': 'Loading',
                     'hp': self.loading_equip[feed.upper()]['power'][0],
                     'machinery': self.equipdic[self.loading_equip[feed.upper()]['type'][0]],
                     'equip_type': self.equip_type_dict[self.loading_equip[feed.upper()]['type'][0]],
                     'activity_rate_hrperdt': self.loading_equip[feed.upper()]['process_rate'][0],
                     }

            sql = """INSERT INTO {prod}.{table} (bdgt_id, feedstock, bdgtyr, tillage, machinery, equip_type, hp, region, activity, oper_type, activity_rate_hrperdt)
                     SELECT DISTINCT 'NULL', '{crop}', bdgtyr, tillage, '{machinery}', '{equip_type}', '{hp}', region, '{activity}', '{oper_type}', {activity_rate_hrperdt}
                     FROM {prod}.{table}
                     WHERE activity = 'Harvest'
            ;""".format(**kvals)
            self.db.execute_sql(sql)

            for col in ('bdgt_id', 'region', 'feedstock', 'bdgtyr', 'tillage', 'oper_type', 'machinery', 'equip_type', 'hp', 'fuel_consump', 'activity'):
                sql = """CREATE INDEX idx_{table}_{col} ON {prod}.{table} ({col});""".format(col=col, table=self.db_table_names[feed], prod=self.production_schema)
                self.db.execute_sql(sql)

    def load_chem_data(self):
        # load chemical (pesticide and fertilizer) data for all feedstocks

        # loop through all feedstocks in feedstock_list
        for feed in self.feedstock_list:
            logger.info("Creating chemical tables for feedstock: %s" % (feed, ))
            # if the feedstock is conventional (conv), populate table the same way for all years
            if self.crop_type_chem[feed] == 'conv':
                # set kvals dictionary for string formatting
                kvals = {'table1': '%s_chem' % (feed, ),
                         'table2': '%s_equip' % (feed, ),
                         'prod': self.production_schema,
                         'col1': self.col_dict_chem[feed][0],
                         'col2': self.col_dict_chem[feed][1],
                         'col3': self.col_dict_chem[feed][2],
                         'col4': self.col_dict_chem[feed][3],
                         'col5': self.col_dict_chem[feed][4],
                         'col6': self.col_dict_chem[feed][5]}

                # drop table
                sql = """DROP TABLE IF EXISTS {prod}.{table1};""".format(**kvals)
                self.db.execute_sql(sql)

                # create string for sql query
                query = """ CREATE TABLE {prod}.{table1}
                            AS (SELECT region,
                                       tillage,
                                       bdgtyr,
                                       sum({col1}) as {col1},
                                       sum({col2}) as {col2},
                                       sum({col3}) as {col3},
                                       sum({col4}) as {col4},
                                       sum({col5}) as {col5},
                                       sum({col6}) as {col6}
                                FROM {prod}.{table2}
                                GROUP BY region, tillage)""".format(**kvals)
                # execute query
                self.db.execute_sql(query)

                # create indices
                for col in ('region', 'tillage'):
                    sql = """CREATE INDEX idx_{table1}_{col} ON {prod}.{table1} ({col});""".format(col=col, **kvals)
                    self.db.execute_sql(sql)

            # if the feedstock is an energy crop, populate the table differently for year 1 versus all remaining years
            elif self.crop_type_chem[feed] == 'energy':
                # set kvals dictionary for string fomatting
                kvals = {'table1': '%s_chem' % (feed, ),
                         'table2': '%s_equip' % (feed, ),
                         'prod': self.production_schema,
                         'col1_yr1': self.col_dict_chem[feed + '_yr1'][0],
                         'col2_yr1': self.col_dict_chem[feed + '_yr1'][1],
                         'col3_yr1': self.col_dict_chem[feed + '_yr1'][2],
                         'col4_yr1': self.col_dict_chem[feed + '_yr1'][3],
                         'col1_yr2to10': self.col_dict_chem[feed + '_yr2to10'][0],
                         'col2_yr2to10': self.col_dict_chem[feed + '_yr2to10'][1],
                         'col3_yr2to10': self.col_dict_chem[feed + '_yr2to10'][2],
                         'col4_yr2to10': self.col_dict_chem[feed + '_yr2to10'][3],
                         'col5': self.col_dict_chem[feed + '_yr1'][4],
                         'col6': self.col_dict_chem[feed + '_yr1'][5]}

                # drop table
                sql = " DROP TABLE IF EXISTS {prod}.{table1};".format(**kvals)
                self.db.execute_sql(sql)

                # create string for sql query
                query = """
                            CREATE TABLE {prod}.{table1}
                            AS (SELECT region,
                                       tillage,
                                       bdgtyr,
                                       sum({col1_yr1}) as {col1_yr1},
                                       sum({col2_yr1}) as {col2_yr1},
                                       sum({col3_yr1}) as {col3_yr1},
                                       sum({col4_yr1}) as {col4_yr1},
                                       sum({col1_yr2to10}) as {col1_yr2to10},
                                       sum({col2_yr2to10}) as {col2_yr2to10},
                                       sum({col3_yr2to10}) as {col3_yr2to10},
                                       sum({col4_yr2to10}) as {col4_yr2to10},
                                       sum({col5}) as {col5},
                                       sum({col6}) as {col6}
                                FROM {prod}.{table2}
                                GROUP BY region, tillage, bdgtyr)""".format(**kvals)

                # execute query
                self.db.execute_sql(query)

                # create indices
                for col in ('region', 'tillage', 'bdgtyr'):
                    sql = "CREATE INDEX idx_{table1}_{col} ON {prod}.{table1} ({col});".format(col=col, **kvals)
                    self.db.execute_sql(sql)

    def join_fips_region(self, type_of_table):
        # join region-based tables with fips to region table

        # loop through all feedstocks in feedstock list
        for feed in self.feedstock_list:
            logger.info("Joining fips-region for feedstock: %s, table: %s" % (feed, type_of_table,))

            # set kvals dictionary for string formatting
            kvals = {'table': '%s_%s' % (feed, type_of_table),
                     'fips_region_table': self.fipsregion_table_name,
                     'prod_schema': self.production_schema,
                     'table_joined_with_fips': '%s_%s_fips' % (feed, type_of_table),
                     'constants_schema': self.constants_schema}

            # loop through all regions (1-13) and create a new table with the joined values of fips and region-based table
            # @TODO: if it is possible to directly join the tables with all regions, replace with correct query, for some reason it didn't work for the current dataset
            for region in range(1, 14):
                # set region for string formatting
                kvals['region'] = region

                # if this is the first region, create the joined fips-region table
                # otherwise, insert data into joined fips-region table
                if region == 1:
                    # drop existing table as needed
                    query = """DROP   TABLE IF EXISTS {prod_schema}.{table_joined_with_fips};""".format(**kvals)
                    self.db.execute_sql(query)

                    # create new table
                    query = """CREATE TABLE {prod_schema}.{table_joined_with_fips} AS
                               SELECT a.*,
                                      b.fips,
                                      b.polyfrr
                               FROM     {prod_schema}.{table}                  a
                                      , {constants_schema}.{fips_region_table} b
                               WHERE  a.region  = {region}
                               AND    b.polyfrr = {region}
                            ;""".format(**kvals)
                    self.db.execute_sql(query)
                else:
                    # create query for inserting data
                    query = """INSERT INTO {prod_schema}.{table_joined_with_fips}
                               SELECT   a.*
                                      , b.fips
                                      , b.polyfrr
                               FROM     {prod_schema}.{table}                  a
                                      , {constants_schema}.{fips_region_table} b
                               WHERE  a.region  = {region}
                               AND    b.polyfrr = {region}
                            ;""".format(**kvals)

                    # execute query
                    self.db.execute_sql(query)

            # create indices
            cols = ()
            if type_of_table == 'chem':
                cols = ('region', 'tillage', 'bdgtyr', 'fips', 'polyfrr')
            elif type_of_table == 'equip':
                cols = ('bdgt_id', 'region', 'feedstock', 'bdgtyr', 'tillage', 'oper_type', 'machinery', 'equip_type', 'hp', 'activity', 'fips', 'polyfrr')

            for col in cols:
                sql = """CREATE INDEX idx_{table_joined_with_fips}_{col} ON {prod_schema}.{table_joined_with_fips} ({col});""".format(col=col, **kvals)
                self.db.execute_sql(sql)

    def load_transport_data(self):
        # load transportation data for all feedstocks

        # loop through years and crops, load raw data, pivot tables, insert into new FPEAM data table for production
        for year in self.system_list:
            for system in self.system_list[year]:
                for case in self.trans_case_list[year]:
                    for crop_type in self.crop_type_list:
                        logger.info("Loading transport data for feedstock: {crop_type}, case: {case}, system: {system}, year: {year}".format(crop_type=crop_type, case=case, system=system, year=year))

                        # drop raw data table if necessary
                        query_drop_rawtable = """DROP TABLE IF EXISTS {prod}.transport_{crop_type}_{case}_{system}_{year};""".format(prod=self.production_schema, crop_type=crop_type, case=case, system=system, columns=self.column_dict[system], year=year)
                        self.db.execute_sql(query_drop_rawtable)

                        # create raw data table
                        query_create_rawtable = """
                        CREATE TABLE {prod}.transport_{crop_type}_{case}_{system}_{year} (
                        {columns}
                        );""".format(prod=self.production_schema, crop_type=crop_type, case=case, system=system, columns=self.column_dict[system], year=year)
                        self.db.execute_sql(query_create_rawtable)

                        # specify path for raw data file
                        year2 = self.year_sub[year]
                        filename = "./development/input_data/logistics_transport_data/transport_{crop_type}_{case}_{system}_{year}.csv".format(crop_type=crop_type, case=case, system=system, year=year2, )

                        # load raw data file
                        query_load_rawdata = """
                        LOAD DATA LOCAL INFILE "{filename}"
                        INTO TABLE {prod}.transport_{crop_type}_{case}_{system}_{year}
                        COLUMNS TERMINATED BY ','
                        OPTIONALLY ENCLOSED BY '"'
                        ESCAPED BY '"'
                        LINES TERMINATED BY '\n'
                        IGNORE 1 LINES;""".format(prod=self.production_schema, crop_type=crop_type, case=case, system=system, filename=filename, year=year, )
                        self.db.execute_sql(query_load_rawdata)

                        query_concat_zeros = """UPDATE {prod}.transport_{crop_type}_{case}_{system}_{year}
                                                SET sply_fips = CONCAT('0', sply_fips)
                                                WHERE length(sply_fips) = 4
                                             ;""".format(prod=self.production_schema, crop_type=crop_type, case=case, system=system, filename=filename, year=year, )
                        self.db.execute_sql(query_concat_zeros)

                        # data provided for 2017 are in a different format than 2040 so need to sum over all residues and whole trees
                        if year == '2040' and case in ('hh', 'bc'):
                            # string formatting dictionary
                            kvals = {'prod': self.production_schema,
                                     'crop_type': crop_type,
                                     'case': case,
                                     'system': system,
                                     'year': year, }

                            # drop summed data table
                            query = """DROP TABLE IF EXISTS {prod}.transport_{crop_type}_{case}_{system}_{year}_summed""".format(**kvals)
                            self.db.execute_sql(query)

                            # create table for summed data
                            query = """CREATE TABLE {prod}.transport_{crop_type}_{case}_{system}_{year}_summed
                                       (sply_fips           char(5),
                                        feed_id             char(20),
                                        used_qnty           float(15,5),
                                        avg_total_cost      float(15, 5),
                                        avg_flddep_dist     float(15,5),
                                        avg_depref_dist     float(15,5),
                                        avg_dist            float(15, 5));
                                    """.format(**kvals)

                            self.db.execute_sql(query)

                            # insert summed data
                            query_insert = """INSERT INTO {prod}.transport_{crop_type}_{case}_{system}_{year}_summed
                                              SELECT sply_fips,
                                                     feed_id,
                                                     sum(used_qnty) AS used_qnty,
                                                     sum(avg_total_cost)/count(avg_total_cost) AS avg_total_cost,
                                                     sum(avg_flddep_dist)/count(avg_flddep_dist) AS avg_flddep_dist,
                                                     sum(avg_depref_dist)/count(avg_dist) AS avg_depref_dist,
                                                     sum(avg_dist)/count(avg_dist) AS avg_dist
                                              FROM {prod}.transport_{crop_type}_{case}_{system}_{year}
                                              GROUP BY sply_fips, feed_id
                                             ;""".format(**kvals)

                            self.db.execute_sql(query_insert)

                            # drop old data and create new transport table
                            query_drop_old = """DROP TABLE {prod}.transport_{crop_type}_{case}_{system}_{year};""".format(**kvals)
                            self.db.execute_sql(query_drop_old)

                            query_create = """CREATE TABLE {prod}.transport_{crop_type}_{case}_{system}_{year} AS
                                                SELECT *
                                                FROM {prod}.transport_{crop_type}_{case}_{system}_{year}_summed;
                                                DROP TABLE {prod}.transport_{crop_type}_{case}_{system}_{year}_summed;
                                             ;""".format(**kvals)

                            self.db.execute_sql(query_create)

                        if year == '2017' and case == 'bc':
                            # string formatting dictionary
                            kvals = {'prod': self.production_schema,
                                     'crop_type': crop_type,
                                     'case': case,
                                     'system': system,
                                     'year': year, }

                            # drop summed data table
                            query = """DROP TABLE IF EXISTS {prod}.transport_{crop_type}_{case}_{system}_{year}_summed""".format(**kvals)
                            self.db.execute_sql(query)

                            # create table for summed data
                            query = """CREATE TABLE {prod}.transport_{crop_type}_{case}_{system}_{year}_summed
                                       (sply_fips           char(5),
                                        feed_id             char(20),
                                        used_qnty           float(15,5),
                                        avg_total_cost      float(15, 5),
                                        avg_dist            float(15, 5));
                                    """.format(**kvals)

                            self.db.execute_sql(query)

                            if crop_type == 'woody':
                                # list crops for forestry
                                list_crops = {'Residues': 'RSD',
                                              'whole tree': 'TRE'}

                                for crop in list_crops:
                                    # set crop and filter ID
                                    kvals['crop'] = crop
                                    kvals['key'] = list_crops[crop]

                                    # insert summed data
                                    query_insert = """INSERT INTO {prod}.transport_{crop_type}_{case}_{system}_{year}_summed
                                                      SELECT sply_fips,
                                                             '{crop}' AS feed_id,
                                                             sum(used_qnty) AS used_qnty,
                                                             sum(avg_total_cost)/count(avg_total_cost) AS avg_total_cost,
                                                             sum(avg_dist)/count(avg_dist) AS avg_dist
                                                      FROM {prod}.transport_{crop_type}_{case}_{system}_{year}
                                                      WHERE RIGHT(feed_id, 3) = '{key}'
                                                      GROUP BY sply_fips
                                                     ;""".format(**kvals)

                                    self.db.execute_sql(query_insert)
                            else:

                                # insert summed data
                                query_insert = """INSERT INTO {prod}.transport_{crop_type}_{case}_{system}_{year}_summed
                                                  SELECT sply_fips,
                                                         feed_id,
                                                         sum(used_qnty) AS used_qnty,
                                                         sum(avg_total_cost)/count(avg_total_cost) AS avg_total_cost,
                                                         sum(avg_dist)/count(avg_dist) AS avg_dist
                                                  FROM {prod}.transport_{crop_type}_{case}_{system}_{year}
                                                  GROUP BY sply_fips, feed_id
                                                 ;""".format(**kvals)

                                self.db.execute_sql(query_insert)

                            # drop old data and create new transport table
                            query_drop_old = """DROP TABLE {prod}.transport_{crop_type}_{case}_{system}_{year};""".format(**kvals)
                            self.db.execute_sql(query_drop_old)

                            query_create = """CREATE TABLE {prod}.transport_{crop_type}_{case}_{system}_{year} AS
                                                SELECT *
                                                FROM {prod}.transport_{crop_type}_{case}_{system}_{year}_summed;
                                                DROP TABLE {prod}.transport_{crop_type}_{case}_{system}_{year}_summed;
                                             ;""".format(**kvals)

                            self.db.execute_sql(query_create)

                        # query_add_index = """ALTER TABLE {prod}.transport_{crop_type}_{case}_{system}_{year} ADD INDEX idx_sply_fips (sply_fips);""".format(prod=self.production_schema, crop_type=crop_type, case=case, system=system, filename=filename, year=year, )
                        # self.db.execute_sql(query_add_index)

                        # add state fips column
                        sql = 'ALTER TABLE {prod}.transport_{crop_type}_{case}_{system}_{year} ADD COLUMN state char(2);' \
                              'UPDATE {prod}.transport_{crop_type}_{case}_{system}_{year} SET state = LEFT(sply_fips, 2);'.format(prod=self.production_schema, crop_type=crop_type, case=case, system=system, year=year)
                        self.db.execute_sql(sql)

                        # add abbreviated feed_id for figure plotting table join
                        sql = 'ALTER TABLE {prod}.transport_{crop_type}_{case}_{system}_{year} ADD COLUMN feed_id_abbr char(2);'.format(prod=self.production_schema, crop_type=crop_type, case=case, system=system, year=year)
                        self.db.execute_sql(sql)

                        # @TODO: this should use a lookup from the config
                        sql = """UPDATE {prod}.transport_{crop_type}_{case}_{system}_{year}
                            SET feed_id_abbr =
                            CASE WHEN feed_id = 'Corn stover' THEN 'cs'
                                 WHEN feed_id = 'Switchgrass' THEN 'sg'
                                 WHEN feed_id = 'Residues'    THEN 'fr'
                                 WHEN feed_id = 'Whole tree'  THEN 'fw'
                                 WHEN feed_id = 'Miscanthus'  THEN 'ms'
                            END;""".format(prod=self.production_schema, crop_type=crop_type, case=case, system=system, year=year)
                        self.db.execute_sql(sql)

                        # add indices
                        for col in ('sply_fips', 'feed_id', 'feed_id_abbr', 'state'):
                            sql = 'CREATE INDEX idx_transport_{crop_type}_{case}_{system}_{year}_{col} ON {prod}.transport_{crop_type}_{case}_{system}_{year} ({col});'.format(prod=self.production_schema, crop_type=crop_type, case=case, system=system, year=year, col=col)
                            self.db.execute_sql(sql)
                        sql = 'CREATE INDEX idx_transport_{crop_type}_{case}_{system}_{year}_sply_fips_2 ON {prod}.transport_{crop_type}_{case}_{system}_{year} (sply_fips(2));'.format(prod=self.production_schema, crop_type=crop_type, case=case, system=system, year=year)
                        self.db.execute_sql(sql)

    def load_equip_data_fr(self):

        for feed in self.forestry_feed_list:
            logger.info('Loading equipment data for feedstock: %s' % (feed, ))

            # set budget name
            bdgt_name = self.bdgt_dict[feed]

            # drop table
            query = """DROP TABLE IF EXISTS {prod}.{table};""".format(table=self.db_table_names[feed], prod=self.production_schema)
            self.db.execute_sql(query)

            # create new table for equipment
            query = """
                    CREATE TABLE {prod}.{table}
                    (
                    bdgt_id    char(25),
                    feedstock    char(55),
                    bdgtyr char(2),
                    tillage   char(55),
                    machinery    char(55),
                    oper_type char(55),
                    equip_type char(30),
                    hp   float,
                    fuel_consump    float,
                    activity char(55),
                    activity_rate_hrperac float,
                    activity_rate_hrperdt float,
                    n_lbac float,
                    p2o5_lbac float,
                    k2o_lbac float,
                    lime_lbac float,
                    n_lbdt float,
                    p2o5_lbdt float,
                    k2o_lbdt float,
                    lime_lbdt float,
                    herb_lbac float,
                    insc_lbac float
                    );""".format(table=self.db_table_names[feed], prod=self.production_schema)

            # insert new table into database
            self.db.execute_sql(query)

            # set filename to the correct value using equipfiles dictionary
            filename = os.path.join(self.filepath_equip, self.equipfiles[feed])
            # read csv file for feedstock equipment
            reader = csv.reader(open(filename, 'rU'))

            forest_equipdict = {'saw': '2270004020',
                                'hand felling': '2270004020',
                                'buncher': '2270007015',
                                'feller': '2270007015',
                                'skidder': '2270007015',
                                'processor': '2270007015',
                                'delimber': '2270007015',
                                'forwarder': '2270007015',
                                'skyline': '2270007015',
                                'loader': '2270007015',
                                'chipper': '2270004066',
                                'crawler': '2270002069'}

            forest_sccdict = {'2270004020': 'Lawn & Garden Equipment Chain Saws',
                              '2270004066': 'Dsl - Chippers/Stump Grinders (com)',
                              '2270007015': 'Dsl - Forest Eqp - Feller/Bunch/Skidder',
                              '2270002069': 'Dsl - Crawler Tractors'}

            forest_typedict = {'2270007015': 'other_forest_eqp',
                               '2270004066': 'chipper',
                               '2270002069': 'crawler',
                               '2270004020': 'chain_saw'}

            header_dict = dict()
            for i, row in enumerate(reader):
                if i == 0:
                    headers = row
                    for j in range(0, len(headers)):
                        header_dict[headers[j]] = j
                else:
                    if row[header_dict['bdgt_id']].startswith(bdgt_name):
                        for k, header in enumerate(headers):
                            if 'oper' in headers[k] and headers[k] != 'opertype':
                                if row[header_dict[headers[k]]] != '' and not row[header_dict[headers[k]]].startswith('Burn'):
                                    activity = self.act_dict[row[header_dict['opertype']]]
                                    # loop through keys in dictionary
                                    time_ac = 'NULL'
                                    time_dt = 'NULL'
                                    fuel_consump = row[k + 1]
                                    hp = row[k + 2]
                                    if headers[k].lower().endswith('dt'):
                                        time_dt = 1/float(row[k + 3])
                                    elif headers[k].lower().endswith('ac'):
                                        time_ac = 1/float(row[k + 3])

                                    for key in forest_equipdict:
                                        # if equipment string starts with dictionary key
                                        if key in row[header_dict[header]].lower():
                                            # set equipment type to dictionary key
                                            equip = forest_sccdict[forest_equipdict[key]]
                                            equip_type = forest_typedict[forest_equipdict[key]]
                                            break

                                    kvals = {'bdgt_id': row[header_dict['bdgt_id']],
                                             'feedstock': feed,
                                             'tillage': 'NT',
                                             'machinery': equip,
                                             'equip_type': equip_type,
                                             'hp': hp,
                                             'fuel_consump': fuel_consump,
                                             'activity': activity,
                                             'activity_rate_hrperdt': time_dt,
                                             'activity_rate_hrperac': time_ac,
                                             'prod': self.production_schema,
                                             'table': self.db_table_names[feed],
                                             'bdgtyr': row[header_dict['bdgtyr']]}

                                    chemical_list = {'n_AC': 'n_lbac',
                                                     'p2o5_AC': 'p2o5_lbac',
                                                     'k2o_AC': 'k2o_lbac',
                                                     'lime_AC': 'lime_lbac',
                                                     'herb_AC': 'herb_lbac', }

                                    # loop through list of chemicals and check data for empty values
                                    for value in chemical_list:
                                        # set string to value of chemical in csv file
                                        string = row[header_dict[value]]
                                        # if the string is empty, set the value to zero
                                        kvals[chemical_list[value]] = string if string else 'NULL'

                                    kvals['n_lbdt'] = 'NULL'
                                    kvals['p2o5_lbdt'] = 'NULL'
                                    kvals['k2o_lbdt'] = 'NULL'
                                    kvals['lime_lbdt'] = 'NULL'
                                    kvals['herb_lbdt'] = 'NULL'
                                    kvals['insc_lbac'] = 'NULL'
                                    kvals['insc_lbdt'] = 'NULL'

                                    self.execute_equip_query_fr(kvals)

            for col in ('bdgt_id', 'feedstock', 'bdgtyr', 'tillage', 'machinery', 'oper_type', 'equip_type', 'hp', 'fuel_consump', 'activity'):
                sql = "CREATE INDEX idx_{table}_{col} ON {prod}.{table} ({col});".format(table=self.db_table_names[feed], prod=self.production_schema, col=col)
                self.db.execute_sql(sql)

    def load_production_data_fr(self):

        crop_type_dict = {'fr': 'resd', 'fw': 'tree'}
        for year in self.fr_year_list:
            for case in self.case_list:
                # specify path for raw data file
                file_name = "{case}{year}cnty_60.csv".format(case=case, year=year, )
                filename = os.path.join(self.filepath_prod_fr, file_name)

                # create kvals dictionary for sql queries
                kvals = {'prod': self.production_schema,
                         'year': year,
                         'case': case,
                         'filename': filename,
                         }

                # drop table
                query = """DROP TABLE IF EXISTS {prod}.forest_{case}_{year};""".format(**kvals)
                self.db.execute_sql(query)

                # create query for generating raw data table
                query_create_rawtable = """
                CREATE TABLE {prod}.forest_{case}_{year}
                 (scenario char(4),
                  splytrgt char(4),
                  year     char(4),
                  frstregn char(3),
                  fips     char(5),
                  crop     char(25),
                  type     char(4),
                  woodprod char(6),
                  owner    char(10),
                  diacls   int,
                  slpcls   char(4),
                  oper     char(4),
                  harv     float(15, 5),
                  prod     float(15, 5),
                  bdgt_id  char(25),
                  produnit char(2)
                 )
                ;""".format(**kvals)
                # execute query
                self.db.execute_sql(query_create_rawtable)

                # create query for loading raw data file
                query_load_rawdata = """
                                        LOAD DATA LOCAL INFILE "{filename}"
                                        INTO TABLE {prod}.forest_{case}_{year}
                                        COLUMNS TERMINATED BY ','
                                        OPTIONALLY ENCLOSED BY '"'
                                        ESCAPED BY '"'
                                        LINES TERMINATED BY '\n'
                                        IGNORE 1 LINES
                                        (scenario, splytrgt, year, frstregn, fips, crop, type, woodprod, owner, diacls, slpcls, oper, @harv, @prod, @bdgt_id, produnit)
                                        SET
                                        bdgt_id = nullif(@bdgt_id,''),
                                        harv = nullif(@harv,''),
                                        prod = nullif(@prod,'')
                                    ;""".format(**kvals)
                logger.info("Inserting data into forest_{case}_{year} table".format(**kvals))
                # execute query
                self.db.execute_sql(query_load_rawdata)

                for crop in self.forestry_feed_list:

                    # create kvals dictionary for sql queries
                    kvals['forest_type'] = crop_type_dict[crop]
                    kvals['crop'] = crop
                    kvals['cropname'] = self.crop_dict_production_data[crop]

                    logger.info("Loading data for crop: {crop}, year: {year}, case: {case}".format(**kvals))

                    # drop table
                    query = """DROP TABLE IF EXISTS {prod}.{crop}_data_{case}_{year};""".format(**kvals)
                    self.db.execute_sql(query)

                    # create query to create table for FPEAM production data
                    query_create_table = """
                                        CREATE TABLE {prod}.{crop}_data_{case}_{year} (fips	char(5),
                                        convtill_yield float(15,5),
                                        convtill_planted_ac float(15,5),
                                        convtill_harv_ac float(15,5),
                                        convtill_prod float(15,5),
                                        reducedtill_yield float(15,5),
                                        reducedtill_planted_ac float(15,5),
                                        reducedtill_harv_ac float(15,5),
                                        reducedtill_prod float(15,5),
                                        notill_yield float(15,5),
                                        notill_planted_ac float(15,5),
                                        notill_harv_ac float(15,5),
                                        notill_prod float(15,5),
                                        total_prod float(15,5),
                                        total_harv_ac float(15,5),
                                        bdgt char(25)
                                        );""".format(**kvals)
                    # execute query
                    self.db.execute_sql(query_create_table)

                    query = """ INSERT INTO {prod}.{crop}_data_{case}_{year} (fips, notill_prod, notill_harv_ac, bdgt, total_prod, total_harv_ac)
                                SELECT  LPAD(fips, 5, '0') AS padfips,
                                        sum(prod),
                                        sum(harv),
                                        bdgt_id,
                                        sum(prod),
                                        sum(harv)
                                FROM {prod}.forest_{case}_{year}
                                WHERE prod IS NOT NULL AND type = '{forest_type}'
                                GROUP BY padfips, bdgt_id
                            ;""".format(**kvals)

                    self.db.execute_sql(query)

    def join_fips_forest(self):

        kvals = {'prod': self.production_schema}
        for feed in self.forestry_feed_list:
            kvals['feed'] = feed
            query = """DROP TABLE IF EXISTS {prod}.{feed}_equip_fips;""".format(**kvals)
            self.db.execute_sql(query)

            query = """ CREATE TABLE {prod}.{feed}_equip_fips AS
                        SELECT * FROM {prod}.{feed}_equip eq
                        LEFT JOIN (SELECT fips, bdgt
                        FROM {prod}.{feed}_data) fd
                        ON fd.bdgt = eq.bdgt_id
                        WHERE fd.fips is not NULL
                    ;""".format(**kvals)

            self.db.execute_sql(query)

    def load_all_data(self):
        # load production data
        self.load_production_data()
        self.load_production_data_fr()

        # load equipment data
        self.load_equip_data()
        self.load_equip_data_fr()

        # load chemical data
        self.load_chem_data()

        # load data for specific scenario into {feed}_data
        self.load_scenario_data()

        # join equipment and chemical tables to fips codes for agricultural crops
        for table in self.table_list:
            self.join_fips_region(type_of_table=table)

        # join equipment to fips for forestry data
        self.join_fips_forest()

        # load transport data
        self.load_transport_data()
