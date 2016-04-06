import SaveDataHelper
from utils import config, logger

# @TODO: refactor to match PEP8 standards
# @TODO: refactor to use string formatting
# @TODO: fill out docstrings

class NEIComparison(SaveDataHelper.SaveDataHelper):
    """

    """

    def __init__(self, cont):
        """

        """
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.document_file = "NEIComparison"
        self.nei_data_by_county = None
        self.scenario_name = cont.get('model_run_title')

        query = """
        CREATE TABLE {scenario}.summedEmissions
        (
        fips      char(5),
        feedstock text,
        prod      float,
        harv_Ac   float,
        NOX       float DEFAULT 0.0,
        NH3       float DEFAULT 0.0,
        SOX       float DEFAULT 0.0,
        VOC       float DEFAULT 0.0,
        PM10      float DEFAULT 0.0,
        PM25      float DEFAULT 0.0,
        CO        float DEFAULT 0.0);""".format(scenario=self.scenario_name)

        self._execute_query(query)

    def __set_nei_ratio_table__(self, feedstock):
        """

        :param feedstock:
        :return:
        """

        query = """
        CREATE TABLE {scenario}.{feedstock}_NEIRatio
        (
        fips char(5),
        nox  float,
        sox  float,
        co   float,
        pm10 float,
        pm25 float,
        voc  float,
        nh3  float);""".format(scenario=self.scenario_name, feedstock=feedstock, )

        self._execute_query(query)

    def create_summed_emissions_table(self, feedstock):
        """
        Create summed dimmensions table in the db.

        :param feedstock:
        :return:

        """

        # @TODO: refactor this whole shebang; I don't even know what to say about 'prod'

        if feedstock == 'CG':
            f = "Corn Grain"
            prod = "dat.total_prod, dat.total_harv_ac"
        elif feedstock == 'SG':
            f = "Switchgrass"
            prod = "dat.prod, dat.harv_ac"
        elif feedstock == 'WS':
            f = "Wheat Straw"
            prod = "dat.prod, dat.harv_ac"
        elif feedstock == 'CS':
            f = "Corn Stover"
            prod = "dat.prod, dat.harv_ac"
        elif feedstock == 'FR':
            f = "Forest Residue"
            prod = "dat.fed_minus_55, 0"

        query = """
                INSERT INTO {scenario_name}.summedEmissions
                WITH
                """
        # populate tables that have fertilizer emissions
        # if feedstock == 'CG' or feedstock == 'SG':
        if feedstock != 'FR':
            query += """
                        (SELECT DISTINCT fips,
                                        sum(nox) AS nox,
                                        sum(nh3) AS nh3
                            FROM %s.%s_nfert
                            GROUP BY fips) AS Fert,
                        ---------------------------------------------------------------------------------------------
                        """ % (self.scenario_name, feedstock,)

        # populate table that have pesticides.
        if feedstock == 'CG' or feedstock == 'SG':
            query += """
                        Chem AS (SELECT DISTINCT fips,
                                        sum(voc) AS voc
                            FROM %s.%s_chem
                            GROUP BY fips),
                        ---------------------------------------------------------------------------------------------
                        """ % (self.scenario_name, feedstock,)

        # populate everything else.
        
        # ########################
        # @change: Not adding fug_pm10
        # old code: (sum(pm10) + sum(fug_pm10)) AS pm10, 
        #           (sum(pm25) + sum(fug_pm25)) AS pm25,
        # new code: (sum(pm10) + 0.0) AS pm10, 
        #           (sum(pm25) + 0.0) AS pm25,
        # ########################
        
        query += """
                    Raw AS (SELECT DISTINCT fips,
                            sum(nox) AS nox,
                            sum(nh3) AS nh3,
                            sum(sox) AS sox,
                            sum(voc) AS voc,
                            (sum(pm10) + sum(fug_pm10)) AS pm10,
                            (sum(pm25) + sum(fug_pm25)) AS pm25,
                            (sum(co)) AS co
                    FROM %s.%s_raw
                    GROUP BY fips)
            ---------------------------------------------------------------------------------------------
            """ % (self.scenario_name, feedstock,)

        if feedstock == 'CG' or feedstock == 'SG': 
            query += """
                        (SELECT dat.fips, %s, %s,
                            (raw.nox + fert.nox) AS nox,
                            (raw.nh3 + fert.nh3) AS nh3,
                            (raw.sox) AS sox,
                            (raw.voc + chem.voc) AS voc,
                            (raw.pm10) AS pm10,
                            (raw.pm25) AS pm25,
                            (raw.co) AS co
                        FROM %s dat
                        LEFT JOIN Fert ON fert.fips = dat.fips
                        LEFT JOIN Chem ON chem.fips = dat.fips
                        LEFT JOIN Raw ON raw.fips = dat.fips
                        )
                        ;""" % ("'" + f + "'", prod, self.db.production_schema + '.' + feedstock + "_data")

        elif feedstock == 'CS' or feedstock == 'WS':
            query += """
                        (SELECT dat.fips, %s, %s,
                            (raw.nox + fert.nox) AS nox,
                            (raw.nh3 + fert.nh3) AS nh3,
                            (raw.sox) AS sox,
                            (raw.voc) AS voc,
                            (raw.pm10) AS pm10,
                            (raw.pm25) AS pm25,
                            (raw.co) AS co
                        FROM %s dat
                        LEFT JOIN Fert ON fert.fips = dat.fips
                        LEFT JOIN Raw ON raw.fips = dat.fips
                        )
                        ;""" % ("'" + f + "'", prod, self.db.production_schema + '.' + feedstock + "_data")
    
        elif feedstock == 'FR':
            query += """
                        (SELECT dat.fips, %s, %s,
                            (raw.nox) AS nox,
                            (raw.nh3) AS nh3,
                            (raw.sox) AS sox,
                            (raw.voc) AS voc,
                            (raw.pm10) AS pm10,
                            (raw.pm25) AS pm25,
                            (raw.co) AS co
                        FROM %s dat
                        LEFT JOIN Raw ON raw.fips = dat.fips
                        )
                        ;""" % ("'" + f + "'", prod, self.db.production_schema + '.' + feedstock + "_data")

        print query
        self._execute_query(query)

    def create_nei_comparison(self, feedstock):

        self.nei_data_by_county = config.get('nei_data_by_county')

        allocation = 0.52

        self.__set_nei_ratio_table__(feedstock)

        f_abbrev = {'CG': 'Corn Grain',
                    'SG': 'Switchgrass',
                    'CS': 'Corn Stover',
                    'WS': 'Wheat Straw',
                    'FR': 'Forest Residue',
                    'cellulosic': 'celluslosic'
                    }

        # feedstock abbreviation for queries
        f = f_abbrev[feedstock]
        # 'not' phrase for where clause
        n = ''

        if f == 'cellulosic':
            # query everything except cg
            f = 'Corn Grain'
            n = 'NOT'

        query = """
                    INSERT INTO {feedstock}_NEIRatio
                        SELECT nrel.fips,
                               (nrel.nox  * {allocation}) / (nei.nox  * 0.907185) AS nox,
                               (nrel.sox  * {allocation}) / (nei.sox  * 0.907185) AS sox,
                               (nrel.co   * {allocation}) / (nei.co   * 0.907185) AS co,
                               (nrel.pm10 * {allocation}) / (nei.pm10 * 0.907185) AS PM10,
                               (nrel.pm25 * {allocation}) / (nei.pm25 * 0.907185) AS PM25,
                               (nrel.voc  * {allocation}) / (nei.voc  * 0.907185) AS VOC,
                               CASE WHEN nei.nh3 > 0 THEN (nrel.nh3 * {allocation}) / (nei.nh3 * 0.907185) ELSE 0.0 END AS NH3
                        FROM (SELECT fips,
                                     sum(nox)  AS nox,
                                     sum(sox)  AS sox,
                                     sum(co)   AS co,
                                     sum(pm10) AS pm10,
                                     sum(pm25) AS pm25,
                                     sum(voc)  AS voc,
                                     sum(nh3)  AS nh3
                              FROM {schema}.summedemissions
                              WHERE feedstock {n} LIKE '%{f}%'
                              GROUP BY fips
                             ) nrel
                        LEFT JOIN (SELECT fips, nox, sox, co, pm10, pm25, voc, nh3 FROM {nei}) nei ON nrel.fips = nei.fips
                        WHERE nrel.nh3 > 0 AND nei.nox > 0
                        ;""".format(feedstock=feedstock, allocation=allocation, f=f, n=n, schema=self.db.schema, nei=self.nei_data_by_county)

        self._execute_query(query)

if __name__ == '__main__':
    raise NotImplementedError
