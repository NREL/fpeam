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

        query = '''DROP SCHEMA IF EXISTS %s CASCADE;
                   CREATE SCHEMA %s;''' % (cont.get('model_run_title'), cont.get('model_run_title'))
        self.db.create(query)

    def create_tables(self, feedstock):
        """
        Create tables (based on feedstock)
        @attention: Insert Primary Keys (from Noah)
        """
        query = """
                        CREATE TABLE %s_raw
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
                        fug_pm25    float);""" % (feedstock,)
                        
        if feedstock != 'FR':
            query += """CREATE TABLE %s_logistics
                        (fips    char(5)    ,
                        electricity    float
                        );""" % (feedstock,)
        if feedstock == 'FR':
            query += """CREATE TABLE %s_logistics
                        (fips    char(5)    ,
                        electricity    float,
                        VOC    float
                        );""" % (feedstock,)
                    
        self._execute_query(query)

        if feedstock != 'FR':
            query = """
                            CREATE TABLE %s_NFert
                            (
                            FIPS    char(5)    ,
                            NOx    float    ,
                            NH3    float    ,
                            SCC    char(10)    ,
                            description    text)""" % (feedstock,)
            self._execute_query(query)

        if feedstock == 'SG' or feedstock == 'CG':
            query = """
                           CREATE TABLE %s_CHEM
                           (
                           FIPS    char(5),
                           SCC    char(10)    ,
                           VOC    float    ,
                           description    text)""" % (feedstock,)
            self._execute_query(query)
