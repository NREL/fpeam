# -*- coding: utf-8 -*-
"""
Created on Tue Apr 12 14:07:42 2016

Creates figures for the 2016 Billion Ton Study

@author: aeberle
"""

from matplotlib import ticker
from pylab import *
from scipy.stats import scoreatpercentile

from model.Database import Database
from utils import config, logger
from matplotlib import ticker


class FigurePlottingBT16:
    def __init__(self, db):
        """

        :param db: model.Database instance
        :return:
        """

        # init properties
        self.db = db

        self.f_color = ['r', 'b', 'g', 'k', 'c', 'y', 'm', 'coral']  # @TODO: remove hardcoded values
        self.f_marker = ['o', 'o', 'o', 'o', 'o', 'o', 'o', 'o']  # @TODO: remove hardcoded values
        self.row_list = [0, 0, 1, 1, 2, 2, 0, 2]  # @TODO: remove hardcoded values
        self.col_list = [0, 1, 0, 1, 0, 1, 2, 2]  # @TODO: remove hardcoded values
        self.pol_list_label = ['$NO_x$', '$NH_3$', '$PM_{2.5}$', '$PM_{10}$', '$CO$', '$SO_x$', '$VOC$']  # @TODO: remove hardcoded values

        self.pol_list = ['nox', 'nh3', 'pm25', 'pm10', 'co', 'sox', 'voc']  # @TODO: remove hardcoded values

        self.feedstock_list = ['Corn Grain', 'Corn Stover', 'Sorghum stubble', 'Wheat Straw', 'Switchgrass', 'Miscanthus', 'Forest Residues', 'Whole Trees']  # @TODO: remove hardcoded values
        self.f_list = ['CG', 'CS', 'SS', 'WS', 'SG', 'MS', 'FR', 'FW']  # @TODO: remove hardcoded values
        self.act_list = ['Non-Harvest', 'Chemical', 'Harvest']  # @TODO: remove hardcoded values

        self.etoh_vals = [2.76 / 0.02756, 89.6, 89.6, 89.6, 89.6, 75.7, 75.7, 89.6]  # gallons per dry short ton  # @TODO: remove hardcoded values (convert to dt from bushels / 0.02756); add reference

        self.feed_id_dict = config.get('feed_id_dict')

    def compile_results(self):
        """

        :return:
        """

        # initialize kvals dict for string formatting
        kvals = {'scenario_name': self.db.schema,
                 'year': config.get('year_dict')['all_crops'],
                 'yield': config.get('yield'),
                 'production_schema': config.get('production_schema'),
                 'constants_schema': config.get('constants_schema'),
                 'te_table': 'total_emissions'
                 }

        # create backup
        # self.db.backup_table(schema=kvals['scenario_name'], table=kvals['te_table'])

        query_drop_table = """DROP TABLE IF EXISTS {scenario_name}.{te_table};""".format(**kvals)
        self.db.execute_sql(query_drop_table)

        query_create_table = """CREATE TABLE {scenario_name}.{te_table} (fips            char(5),
                                                                         year            char(4),
                                                                         yield           char(2),
                                                                         tillage         char(255),
                                                                         nox             float,
                                                                         nh3             float,
                                                                         voc             float,
                                                                         pm10            float,
                                                                         pm25            float,
                                                                         sox             float,
                                                                         co              float,
                                                                         source_category char(255),
                                                                         nei_category    char(2),
                                                                         feedstock       char(2))
                                ;""".format(**kvals)

        # self.db.execute_sql(query_drop_table)
        self.db.execute_sql(query_create_table)

        for feedstock in self.f_list:
            kvals['feed'] = feedstock.lower()
            kvals['years_rot'] = config.get('crop_budget_dict')['years'][feedstock]

            logger.info('Inserting data for chemical emissions for feedstock: {feed}'.format(**kvals))
            self.get_chem(kvals)

            logger.info('Inserting data for fertilizer emissions for feedstock: {feed}'.format(**kvals))
            self.get_fert(kvals)

            if feedstock == 'CG':
                logger.info('Inserting data for irrigation for feedstock: {feed}'.format(**kvals))
                self.get_irrig(kvals)

            if config['regional_crop_budget'] is True:
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

            logger.info('Inserting data for off-farm transportation and pre-processing for feedstock: {feed}'.format(**kvals))
            self.get_logistics(kvals)

        # add indicies
        columns = ('fips', 'year', 'yield', 'tillage', 'source_category', 'feedstock')
        for column in columns:
            sql = """CREATE INDEX idx_{te_table}_{c} ON {scenario_name}.{te_table} ({c});""".format(c=column, **kvals)
            self.db.execute_sql(sql)

        logger.info('Joining total emissions with production data')
        self.join_with_production_data(kvals)

        logger.info('Adding summed emissions and production columns')
        self.sum_emissions(kvals)

        logger.info('Joining NEI, NAA, and transportation data')
        self.add_nei_naa_and_transport(kvals)

    def add_nei_naa_and_transport(self, kvals):

        kvals['new_table'] = 'total_emissions_join_prod_sum_emissions_nei_trans'

        logistics_dict = {'A': 'adv',
                          'C': 'conv'}

        kvals['logistics'] = logistics_dict[config['logistics_type']]

        # feed_type_dict = config.get('feed_type_dict')
        # table_dict = config.get('transport_table_dict')
        # logistics = config.get('logistics_type')

        # back up table
        # self.db.backup_table(schema=kvals['scenario_name'], table=kvals['new_table'])


        # # create full join of NAA and total emissions
        # sql = "CREATE VIEW {scenario_name}.te_fulljoin_naa AS " \
        #       "SELECT * " \
        #       "FROM {scenario_name}.total_emissions_join_prod_sum_emissions te " \
        #       "LEFT JOIN naa.naa_2012 na " \
        #       "ON na.fips = te.fips " \
        #       "UNION " \
        #       "(SELECT * " \
        #       "FROM {scenario_name}.total_emissions_join_prod_sum_emissions te " \
        #       "RIGHT JOIN naa.naa_2012 na " \
        #       "ON na.fips = te.fips)".format(**kvals)
        # self.db.execute_sql(sql)

        # drop and then create table with combinations of year, yield, feedstock, tillage and fips for scenario
        sql = """DROP TABLE IF EXISTS {scenario_name}.scenario_combo;""".format(**kvals)
        self.db.execute_sql(sql)

        sql = """CREATE TABLE {scenario_name}.scenario_combo AS
                 SELECT ca.fips
                      , b.source_category
                      , c.yield
                      , d.year
                      , e.tillage
                      , f.feedstock
                 FROM   {constants_schema}.county_attributes ca
                 CROSS JOIN (SELECT DISTINCT source_category FROM {scenario_name}.total_emissions_join_prod_sum_emissions) b
                 CROSS JOIN (SELECT DISTINCT yield           FROM {scenario_name}.total_emissions_join_prod_sum_emissions) c
                 CROSS JOIN (SELECT DISTINCT year            FROM {scenario_name}.total_emissions_join_prod_sum_emissions) d
                 CROSS JOIN (SELECT DISTINCT tillage         FROM {scenario_name}.total_emissions_join_prod_sum_emissions) e
                 CROSS JOIN (SELECT DISTINCT feedstock       FROM {scenario_name}.total_emissions_join_prod_sum_emissions) f
              """.format(**kvals)
        self.db.execute_sql(sql)

        for col in ('fips', 'source_category', 'yield', 'year', 'tillage', 'feedstock'):
            sql = 'ALTER TABLE {scenario_name}.scenario_combo ADD INDEX idx_scenario_combo_{col} ({col});'.format(col=col, **kvals)
            self.db.execute_sql(sql)

        # # drop and then create view of total emissions joined with naa
        # sql = """DROP VIEW IF EXISTS {scenario_name}.te_fulljoin_naa;""".format(**kvals)
        # self.db.execute_sql(sql)

        # drop and then create view of total emissions joined with naa
        sql = """DROP TABLE IF EXISTS {scenario_name}.{new_table};""".format(**kvals)
        self.db.execute_sql(sql)

        # sql = """CREATE VIEW {scenario_name}.te_fulljoin_naa AS
        sql = """CREATE TABLE           {scenario_name}.{new_table} AS
                 SELECT sc.fips
                      , sc.year
                      , sc.yield
                      , sc.tillage
                      , sc.source_category
                      , sc.feedstock

                      , te.nox, te.nh3, te.voc, te.pm10, te.pm25, te.sox, te.co, te.nei_category, te.prod, te.harv_ac,
                        te.total_nox, te.total_nh3, te.total_voc, te.total_pm10, te.total_pm25, te.total_sox,
                        te.total_co, te.total_prod, te.total_harv_ac, te.total_nox_trans, te.total_nh3_trans,
                        te.total_voc_trans, te.total_pm10_trans, te.total_pm25_trans, te.total_sox_trans, te.total_co_trans

                      , na.ozone_8hr_2008
                      , na.co_1971
                      , na.no2_1971
                      , na.pm10_1987
                      , na.pm25_1997_2006_2012
                      , na.so2_1971_2010

                      , nei_npnror.nei_nox_npnror
                      , nei_npnror.nei_sox_npnror
                      , nei_npnror.nei_pm10_npnror
                      , nei_npnror.nei_pm25_npnror
                      , nei_npnror.nei_voc_npnror
                      , nei_npnror.nei_nh3_npnror
                      , nei_npnror.nei_co_npnror
                      , nei_npnrorp.nei_voc__npnrorp

                      , COALESCE(trans.avg_total_cost, trans2.avg_total_cost) AS avg_total_cost
                      , COALESCE(trans.avg_dist, trans2.avg_dist)             AS avg_dist
                      , COALESCE(trans.used_qnty, trans2.used_qnty)           AS used_qnty

                 FROM      {scenario_name}.scenario_combo                          sc
                 LEFT JOIN naa.naa_2012                                            na ON (    na.fips            = sc.fips)
                 LEFT JOIN {scenario_name}.total_emissions_join_prod_sum_emissions te ON (    te.fips            = sc.fips
                                                                                          AND te.source_category = sc.source_category
                                                                                          AND te.yield           = sc.yield
                                                                                          AND te.year            = sc.year
                                                                                          AND te.tillage         = sc.tillage
                                                                                          AND te.feedstock       = sc.feedstock
                                                                                         )

                 LEFT JOIN (SELECT fips      AS fips
                                 , SUM(nox)  AS nei_nox_npnror
                                 , SUM(sox)  AS nei_sox_npnror
                                 , SUM(pm10) AS nei_pm10_npnror
                                 , SUM(pm25) AS nei_pm25_npnror
                                 , SUM(voc)  AS nei_voc_npnror
                                 , SUM(nh3)  AS nei_nh3_npnror
                                 , SUM(co)   AS nei_co_npnror
                            FROM nei.nei_2011
                            WHERE category != 'BVOC' AND category != 'P'
                            GROUP BY fips)                                         nei_npnror ON nei_npnror.fips = te.fips

                 LEFT JOIN (SELECT fips
                                 , SUM(voc) AS nei_voc__npnrorp
                            FROM nei.nei_2011
                            WHERE category != 'BVOC'
                            GROUP BY fips)                                    nei_npnrorp ON nei_npnrorp.fips = te.fips

                 LEFT JOIN (SELECT sply_fips
                                 , SUM(avg_total_cost) / COUNT(avg_total_cost) AS avg_total_cost
                                 , SUM(avg_dist)/count(avg_dist)               AS avg_dist
                                 , SUM(used_qnty)                              AS used_qnty
                                 , feed_abbr                                   AS feedstock
                            FROM {production_schema}.transport_herb_{yield}_{logistics}_{year}
                            GROUP BY sply_fips, feed_id)                           trans ON (trans.sply_fips = te.fips AND te.feedstock = trans.feedstock)

                 LEFT JOIN (SELECT sply_fips
                                 , SUM(avg_total_cost) / COUNT(avg_total_cost) AS avg_total_cost
                                 , SUM(avg_dist)       / COUNT(avg_dist)       AS avg_dist
                                 , SUM(used_qnty)                              AS used_qnty
                                 , feed_abbr                                  AS feedstock
                            FROM {production_schema}.transport_woody_{yield}_{logistics}_{year}
                            GROUP BY sply_fips, feed_id)                           trans2 ON (trans2.sply_fips = te.fips AND te.feedstock = trans2.feedstock)
              ;""".format(**kvals)

        self.db.execute_sql(sql=sql)

        for col in ('fips', 'year', 'yield', 'tillage', 'source_category', 'feedstock', 'nox', 'nh3', 'voc', 'pm10', 'pm25', 'sox', 'co', 'nei_category', 'prod', 'harv_ac', 'total_nox', 'total_nh3', 'total_voc', 'total_pm10', 'total_pm25', 'total_sox', 'total_co', 'total_prod', 'total_harv_ac', 'total_nox_trans', 'total_nh3_trans'):
            sql = 'CREATE INDEX idx_{new_table}_{col} ON {scenario_name}.{new_table} ({col});'.format(col=col, **kvals)
            self.db.execute_sql(sql=sql)

    def sum_emissions(self, kvals):

        kvals['table'] = 'total_emissions_join_prod'
        kvals['new_table'] = 'total_emissions_join_prod_sum_emissions'

        for i, feed in enumerate(self.f_list):
            logger.info('Adding summed emissions for feed: %s' % (feed, ))
            kvals['feed'] = feed.lower()
            if i == 0:
                    # back up table
                    # self.db.backup_table(schema=kvals['scenario_name'], table=kvals['new_table'])

                    # drop old table and create new table
                    sql = "DROP   TABLE IF EXISTS {scenario_name}.{new_table};\n".format(**kvals)
                    self.db.execute_sql(sql)

                    sql = "CREATE TABLE           {scenario_name}.{new_table} AS\n"
            else:
                # insert data
                sql = "INSERT INTO {scenario_name}.{new_table}\n"

            if feed == 'CG':
                kvals['convert_bushel'] = 0.025
            else:
                kvals['convert_bushel'] = 1

            sql += """SELECT tot.*,
                             sum.total_nox,
                             sum.total_nh3,
                             sum.total_voc,
                             sum.total_pm10,
                             sum.total_pm25,
                             sum.total_sox,
                             sum.total_co,
                             dat.total_prod * {convert_bushel} AS total_prod,
                             dat.total_harv_ac,
                             sum.total_nox  + sum_trans.total_nox_with_transport  AS total_nox_trans,
                             sum.total_nh3  + sum_trans.total_nh3_with_transport  AS total_nh3_trans,
                             sum.total_voc  + sum_trans.total_voc_with_transport  AS total_voc_trans,
                             sum.total_pm10 + sum_trans.total_pm10_with_transport AS total_pm10_trans,
                             sum.total_pm25 + sum_trans.total_pm25_with_transport AS total_pm25_trans,
                             sum.total_sox  + sum_trans.total_sox_with_transport  AS total_sox_trans,
                             sum.total_co   + sum_trans.total_co_with_transport   AS total_co_trans
                        FROM {scenario_name}.{table} tot
                        LEFT JOIN  (SELECT fips,
                                           feedstock,
                                           year,
                                           yield,
                                           tillage,
                                           SUM(nox)  AS total_nox,
                                           SUM(nh3)  AS total_nh3,
                                           SUM(voc)  AS total_voc,
                                           SUM(pm10) AS total_pm10,
                                           SUM(pm25) AS total_pm25,
                                           SUM(sox)  AS total_sox,
                                           SUM(co)   AS total_co
                                    FROM  {scenario_name}.{table}
                                    WHERE feedstock = '{feed}' AND source_category NOT LIKE '%transport%' AND source_category NOT LIKE '%process%'
                                    GROUP BY fips, feedstock, year, yield, tillage) sum
                        ON tot.fips = SUM.fips AND tot.feedstock = sum.feedstock AND tot.year = sum.year AND tot.yield = sum.yield AND tot.tillage = sum.tillage
                        LEFT JOIN  (SELECT fips,
                                           feedstock,
                                           year,
                                           yield,
                                           source_category,
                                           tillage,
                                           SUM(nox)  AS total_nox_with_transport,
                                           SUM(nh3)  AS total_nh3_with_transport,
                                           SUM(voc)  AS total_voc_with_transport,
                                           SUM(pm10) AS total_pm10_with_transport,
                                           SUM(pm25) AS total_pm25_with_transport,
                                           SUM(sox)  AS total_sox_with_transport,
                                           SUM(co)   AS total_co_with_transport
                                    FROM  {scenario_name}.{table}
                                    WHERE feedstock = '{feed}' AND (source_category LIKE '%transport%' OR source_category LIKE '%process%')
                                    GROUP BY fips, feedstock, year, yield, tillage) sum_trans
                        ON tot.fips = sum_trans.fips AND tot.feedstock = sum_trans.feedstock AND tot.year = sum_trans.year AND tot.yield = sum_trans.yield AND tot.tillage = sum_trans.tillage
                        LEFT JOIN (SELECT fips,
                                          SUM(total_prod) * {convert_bushel}  AS total_prod,
                                          SUM(total_harv_ac)                  AS total_harv_ac
                                   FROM {production_schema}.{feed}_data cd
                                   GROUP BY    cd.fips) dat
                        ON tot.fips = dat.fips AND tot.feedstock = '{feed}'
                        WHERE tot.feedstock = '{feed}'
                        ;""".format(**kvals)
            sql = sql.format(**kvals)
            self.db.execute_sql(sql=sql)

        for col in ('fips', 'source_category', 'yield', 'year', 'tillage', 'feedstock'):
            sql = "CREATE INDEX idx_{new_table}_{col} ON {scenario_name}.{new_table} ({col});".format(col=col, **kvals)
            self.db.execute_sql(sql)

    def join_with_production_data(self, kvals):
        """

        :param kvals: dictionary for string formatting
        :return:
        """
        kvals['table'] = 'total_emissions_join_prod'
        kvals['te_table'] = 'total_emissions'

        i = 0
        for feedstock in self.f_list:
            feed = feedstock.lower()
            kvals['feed'] = feed

            if feed == 'sg':
                till_dict = {'NT': 'notill'}
            elif feed == 'ms':
                till_dict = {'CT': 'convtill'}
            elif feed.startswith('f'):
                till_dict = {'NT': 'notill'}
            else:
                till_dict = {'CT': 'convtill',
                             'RT': 'reducedtill',
                             'NT': 'notill'}

            for till in till_dict:
                kvals['till'] = till
                kvals['tillage'] = till_dict[till]
                logger.info('Joining production data for %s %s' % (feedstock, till))
                if i == 0:
                    # back up table
                    # self.db.backup_table(schema=kvals['scenario_name'], table=kvals['table'])

                    # drop old table and create new table
                    sql = "DROP   TABLE IF EXISTS {scenario_name}.{table};\n".format(**kvals)
                    self.db.execute_sql(sql)
                    sql = "CREATE TABLE           {scenario_name}.{table} AS\n"
                else:
                    # insert data
                    sql = "INSERT INTO {scenario_name}.{table}\n"

                if feedstock == 'CG':
                    kvals['convert_bushel'] = 0.025
                else:
                    kvals['convert_bushel'] = 1

                # gather data
                sql += "SELECT      tot.*,\n"
                sql += "            SUM(cd.{tillage}_prod) * {convert_bushel}    AS prod,\n"
                sql += "            SUM(cd.{tillage}_harv_ac) AS harv_ac\n"
                sql += "FROM        {scenario_name}.{te_table} tot\n"
                sql += "LEFT JOIN   {production_schema}.{feed}_data cd\n"
                sql += "       ON   cd.fips = tot.fips\n"
                sql += "WHERE       tot.tillage   = '{till}' AND\n"
                sql += "            tot.feedstock = '{feed}' \n" \
                       "GROUP BY    cd.fips, source_category \n"
                sql += ";"
                sql = sql.format(**kvals)

                self.db.execute_sql(sql=sql)

                i += 1

            # update total emissions for transport to allocate using actual production values rather than reduction factor (1/3)
            # @TODO: transport emissions need to be weighted correctly when inserted into total emissions table (under get_logistics)
            for pollutant in self.pol_list:
                kvals['pollutant'] = pollutant
                sql = """UPDATE {scenario_name}.{table} a
                             LEFT JOIN (SELECT fips, feedstock, year, yield, source_category, sum({pollutant}) AS sum_{pollutant}, sum(prod) AS total_prod
                                        FROM {scenario_name}.{table}
                                        WHERE source_category LIKE '%transport%'
                                        GROUP BY fips, feedstock, year, yield, source_category) b
                             ON (a.fips = b.fips AND
                                a.feedstock = b.feedstock AND
                                a.year = b.year AND
                                a.yield = b.yield AND
                                a.source_category = b.source_category)
                             SET a.{pollutant} = b.sum_{pollutant} * a.prod / b.total_prod
                             WHERE a.source_category LIKE '%transport%'""".format(**kvals)

                self.db.execute_sql(sql=sql)

        for col in ('fips', 'year', 'yield', 'tillage', 'source_category', 'feedstock'):
            sql = "CREATE INDEX idx_{table}_{col} ON {scenario_name}.{table} ({col});".format(col=col, **kvals)
            self.db.execute_sql(sql)

    def get_chem(self, kvals):
        """
        Add chemical emissions to total emissions table.

        :param kvals: dictionary for string formatting
        :return:
        """

        query_fert_chem = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                             SELECT
                                 chem.fips    AS fips,
                                 '{year}'     AS year,
                                 '{yield}'    AS yield,
                                 chem.tillage AS tillage,
                                 0            AS nox,
                                 0            AS nh3,
                                 chem.voc     AS voc,
                                 0            AS pm10,
                                 0            AS pm25,
                                 0            AS sox,
                                 0            AS co,
                                 'Chemical'   AS source_category,
                                 'NP'         AS nei_category,
                                 '{feed}'     AS feedstock
                             FROM (SELECT
                                       fips                   AS fips,
                                       tillage                AS tillage,
                                       SUM(voc) / {years_rot} AS voc
                                   FROM {scenario_name}.{feed}_chem
                                   GROUP BY fips, tillage
                                  ) chem
                             ;""".format(**kvals)

        self.db.input(query_fert_chem)

    def get_fert(self, kvals):
        """
        Add fertilizer emissions to total emissions table.

        :param kvals: dictionary for string formatting
        :return:
        """

        query_fert_fert = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                             SELECT fert.fips,
                                    '{year}'     AS year,
                                    '{yield}'    AS yield,
                                    fert.tillage AS tillage,
                                    fert.nox     AS nox,
                                    fert.nh3     AS nh3,
                                    0            AS voc,
                                    0            AS pm10,
                                    0            AS pm25,
                                    0            AS sox,
                                    0            AS co,
                                    'Fertilizer' AS source_category,
                                    'NP'         AS nei_category,
                                    '{feed}'     AS feedstock
                             FROM (SELECT
                                       fips,
                                       SUM(nox) / {years_rot}  AS nox,
                                       SUM(nh3) / {years_rot}  AS nh3,
                                       tillage
                                   FROM {scenario_name}.{feed}_nfert
                                   GROUP BY fips, tillage
                                  ) fert
                             ;""".format(**kvals)

        self.db.input(query_fert_fert)

    def get_non_harvest(self, kvals):
        """
        Add non-harvest activity emissions to total emissions table.

        :param kvals: dictionary for string formatting
        :return:
        """

        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms' and (not kvals['feed'].startswith('f')):
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2),1), 'T')"
        elif kvals['feed'] == 'sg':
            kvals['tillage'] = "'NT'"
        elif kvals['feed'] == 'ms':
            kvals['tillage'] = "'CT'"
        elif kvals['feed'].startswith('f'):
            kvals['tillage'] = "'NT'"

        query_non_harvest = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                               SELECT fips                                          AS fips,
                                      '{year}'                                      AS year,
                                      '{yield}'                                     AS yield,
                                      {tillage}                                     AS tillage,
                                      SUM(nox)                        / {years_rot} AS nox,
                                      SUM(nh3)                        / {years_rot} AS nh3,
                                      SUM(voc)                        / {years_rot} AS voc,
                                      SUM(pm10 + IFNULL(fug_pm10, 0)) / {years_rot} AS pm10,
                                      SUM(pm25 + IFNULL(fug_pm25, 0)) / {years_rot} AS pm25,
                                      SUM(sox)                        / {years_rot} AS sox,
                                      SUM(co)                         / {years_rot} AS co,
                                      'Non-Harvest'                                 AS source_category,
                                      'NR'                                          AS nei_category,
                                      '{feed}'                                      AS feedstock
                               FROM {scenario_name}.{feed}_raw
                               WHERE description     LIKE '%Non-Harvest%'
                                 AND description NOT LIKE '%dust%'
                                 AND LEFT(RIGHT(run_code, 2), 1) != 'I'
                               GROUP BY fips, tillage
                               ;""".format(**kvals)

        self.db.input(query_non_harvest)

    def get_nh_fd(self, kvals):
        """
        Add non-harvest fugitive dust emissions to total emissions table.

        :param kvals: dictionary for string formatting
        :return:
        """

        kvals['source_category'] = 'Non-Harvest - fug dust'

        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms' and (not kvals['feed'].startswith('f')):
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2),1), 'T')"
        elif kvals['feed'] == 'sg':
            kvals['tillage'] = "'NT'"
        elif kvals['feed'] == 'ms':
            kvals['tillage'] = "'CT'"
        elif kvals['feed'].startswith('f'):
            kvals['tillage'] = "'NT'"

        query_non_harvest = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                               SELECT  fips,
                                       '{year}'                                      AS year,
                                       '{yield}'                                     AS yield,
                                       {tillage}                                     AS tillage,
                                       SUM(nox)                        / {years_rot} AS nox,
                                       SUM(nh3)                        / {years_rot} AS nh3,
                                       SUM(voc)                        / {years_rot} AS voc,
                                       SUM(pm10 + IFNULL(fug_pm10, 0)) / {years_rot} AS pm10,
                                       SUM(pm25 + IFNULL(fug_pm25, 0)) / {years_rot} AS pm25,
                                       SUM(sox)                        / {years_rot} AS sox,
                                       SUM(co)                         / {years_rot} AS co,
                                       '{source_category}'                           AS source_category,
                                       'NR'                                          AS nei_category,
                                       '{feed}'                                      AS feedstock
                              FROM     {scenario_name}.{feed}_raw
                              WHERE    description LIKE '%Non-Harvest%' AND
                                       description LIKE '%dust%'
                              GROUP BY fips, tillage
                              ;""".format(**kvals)

        self.db.input(query_non_harvest)

    def get_irrig(self, kvals):
        """
        Add chemical emissions to total emissions table.

        :param kvals: dictionary for string formatting
        :return:
        """

        if kvals['feed'] == 'cg':
            # possible tillage types and their corresponding column names for production data
            tillage_dict = {'CT': 'convtill',
                            'RT': 'reducedtill',
                            'NT': 'notill'}

            # set reduction factor
            kvals['red_fact'] = 1.0 / len(tillage_dict)

            for tillage in tillage_dict:
                kvals['tillage'] = tillage
                kvals['till_type'] = tillage_dict[tillage]
                query_non_harvest = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                                       SELECT rd.fips,
                                              '{year}'                                                                                AS year,
                                              '{yield}'                                                                               AS yield,
                                              '{tillage}'                                                                             AS tillage,
                                              SUM(nox)                        / {years_rot} * {till_type}_harv_ac / total_harv_ac     AS nox,
                                              SUM(nh3)                        / {years_rot} * {till_type}_harv_ac / total_harv_ac     AS nh3,
                                              SUM(voc)                        / {years_rot} * {till_type}_harv_ac / total_harv_ac     AS voc,
                                              SUM(pm10 + IFNULL(fug_pm10, 0)) / {years_rot} * {till_type}_harv_ac / total_harv_ac     AS pm10,
                                              SUM(pm25 + IFNULL(fug_pm25, 0)) / {years_rot} * {till_type}_harv_ac / total_harv_ac     AS pm25,
                                              SUM(sox)                        / {years_rot} * {till_type}_harv_ac / total_harv_ac     AS sox,
                                              SUM(co)                         / {years_rot} * {till_type}_harv_ac / total_harv_ac     AS co,
                                              'Irrigation'                                                                            AS source_category,
                                              'NR'                                                                                    AS nei_category,
                                              '{feed}'                                                                                AS cg
                                       FROM  {scenario_name}.{feed}_raw rd
                                       LEFT JOIN {production_schema}.{feed}_data pd ON rd.fips = pd.fips
                                       WHERE description     LIKE '%Non-Harvest%'
                                         AND description NOT LIKE '%dust%'
                                         AND LEFT(RIGHT(run_code, 2), 1) = 'I'
                                         AND {till_type}_harv_ac > 0
                                       GROUP BY rd.fips
                                       ;""".format(**kvals)

                self.db.input(query_non_harvest)

    def get_harvest(self, kvals):
        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms' and (not kvals['feed'].startswith('f')):
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2), 1), 'T')"
        elif kvals['feed'] == 'sg':
            kvals['tillage'] = "'NT'"
        elif kvals['feed'] == 'ms':
            kvals['tillage'] = "'CT'"
        elif kvals['feed'].startswith('f'):
            kvals['tillage'] = "'NT'"

        query_harvest = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                           SELECT   fips,
                                    '{year}'                                      AS year,
                                    '{yield}'                                     AS yield,
                                    {tillage}                                     AS tillage,
                                    SUM(nox)                        / {years_rot} AS nox,
                                    SUM(nh3)                        / {years_rot} AS nh3,
                                    SUM(voc)                        / {years_rot} AS voc,
                                    SUM(pm10 + IFNULL(fug_pm10, 0)) / {years_rot} AS pm10,
                                    SUM(pm25 + IFNULL(fug_pm25, 0)) / {years_rot} AS pm25,
                                    SUM(sox)                        / {years_rot} AS sox,
                                    SUM(co)                         / {years_rot} AS co,
                                    'Harvest'                                     AS source_category,
                                    'NR'                                          AS nei_category,
                                    '{feed}'                                      AS feedstock
                           FROM     {scenario_name}.{feed}_raw
                           WHERE    description     LIKE '% Harvest%'
                             AND    description NOT LIKE '%dust%'
                             AND    LEFT(RIGHT(run_code, 2), 1) != 'I'
                           GROUP BY fips, tillage
                           ;""".format(**kvals)

        self.db.input(query_harvest)

    def get_h_fd(self, kvals):
        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms' and (not kvals['feed'].startswith('f')):
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2),1), 'T')"
        elif kvals['feed'] == 'sg':
            kvals['tillage'] = "'NT'"
        elif kvals['feed'] == 'ms':
            kvals['tillage'] = "'CT'"
        elif kvals['feed'].startswith('f'):
            kvals['tillage'] = "'NT'"

        query_harvest = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                           SELECT   fips,
                                    '{year}'                                      AS year,
                                    '{yield}'                                     AS yield,
                                    {tillage}                                     AS tillage,
                                    SUM(nox)                        / {years_rot} AS nox,
                                    SUM(nh3)                        / {years_rot} AS nh3,
                                    SUM(voc)                        / {years_rot} AS voc,
                                    SUM(pm10 + IFNULL(fug_pm10, 0)) / {years_rot} AS pm10,
                                    SUM(pm25 + IFNULL(fug_pm25, 0)) / {years_rot} AS pm25,
                                    SUM(sox)                        / {years_rot} AS sox,
                                    SUM(co)                         / {years_rot} AS co,
                                    'Harvest - fug dust'                          AS source_category,
                                    'NR'                                          AS nei_category,
                                    '{feed}'                                      AS feedstock
                           FROM     {scenario_name}.{feed}_raw
                           WHERE    description LIKE '% Harvest%'
                             AND    description LIKE '%dust%'
                             AND    LEFT(RIGHT(run_code, 2), 1) != 'I'
                           GROUP BY fips, tillage
                           ;""".format(**kvals)

        self.db.input(query_harvest)

    def get_loading(self, kvals):
        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms' and (not kvals['feed'].startswith('f')):
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2), 1), 'T')"
        elif kvals['feed'] == 'sg':
            kvals['tillage'] = "'NT'"
        elif kvals['feed'] == 'ms':
            kvals['tillage'] = "'CT'"
        elif kvals['feed'].startswith('f'):
            kvals['tillage'] = "'NT'"

        query_loading = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                           SELECT   fips,
                                    '{year}'                                      AS year,
                                    '{yield}'                                     AS yield,
                                    {tillage}                                     AS tillage,
                                    SUM(nox)                        / {years_rot} AS nox,
                                    SUM(nh3)                        / {years_rot} AS nh3,
                                    SUM(voc)                        / {years_rot} AS voc,
                                    SUM(pm10 + IFNULL(fug_pm10, 0)) / {years_rot} AS pm10,
                                    SUM(pm25 + IFNULL(fug_pm25, 0)) / {years_rot} AS pm25,
                                    SUM(sox)                        / {years_rot} AS sox,
                                    SUM(co)                         / {years_rot} AS co,
                                    'Loading'                                     AS source_category,
                                    'NR'                                          AS nei_category,
                                    '{feed}'                                      AS feedstock
                           FROM     {scenario_name}.{feed}_raw
                           WHERE    description LIKE '%Loading%'
                             AND    LEFT(RIGHT(run_code, 2), 1) != 'I'
                           GROUP BY fips, tillage
                           ;""".format(**kvals)

        self.db.input(query_loading)

    def get_logistics(self, kvals):
        system_list = [config.get('logistics_type'), ]
        pol_list = ['sox', 'nox', 'pm10', 'pm25', 'voc', 'co', 'nh3']
        logistics = {'A': 'Advanced', 'C': 'Conventional'}
        feedstock = kvals['feed']
        categories = ['Transport', 'Pre-processing']

        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms' and (not kvals['feed'].startswith('f')):
            tillage_list = ['NT', 'RT', 'CT']
        elif kvals['feed'] == 'sg':
            tillage_list = ['NT', ]
        elif kvals['feed'] == 'ms':
            tillage_list = ['CT', ]
        elif kvals['feed'].startswith('f'):
            tillage_list = ['NT', ]

        run_logistics = self.feed_id_dict[feedstock.upper()]
        if run_logistics != 'None':
            for system in system_list:  # logistics type
                kvals['system'] = system
                for tillage in tillage_list:
                    kvals['tillage'] = tillage
                    kvals['reduction_factor'] = len(tillage_list)
                    for cat in categories:
                        kvals['cat'] = '%s, %s' % (cat, logistics[system],)
                        query = str()

                        if cat == 'Transport':

                            for i, pollutant in enumerate(pol_list):

                                if pollutant == 'sox':
                                    kvals['pollutant'] = 'so2'
                                else:
                                    kvals['pollutant'] = pollutant
                                kvals['pollutant_name'] = pollutant

                                kvals['selection'] = """trans.feedstock  = '{feed}'
                                    AND       trans.pollutantID    = '{pollutant}'
                                    AND       trans.logistics_type = '{system}'
                                    AND       trans.yield_type     = '{yield}'
                                    AND       trans.yearID         = '{year}'""".format(**kvals)
                                logger.info('Inserting data for {cat}, {tillage}, {pollutant}'.format(**kvals))
                                if i == 0:
                                    query += """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                                                SELECT feed_sox.fips,
                                                       '{year}',
                                                       '{yield}',
                                                       '{tillage}',
                                                       feed_nox.nox,
                                                       feed_nh3.nh3,
                                                       feed_voc.voc,
                                                       feed_pm10.pm10_trans + feed_pm10fd.pm10_fug AS pm10,
                                                       feed_pm25.pm25_trans + feed_pm25fd.pm25_fug AS pm25,
                                                       feed_sox.sox,
                                                       feed_co.co,
                                                       '{cat}',
                                                       'OR' AS nei_category,
                                                       '{feed}'
                                                FROM   (SELECT trans.pollutantID,
                                                               trans.fips AS fips,
                                                               trans.total_emissions / {reduction_factor} AS sox
                                                        FROM   {scenario_name}.transportation trans
                                                        WHERE  {selection}
                                                       ) feed_sox
                                                """.format(**kvals)
                                else:
                                    if not pollutant.startswith('pm'):  # @TODO: verify 'DISTINCT' is needed/correct
                                        query += """LEFT JOIN (SELECT DISTINCT trans.pollutantID,
                                                                      trans.total_emissions / {reduction_factor} AS {pollutant},
                                                                      trans.fips                                 AS fips
                                                               FROM   {scenario_name}.transportation trans
                                                               WHERE  {selection}
                                                              ) feed_{pollutant}
                                                           ON feed_{pollutant}.fips = feed_sox.fips

                                                    """.format(**kvals)
                                    elif pollutant.startswith('pm'):
                                        query += """LEFT JOIN (SELECT pollutantID,
                                                                      trans.total_emissions/{reduction_factor} AS '{pollutant}_trans',
                                                                      trans.fips as 'fips'
                                                                    FROM {scenario_name}.transportation  trans
                                                                    WHERE 	{selection}) feed_{pollutant}
                                                                    ON feed_{pollutant}.fips = feed_sox.fips

                                                                    LEFT JOIN (SELECT pollutantID,
                                                                                      fd.total_fd_emissions / {reduction_factor} AS '{pollutant}_fug',
                                                                                      fd.fips as 'fips'
                                                                    FROM {scenario_name}.fugitive_dust fd
                                                                    WHERE 		fd.feedstock      = '{feed}'
                                                                      AND       fd.pollutantID    = '{pollutant}'
                                                                      AND       fd.logistics_type = '{system}'
                                                                      AND       fd.yield_type     = '{yield}'
                                                                      AND       fd.yearID         = '{year}'
                                                                      ) feed_{pollutant}fd

                                                    ON feed_{pollutant}fd.fips = feed_sox.fips
                                                """.format(**kvals)
                        elif cat == 'Pre-processing':
                            kvals['selection'] = """proc.feed  = '{feed}'
                                                    AND       proc.logistics_type = '{system}'
                                                    AND       proc.yield_type = '{yield}'""".format(**kvals)

                            query += """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, voc, source_category, nei_category, feedstock)
                                SELECT feed_voc.fips,
                                       '{year}',
                                       '{yield}',
                                       '{tillage}',
                                       feed_voc.voc,
                                       '{cat}',
                                       'P' AS nei_category,
                                       '{feed}'
                                FROM   (SELECT   proc.fips AS fips,
                                                 SUM(proc.voc_wood) / {reduction_factor} AS voc
                                        FROM     {scenario_name}.processing proc
                                        WHERE    {selection}
                                        GROUP BY proc.fips
                                       ) feed_voc
                                """.format(**kvals)

                        self.db.input(query)

    def get_data(self):
        """

        :return: {'emissions_per_dt': <float>,
                  'total_emissions': <float>}
        """

        emissions_per_dt = dict()
        total_emissions = dict()

        for f_num, feedstock in enumerate(self.f_list):
            pol_dict_dt = dict()
            pol_dict_tot = dict()
            for p_num, pollutant in enumerate(self.pol_list):
                logger.info('Collecting data for pollutant: %s, feedstock: %s' % (pollutant, feedstock,))
                pol_dict_dt[pollutant] = self.collect_data_per_prod(p_num=p_num, f_num=f_num)
                pol_dict_tot[pollutant] = self.collect_data_total_emissions(p_num=p_num, f_num=f_num)

            emissions_per_dt[feedstock] = pol_dict_dt
            total_emissions[feedstock] = pol_dict_tot

        results = {'emissions_per_dt': emissions_per_dt,
                   'total_emissions': total_emissions}

        return results

    def plot_emissions_per_gal(self, emissions_per_dt_dict):
        """

        :param emissions_per_dt_dict:
        :return:
        """

        logger.info('Plotting emissions per gal')
        fig, axarr = plt.subplots(3, 3, figsize=(8.5, 7))
        matplotlib.rcParams.update({'font.size': 13})

        for p_num, pollutant in enumerate(self.pol_list):
            logger.info('Plotting emissions per gal for pollutant %s' % (pollutant,))
            plotvals = list()
            for f_num, feedstock in enumerate(self.f_list):
                total_emissions = emissions_per_dt_dict[feedstock][pollutant]

                emissions_per_gal = list(x[0] * (1e6 / self.etoh_vals[f_num]) for x in total_emissions)
                plotvals.append(emissions_per_gal)

            row = self.row_list[p_num]
            col = self.col_list[p_num]
            ax1 = axarr[row, col]
            ax1.set_yscale('log')
            ax1.set_ylim(bottom=1e-4, top=1e3)
            formatter = ticker.ScalarFormatter(useMathText=True)
            formatter.set_scientific(True)
            formatter.set_powerlimits((-4, 3))

            # ax1.set_title(self.pol_list_label[p_num])
            ax1.text(len(self.feedstock_list) + 0.3, 4e2, self.pol_list_label[p_num], fontsize=13, ha='right', va='top', weight='heavy')
            # ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter("%s"))  # enable for non-scientific formatting

            bp = ax1.boxplot(plotvals, notch=0, sym='', vert=1, whis=1000)
            ax1.set_xlim(0.5, len(self.feedstock_list) + 0.5)

            plt.setp(bp['boxes'], color='black')
            plt.setp(bp['whiskers'], color='black', linestyle='-')
            plt.setp(bp['medians'], color='black')

            self.__plot_interval__(plotvals, ax1)
            ax1.set_xticklabels(self.f_list, rotation='horizontal')

        # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
        plt.setp([a.get_xticklabels() for a in axarr[0, :]], visible=False)
        plt.setp([a.get_xticklabels() for a in axarr[1, :]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)
        # plt.setp([a.get_yticklabels() for a in axarr[:, 2]], visible=False)

        axarr[0, 0].set_ylabel('Emissions \n (g/gal EtOH)', color='black', fontsize=13)
        axarr[1, 0].set_ylabel('Emissions \n (g/gal EtOH)', color='black', fontsize=13)
        axarr[2, 0].set_ylabel('Emissions \n (g/gal EtOH)', color='black', fontsize=13)

        fig.tight_layout()

        if config.as_bool('show_figures') is True:
            plt.show()

        data = [emissions_per_gal, ]

        return data

    def plot_emissions_per_dt(self, emissions_per_dt_dict):

        logger.info('Plotting emissions per dt')

        fig, axarr = plt.subplots(3, 3, figsize=(8.5, 7))
        matplotlib.rcParams.update({'font.size': 13})

        for p_num, pollutant in enumerate(self.pol_list):
            logger.info('Plotting emissions per dt for pollutant %s' % (pollutant,))
            plotvals = list()
            for f_num, feedstock in enumerate(self.f_list):
                emissions_per_dt = emissions_per_dt_dict[feedstock][pollutant]

                g_per_dt = list(x[0] * 1e3 for x in emissions_per_dt)
                plotvals.append(g_per_dt)

            row = self.row_list[p_num]
            col = self.col_list[p_num]
            ax1 = axarr[row, col]
            ax1.set_yscale('log')
            ax1.set_ylim(bottom=1e-6, top=1e3)
            formatter = ticker.ScalarFormatter(useMathText=True)
            formatter.set_scientific(True)
            formatter.set_powerlimits((-6, 3))

            for label in ax1.get_yticklabels()[::2]:
                label.set_visible(False)

            ax1.text(len(self.feedstock_list) + 0.3, 4e2, self.pol_list_label[p_num], fontsize=13, ha='right', va='top', weight='heavy')
            # ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter("%s"))  # enable for non-scientific formatting
            bp = ax1.boxplot(plotvals, notch=0, sym='', vert=1, whis=1000)
            ax1.set_xlim(0.5, len(self.feedstock_list) + 0.5)

            plt.setp(bp['boxes'], color='black')
            plt.setp(bp['whiskers'], color='black', linestyle='-')
            plt.setp(bp['medians'], color='black')

            self.__plot_interval__(plotvals, ax1)
            ax1.set_xticklabels(self.f_list, rotation='horizontal')

        # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
        plt.setp([axarr[0, 0].get_xticklabels()], visible=False)
        plt.setp([axarr[0, 1].get_xticklabels()], visible=False)
        plt.setp([a.get_xticklabels() for a in axarr[1, :]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 2]], visible=False)

        axarr[0, 0].set_ylabel('Emissions \n (kg/dt)', color='black', fontsize=13)
        axarr[1, 0].set_ylabel('Emissions \n (kg/dt)', color='black', fontsize=13)
        axarr[2, 0].set_ylabel('Emissions \n (kg/dt)', color='black', fontsize=13)

        fig.tight_layout()

        if config.as_bool('show_figures') is True:
            plt.show()

        data = [emissions_per_dt, ]

        return data

    def __plot_interval__(self, data_array, ax):

        num_feed = len(self.feedstock_list)
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

        kvals = {'feedstock': self.f_list[f_num].lower(),
                 'pollutant': self.pol_list[p_num],
                 'scenario_name': config.get('title'),
                 'te_table': 'total_emissions_join_prod'  # @TODO: this is manually defined several places; consolidate
                 }

        query_emissions_per_prod = """SELECT   SUM({pollutant} / (prod)) AS mt_{pollutant}_perdt
                                      FROM     {scenario_name}.{te_table}
                                      WHERE    prod                   > 0.0
                                        AND    feedstock              = '{feedstock}'
                                        AND    source_category NOT LIKE '%transport%'
                                        AND    source_category NOT LIKE '%processing%'
                                      GROUP BY fips
                                      ORDER BY fips
                                      ;""".format(**kvals)
        output = self.db.output(query_emissions_per_prod)

        emissions_per_production = list()
        if output is not None:
            emissions_per_production = output[0]

        return emissions_per_production

    def collect_data_total_emissions(self, p_num, f_num):
        """
        Collect data for one pollutant/feedstock combination
        Return the total emissions

        :param f_num: feedstock number
        :param p_num: pollutant number
        :return emissions_per_pollutant: emissions in (pollutant dt) / (total feedstock harvested dt)
        """

        kvals = {'feedstock': self.f_list[f_num].lower(),
                 'pollutant': self.pol_list[p_num],
                 'scenario_name': config.get('title'),
                 'te_table': 'total_emissions_join_prod'  # @TODO: defined multiple places
                 }

        query_emissions = """SELECT   SUM({pollutant}) AS {pollutant}
                             FROM     {scenario_name}.{te_table}
                             WHERE    prod > 0.0
                               AND    feedstock = '{feedstock}'
                               AND    source_category NOT LIKE '%transport%'
                               AND    source_category NOT LIKE '%processing%'
                             GROUP BY fips
                             ORDER BY fips
                             ;""".format(**kvals)

        output = self.db.output(query_emissions)

        emissions = list()
        if output is not None:
            emissions = output[0]

        return emissions

    def contribution_figure(self):
        kvals = {'scenario_name': config.get('title'),
                 'te_table': 'total_emissions_join_prod_sum_emissions'}

        condition_list = {'Non-Harvest': """(source_category = \'Irrigation\' OR source_category = \'Non-Harvest\' OR source_category = \'Non-Harvest - fug dust\')""",
                          'Harvest': """(source_category = \'Harvest\' OR source_category = \'Harvest - fug dust\' OR source_category = \'Loading\')""",
                          'Chemical': """(source_category = \'Chemical\' OR source_category = \'Fertilizer\')"""}
        emissions_per_activity = dict()
        for f_num, feedstock in enumerate(self.f_list):
            pol_dict = dict()
            kvals['feed'] = feedstock.lower()
            for p_num, pollutant in enumerate(self.pol_list):
                kvals['pollutant'] = pollutant
                logger.info('Collecting data for emissions contribution figure for feedstock %s, pollutant %s' % (feedstock, pollutant,))
                act_dict = dict()
                for act_num, activity in enumerate(self.act_list):
                    kvals['cond'] = condition_list[activity]

                    query = """ SELECT   SUM({pollutant} / total_{pollutant})
                                FROM     {scenario_name}.{te_table}
                                WHERE    {cond}
                                  AND    feedstock         = '{feed}'
                                  AND    total_{pollutant} > 0
                                  AND    prod              > 0
                                GROUP BY fips
                                """.format(**kvals)

                    output = self.db.output(query)
                    act_dict[activity] = list()
                    if output is not None:
                        act_dict[activity] = output[0]
                    if feedstock == 'FR' and activity == 'Non-Harvest':
                        act_dict[activity] = ((0, ), )

                pol_dict[pollutant] = act_dict
            emissions_per_activity[feedstock] = pol_dict

        fig, axarr = plt.subplots(3, 7, figsize=(12, 5.5))

        matplotlib.rcParams.update({'font.size': 13})

        for i, pollutant in enumerate(self.pol_list):
            logger.info('Plotting data for emissions contribution figure for pollutant %s' % (pollutant, ))
            for j, activity in enumerate(self.act_list):
                for f_num, feedstock in enumerate(self.f_list):
                    emissions = emissions_per_activity[feedstock][pollutant][activity]

                    if not emissions:
                        logger.warning('No data found for %s, %s, %s' % (pollutant, activity, feedstock))
                        break
                    else:
                        logger.info('Plotting data for %s, %s, %s' % (pollutant, activity, feedstock))

                    # mean_val = mean(emissions)
                    med_val = median(emissions)
                    max_val = max(emissions)[0]
                    min_val = min(emissions)[0]

                    col = j
                    row = i
                    ax1 = axarr[col, row]
                    ax1.set_ylim(bottom=-0.05, top=1.05)

                    if col == 0:
                        ax1.set_title(self.pol_list_label[i])

                    if row == 0:
                        axarr[col, row].set_ylabel(activity)

                    # ax1.plot([f_num + 1], mean_val, color=self.f_color[f_num], marker='_', markersize=20)
                    ax1.plot([f_num + 1], med_val, color=self.f_color[f_num], marker='_', markersize=12, markeredgewidth=2)

                    # Plot the max/min values
                    ax1.plot([f_num + 1] * 2, [max_val, min_val], color=self.f_color[f_num], marker=self.f_marker[f_num], markersize=7, linewidth=2, markeredgewidth=0.0)

                    # Set axis limits
                    ax1.set_xlim([0, 8])

                    ax1.set_xticklabels(([''] + self.f_list), rotation='vertical')

        # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
        plt.setp([a.get_xticklabels() for a in axarr[0, :]], visible=False)
        plt.setp([a.get_xticklabels() for a in axarr[1, :]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 2]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 3]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 4]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 5]], visible=False)
        plt.setp([a.get_yticklabels() for a in axarr[:, 6]], visible=False)

        fig.tight_layout()

        if config.as_bool('show_figures') is True:
            plt.show()


if __name__ == '__main__':
    # get scenario title
    title = config.get('title')
    logger.debug('Saving figure data in: %s' % (title, ))

    # create database
    db = Database(model_run_title=title)

    FigPlot16 = FigurePlottingBT16(db=db)
    FigPlot16.compile_results()
    results = FigPlot16.get_data()
    FigPlot16.plot_emissions_per_gal(emissions_per_dt_dict=results['emissions_per_dt'])
    FigPlot16.plot_emissions_per_dt(emissions_per_dt_dict=results['emissions_per_dt'])
    FigPlot16.contribution_figure()
