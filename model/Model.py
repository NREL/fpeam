class Model():
    
    def __init__(self, _db):
        self.db = _db
        self.schemas = self.getSchemas()
        self.model = []
        self.header = []
    
    def newModel(self, schema, table):
        tables = self.getTables(schema)
        if schema in self.schemas and table in tables:
            self.model = self.summedDimmesnios(schema, table) 
            self.header = self.getHeaders(schema, table)          
    
    def summedDimmesnios(self, schema, table):
        query = self.selectAll(schema, table)
        data = self.db.output(query, schema)
        return data
    
    def selectAll(self, schema, table):
        query = 'SELECT * FROM %s.%s' % (schema, table)
        return query
     
    def getHeaders(self, schema, table):
        query = """SELECT column_name FROM information_schema.columns
                WHERE table_schema = '%s' AND table_name = '%s'""" % (schema, table)
        headers = self.db.output(query, schema)
        headers = [h[0] for h in headers]
        return headers
        
    def getSchemas(self):
        # grab schema names.
        exclude = ['pg_toast', 'pg_temp_1', 'pg_toast_temp_1', 'pg_catalog', 'public', 
                   'information_schema', 'bts2dat_55', 'constantvals', 'full2008nei'] 
        query = 'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA'
        schemas = self.db.output(query, self.db.production_schema)
        # list to hold new schema names
        cleanedSchemas = []
        # look through every schema name in the db and find the output ones.
        for schema in schemas:
            # get the name of the schema.
            if schema[0] not in exclude:
                cleanedSchemas.append(schema[0])
        return cleanedSchemas
                
    '''
    Get all of the table names from a schema.
    @param schema: Schema to look for table names.
    @return: All of the table names from a schema.  
    '''
    def getTables(self, schema):
        tableNameId   = 2
        query = """select * from information_schema.tables 
                   where table_schema = '%s'""" % (schema)
        data = self.db.output(query, schema)
        tables = [ row[tableNameId] for row in data]
        return tables

    
    
    
    
    
    
    
    
    