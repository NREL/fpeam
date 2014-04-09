'''
Records queries to a text file for debugging purposes.
'''
class QueryRecorder:
    
    '''
    Need to know path to save queries to.
    @param path: Path to where queries are saved. 
    '''
    def __init__(self, _path):
        # path to directory where queries are recorded.
        self.path = _path + "QUERIES/"
        # keep track of what files have allready been created.
        self.files = []
        # current file to write to.
        self.docFile = None
    
    '''
    Documents query by saving the string to a files.
    @param file: File's name to save the query to.
    @param query: Query string that is being recorded. 
    '''
    def documentQuery(self, _file, query):
        self.docFile = self._open(_file)
        self.docFile.write(query)
    
    '''
    Creates a new doc file if the file does not exist yet,
    otherwise returns the previously created document.
    @param file: Name of the file to open.
    @return: Document to write to. 
    '''
    def _open(self, _file):
        # create a new docFile to return.
        if file not in self.files:
            docFile = open(self.path + _file + ".sql",'w')
            self.files.append(_file)
            return docFile
        # return the allready created docFile.
        else:
            return self.docFile
        
        
        
        