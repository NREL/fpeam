"""
Used to initiate a schema for saving all the results.
The schema is titled as the name as the scenario title.
Input run_codes in study and create appropriate tables.
"""

import SaveDataHelper


class UpdateDatabase(SaveDataHelper.SaveDataHelper):
    """
    Create schema and tables for results.

    Schema is titled with the model run title.
    """

    def __init__(self, cont):

        SaveDataHelper.SaveDataHelper.__init__(self, cont)

        self.document_file = "UpdateDatabase"
        self.kvals = cont.get('kvals')

        query = '''DROP   SCHEMA IF EXISTS {scenario_name};
                   CREATE SCHEMA           {scenario_name};'''.format(**self.kvals)

        self.db.create(query)

        # generate average speed table for MOVES data analysis by joining tables for average speed and "dayhour"
        query = """DROP TABLE IF EXISTS {constants_schema}.averageSpeed;
                   CREATE TABLE {constants_schema}.averageSpeed
                   AS (SELECT table1.roadTypeID, table1.avgSpeedBinID, table1.avgSpeedFraction, table2.hourID, table2.dayID, table1.hourDayID
                   FROM {moves_database}.avgspeeddistribution table1
                   LEFT JOIN {moves_database}.hourday table2
                   ON table1.hourDayID = table2.hourDayID
                   WHERE sourceTypeID = '61')
                   ;""".format(**self.kvals)

        self.db.create(query)

        # fugitive dust table for off-farm transport
        query = """CREATE TABLE {scenario_name}.fugitive_dust
                    (fips                   char(5),
                     feedstock              char(5),
                     yearID                 char(4),
                     pollutantID            char(45),
                     yield_type             char(2),
                     logistics_type         char(2),
                     unpaved_fd_emissions   float,
                     sec_paved_fd_emissions float,
                     pri_paved_fd_emissions float,
                     total_fd_emissions     float
                    )
                   ;""".format(**self.kvals)

        self._execute_query(query)

        # combustion emissions table for off-farm transportation
        query = """CREATE TABLE {scenario_name}.transportation
                    (fips                           char(5),
                     feedstock                      char(5),
                     yearID                         char(4),
                     logistics_type                 char(2),
                     yield_type                     char(2),
                     pollutantID                    char(45),
                     run_emissions                  float,
                     start_hotel_emissions          float,
                     rest_evap_emissions            float DEFAULT 0,
                     total_emissions                float
                    )
                   ;""".format(**self.kvals)

        self._execute_query(query)

        # feedstock processing table (contains VOC emission for wood drying for FR and electricity consumption for all crops)
        query = """CREATE TABLE {scenario_name}.processing
                    (fips           char(5),
                     feed           char(2),
                     electricity    float,
                     run_code       char(5),
                     logistics_type char(2),
                     yield_type     char(2),
                     voc_wood       float
                    )
                   ;""".format(**self.kvals)

        self._execute_query(query)

    def create_tables(self, feedstock):
        """
        Create fugitive dust, transportation, processing, and raw data tables for <feedstock>.

        :param feedstock: STRING feedstock type
        """

        self.kvals['feed'] = feedstock.lower()

        # raw data tables for fugitive dust and combustion emissions associated with NONROAD equipment
        query = """CREATE TABLE {scenario_name}.{feed}_raw
                    (FIPS             char(5),
                     SCC              char(10),
                     HP               int,
                     fuel_consumption float,
                     THC              float,
                     VOC              float,
                     CO               float,
                     NOx              float,
                     CO2              float,
                     SOx              float,
                     PM10             float,
                     PM25             float,
                     NH3              float,
                     Description      text,
                     run_code         char(6),
                     fug_pm10         float,
                     fug_pm25         float
                    )
                   ;""".format(**self.kvals)

        self._execute_query(query)

        # fertilizer tables for all crops
        query = """CREATE TABLE {scenario_name}.{feed}_nfert
                    (FIPS        char(5),
                     tillage     char(5),
                     budget_year char(2),
                     NOx         float,
                     NH3         float,
                     SCC         char(10),
                     description text
                    )
                   ;""".format(**self.kvals)

        self._execute_query(query)

        # chemical tables for those crops that use herbicides (previously only CG and SG, now populating for all crops when using regional crop budget)
        query = """CREATE TABLE {scenario_name}.{feed}_chem
                    (FIPS        char(5),
                     tillage     char(5),
                     budget_year char(2),
                     SCC         char(10),
                     VOC         float,
                     description text
                    )
                   ;""".format(**self.kvals)

        self._execute_query(query)
