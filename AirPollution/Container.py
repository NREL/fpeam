'''
A container to keep track of important variables.
Is a dictionary that maps a keyword to a variable or class.
'''
class Container:
    
    '''
    Add known variables to the container to be used through out the program.
    '''
    def __init__(self):
        keys = ['modelRunTitle', 'run_codes', 'path', 'db', 'qr']
        self.c = {}
        for key in keys:
            self.c[key] = None      
    
    '''
    Set a new value in the container.
    @param key: Keyword.
    @param data: Data that is mapped to the uniquer keyword.  
    '''
    def set(self, key, data):
        self.c[key] = data
    
    '''
    Get data from the container.
    @param key: Keyword to access container.
    @return: The variable or class mapped to the key. 
    '''
    def get(self, key):
        if self.c.has_key(key):
            return self.c[key]