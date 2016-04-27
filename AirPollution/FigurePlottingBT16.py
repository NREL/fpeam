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
        self.pol_list_label = ['$NO_x$', '$voc$', '$PM_{2.5}$', '$PM_{10}$', '$CO$', '$SO_x$']  # @TODO: remove hardcoded values

        self.pol_list = ['nox', 'voc', 'pm25', 'co', 'pm10', 'sox']  # @TODO: remove hardcoded values

        self.feedstock_list = ['Corn Grain', 'Switchgrass', 'Corn Stover', 'Wheat Straw']  # 'Miscanthus', ]  # 'Forest Residue'] @TODO: remove hardcoded values
        self.f_list = ['CG', 'SG', 'CS', 'WS', ]  # 'MS', ]  # 'FR'] # @TODO: remove hardcoded values
        self.act_list = ['Non-Harvest', 'Chemical', 'Harvest']  # @TODO: remove hardcoded values

        self.etoh_vals = [2.76 / 0.02756, 89.6, 89.6, 89.6, 89.6, ]  # 75.7]  # gallons per dry short ton  # @TODO: remove hardcoded values

        self.feed_id_dict = config.get('feed_id_dict')

    def compile_results(self):
        """

        :return:
        """

        # initialize kvals dict for string formatting
        kvals = {'scenario_name': db.schema,
                 'year': config.get('year_dict')['all_crops'],
                 'yield': config.get('yield'),
                 'production_schema': config.get('production_schema'),
                 'te_table': 'total_emissions'
                 }

        # create backup
        self.db.backup_table(schema=kvals['scenario_name'], table=kvals['te_table'])

        query_create_table = """DROP TABLE IF EXISTS {scenario_name}.{te_table};
                                CREATE TABLE {scenario_name}.{te_table} (fips            char(5),
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

        self.db.execute_sql(query_create_table)

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
        """

        :param kvals: dictionary for string formatting
        :return:
        """

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
                if i == 0:
                    # back up table
                    self.db.backup_table(schema=kvals['scenario_name'], table=kvals['table'])

                    # drop old table and create new table
                    sql = "DROP   TABLE IF EXISTS {scenario_name}.{table};\n"
                    sql += "CREATE TABLE           {scenario_name}.{table} AS\n"
                else:
                    # insert data
                    sql = "INSERT INTO {scenario_name}.{table}\n"

                # gather data
                sql += "SELECT      tot.*,\n"
                sql += "            cd.{tillage}_prod    AS prod,\n"
                sql += "            cd.{tillage}_harv_ac AS harv_ac\n"
                sql += "FROM        {scenario_name}.{te_table} tot\n"
                sql += "LEFT JOIN   {production_schema}.{feed}_data cd\n"
                sql += "       ON   cd.fips = tot.fips\n"
                sql += "WHERE       tot.tillage   = %(till)s AND\n"
                sql += "            tot.feedstock = %(feed)s\n"
                sql += ";".format(**kvals)

                self.db.execute_sql(sql=sql, vals=kvals)

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
                                       SUM(voc) / {years_rot} AS voc,
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
                                       SUM(nox) / {years_rot} AS nox,
                                       SUM(nh3) / {years_rot} AS nh3,
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

        if kvals['feed'] != 'sg':
            kvals['tillage'] = "coNCAT(LEFT(RIGHT(run_code, 2), 1), 'T')"
        else:
            kvals['tillage'] = 'NT'

        query_non_harvest = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, tillage, nox, nh3, voc, pm10, pm25, sox, co, source_category, nei_category, feedstock)
                               SELECT fips                                          AS fips,
                                      '{year}'                                      AS year,
                                      '{yield}'                                     AS yield,
                                      '{tillage}'                                   AS tillage,
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
        Add non-harvest fugiitive dust emissions to total emissions table.

        :param kvals: dictionary for string formatting
        :return:
        """

        kvals['source_category'] = 'Non-Harvest - fug dust'

        if kvals['feed'] != 'sg':
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2), 1), 'T')"
        else:
            kvals['tillage'] = 'NT'

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
                                       '{source_category}                            AS source_category,
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
        if kvals['feed'] != 'sg':
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2),1), 'T')"
        else:
            kvals['tillage'] = 'NT'

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
        if kvals['feed'] != 'sg':
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2),1), 'T')"

        else:
            kvals['tillage'] = 'NT'

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
        if kvals['feed'] != 'sg':
            kvals['tillage'] = "CONCAT(LEFT(RIGHT(run_code, 2),1), 'T')"
        else:
            kvals['tillage'] = 'NT'

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
                        WHERE     description                  = 'Loading' AND
                                  LEFT(RIGHT(run_code, 2), 1) != 'I')
                        GROUP BY  fips, {tillage}
                        ;""".format(**kvals)

        self.db.input(query_loading)

    def get_logistics(self, kvals):
        system_list = ['A', 'C']
        pol_list = ['nox', 'pm10', 'pm25', 'sox', 'voc', 'co', 'nh3']
        logistics = {'A': 'Advanced', 'C': 'Conventional'}
        feedstock = kvals['feed']

        run_logistics = self.feed_id_dict[feedstock.upper()]
        if run_logistics != 'None':
            for system in system_list:
                kvals['system'] = system
                for i, pollutant in enumerate(pol_list):
                    if pollutant == 'sox':
                        kvals['pollutant'] = 'SO2'
                    else:
                        kvals['pollutant'] = pollutant
                    kvals['pollutant_name'] = pollutant
                    kvals['transport_cat'] = 'Transport, %s' % (logistics[system],)
                    kvals['preprocess_cat'] = 'Pre-processing, %s' % (logistics[system],)

                    logger.debug('Inserting data {transport_cat}, pollutant: {pollutant}'.format(**kvals))
                    if i == 0:
                        query_transport = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, {pollutant}, source_category, nei_category, feedstock)
                                             SELECT   fips,
                                                      '{year}'                      AS year,
                                                      '{yield}'                     AS yield,
                                                      total_emissions / {years_rot} AS {pollutant_name},
                                                      '{transport_cat}'             AS source_category,
                                                      'OR'                          AS nei_category,
                                                      '{feed}'                      AS feedstock
                                             FROM     {scenario_name}.transportation
                                             WHERE    logistics_type = '{system}' AND
                                                      yield_type     = '{yield}'  AND
                                                      feedstock      = '{feed}'   AND
                                                      pollutantID    = '{pollutant_name}'
                                             GROUP BY fips
                                             :""".format(**kvals)

                        self.db.input(query_transport)

                        if pollutant == 'voc':
                            query_pre_process = """INSERT INTO {scenario_name}.{te_table} (fips, year, yield, {pollutant}, source_category, nei_category, feedstock)
                                                   SELECT   fips,
                                                            '{year}'                          AS year,
                                                            '{yield}'                         AS yield,
                                                            IFNULL(voc_wood, 0) / {years_rot} AS {pollutant_name},
                                                            '{preprocess_cat}'                AS source_category,
                                                            'P'                               AS nei_category,
                                                            '{feed}'                          AS feedstock
                                                   FROM     {scenario_name}.processing
                                                   WHERE    logistics_type = '{system}' AND
                                                            yield_type     = '{yield}'  AND
                                                            feed           = '{feed}'
                                                   GROUP BY fips
                                                   ;""".format(**kvals)
                            self.db.input(query_pre_process)
                    elif i > 0:
                        if not pollutant.startswith('PM'):
                            query_transport = """UPDATE     {scenario_name}.{te_table} tot
                                                 INNER JOIN {scenario_name}.transportation  trans
                                                         ON trans.fips       = tot.fips  AND
                                                            trans.yield_type = tot.yield AND
                                                            trans.feedstock  = tot.feedstock
                                                 SET        tot.{pollutant_name} = trans.total_emissions / {years_rot}
                                                 WHERE      trans.pollutantID    = '{pollutant}'     AND
                                                            tot.source_category  = '{transport_cat}' AND
                                                            trans.logistics_type = '{system}'
                                                 ;""".format(**kvals)
                            self.db.input(query_transport)
                        elif pollutant.startswith('PM'):
                            query_transport = """UPDATE     {scenario_name}.{te_table} tot
                                                 INNER JOIN {scenario_name}.transportation trans
                                                         ON trans.fips       = tot.fips  AND
                                                            trans.yield_type = tot.yield AND
                                                            trans.feedstock  = tot.feedstock
                                                 LEFT JOIN  {scenario_name}.fugitive_dust fd
                                                        ON  fd.fips       = tot.fips  AND
                                                            fd.yield_type = tot.yield AND
                                                            fd.feedstock  = tot.feedstock
                                                 SET        tot.{pollutant_name} = IF(trans.total_emissions > 0.0, (trans.total_emissions + fd.total_fd_emissions) / {years_rot}, 0)
                                                 WHERE      trans.pollutantID    = '{pollutant}'     AND
                                                            fd.pollutantID       = '{pollutant}'     AND
                                                            tot.source_category  = '{transport_cat}' AND
                                                            trans.logistics_type = '{system}'        AND
                                                            fd.logistics_type    = '{system}'
                                                 ;""".format(**kvals)
                            self.db.input(query_transport)

                            if pollutant == 'voc':
                                query_pre_process = """UPDATE     {scenario_name}.{te_table} tot
                                                       INNER JOIN {scenario_name}.processing log
                                                               ON log.fips       = tot.fips  AND
                                                                  log.yield_type = tot.yield AND
                                                                  log.feedstock  = tot.feedstock
                                                       SET        tot.{pollutant_name} = IFNULL(voc_wood, 0) / {years_rot}
                                                       WHERE      tot.source_category = '{preprocess_cat}' AND
                                                                  log.logistics_type  = '{system}'
                                                       ;""".format(**kvals)
                                self.db.input(query_pre_process)

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
                 'production_schema': config.get('production_schema'),
                 'te_table': 'total_emissions'  # @TODO: this is manually defined several places; consolidate
                 }

        query_emissions_per_prod = """SELECT    (sum({pollutant}) / prod.total_prod) AS mt_{pollutant}_perdt
                                      FROM      {scenario_name}.{te_table} tot
                                      LEFT JOIN {production_schema}.{feed_abr}_data prod ON tot.fips = prod.fips
                                      WHERE     prod.total_prod > 0.0 AND tot.{pollutant} > 0
                                      GROUP BY  tot.FIPS
                                      ORDER BY  tot.FIPS
                                      ;""".format(**kvals)
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
                 'production_schema': config.get('production_schema'),
                 'te_table': 'total_emissions'  # @TODO: defined multiple places
                 }

        query_emissions = """SELECT    sum({pollutant}) AS {pollutant}
                             FROM      {scenario_name}.{te_table} tot
                             LEFT JOIN {production_schema}.{feed_abr}_data prod
                                    ON tot.fips = prod.fips
                             WHERE     prod.total_prod > 0.0 AND tot.{pollutant} > 0
                             GROUP BY  tot.FIPS
                             ORDER BY  tot.FIPS
                             ;""".format(**kvals)

        emissions = self.db.output(query_emissions)

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
