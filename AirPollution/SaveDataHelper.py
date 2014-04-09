'''
Parent class to 
Fertilizer, Chemical, CombustionEmissions, UpdateDatabase, FugitiveDust, and NEIComparison.
Instantiates important variables and used to execute queries.
'''
class SaveDataHelper:
    
    '''
    Instantiate main variables.
    @param db: Database for saving data.
    @param qr: Query recorder for debugging sql.  
    '''
    def __init__(self, cont):
        self.db = cont.get('db')
        self.qr = cont.get('qr')
        
    '''
    used to execute a sql query that inserts data into the databse.
    uses isQuery to create a text file for the sql queries to be recorded. Only occurs during first query.
    @param query: sql insert query. 
    '''     
    def _executeQuery(self, query):
        self.qr.documentQuery(self.documentFile, query)   
        #print query     
        self.db.input(query)