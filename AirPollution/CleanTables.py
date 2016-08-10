from model.Database import Database
from src.AirPollution.utils import cdate as CDATE
from utils import logger, config

# make backup table
MAKE_BACKUP_TABLE = config.as_bool('make_backup_table')
# fix missing leading zeros in MOVESScenarioID
FIX_LEADING_ZEROS = config.as_bool('fix_leading_zeros')
# remove extraneous results
REMOVE_DUPLICATE_SCEANRIOIDS = config.as_bool('remove_duplicate_scenario_ids')
# add indices across <length> characters (this helps joins that have not been updated to use state and county FIPS columns)
ADD_INDICES = config.as_bool('add_indices')
# add state column (supercedes joins on LEFT(MOVESScenarioID, 2)
ADD_STATE_COLUMN = config.as_bool('add_state_column')
# add FIPS column (supercedes joins on LEFT(MOVESScenarioID, 5)
ADD_FIPS_COLUMN = config.as_bool('add_fips_column')
# optimize table
OPTIMIZE_TABLE = config.as_bool('optimize_table')

# tables to process
TABLES = [  # 'baserateoutput',
    # 'baserateunits',
    # 'bundletracking',
    # 'movesactivityoutput',
    # 'moveserror',
    # 'moveseventlog',
    # 'movesoutput',
    # 'movesrun',
    # 'movestablesused',
    # 'movesworkersused',
    'rateperdistance',
    # 'rateperhour',
    # 'rateperprofile',
    'rateperstart',
    'ratepervehicle',
    'startspervehicle']

# columns for LEFT(<col>, <length>) indicies
COLUMNS = ['MOVESScenarioID', ]

# lengths for LEFT(<col>, <length>) indicies
LENGTHS = [2, 5]

# get database name
TITLE = config.get('title')

# make db
DB = Database(model_run_title=TITLE)

# Set schema name for MOVES output database
MOVES_OUTPUT_DB = config.get('moves_output_db')

# init string formatting container
KVALS = {'schema': MOVES_OUTPUT_DB}


class TableCleaner(object):
    """

    """

    def __init__(self, schema, table):
        """

        :param schema:
        :param table:
        """

        # init
        self.schema = schema
        self.table = table

    def execute_sql(self, sql, vals=None):
        """
        Execute arbitrary SQL statement.

        :param sql:
        :param vals:
        :return:
        """

        try:
            DB.execute_sql(sql=sql, vals=vals)
        except Exception, e:
            logger.error(e)
            return False

        return True

    def add_missing_fips_leading_zero(self, schema, table):
        """
        Prepend '0' to MOVESSCenarioID values that appear to be truncated.

        :param schema:
        :param table:
        :return:
        """

        kvals = {'schema': schema,
                 'table': table
                 }

        sql = "UPDATE {schema}.{table} SET MOVESScenarioID = CONCAT('0', MOVESScenarioID) WHERE (length(MOVESScenarioID) = 24 AND LENGTH(monthID) = 2) OR (length(MOVESScenarioID) = 23 AND LENGTH(monthID = 2));".format(**kvals)

        return self.execute_sql(sql)

    def remove_extra_rows(self, schema, table):
        """
        Delete rows that are not from the most recent MOVES run.

        :param schema: schema name containing table
        :param table: table name to clean
        :return: True if successful
        """

        kvals = {'schema': schema,
                 'table': table
                 }

        # get scenario IDs
        sql = 'SELECT MOVESScenarioID FROM {schema}.{table} GROUP BY MOVESScenarioID HAVING COUNT(*) > 1 ORDER BY MOVESScenarioID;'.format(**kvals)
        scenario_ids = DB.execute_sql(sql)
        if scenario_ids is not None:
            scenario_ids = scenario_ids[0]

        # remove records that do not match the latest (largest ID) MOVES run
        for scenario_id in scenario_ids:
            val = {'scenario_id': scenario_id[0]}

            # get largest run id
            sql = """SELECT MAX(MOVESRunID) FROM {schema}.{table} WHERE MOVESScenarioID = %(scenario_id)s;""".format(**kvals)
            logger.debug(sql % val)

            try:
                run_id = DB.execute_sql(sql, val)[0][0][0]
                val['run_id'] = run_id
            except Exception, e:
                logger.error(e)
                return False

            sql = """DELETE FROM {schema}.{table} WHERE MOVESRunID != %(run_id)s AND MOVESScenarioID = %(scenario_id)s;""".format(**kvals)

            return self.execute_sql(sql=sql, vals=val)

    def make_length_index(self, schema, table, column, char_length):
        """
        Create index on split <column> in <schema>.<table> using <column>(<len>).

        :param schema:
        :param table:
        :param column:
        :param char_length:
        :return:
        """

        kvals = {'schema': schema,
                 'table': table,
                 'column': column,
                 'char_length': char_length
                 }

        sql = 'CREATE INDEX idx_{table}_{column}_{char_length} ON {schema}.{table} ({column}({char_length}));'.format(**kvals)

        return self.execute_sql(sql=sql)

    def add_state_col(self, schema, table):
        """
        Add state FIPS column based on MOVESScenarioID.

        :param schema:
        :param table:
        :return:
        """

        kvals = {'schema': schema,
                 'table': table
                 }

        sql = 'ALTER TABLE {schema}.{table} ADD COLUMN state CHAR(2);'.format(**kvals)
        self.execute_sql(sql=sql)

        sql = 'UPDATE {schema}.{table} SET state = LEFT(MOVESScenarioID, 2);'.format(**kvals)
        if not self.execute_sql(sql=sql):
            return False

        sql = 'CREATE INDEX idx_{table}_state ON {schema}.{table} (state);'.format(**kvals)

        return self.execute_sql(sql=sql)

    def make_backup(self, schema, table):
        """
        Make backup of <schema>.<table> as <schema>.<table>_bak_YYYYMMDD. Will sliently drop an existing table of the same name.

        :param schema:
        :param table:
        :return:
        """

        kvals = {'schema': schema,
                 'table': table,
                 'date': CDATE
                 }

        # drop existing back
        sql = """DROP TABLE IF EXISTS {schema}.{table}_bak_{date};""".format(**kvals)

        if not self.execute_sql(sql=sql):
            return False

        # make backup
        sql = """CREATE TABLE {schema}.{table}_bak_{date} AS SELECT * FROM {schema}.{table};""".format(**kvals)

        return self.execute_sql(sql=sql)

    def add_county_col(self, schema, table):
        """
        Add county FIPS column based on MOVESScenarioID.

        :param schema:
        :param table:
        :return:
        """

        kvals = {'schema': schema,
                 'table': table
                 }

        sql = 'ALTER TABLE {schema}.{table} ADD COLUMN fips CHAR(5);'.format(**kvals)
        if not self.execute_sql(sql=sql):
            return False

        sql = 'UPDATE {schema}.{table} SET fips = LEFT(MOVESScenarioID, 5);'.format(**kvals)
        if not self.execute_sql(sql=sql):
            return False

        sql = 'CREATE INDEX idx_{table}_fips ON {schema}.{table} (fips);'.format(**kvals)

        return self.execute_sql(sql=sql)

    def optimize_table(self, schema, table):
        """

        :param schema:
        :param table:
        :return:
        """

        kvals = {'schema': schema,
                 'table': table
                 }

        sql = 'OPTIMIZE TABLE {schema}.{table};'.format(**kvals)
        logger.debug(sql)

        try:
            DB.execute_sql(sql)
        except Exception, e:
            logger.error(e)
            return False

        return True


def main():
    """

    :return:
    """

    for table in TABLES:
        KVALS['table'] = table

        table_cleaner = TableCleaner(schema=MOVES_OUTPUT_DB, table=table)

        # make backup table
        if MAKE_BACKUP_TABLE:
            logger.info('Backing up {schema}.{table}'.format(**KVALS))
            _ = table_cleaner.make_backup(schema=MOVES_OUTPUT_DB, table=table)
            logger.debug('make_backup(%s): %s' % (table, _))

        # fix missing leading zeros in MOVESScenarioID
        if FIX_LEADING_ZEROS:
            logger.info('Add leading zero to MOVESScenarioIDs in {schema}.{table}'.format(**KVALS))
            _ = table_cleaner.add_missing_fips_leading_zero(schema=MOVES_OUTPUT_DB, table=table)
            logger.debug('add_missing_fips_leading_zero(%s): %s' % (table, _))

        # remove extraneous results
        if REMOVE_DUPLICATE_SCEANRIOIDS:
            logger.info('Removing extraneous results {schema}.{table}'.format(**KVALS))
            _ = table_cleaner.remove_extra_rows(schema=MOVES_OUTPUT_DB, table=table)
            logger.debug('remove_extra_rows(%s): %s' % (table, _))

        # add indices across <length> characters (this helps joins that have not been updated to use state and county FIPS columns)
        if ADD_INDICES:
            for column in COLUMNS:
                KVALS['column'] = column
                for length in LENGTHS:
                    KVALS['length'] = length

                    logger.info('Adding index to {schema}.{table}.{column} across first {length} characters'.format(**KVALS))
                    _ = table_cleaner.make_length_index(schema=MOVES_OUTPUT_DB, table=table, column=column,
                                                        char_length=length)
                    logger.debug('make_length_index({table}, {column}, {length}): {result}'.format(result=_, **KVALS))

        # add state column (supercedes joins on LEFT(MOVESScenarioID, 2)
        if ADD_STATE_COLUMN:
            logger.info('Adding state FIPS column to {schema}.{table}'.format(**KVALS))
            _ = table_cleaner.add_state_col(schema=MOVES_OUTPUT_DB, table=table)
            logger.info('add_state_col(%s): %s' % (table, _))

        # add FIPS column (supercedes joins on LEFT(MOVESScenarioID, 5)
        if ADD_FIPS_COLUMN:
            logger.info('Adding state FIPS column to {schema}.{table}'.format(**KVALS))
            _ = table_cleaner.add_county_col(schema=MOVES_OUTPUT_DB, table=table)
            logger.debug('add_fips_col(%s): %s' % (table, _))

        # optimize table
        if OPTIMIZE_TABLE:
            logger.info('Optimizing {schema}.{table}'.format(**KVALS))
            _ = table_cleaner.optimize_table(schema=MOVES_OUTPUT_DB, table=table)
            logger.debug('optimize_table(%s): %s' % (table, _))

    logger.info('Complete!')


if __name__ == '__main__':
    main()
