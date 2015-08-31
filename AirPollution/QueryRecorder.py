"""
Records queries to a text file for debugging purposes.
"""


class QueryRecorder:
    def __init__(self, _path):
        """
        Need to know path to save queries to.
        @param path: Path to where queries are saved.
        """
        # path to directory where queries are recorded.
        self.path = _path + "QUERIES/"
        # keep track of what files have allready been created.
        self.files = []
        # current file to write to.
        self.doc_file = None

    def document_query(self, _file, query):
        """
        Documents query by saving the string to a files.
        @param file: File's name to save the query to.
        @param query: Query string that is being recorded.
        """
        self.doc_file = self._open(_file)
        self.doc_file.write(query)

    def _open(self, _file):
        """
        Creates a new doc file if the file does not exist yet,
        otherwise returns the previously created document.
        @param _file: Name of the file to open.
        @return: Document to write to.
        """

        # create a new doc_file to return.
        if file not in self.files:
            doc_file = open(self.path + _file + ".sql", 'w')
            self.files.append(_file)
            return doc_file
        # return the already created doc_file.
        else:
            return self.doc_file
