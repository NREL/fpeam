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


class FigurePlottingBT16:
    def __init__(self, db):
        """

        :param db: model.Database instance
        :return:
        """

        # init properties
        self.db = db

        self.f_color = ['r', 'b', 'g', 'k', 'c']  # @TODO: remove hardcoded values
        self.f_marker = ['o', 'o', 'o', 'o', 'o']  # @TODO: remove hardcoded values
        self.row_list = [0, 0, 1, 1, 2, 2]  # @TODO: remove hardcoded values
        self.col_list = [0, 1, 0, 1, 0, 1]  # @TODO: remove hardcoded values
        self.pol_list_label = ['$NO_x$', '$VOC$', '$PM_{2.5}$', '$CO$', '$PM_{10}$', '$SO_x$']  # @TODO: remove hardcoded values

        self.pol_list = ['nox', 'voc', 'pm25', 'co', 'pm10', 'sox']  # @TODO: remove hardcoded values

        self.feedstock_list = ['Corn Grain', 'Switchgrass', 'Corn Stover', 'Wheat Straw', 'Miscanthus', ]  # 'Forest Residue'] @TODO: remove hardcoded values
        self.f_list = ['CG', 'SG', 'CS', 'WS', 'MS', ]  # 'FR'] # @TODO: remove hardcoded values
        self.act_list = ['Non-Harvest', 'Chemical', 'Harvest']  # @TODO: remove hardcoded values

        self.etoh_vals = [2.76 / 0.02756, 89.6, 89.6, 89.6, 89.6, ]  # 75.7]  # gallons per dry short ton  # @TODO: remove hardcoded values (convert to dt from bushels / 0.02756)

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
                 'te_table': 'total_emissions'
                 }

        # create backup
        self.db.backup_table(schema=kvals['scenario_name'], table=kvals['te_table'])

        query_drop_table = """DROP TABLE IF EXISTS {scenario_name}.{te_table};""".format(**kvals)

        query_create_table = """CREATE TABLE {scenario_name}.{te_table} (fips            char(5),
                                                                         year            char(4),
                                                                         yield           char(2),
                                                                         tillage         varchar(255),
                                                                         nox             float,
                                                                         nh3             float,
                                                                         voc             float,
                                                                         pm10            float,
                                                                         pm25            float,
                                                                         sox             float,
                                                                         co              float,
                                                                         source_category varchar(255),
                                                                         nei_category    char(2),
                                                                         feedstock       char(2))
                                ;""".format(**kvals)

        self.db.execute_sql(query_drop_table)
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

        logger.info('Joining total emissions with production data')
        self.join_with_production_data(kvals)

        logger.info('Adding summed emissions and production columns')
        self.sum_emissions(kvals)

        # logger.info('Adding NEI data (summed OR, NR, NP)')
        # self.add_nei_and_transport(kvals)

    def add_nei_and_transport(self, kvals):

        kvals['new_table'] = 'total_emissions_join_prod_sum_emissions_nei_trans'

        feed_type_dict = config.get('feed_type_dict')
        table_dict = config.get('transport_table_dict')
        logistics = config.get('logistics_type')

        # back up table
        self.db.backup_table(schema=kvals['scenario_name'], table=kvals['new_table'])

        # drop old table and create new table
        sql = "DROP   TABLE IF EXISTS {scenario_name}.{new_table};\n".format(**kvals)
        sql += "CREATE TABLE           {scenario_name}.{new_table} AS\n".format(**kvals)

        sql += """  SELECT * FROM {scenario_name}.total_emissions_join_prod_sum_emissions te
                    LEFT JOIN (SELECT fips, sum(nox) as nei_nox, sum(sox) as nei_sox, sum(pm10) as nei_pm10, sum(pm25) as nei_pm25, sum(voc) as nei_voc, sum(nh3) as nei_nh3, sum(co) as nei_co
                    FROM nei.nei_2011
                    WHERE category != 'BVOC' AND category != 'P'
                    GROUP BY fips) nei
                    ON nei.fips = te.fips""".format(**kvals)

        for feedstock in self.feed_id_dict:
            if self.feed_id_dict[feedstock] != 'None':
                feed_type = feed_type_dict[feedstock]
                kvals['transport_table'] = table_dict[feed_type][kvals['yield']][logistics]
                kvals['feed'] = feedstock.lower()
                sql += """ LEFT JOIN (SELECT fips, avg_total_cost, avg_dist
                                      FROM {production_schema}.{transport_table}_{year}) trans
                           ON trans.fips = te.fips AND te.feedstock = '{feed}' AND source_category LIKE '%transport%'""".format(**kvals)

        self.db.execute_sql(sql=sql)

    def sum_emissions(self, kvals):

        kvals['table'] = 'total_emissions_join_prod'
        kvals['new_table'] = 'total_emissions_join_prod_sum_emissions'

        i = 0
        for feed in self.f_list:
            kvals['feed'] = feed.lower()
            if i == 0:
                    # back up table
                    self.db.backup_table(schema=kvals['scenario_name'], table=kvals['new_table'])

                    # drop old table and create new table
                    sql = "DROP   TABLE IF EXISTS {scenario_name}.{new_table};\n"
                    sql += "CREATE TABLE           {scenario_name}.{new_table} AS\n"
            else:
                # insert data
                sql = "INSERT INTO {scenario_name}.{new_table}\n"

            if feed == 'CG':
                kvals['convert_bushel'] = 0.025
            else:
                kvals['convert_bushel'] = 1

            sql += """ SELECT  tot.*,
                                sum.total_nox,
                                sum.total_nh3,
                                sum.total_voc,
                                sum.total_pm10,
                                sum.total_pm25,
                                sum.total_sox,
                                sum.total_co,
                                dat.total_prod * {convert_bushel} AS total_prod,
                                dat.total_harv_ac
                        FROM {scenario_name}.{table} tot
                        LEFT JOIN  (SELECT
                                        fips,
                                        feedstock,
                                        year,
                                        yield,
                                        sum(nox) as total_nox,
                                        sum(nh3) AS total_nh3,
                                        sum(voc) as total_voc,
                                        sum(pm10) as total_pm10,
                                        sum(pm25) as total_pm25,
                                        sum(sox) as total_sox,
                                        sum(co) as total_co
                                    FROM {scenario_name}.{table}
                                    WHERE feedstock = '{feed}' AND source_category NOT LIKE '%transport%' AND source_category NOT LIKE '%process%'
                                    GROUP BY fips, feedstock, year, yield) sum
                        ON tot.fips = sum.fips AND tot.feedstock = sum.feedstock AND tot.year = sum.year AND tot.yield = sum.yield
                        LEFT JOIN  (SELECT fips, total_prod, total_harv_ac
                                    FROM {production_schema}.{feed}_data) dat
                        ON tot.fips = dat.fips AND tot.feedstock = '{feed}'
                        WHERE tot.feedstock = '{feed}'""".format(**kvals)
            sql = sql.format(**kvals)
            self.db.execute_sql(sql=sql)

            i += 1

    def join_with_production_data(self, kvals):
        """

        :param kvals: dictionary for string formatting
        :return:
        """
        # # initialize kvals dict for string formatting
        # kvals = {'scenario_name': self.db.schema,
        #          'year': config.get('year_dict')['all_crops'],
        #          'yield': config.get('yield'),
        #          'production_schema': config.get('production_schema'),
        #          'te_table': 'total_emissions'
        #          }

        till_dict = {'CT': 'convtill',
                     'RT': 'reducedtill',
                     'NT': 'notill'}

        kvals['table'] = 'total_emissions_join_prod'

        i = 0
        for feed in self.f_list:
            kvals['feed'] = feed.lower()
            for till in till_dict:
                kvals['till'] = till
                kvals['tillage'] = till_dict[till]
                logger.info('Joining production data for %s %s' % (feed, till))
                if i == 0:
                    # back up table
                    self.db.backup_table(schema=kvals['scenario_name'], table=kvals['table'])

                    # drop old table and create new table
                    sql = "DROP   TABLE IF EXISTS {scenario_name}.{table};\n"
                    sql += "CREATE TABLE           {scenario_name}.{table} AS\n"
                else:
                    # insert data
                    sql = "INSERT INTO {scenario_name}.{table}\n"

                if feed == 'CG':
                    kvals['convert_bushel'] = 0.025
                else:
                    kvals['convert_bushel'] = 1

                # gather data
                sql += "SELECT      tot.*,\n"
                sql += "            cd.{tillage}_prod * {convert_bushel}    AS prod,\n"
                sql += "            cd.{tillage}_harv_ac AS harv_ac\n"
                sql += "FROM        {scenario_name}.{te_table} tot\n"
                sql += "LEFT JOIN   {production_schema}.{feed}_data cd\n"
                sql += "       ON   cd.fips = tot.fips\n"
                sql += "WHERE       tot.tillage   = '{till}' AND\n"
                sql += "            tot.feedstock = '{feed}' \n"
                sql += ";"
                sql = sql.format(**kvals)

                self.db.execute_sql(sql=sql)

                i += 1

    def _make_query(self, tillage, source_category, from_clause):
        """
        Create query to collect emission values.

        :param tillage: tillage type or SQL phrase to generate tillage type
        :param source_category: NEI categroy value
        :param from_clause: source clause
        :return: <string>
        """

        kvals = {}

        sql = "INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)" \
              "SELECT" \
              "    chem.fips    AS fips," \
              "    '{year}'     AS year," \
              "    '{yield}'    AS yield," \
              "    chem.tillage AS tillage," \
              "    0            AS nox," \
              "    0            AS nh3," \
              "    chem.voc     AS voc," \
              "    0            AS pm10," \
              "    0            AS pm25," \
              "    0            AS sox," \
              "    0            AS co," \
              "    'Chemical'   AS source_category," \
              "    'NP'         AS nei_category," \
              "    '{feed}'     AS feedstock" \
              "FROM (SELECT" \
              "          fips                   AS fips," \
              "          tillage                AS tillage" \
              "          SUM(voc) / {years_rot} AS voc," \
              "          FROM {scenario_name}.{feed}_chem" \
              "          GROUP BY fips, tillage" \
              "      ) chem" \
              ";".format(**kvals)

        raise NotImplementedError

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

        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms':
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2),1), 'T')"
        elif kvals['feed'] == 'sg':
            kvals['tillage'] = "'NT'"
        elif kvals['feed'] == 'ms':
            kvals['tillage'] = "'CT'"

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
                               GROUP BY fips
                               ;""".format(**kvals)

        self.db.input(query_non_harvest)

    def get_nh_fd(self, kvals):
        """
        Add non-harvest fugitive dust emissions to total emissions table.

        :param kvals: dictionary for string formatting
        :return:
        """

        kvals['source_category'] = 'Non-Harvest - fug dust'

        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms':
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2),1), 'T')"
        elif kvals['feed'] == 'sg':
            kvals['tillage'] = "'NT'"
        elif kvals['feed'] == 'ms':
            kvals['tillage'] = "'CT'"

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
                              GROUP BY fips, {tillage}
                              ;""".format(**kvals)

        self.db.input(query_non_harvest)

    def get_irrig(self, kvals):
        """
        Add chemical emissions to total emissions table.

        :param kvals: dictionary for string formatting
        :return:
        """

        if kvals['feed'] == 'cg':
            # possible tillage types
            tillages = ('CT', 'RT', 'NT')

            # set reduction factor
            kvals['red_fact'] = 1.0 / len(tillages)

            for tillage in tillages:
                kvals['tillage'] = tillage
                query_non_harvest = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                                       SELECT fips,
                                              '{year}'                                                   AS year,
                                              '{yield}'                                                  AS yield,
                                              '{tillage}'                                                AS tillage,
                                              SUM(nox)                        / {years_rot} * {red_fact} AS nox,
                                              SUM(nh3)                        / {years_rot} * {red_fact} AS nh3,
                                              SUM(voc)                        / {years_rot} * {red_fact} AS voc,
                                              SUM(pm10 + IFNULL(fug_pm10, 0)) / {years_rot} * {red_fact} AS pm10,
                                              SUM(pm25 + IFNULL(fug_pm25, 0)) / {years_rot} * {red_fact} AS pm25,
                                              SUM(sox)                        / {years_rot} * {red_fact} AS sox,
                                              SUM(co)                         / {years_rot} * {red_fact} AS co,
                                              'Irrigation'                                               AS source_category,
                                              'NR'                                                       AS nei_category,
                                              '{feed}'                                                   AS cg
                                       FROM {scenario_name}.{feed}_raw
                                       WHERE description     LIKE '%Non-Harvest%'
                                         AND description NOT LIKE '%dust%'
                                         AND LEFT(RIGHT(run_code, 2), 1) = 'I'
                                       GROUP BY fips
                                       ;""".format(**kvals)

                self.db.input(query_non_harvest)

    def get_harvest(self, kvals):
        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms':
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2),1), 'T')"
        elif kvals['feed'] == 'sg':
            kvals['tillage'] = "'NT'"
        elif kvals['feed'] == 'ms':
            kvals['tillage'] = "'CT'"

        query_harvest = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                           SELECT fips,
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
                           FROM {scenario_name}.{feed}_raw
                           WHERE description     LIKE '% Harvest%'
                             AND description NOT LIKE '%dust%'
                             AND LEFT(RIGHT(run_code, 2), 1) != 'I'
                           GROUP BY fips, {tillage}
                           ;""".format(**kvals)

        self.db.input(query_harvest)

    def get_h_fd(self, kvals):
        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms':
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2),1), 'T')"
        elif kvals['feed'] == 'sg':
            kvals['tillage'] = "'NT'"
        elif kvals['feed'] == 'ms':
            kvals['tillage'] = "'CT'"

        query_harvest = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                           SELECT fips,
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
                           FROM {scenario_name}.{feed}_raw
                           WHERE description LIKE '% Harvest%'
                             AND description LIKE '%dust%'
                             AND LEFT(RIGHT(run_code, 2), 1) != 'I'
                           GROUP BY fips, {tillage}
                           ;""".format(**kvals)

        self.db.input(query_harvest)

    def get_loading(self, kvals):
        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms':
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2),1), 'T')"
        elif kvals['feed'] == 'sg':
            kvals['tillage'] = "'NT'"
        elif kvals['feed'] == 'ms':
            kvals['tillage'] = "'CT'"

        query_loading = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                           SELECT fips,
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
                        FROM      {scenario_name}.{feed}_raw
                        WHERE     description LIKE '%Loading%' AND
                                  LEFT(RIGHT(run_code, 2), 1) != 'I'
                        GROUP BY  fips, {tillage}
                        ;""".format(**kvals)

        self.db.input(query_loading)

    def get_logistics(self, kvals):
        system_list = ['A', 'C']
        pol_list = ['sox', 'nox', 'pm10', 'pm25', 'voc', 'co', 'nh3']
        logistics = {'A': 'Advanced', 'C': 'Conventional'}
        feedstock = kvals['feed']

        if kvals['feed'] != 'sg' and kvals['feed'] != 'ms':
            tillage_list = ['NT', 'RT', 'CT']
        elif kvals['feed'] == 'sg':
            tillage_list = ['NT', ]
        elif kvals['feed'] == 'ms':
            tillage_list = ['CT', ]

        run_logistics = self.feed_id_dict[feedstock.upper()]
        if run_logistics != 'None':
            for system in system_list:
                kvals['system'] = system
                for tillage in tillage_list:
                    kvals['tillage'] = tillage
                    query = str()
                    kvals['reduction_factor'] = len(tillage_list)
                    for i, pollutant in enumerate(pol_list):
                        if pollutant == 'sox':
                            kvals['pollutant'] = 'so2'
                        else:
                            kvals['pollutant'] = pollutant
                        kvals['pollutant_name'] = pollutant
                        kvals['transport_cat'] = 'Transport, %s' % (logistics[system],)
                        kvals['preprocess_cat'] = 'Pre-processing, %s' % (logistics[system],)

                        logger.info('Inserting data {transport_cat}, pollutant: {pollutant}'.format(**kvals))
                        if i == 0:
                            query += """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                                        SELECT      feed_sox.fips, '{year}', '{yield}', '{tillage}', feed_nox.nox, feed_nh3.nh3, feed_voc.voc,
                                                    (feed_pm10.pm10_trans+ feed_pm10fd.pm10_fug) AS 'pm10', (feed_pm25.pm25_trans + feed_pm25fd.pm25_fug) AS 'pm25', feed_sox.sox,
                                                    feed_co.co,  '{transport_cat}', 'OR' as nei_category, '{feed}'
                                        FROM       (SELECT trans.fips as 'fips', trans.total_emissions/{reduction_factor} AS 'sox'
                                                    FROM {scenario_name}.transportation  trans
                                                    WHERE 		trans.feedstock  = '{feed}' AND
                                                                trans.pollutantID    = '{pollutant}'     AND
                                                                trans.logistics_type = '{system}' AND
                                                                trans.yield_type = '{yield}' AND
                                                                trans.yearID = '{year}') feed_sox
                                    """.format(**kvals)
                        else:
                            if not pollutant.startswith('pm'):
                                query += """LEFT JOIN (SELECT trans.total_emissions/{reduction_factor} AS '{pollutant}', trans.fips as 'fips'
                                            FROM {scenario_name}.transportation  trans
                                            WHERE 		trans.feedstock  = '{feed}' AND
                                                        trans.pollutantID    = '{pollutant}'     AND
                                                        trans.logistics_type = '{system}' AND
                                                        trans.yield_type = '{yield}' AND
                                                        trans.yearID = '{year}') feed_{pollutant}
                                            ON feed_{pollutant}.fips = feed_sox.fips
                                        """.format(**kvals)
                            elif pollutant.startswith('pm'):
                                query += """LEFT JOIN (SELECT trans.total_emissions/{reduction_factor} AS '{pollutant}_trans', trans.fips as 'fips'
                                            FROM {scenario_name}.transportation  trans
                                            WHERE 		trans.feedstock  = '{feed}' AND
                                                        trans.pollutantID    = '{pollutant}'     AND
                                                        trans.logistics_type = '{system}' AND
                                                        trans.yield_type = '{yield}' AND
                                                        trans.yearID = '{year}') feed_{pollutant}
                                                        ON feed_{pollutant}.fips = feed_sox.fips
                                            LEFT JOIN (SELECT fd.total_fd_emissions/{reduction_factor} AS '{pollutant}_fug', fd.fips as 'fips'
                                            FROM {scenario_name}.fugitive_dust fd
                                            WHERE 		fd.feedstock  = '{feed}' AND
                                                        fd.pollutantID    = 'pm25'     AND
                                                        fd.logistics_type = '{system}' AND
                                                        fd.yield_type = 'bc' AND
                                                        fd.yearID = '{year}') feed_{pollutant}fd
                                            ON feed_{pollutant}fd.fips = feed_sox.fips
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

        logger.info('Plotting emissions per gal')
        fig, axarr = plt.subplots(3, 2, figsize=(9, 9.5))
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
            ax1.set_ylim(bottom=1e-3, top=1e2)

            #ax1.set_title(self.pol_list_label[p_num])
            ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter("%s"))

            bp = ax1.boxplot(plotvals, notch=0, sym='', vert=1, whis=1000)
            ax1.set_xlim(0.5, 5.5)

            plt.setp(bp['boxes'], color='black')
            plt.setp(bp['whiskers'], color='black', linestyle='-')
            plt.setp(bp['medians'], color='black')
            # self.ax1.yaxis.set_major_formatter(FixedFormatter([0.00001, 0.0001, 0.001]))#for below y-axis

            self.__plot_interval__(plotvals, ax1)
            ax1.set_xticklabels(self.f_list, rotation='horizontal')

        # # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
        # plt.setp([a.get_xticklabels() for a in axarr[0, :]], visible=False)
        # plt.setp([a.get_xticklabels() for a in axarr[1, :]], visible=False)
        # plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)
        # # plt.setp([a.get_yticklabels() for a in axarr[:, 2]], visible=False)

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
            logger.info('Plotting emissions per dt for pollutant %s' % (pollutant,))
            plotvals = list()
            for f_num, feedstock in enumerate(self.f_list):
                emissions_per_dt = emissions_per_dt_dict[feedstock][pollutant]

                g_per_dt = list(x[0] * 1e6 for x in emissions_per_dt)
                plotvals.append(g_per_dt)

            row = self.row_list[p_num]
            col = self.col_list[p_num]
            ax1 = axarr[row, col]
            ax1.set_yscale('log')
            ax1.set_ylim(bottom=1e-3, top=1e4)

            #ax1.set_title(self.pol_list_label[p_num])
            ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter("%s"))
            bp = ax1.boxplot(plotvals, notch=0, sym='', vert=1, whis=1000)
            ax1.set_xlim(0.5, 5.5)

            plt.setp(bp['boxes'], color='black')
            plt.setp(bp['whiskers'], color='black', linestyle='-')
            plt.setp(bp['medians'], color='black')
            # self.ax1.yaxis.set_major_formatter(FixedFormatter([0.00001, 0.0001, 0.001]))#for below y-axis

            self.__plot_interval__(plotvals, ax1)
            ax1.set_xticklabels(self.f_list, rotation='horizontal')

        # # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
        # plt.setp([a.get_xticklabels() for a in axarr[0, :]], visible=False)
        # plt.setp([a.get_xticklabels() for a in axarr[1, :]], visible=False)
        # plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)
        # # plt.setp([a.get_yticklabels() for a in axarr[:, 2]], visible=False)

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

        kvals = {'feedstock': self.f_list[f_num].lower(),
                 'pollutant': self.pol_list[p_num],
                 'scenario_name': config.get('title'),
                 'te_table': 'total_emissions_join_prod'  # @TODO: this is manually defined several places; consolidate
                 }

        query_emissions_per_prod = """SELECT    sum({pollutant})/(prod) AS mt_{pollutant}_perdt
                                      FROM      {scenario_name}.{te_table}
                                      WHERE     prod > 0.0 AND {pollutant} > 0 AND feedstock = '{feedstock}'
                                      GROUP BY  fips
                                      ORDER BY  fips
                                      ;""".format(**kvals)
        emissions_per_production = self.db.output(query_emissions_per_prod)[0]

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

        query_emissions = """SELECT    sum({pollutant}) AS {pollutant}
                             FROM      {scenario_name}.{te_table}
                             WHERE     prod > 0.0 AND {pollutant} > 0 AND feedstock = '{feedstock}'
                             GROUP BY  fips
                             ORDER BY  fips
                             ;""".format(**kvals)

        emissions = self.db.output(query_emissions)[0]

        return emissions

    def contribution_figure(self):
        kvals = {'scenario_name': config.get('title'),}

        emissions_per_activity = dict()
        for f_num, feedstock in enumerate(self.f_list):
            pol_dict = dict()
            kvals['feed'] = feedstock.lower()
            for p_num, pollutant in enumerate(self.pol_list):
                kvals['pollutant'] = pollutant
                logger.info('Collecting data for emissions contribution figure for feedstock %s, pollutant %s' % (
                feedstock, pollutant,))
                act_dict = dict()
                for act_num, activity in enumerate(self.act_list):
                    kvals['act'] = activity
                    if activity != 'Harvest':
                        query = """ SELECT    selected.{pollutant}/total.sum_pol
                                    FROM      {scenario_name}.{te_table} selected
                                    LEFT JOIN (SELECT fips,
                                                      SUM({pollutant}) AS sum_pol
                                                      FROM {scenario_name}.{te_table} tot
                                                      WHERE feedstock = '{feed}'
                                                      GROUP by tot.fips) total
                                           ON total.fips = selected.fips
                                    WHERE     source_category LIKE '%{act}%' AND
                                              feedstock          = '{feed}'  AND
                                              total.sum_pol      > 0
                                    GROUP BY  selected.fips
                                    """.format(**kvals)
                    else:
                        query = """SELECT    selected.{pollutant}/total.sum_pol
                                   FROM      {scenario_name}.{te_table} selected
                                   LEFT JOIN (SELECT   fips,
                                                       SUM({pollutant}) AS sum_pol
                                              FROM     {scenario_name}.{te_table} tot
                                              WHERE    feedstock = '{feed}'
                                              GROUP by tot.fips) total
                                          ON total.fips = selected.fips
                                   WHERE         source_category LIKE '%{act}%'       AND
                                             NOT source_category LIKE '%Non-Harvest%' AND
                                             feedstockpol           = '{feed}'
                                             AND total.sum_pol      > 0
                                   GROUP BY selected.fips
                                   ;""".format(**kvals)
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


if __name__ == '__main__':
    # get scenario title
    title = 'b2nat'  # config.get('title')
    logger.debug('Saving figure data in: %s' % (title,))

    # create database
    db = Database(model_run_title=title)

    FigPlot16 = FigurePlottingBT16(db=db)
    FigPlot16.compile_results()
    results = FigPlot16.get_data()
    FigPlot16.plot_emissions_per_gal(emissions_per_dt_dict=results['emissions_per_dt'])
    FigPlot16.plot_emissions_per_dt(emissions_per_dt_dict=results['emissions_per_dt'])
    FigPlot16.contribution_figure()
