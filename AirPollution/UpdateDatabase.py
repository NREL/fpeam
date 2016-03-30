"""
Used to initiate a schema for saving all the results.
The schema is titled as the name as the scenario title.
Input run_codes in study and create appropriate tables.
"""

import SaveDataHelper


class UpdateDatabase(SaveDataHelper.SaveDataHelper):

    def __init__(self, cont):
        """
        Create shcema in database to store results.
        Schema is titled with the model run title.
        """
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.document_file = "UpdateDatabase"
        self.kvals = cont.get('kvals')

        query = '''DROP SCHEMA IF EXISTS {scenario_name};
                   CREATE SCHEMA {scenario_name};'''.format(**self.kvals)
        self.db.create(query)

    def create_tables(self, feedstock):
        """
        Create tables (based on feedstock)
        @attention: Insert Primary Keys (from Noah)
        @param feedstock = feedstock type
        """
        self.kvals['feed'] = feedstock

        query = """
                        CREATE TABLE {scenario_name}.{feed}_raw
                        (
                        FIPS    char(5)    ,
                        SCC    char(10)    ,
                        HP    int    ,
                        fuel_consumption float    ,
                        THC    float    ,
                        VOC    float    ,
                        CO    float    ,
                        NOx    float    ,
                        CO2    float    ,
                        SOx    float    ,
                        PM10    float    ,
                        PM25    float    ,
                        NH3    float    ,
                        Description    text    ,
                        run_code    text    ,
                        fug_pm10    float    , 
                        fug_pm25    float);""".format(**self.kvals)

        query += """    DROP TABLE IF EXISTS {scenario_name}.{feed}_processing;
                        CREATE TABLE {scenario_name}.{feed}_processing
                        (fips    char(5)    ,
                        electricity    float,
                        run_code    text,
                        logistics_type text
                        );""".format(**self.kvals)

        if feedstock == 'FR':

            query += """ALTER TABLE {scenario_name}.{feed}_processing
                        ADD voc_wood float;""".format(**self.kvals)
                    
        self._execute_query(query)

        if feedstock != 'FR':
            query = """
                            CREATE TABLE {scenario_name}.{feed}_NFert
                            (
                            FIPS    char(5)    ,
                            NOx    float    ,
                            NH3    float    ,
                            SCC    char(10)    ,
                            description    text)""".format(**self.kvals)
            self._execute_query(query)

        if feedstock == 'SG' or feedstock == 'CG':
            query = """
                           CREATE TABLE {scenario_name}.{feed}_CHEM
                           (
                           FIPS    char(5),
                           SCC    char(10)    ,
                           VOC    float    ,
                           description    text)""".format(**self.kvals)
            self._execute_query(query)
