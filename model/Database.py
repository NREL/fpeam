"""
Database.py - Database connection and querying.
@author: Jeremy Bohrer
@organization: NREL
@date: 6/2/2013
"""

import warnings

import pymysql

warnings.filterwarnings("ignore", "Unknown table.*")
# warnings.filterwarnings("ignore", "")

from AirPollution.utils import config, logger


class Database:

    def __init__(self, model_run_title):
        """
        Initialize the database and set production and constants schemas.

        :param model_run_title: Scenario title. Also used as the name for the database schema used to save emission results.
        """

        # Open connection to database
        self.conn = self.connect()

        # Set schema name for production data
        self.production_schema = config.get('production_schema')
        logger.debug('Using production schema: %s' % (self.production_schema, ))

        # Set schema name for stored constants (N application rates, N distribution, NEI data, etc...)
        self.constants_schema = config.get('constants_schema')
        logger.debug('Using constants schema: %s' % (self.constants_schema, ))

        # Set schema name for MOVES default database
        self.moves_default_db = config.get('moves_database')
        logger.debug('Using MOVES default database: %s' % (self.moves_default_db, ))

        # Set schema name for MOVES output database
        self.moves_output_db = config.get('moves_output_db')
        logger.debug('Using MOVES default database: %s' % (self.moves_output_db, ))

        # Set base schema name
        self.schema = model_run_title

    def connect(self, _db_name=None, _user=None, _password=None, host=None):
        """
        Connect to the database using supplied credentials or, if not supplied, config values.

        @param _db_name: database name
        @param _user: user name
        @param _password: password
        @param host: database host server
        """

        db_name = _db_name or config.get('db_name')
        user = _user or config.get('db_user')
        password = _password or config.get('db_pass')
        host = host or config.get('db_host')
        logger.debug('Opening database connection')
        # force MySQL warnings to raise as exceptions
        # warnings.filterwarnings('error', category=pymysql.Warning)

        return pymysql.connect(host=host, user=user, password=password, db=db_name, local_infile=True)

    def input(self, query):
        """
        Deprecated. Use Database.execute_sql() instead.

        Execute a SQL query. Intended to be used to insert data, but as written will simply execute any SQL passed.

        :param query: SQL query. Can also be a list of queries to run in batch.
        """

        return self.execute_sql(sql=query, vals=None)

    def output(self, query):
        """
        Deprecated. Use Database.execute_sql() instead.

        Execute a SQL query, returning all results as a list.

        @param query: SQL query
        @return: rows returned by <query>
        """

        return self.execute_sql(sql=query, vals=None)

    def create(self, query):
        """
        Deprecated. Use Database.execute_sql() instead.

        Execute a SQL query. Intended to be used to create structures such as schemas or tables, but as written will simply
        execute any SQL passed.

        @param query: SQL query
        """

        return self.execute_sql(sql=query, vals=None)

    def backup_table(self, schema, table):
        """
        Create a backup of <schema>.<table> in <schema>.<table>_bak.

        :param schema: schema name
        :param table: table name
        :return:
        """

        sql_drop = 'DROP TABLE IF EXISTS {s}.{t}_bak; '.format(s=schema, t=table)

        sql_create = 'CREATE TABLE {s}.{t}_bak AS SELECT * FROM {s}.{t}' \
                     ';'.format(s=schema, t=table)

        self.execute_sql(sql=sql_drop)
        self.execute_sql(sql=sql_create)

    def execute_sql(self, sql, vals=None):
        """
        Execute SQL statement.

        :param sql: SQL statement(s) to execute
        :param vals: Replacement values
        :return: Results set if applicable
        """

        # # convert to list if not already iterable collection @TODO: replace with collections.iterable
        if not isinstance(sql, (list, tuple, set)):
            sql = (sql, )

        results = []
        with self.conn.cursor() as cur:
            for s in sql:
                # execute query
                logger.debug(cur.mogrify(s, vals))
                try:
                    cur.execute(s, vals)
                except Exception, e:
                    logger.error(e)

                self.conn.commit()
                # save any results
                if cur.rowcount > 0:
                    results.append(cur.fetchall())

        cur.close()
        # return any results
        if len(results) > 0:
            return results

    def close(self):
        """
        Close the database connection.
        """

        logger.debug('Closing database connection')
        self.conn.close()


if __name__ == "__main__":     
    raise NotImplementedError
