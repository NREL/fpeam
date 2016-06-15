from utils import logger

class SaveDataHelper:
    """
    Parent class to
    Fertilizer, Chemical, CombustionEmissions, UpdateDatabase, FugitiveDust, and NEIComparison.
    Instantiates important variables and used to execute queries.
    """

    def __init__(self, cont):
        """
        Instantiate main variables.
        @param db: Database for saving data.
        @param qr: Query recorder for debugging sql.
        """
        self.db = cont.get('db')
        self.qr = cont.get('qr')

    def _execute_query(self, query):
        """
        used to execute a sql query that inserts data into the databse.
        uses isQuery to create a text file for the sql queries to be recorded. Only occurs during first query.
        @param query: sql insert query.
        """
        # try:
        #     self.qr.document_query(_file=self.document_file, query=query)
        # except:
        #     # logger.error('Failed to document SQL query')
        #     logger.debug('Failed to document (filename: %s) SQL query: %s' % (self.document_file, query, ))
        #     pass

        try:
            self.db.input(query=query)
            return True
        except:
            # logger.error('Failed to execute SQL query')
            logger.error('Failed to execute SQL query: %s' % (query, ))
            return False
