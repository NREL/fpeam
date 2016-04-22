# -*- coding: utf-8 -*-
"""
Created on Tue Apr 12 14:07:42 2016

Creates figures for the 2016 Billion Ton Study

@author: aeberle
"""

import matplotlib
import matplotlib.pyplot as plt
from utils import config, logger
from pylab import median, mean
from scipy.stats import scoreatpercentile
from pylab import *
from matplotlib import ticker


class FigurePlottingBT16:
    def __init__(self, db):
        self.db = db

        self.f_color = ['r', 'b', 'g', 'k', 'c']
        self.f_marker = ['o', 'o', 'o', 'o', 'o']
        self.row_list = [0, 0, 1, 1, 2, 2]
        self.col_list = [0, 1, 0, 1, 0, 1]
        self.pol_list_label = ['$NO_x$', '$VOC$', '$PM_{2.5}$', '$PM_{10}$', '$CO$', '$SO_x$', ]
        self.pol_list = ['NOx', 'VOC', 'PM25', 'CO', 'PM10', 'SOx', ]

        self.feedstock_list = ['Corn Grain', 'Switchgrass', 'Corn Stover', 'Wheat Straw',]# 'Miscanthus', ]  # 'Forest Residue'] @TODO: remove hardcoded values
        self.f_list = ['CG', 'SG', 'CS', 'WS',]# 'MS', ]  # 'FR'] # @TODO: remove hardcoded values
        self.act_list = ['Non-Harvest', 'Chemical', 'Harvest']

        self.etoh_vals = [2.76/0.02756, 89.6, 89.6, 89.6, 89.6, ]  # 75.7]  # gallons per dry short ton

        self.feed_id_dict = config.get('feed_id_dict')

    def compile_results(self):
        # initialize kvals dict for string formatting

        kvals = {'scenario_name': config.get('title'),
                 'year': config.get('year_dict')['all_crops'],
                 'yield': config.get('yield'),
                 'production_schema': config.get('production_schema')}

        query_create_table = """ DROP TABLE IF EXISTS {scenario_name}.total_emissions;
                                 CREATE TABLE {scenario_name}.total_emissions (fips char(5),
                                                                              Year char(4),
                                                                              Yield char(2),
                                                                              Tillage varchar(255),
                                                                              NOx float,
                                                                              NH3 float,
                                                                              VOC float,
                                                                              PM10 float,
                                                                              PM25 float,
                                                                              SOx float,
                                                                              CO float,
                                                                              Source_Category varchar(255),
                                                                              NEI_Category char(2),
                                                                              Feedstock char(2))
                            """.format(**kvals)
        self.db.create(query_create_table)

        for feedstock in self.f_list:
            kvals['years_rot'] = config.get('crop_budget_dict')['years'][feedstock]
            kvals['feed'] = feedstock.lower()

            logger.info('Inserting data for chemical emissions for feedstock: {feed}'.format(**kvals))
            self.get_chem(kvals)

            logger.info('Inserting data for fertilizer emissions for feedstock: {feed}'.format(**kvals))
            self.get_fert(kvals)

            if feedstock == 'CG':
                logger.info('Inserting data for irrigation for feedstock: {feed}'.format(**kvals))
                self.get_irrig(kvals)

            logger.info('Inserting data for loading for feedstock: {feed}'.format(**kvals))
            self.get_loading(kvals)

            logger.info('Inserting data for harvest fugitive dust: {feed}'.format(**kvals))
            self.get_h_fd(kvals)

            logger.info('Inserting data for non-harvest fugitive dust for feedstock: {feed}'.format(**kvals))
            self.get_nh_fd(kvals)

            logger.info('Inserting data for non-harvest emissions for feedstock: {feed}'.format(**kvals))
            self.get_non_harvest(kvals)

            logger.info('Inserting data for harvest emissions for feedstock: {feed}'.format(**kvals))
            self.get_harvest(kvals)

#            logger.info('Inserting data for off-farm transportation and pre-processing for feedstock: {feed}'.format(**kvals))
#            self.get_logistics(kvals)

        logger.info('Joining total emissions with production data')
        self.join_with_production_data(kvals)

    def join_with_production_data(self, kvals):

        till_dict = {'CT': 'convtill',
                     'RT': 'reducedtill',
                     'NT': 'notill'}

        for i, feed in enumerate(self.f_list):
            kvals['feed'] = feed.lower()
            for till in till_dict:
                kvals['till'] = till
                kvals['tillage'] = till_dict[till]
                if i == 0:
                    query_create = """  DROP TABLE IF EXISTS {scenario_name}.total_emissions_join_prod;
                                        CREATE TABLE {scenario_name}.total_emissions_join_prod
                                        AS (SELECT tot.*, cd.convtill_prod as 'prod', cd.convtill_harv_ac as 'harv_ac'
                                        FROM {scenario_name}.total_emissions tot
                                        LEFT JOIN {production_schema}.cg_data cd ON cd.fips = tot.fips
                                        WHERE tot.Tillage = 'CT' AND tot.Feedstock = 'cg');""".format(**kvals)
                    self.db.create(query_create)
                else:
                    query_insert = """  INSERT INTO {scenario_name}.total_emissions_join_prod
                                        SELECT tot.*, cd.{tillage}_prod as 'prod', cd.{tillage}_harv_ac as 'harv_ac'
                                        FROM {scenario_name}.total_emissions tot
                                        LEFT JOIN {production_schema}.cs_data cd ON cd.fips = tot.fips
                                        WHERE tot.Tillage = '{till}' AND tot.Feedstock = '{feed}';""".format(**kvals)
                    self.db.input(query_insert)

    def get_chem(self, kvals):

        query_fert_chem = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                              SELECT   chem.fips,
                                       '{year}' as 'Year',
                                       '{yield}' as 'Yield',
                                       chem.tillage as 'Tillage',
                                       0 as 'NOx',
                                       0 as 'NH3',
                                       chem.VOC as 'VOC',
                                       0 as 'PM10',
                                       0 as 'PM25',
                                       0 as 'SOx',
                                       0 as 'CO',
                                       'Chemical' as 'Source_Category',
                                       'NP' as 'NEI_Category',
                                       '{feed}' as 'Feedstock'
                              FROM  (SELECT fips, sum(VOC)/{years_rot} as 'VOC', tillage
                                    FROM {scenario_name}.{feed}_chem
                                    GROUP BY fips) chem;
                         """.format(**kvals)
        self.db.input(query_fert_chem)

    def get_fert(self, kvals):

        query_fert_fert = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                              SELECT   fert.fips,
                                       '{year}' as 'Year',
                                       '{yield}' as 'Yield',
                                       fert.tillage as 'Tillage',
                                       fert.NOx as 'NOx',
                                       fert.NH3 as 'NH3',
                                       0 as 'VOC',
                                       0 as 'PM10',
                                       0 as 'PM25',
                                       0 as 'SOx',
                                       0 as 'CO',
                                       'Fertilizer' as 'Source_Category',
                                       'NP' as 'NEI_Category',
                                       '{feed}' as 'Feedstock'
                              FROM (SELECT fips, sum(NOx)/{years_rot} as 'NOx', sum(NH3)/{years_rot} as 'NH3', tillage
                                    FROM {scenario_name}.{feed}_nfert
                                    GROUP BY fips) fert;
                         """.format(**kvals)
        self.db.input(query_fert_fert)

    def get_non_harvest(self, kvals):
        if kvals['feed'] != 'sg':
            query_non_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                    SELECT fips,
                                           '{year}' as 'Year',
                                           '{yield}' as 'Yield',
                                           CONCAT(LEFT(RIGHT(run_code, 2),1), 'T') as 'Tillage',
                                           sum(NOx)/{years_rot} as 'NOx',
                                           sum(NH3)/{years_rot} as 'NH3',
                                           sum(VOC)/{years_rot} as 'VOC',
                                           sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)) as 'PM10',
                                           sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)) as 'PM25',
                                           sum(SOx)/{years_rot} as 'SOx',
                                           sum(CO)/{years_rot} as 'CO',
                                           'Non-Harvest' as 'Source_Category',
                                           'NR' as 'NEI_Category',
                                           '{feed}' as 'Feedstock'
                                    FROM {scenario_name}.{feed}_raw
                                    WHERE description LIKE '%Non-Harvest%' AND description not LIKE '%dust%' AND LEFT(RIGHT(run_code,2),1) != 'I'
                                    GROUP BY fips;
                                """.format(**kvals)
            self.db.input(query_non_harvest)
        else:
            query_non_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                    SELECT fips,
                                           '{year}' as 'Year',
                                           '{yield}' as 'Yield',
                                           'NT' as 'Tillage',
                                           sum(NOx)/{years_rot} as 'NOx',
                                           sum(NH3)/{years_rot} as 'NH3',
                                           sum(VOC)/{years_rot} as 'VOC',
                                           sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)) as 'PM10',
                                           sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)) as 'PM25',
                                           sum(SOx)/{years_rot} as 'SOx',
                                           sum(CO)/{years_rot} as 'CO',
                                           'Non-Harvest' as 'Source_Category',
                                           'NR' as 'NEI_Category',
                                           '{feed}' as 'Feedstock'
                                    FROM {scenario_name}.{feed}_raw
                                    WHERE description LIKE '%Non-Harvest%' AND description not LIKE '%dust%' AND LEFT(RIGHT(run_code,2),1) != 'I'
                                    GROUP BY fips;
                                """.format(**kvals)
            self.db.input(query_non_harvest)

    def get_nh_fd(self, kvals):
        if kvals['feed'] != 'sg':
            query_non_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                    SELECT fips,
                                           '{year}' as 'Year',
                                           '{yield}' as 'Yield',
                                           CONCAT(LEFT(RIGHT(run_code, 2),1), 'T') as 'Tillage',
                                           sum(NOx)/{years_rot} as 'NOx',
                                           sum(NH3)/{years_rot} as 'NH3',
                                           sum(VOC)/{years_rot} as 'VOC',
                                           sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)) as 'PM10',
                                           sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)) as 'PM25',
                                           sum(SOx)/{years_rot} as 'SOx',
                                           sum(CO)/{years_rot} as 'CO',
                                           'Non-Harvest - fug dust' as 'Source_Category',
                                           'NR' as 'NEI_Category',
                                           '{feed}' as 'Feedstock'
                                    FROM {scenario_name}.{feed}_raw
                                    WHERE description LIKE '%Non-Harvest%' AND description LIKE '%dust%' AND LEFT(RIGHT(run_code,2),1) != 'I'
                                    GROUP BY fips;
                                """.format(**kvals)
            self.db.input(query_non_harvest)
        else:
            query_non_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                SELECT fips,
                                       '{year}' as 'Year',
                                       '{yield}' as 'Yield',
                                       'NT',
                                       sum(NOx)/{years_rot} as 'NOx',
                                       sum(NH3)/{years_rot} as 'NH3',
                                       sum(VOC)/{years_rot} as 'VOC',
                                       sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)) as 'PM10',
                                       sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)) as 'PM25',
                                       sum(SOx)/{years_rot} as 'SOx',
                                       sum(CO)/{years_rot} as 'CO',
                                       'Non-Harvest - fug dust' as 'Source_Category',
                                       'NR' as 'NEI_Category',
                                       '{feed}' as 'Feedstock'
                                FROM {scenario_name}.{feed}_raw
                                WHERE description LIKE '%Non-Harvest%' AND description LIKE '%dust%' AND LEFT(RIGHT(run_code,2),1) != 'I'
                                GROUP BY fips;
                            """.format(**kvals)
        self.db.input(query_non_harvest)

    def get_irrig(self, kvals):
        if kvals['feed'] == 'cg':
            query_non_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                    SELECT fips,
                                           '{year}' as 'Year',
                                           '{yield}' as 'Yield',
                                           'CT',
                                           sum(NOx)/{years_rot} as 'NOx',
                                           sum(NH3)/{years_rot} as 'NH3',
                                           sum(VOC)/{years_rot} as 'VOC',
                                           sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)) as 'PM10',
                                           sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)) as 'PM25',
                                           sum(SOx)/{years_rot} as 'SOx',
                                           sum(CO)/{years_rot} as 'CO',
                                           'Irrigation' as 'Source_Category',
                                           'NR' as 'NEI_Category',
                                           '{feed}' as 'cg'
                                    FROM {scenario_name}.{feed}_raw
                                    WHERE description LIKE '%Non-Harvest%' AND description not LIKE '%dust%' AND LEFT(RIGHT(run_code,2),1) = 'I'
                                    GROUP BY fips;
                                """.format(**kvals)
            self.db.input(query_non_harvest)
            query_non_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                    SELECT fips,
                                           '{year}' as 'Year',
                                           '{yield}' as 'Yield',
                                           'RT',
                                           sum(NOx)/{years_rot} as 'NOx',
                                           sum(NH3)/{years_rot} as 'NH3',
                                           sum(VOC)/{years_rot} as 'VOC',
                                           sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)) as 'PM10',
                                           sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)) as 'PM25',
                                           sum(SOx)/{years_rot} as 'SOx',
                                           sum(CO)/{years_rot} as 'CO',
                                           'Irrigation' as 'Source_Category',
                                           'NR' as 'NEI_Category',
                                           '{feed}' as 'cg'
                                    FROM {scenario_name}.{feed}_raw
                                    WHERE description LIKE '%Non-Harvest%' AND description not LIKE '%dust%' AND LEFT(RIGHT(run_code,2),1) = 'I'
                                    GROUP BY fips;
                                """.format(**kvals)
            self.db.input(query_non_harvest)
            query_non_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                    SELECT fips,
                                           '{year}' as 'Year',
                                           '{yield}' as 'Yield',
                                           'NT',
                                           sum(NOx)/{years_rot} as 'NOx',
                                           sum(NH3)/{years_rot} as 'NH3',
                                           sum(VOC)/{years_rot} as 'VOC',
                                           sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)) as 'PM10',
                                           sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)) as 'PM25',
                                           sum(SOx)/{years_rot} as 'SOx',
                                           sum(CO)/{years_rot} as 'CO',
                                           'Irrigation' as 'Source_Category',
                                           'NR' as 'NEI_Category',
                                           '{feed}' as 'cg'
                                    FROM {scenario_name}.{feed}_raw
                                    WHERE description LIKE '%Non-Harvest%' AND description not LIKE '%dust%' AND LEFT(RIGHT(run_code,2),1) = 'I'
                                    GROUP BY fips;
                                """.format(**kvals)
            self.db.input(query_non_harvest)

    def get_harvest(self, kvals):
        if kvals['feed'] != 'sg':
            query_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                SELECT fips,
                                       '{year}' as 'Year',
                                       '{yield}' as 'Yield',
                                       CONCAT(LEFT(RIGHT(run_code, 2),1), 'T') as 'Tillage',
                                       sum(NOx)/{years_rot} as 'NOx',
                                       sum(NH3)/{years_rot} as 'NH3',
                                       sum(VOC)/{years_rot} as 'VOC',
                                       sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)/{years_rot}) as 'PM10',
                                       sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)/{years_rot}) as 'PM25',
                                       sum(SOx)/{years_rot} as 'SOx',
                                       sum(CO)/{years_rot} as 'CO',
                                       'Harvest' as 'Source_Category',
                                       'NR' as 'NEI_Category',
                                       '{feed}' as 'Feedstock'
                                FROM {scenario_name}.{feed}_raw
                                WHERE (description LIKE '% Harvest%' AND description not LIKE '%dust%' AND LEFT(RIGHT(run_code,2),1) != 'I')
                                GROUP BY fips;
                            """.format(**kvals)
            self.db.input(query_harvest)
        else:
            query_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                            SELECT fips,
                                   '{year}' as 'Year',
                                   '{yield}' as 'Yield',
                                   'NT',
                                   sum(NOx)/{years_rot} as 'NOx',
                                   sum(NH3)/{years_rot} as 'NH3',
                                   sum(VOC)/{years_rot} as 'VOC',
                                   sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)/{years_rot}) as 'PM10',
                                   sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)/{years_rot}) as 'PM25',
                                   sum(SOx)/{years_rot} as 'SOx',
                                   sum(CO)/{years_rot} as 'CO',
                                   'Harvest' as 'Source_Category',
                                   'NR' as 'NEI_Category',
                                   '{feed}' as 'Feedstock'
                            FROM {scenario_name}.{feed}_raw
                            WHERE (description LIKE '% Harvest%' AND description not LIKE '%dust%' AND LEFT(RIGHT(run_code,2),1) != 'I')
                            GROUP BY fips;
                        """.format(**kvals)
        self.db.input(query_harvest)

    def get_h_fd(self, kvals):
        if kvals['feed'] != 'sg':
            query_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                SELECT fips,
                                       '{year}' as 'Year',
                                       '{yield}' as 'Yield',
                                       CONCAT(LEFT(RIGHT(run_code, 2),1), 'T') as 'Tillage',
                                       sum(NOx)/{years_rot} as 'NOx',
                                       sum(NH3)/{years_rot} as 'NH3',
                                       sum(VOC)/{years_rot} as 'VOC',
                                       sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)/{years_rot}) as 'PM10',
                                       sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)/{years_rot}) as 'PM25',
                                       sum(SOx)/{years_rot} as 'SOx',
                                       sum(CO)/{years_rot} as 'CO',
                                       'Harvest - fug dust' as 'Source_Category',
                                       'NR' as 'NEI_Category',
                                       '{feed}' as 'Feedstock'
                                FROM {scenario_name}.{feed}_raw
                                WHERE (description LIKE '% Harvest%' AND description LIKE '%dust%' AND LEFT(RIGHT(run_code,2),1) != 'I')
                                GROUP BY fips;
                            """.format(**kvals)
            self.db.input(query_harvest)
        else:
            query_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                SELECT fips,
                                       '{year}' as 'Year',
                                       '{yield}' as 'Yield',
                                       'NT',
                                       sum(NOx)/{years_rot} as 'NOx',
                                       sum(NH3)/{years_rot} as 'NH3',
                                       sum(VOC)/{years_rot} as 'VOC',
                                       sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)/{years_rot}) as 'PM10',
                                       sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)/{years_rot}) as 'PM25',
                                       sum(SOx)/{years_rot} as 'SOx',
                                       sum(CO)/{years_rot} as 'CO',
                                       'Harvest - fug dust' as 'Source_Category',
                                       'NR' as 'NEI_Category',
                                       '{feed}' as 'Feedstock'
                                FROM {scenario_name}.{feed}_raw
                                WHERE (description LIKE '% Harvest%' AND description LIKE '%dust%' AND LEFT(RIGHT(run_code,2),1) != 'I')
                                GROUP BY fips;
                            """.format(**kvals)
            self.db.input(query_harvest)

    def get_loading(self, kvals):
        if kvals['feed'] != 'sg':
            query_loading = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                SELECT fips,
                                       '{year}' as 'Year',
                                       '{yield}' as 'Yield',
                                       CONCAT(LEFT(RIGHT(run_code, 2),1), 'T') as 'Tillage',
                                       sum(NOx)/{years_rot} as 'NOx',
                                       sum(NH3)/{years_rot} as 'NH3',
                                       sum(VOC)/{years_rot} as 'VOC',
                                       sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)/{years_rot}) as 'PM10',
                                       sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)/{years_rot}) as 'PM25',
                                       sum(SOx)/{years_rot} as 'SOx',
                                       sum(CO)/{years_rot} as 'CO',
                                       'Loading' as 'Source_Category',
                                       'NR' as 'NEI_Category',
                                       '{feed}' as 'Feedstock'
                                FROM {scenario_name}.{feed}_raw
                                WHERE (description = 'Loading' AND LEFT(RIGHT(run_code,2),1) != 'I')
                                GROUP BY fips;
                            """.format(**kvals)
            self.db.input(query_loading)
        else:
            query_loading = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, Tillage, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                            SELECT fips,
                                   '{year}' as 'Year',
                                   '{yield}' as 'Yield',
                                   'NT',
                                   sum(NOx)/{years_rot} as 'NOx',
                                   sum(NH3)/{years_rot} as 'NH3',
                                   sum(VOC)/{years_rot} as 'VOC',
                                   sum(PM10)/{years_rot} + sum(IFNULL(fug_pm10, 0)/{years_rot}) as 'PM10',
                                   sum(PM25)/{years_rot} + sum(IFNULL(fug_pm25, 0)/{years_rot}) as 'PM25',
                                   sum(SOx)/{years_rot} as 'SOx',
                                   sum(CO)/{years_rot} as 'CO',
                                   'Loading' as 'Source_Category',
                                   'NR' as 'NEI_Category',
                                   '{feed}' as 'Feedstock'
                            FROM {scenario_name}.{feed}_raw
                            WHERE (description = 'Loading' AND LEFT(RIGHT(run_code,2),1) != 'I')
                            GROUP BY fips;
                        """.format(**kvals)
        self.db.input(query_loading)

    def get_logistics(self, kvals):
        system_list = ['A', 'C']
        pol_list = ['NOx', 'PM10', 'PM25', 'SOx', 'VOC', 'CO', 'NH3']
        logistics = {'A': 'Advanced', 'C': 'Conventional'}
        feedstock = kvals['feed']

        run_logistics = self.feed_id_dict[feedstock.upper()]
        if run_logistics != 'None':
            for system in system_list:
                kvals['system'] = system
                for i, pollutant in enumerate(pol_list):
                    if pollutant == 'SOx':
                        kvals['pollutant'] = 'SO2'
                    else:
                        kvals['pollutant'] = pollutant
                    kvals['pollutant_name'] = pollutant
                    kvals['transport_cat'] = 'Transport, %s' % (logistics[system])
                    kvals['preprocess_cat'] = 'Pre-processing, %s' % (logistics[system])

                    logger.debug('Inserting data {transport_cat}, pollutant: {pollutant}'.format(**kvals))
                    if i == 0:
                        query_transport = """   INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, {pollutant}, Source_Category, NEI_Category, Feedstock)
                                                SELECT fips,
                                                       '{year}' as 'Year',
                                                       '{yield}' as 'Yield',
                                                       total_emissions/{years_rot} as '{pollutant_name}',
                                                       '{transport_cat}' as 'Source_Category',
                                                       'OR' as 'NEI_Category',
                                                       '{feed}' as 'Feedstock'
                                                FROM {scenario_name}.transportation
                                                WHERE  (logistics_type = '{system}' AND
                                                       yield_type = '{yield}' AND
                                                       feedstock = '{feed}' AND
                                                       pollutantID = '{pollutant_name}')
                                                GROUP BY fips;
                                            """.format(**kvals)
                        self.db.input(query_transport)

                        if pollutant == 'VOC':
                            query_pre_process = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, {pollutant}, Source_Category, NEI_Category, Feedstock)
                                                    SELECT fips,
                                                           '{year}' as 'Year',
                                                           '{yield}' as 'Yield',
                                                           IFNULL(voc_wood, 0)/{years_rot} as '{pollutant_name}',
                                                           '{preprocess_cat}' as 'Source_Category',
                                                           'P' as 'NEI_Category',
                                                           '{feed}' as 'Feedstock'
                                                    FROM {scenario_name}.processing
                                                    WHERE  (logistics_type = '{system}' AND
                                                           yield_type = '{yield}' AND
                                                           feed = '{feed}')
                                                    GROUP BY fips;
                                                """.format(**kvals)
                            self.db.input(query_pre_process)

                    elif i > 0:
                        if not pollutant.startswith('PM'):
                            query_transport = """   UPDATE {scenario_name}.total_emissions tot
                                                    INNER JOIN {scenario_name}.transportation trans
                                                    ON trans.fips = tot.fips AND trans.yield_type = tot.Yield AND trans.feedstock = tot.feedstock
                                                    SET tot.{pollutant_name} = trans.total_emissions/{years_rot}
                                                    WHERE   trans.pollutantID = '{pollutant}' AND
                                                            tot.Source_Category = '{transport_cat}' AND
                                                            trans.logistics_type = '{system}';
                                              """.format(**kvals)
                        elif pollutant.startswith('PM'):
                            query_transport = """   UPDATE {scenario_name}.total_emissions tot
                                                    INNER JOIN {scenario_name}.transportation trans
                                                    ON trans.fips = tot.fips AND trans.yield_type = tot.Yield AND trans.feedstock = tot.feedstock
                                                    LEFT JOIN {scenario_name}.fugitive_dust fd
                                                    ON fd.fips = tot.fips AND fd.yield_type = tot.Yield AND fd.feedstock = tot.feedstock
                                                    SET tot.{pollutant_name} = IF(trans.total_emissions > 0.0, (trans.total_emissions + fd.total_fd_emissions)/{years_rot}, 0)
                                                    WHERE   trans.pollutantID = '{pollutant}' AND
                                                            fd.pollutantID = '{pollutant}' AND
                                                            tot.Source_Category = '{transport_cat}' AND
                                                            trans.logistics_type = '{system}' AND
                                                            fd.logistics_type = '{system}';
                                              """.format(**kvals)
                            if pollutant == 'VOC':
                                query_pre_process = """ UPDATE {scenario_name}.total_emissions tot
                                                        INNER JOIN {scenario_name}.processing log
                                                        ON log.fips = tot.fips AND log.yield_type = tot.Yield AND log.feedstock = tot.feedstock
                                                        SET tot.{pollutant_name} = IFNULL(voc_wood, 0)/{years_rot}
                                                        WHERE   tot.Source_Category = '{preprocess_cat}' AND
                                                                log.logistics_type = '{system}';
                                                  """.format(**kvals)
                                self.db.input(query_pre_process)

                        self.db.input(query_transport)

    def get_data(self): 
        emissions_per_dt = dict()
        total_emissions = dict()
        for f_num, feedstock in enumerate(self.f_list):
            pol_dict_dt = dict()
            pol_dict_tot = dict()
            for p_num, pollutant in enumerate(self.pol_list):
                logger.info('Collecting data for pollutant: %s, feedstock: %s' % (pollutant, feedstock, ))
                pol_dict_dt[pollutant] = self.collect_data_per_prod(p_num=p_num, f_num=f_num)
                pol_dict_tot[pollutant] = self.collect_data_total_emissions(p_num=p_num, f_num=f_num)
            emissions_per_dt[feedstock] = pol_dict_dt
            total_emissions[feedstock] = pol_dict_tot

        results = {'emissions_per_dt': emissions_per_dt,
                   'total_emissions': total_emissions}
        return results
        
    def plot_emissions_per_gal(self, emissions_per_dt_dict):

        logger.info('Plotting emissions per gal')
        fig, axarr = plt.subplots(3, 2, figsize=(9, 9.5))
        matplotlib.rcParams.update({'font.size': 13})
        
        for p_num, pollutant in enumerate(self.pol_list):
            logger.info('Plotting emissions per gal for pollutant %s' % (pollutant, ))
            plotvals = list() 
            for f_num, feedstock in enumerate(self.f_list):
                total_emissions = emissions_per_dt_dict[feedstock][pollutant]
                
                emissions_per_gal = list(x[0]*(1e6/self.etoh_vals[f_num]) for x in total_emissions) 
                plotvals.append(emissions_per_gal)

            row = self.row_list[p_num]
            col = self.col_list[p_num]
            ax1 = axarr[row, col]
            ax1.set_yscale('log')
            ax1.set_ylim(bottom=1e-3, top=1e2)

            ax1.set_title(self.pol_list_label[p_num])
            ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter("%s"))
            
            bp = ax1.boxplot(plotvals, notch=0, sym='', vert=1, whis=1000)
                
            plt.setp(bp['boxes'], color='black')
            plt.setp(bp['whiskers'], color='black', linestyle='-')
            plt.setp(bp['medians'], color='black')
            # self.ax1.yaxis.set_major_formatter(FixedFormatter([0.00001, 0.0001, 0.001]))#for below y-axis
            
            self.__plot_interval__(plotvals, ax1)
            ax1.set_xticklabels(self.f_list, rotation='vertical')

        # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
        plt.setp([a.get_xticklabels() for a in axarr[0, :]], visible=False)
        plt.setp([a.get_xticklabels() for a in axarr[1, :]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)
        # plt.setp([a.get_yticklabels() for a in axarr[:, 2]], visible=False)

        axarr[0, 0].set_ylabel('g/gal EtOH', color='black', fontsize=14)
        axarr[1, 0].set_ylabel('g/gal EtOH', color='black', fontsize=14)
        axarr[2, 0].set_ylabel('g/gal EtOH', color='black', fontsize=14)

        fig.tight_layout()

        plt.show()
        
        data = [emissions_per_gal]
        
        return data

    def plot_emissions_per_dt(self, emissions_per_dt_dict):

        logger.info('Plotting emissions per dt')

        fig, axarr = plt.subplots(3, 2, figsize=(9, 10))
        matplotlib.rcParams.update({'font.size': 13})
        
        for p_num, pollutant in enumerate(self.pol_list):
            logger.info('Plotting emissions per dt for pollutant %s' % (pollutant, ))
            plotvals = list() 
            for f_num, feedstock in enumerate(self.f_list):
                emissions_per_dt = emissions_per_dt_dict[feedstock][pollutant]
                
                g_per_dt = list(x[0]*1e6 for x in emissions_per_dt)
                plotvals.append(g_per_dt)

            row = self.row_list[p_num]
            col = self.col_list[p_num]
            ax1 = axarr[row, col]
            ax1.set_yscale('log')
            ax1.set_ylim(bottom=1e-4, top=1e8)

            ax1.set_title(self.pol_list_label[p_num])
            ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter("%s"))
            
            bp = ax1.boxplot(plotvals, notch=0, sym='', vert=1, whis=1000)
                
            plt.setp(bp['boxes'], color='black')
            plt.setp(bp['whiskers'], color='black', linestyle='-')
            plt.setp(bp['medians'], color='black')
            # self.ax1.yaxis.set_major_formatter(FixedFormatter([0.00001, 0.0001, 0.001]))#for below y-axis
            
            self.__plot_interval__(plotvals, ax1)
            ax1.set_xticklabels(self.f_list, rotation='vertical')

        # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
        plt.setp([a.get_xticklabels() for a in axarr[0, :]], visible=False)
        plt.setp([a.get_xticklabels() for a in axarr[1, :]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)
        # plt.setp([a.get_yticklabels() for a in axarr[:, 2]], visible=False)

        axarr[0, 0].set_ylabel('Emissions (g/dt)', color='black', fontsize=14)
        axarr[1, 0].set_ylabel('Emissions (g/dt)', color='black', fontsize=14)
        axarr[2, 0].set_ylabel('Emissions (g/dt)', color='black', fontsize=14)

        fig.tight_layout()

        plt.show()
        
        data = [emissions_per_dt]
        
        return data
        
    def __plot_interval__(self, data_array, ax):

        num_feed = 4
        num_array = array([x for x in range(num_feed)]) + 1  # index starts at 1, not zero

        perc95list = list()
        perc5list = list()
        for i in range(0, num_feed):
            # plot 95% interval
            perc95list.append(scoreatpercentile(data_array[i], 95))

            # plot 5% interval
            perc5list.append(scoreatpercentile(data_array[i], 5))
        perc95 = array(perc95list)
        perc5 = array(perc5list)

        ax.plot(num_array, perc95, '_', markersize=15, color='k')
        ax.plot(num_array, perc5, '_', markersize=15, color='k')

    def collect_data_per_prod(self, p_num, f_num):
        """
        Collect data for one pollutant/feedstock combination
        Return the total emissions

        :param f_num: feedstock number
        :param p_num: pollutant number
        :return emissions_per_pollutant: emissions in (pollutant dt) / (total feedstock harvested dt)
        """

        kvals = {'feed_abr': self.f_list[f_num],
                 'feedstock': self.f_list[f_num],
                 'pollutant': self.pol_list[p_num],
                 'scenario_name': config.get('title'),
                 'production_schema': config.get('production_schema')}

        query_emissions_per_prod = """ SELECT (sum({pollutant}))/prod.total_prod AS 'mt_{pollutant}_perdt'
                                       FROM {scenario_name}.total_emissions tot
                                       LEFT JOIN {production_schema}.{feed_abr}_data prod ON tot.fips = prod.fips
                                       WHERE  prod.total_prod > 0.0 AND tot.{pollutant} > 0
                                       GROUP BY tot.FIPS
                                       ORDER BY tot.FIPS""".format(**kvals)
        emissions_per_production = self.db.output(query_emissions_per_prod)

        return emissions_per_production

    def collect_data_total_emissions(self, p_num, f_num):
        """
        Collect data for one pollutant/feedstock combination
        Return the total emissions

        :param f_num: feedstock number
        :param p_num: pollutant number
        :return emissions_per_pollutant: emissions in (pollutant dt) / (total feedstock harvested dt)
        """

        kvals = {'feed_abr': self.f_list[f_num],
                 'feedstock': self.f_list[f_num],
                 'pollutant': self.pol_list[p_num],
                 'scenario_name': config.get('title'),
                 'production_schema': config.get('production_schema')}

        query_emissions = """ SELECT (sum({pollutant}))
                               FROM {scenario_name}.total_emissions tot
                               LEFT JOIN {production_schema}.{feed_abr}_data prod ON tot.fips = prod.fips
                               WHERE  prod.total_prod > 0.0 AND tot.{pollutant} > 0
                               GROUP BY tot.FIPS
                               ORDER BY tot.FIPS""".format(**kvals)

        emissions = self.db.output(query_emissions)

        return emissions

    def contribution_figure(self):
        kvals = {'scenario_name': config.get('title'), }

        emissions_per_activity = dict()
        for f_num, feedstock in enumerate(self.f_list):
            pol_dict = dict()
            kvals['feed'] = feedstock.lower()
            for p_num, pollutant in enumerate(self.pol_list):
                kvals['pollutant'] = pollutant
                logger.info('Collecting data for emissions contribution figure for feedstock %s, pollutant %s' % (feedstock, pollutant, ))
                act_dict = dict()
                for act_num, activity in enumerate(self.act_list):
                    kvals['act'] = activity
                    if activity != 'Harvest':
                        query = """ SELECT selected.{pollutant}/total.sum_pol
                                    FROM {scenario_name}.total_emissions selected
                                    LEFT JOIN (SELECT fips, sum({pollutant}) as 'sum_pol'
                                                                                FROM {scenario_name}.total_emissions tot
                                                                                WHERE Feedstock = '{feed}'
                                                                                GROUP by tot.fips) total ON total.fips = selected.fips
                                    WHERE Source_Category Like '%{act}%' AND Feedstock = '{feed}' AND total.sum_pol > 0
                                    GROUP BY selected.fips
                                    """.format(**kvals)
                    else:
                        query = """ SELECT selected.{pollutant}/total.sum_pol
                                    FROM {scenario_name}.total_emissions selected
                                    LEFT JOIN (SELECT fips, sum({pollutant}) as 'sum_pol'
                                                                                FROM {scenario_name}.total_emissions tot
                                                                                WHERE Feedstock = '{feed}'
                                                                                GROUP by tot.fips) total ON total.fips = selected.fips
                                    WHERE Source_Category Like '%{act}%' AND not Source_Category LIKE '%Non-Harvest%' AND Feedstock = '{feed}' AND total.sum_pol > 0
                                    GROUP BY selected.fips
                                    """.format(**kvals)
                    act_dict[activity] = self.db.output(query)
                pol_dict[pollutant] = act_dict
            emissions_per_activity[feedstock] = pol_dict

        fig, axarr = plt.subplots(3, 6)
        matplotlib.rcParams.update({'font.size': 13})

        for i, pollutant in enumerate(self.pol_list):
            logger.info('Plotting data for emissions contribution figure for pollutant %s' % (pollutant, ))
            for j, activity in enumerate(self.act_list):
                for f_num, feedstock in enumerate(self.f_list):
                    emissions = emissions_per_activity[feedstock][pollutant][activity]

                    mean_val = mean(emissions)
                    med_val = median(emissions)
                    max_val = max(emissions)
                    min_val = min(emissions)

                    col = j
                    row = i
                    ax1 = axarr[col, row]
                    ax1.set_ylim(bottom=-0.05, top=1.05)

                    if col == 0:
                        ax1.set_title(self.pol_list_label[i])

                    if row == 0:
                        axarr[col, row].set_ylabel(activity)

                    ax1.plot([f_num + 1], mean_val, color=self.f_color[f_num], marker='_', markersize=20)
                    ax1.plot([f_num + 1], med_val, color=self.f_color[f_num], marker='_', markersize=7)

                    # Plot the max/min values
                    ax1.plot([f_num + 1] * 2, [max_val, min_val], color=self.f_color[f_num], marker=self.f_marker[f_num], markersize=2)

                    # Set axis limits
                    ax1.set_xlim([0, 6])

                    ax1.set_xticklabels(([''] + self.f_list), rotation='vertical')

        # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
        plt.setp([a.get_xticklabels() for a in axarr[0, :]], visible=False)
        plt.setp([a.get_xticklabels() for a in axarr[1, :]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 2]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 3]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 4]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 5]], visible=False)


        fig.tight_layout()

        plt.show()
