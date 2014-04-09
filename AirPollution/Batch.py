from subprocess import Popen

'''
Batches files for running.
Keeps track of the master batch file, which runs the smaller batch files
for each run code.
'''
class Batch:
    
    '''
    Initiate Batch class by recording batch paths and creating the Document.
    @param path: Path to scenario directory.
    @param modelRunTitle: Title of the scenario.
    '''
    def __init__(self, cont):
        # run title.
        self.modelRunTitle = cont.get('modelRunTitle')
        # path to batch directory.
        self.path = cont.get('path') + 'OPT/'
        # path to batch to be used in a batch file.
        self.batchPath = self.path.replace('/', '\\') 
        # master path to the batch file that keeps track of all the run_code batch files.
        self.masterPath = self.path + cont.get('modelRunTitle') + '.bat'
        # create scenario level batch file. Needs the file directory to be created before creating.
        self.scenarioBatchFile = None
        # current batch file being made.
        self.batchFile = None
    
    '''
    Create master batch file.
    @param mode: weather to read or write.
    w - write
    r - read
    '''
    def getMaster(self, mode):
        self.scenarioBatchFile = open(self.masterPath, mode)
            
    '''
    Create Batch File for each run_code. 
    @param run_code: Name of new batch file.
    '''              
    def initialize(self, run_code):
        self.scenarioBatchFile.write('\n')
        self.batchFile = open(self.path + run_code + '.bat', 'w')
        self.batchFile.write("cd C:\\NonRoad\n")          

    '''
    Add states to the batch file.
    To run a batch file in DOS for this model, type:
    >NONROAD.exe C:\\NONROAD\\NewModel\\OPT\\<run_code>\\<option_file.opt>
    @param state: state the batch file is running.
    @param run_code: run code. 
    '''
    def append(self, state, run_code):
        lines = "NONROAD.exe " + self.batchPath + run_code + '\\' + state + ".opt\n"
        self.batchFile.writelines(lines) 
    
    '''
    finish the batch file and add the finished batch file to the full 'Scenario' batch file.
    @param run_code: run code.  
    '''
    def finish(self, run_code):
        self.batchFile.close()        
        self.scenarioBatchFile.write("CALL " + "\"" + self.batchPath + run_code + '.bat\"\n')
    
    '''
    ****************************************
    **    Acess point to NONROAD model    **
    ****************************************
    Call master batch file.
    Runs NONROAD model through function.
    
    @deprecated: deprecated subprocess.
    p = Popen(self.masterPath)
    p.wait()
     
    @param qprocess: sub process controller from  controller.Controller.
    * uses PyQt4.QtCore.QProcess.startDetached('file.exe') to run batch.
    Runs the NONROAD program in the background.
    When finished it will send a signal to the controller.
    ''' 
    def run(self, qprocess):
        # start subprocess.
        if qprocess:
            qprocess.start(self.masterPath)
        else:
            p = Popen(self.masterPath)
            p.wait()
    
    '''
    Get the total number of files that will be run through the subprocess.
    @return: total number of files.
    '''   
    def getBatchFiles(self):
        self.getMaster('r')
        # number of files that each sub .bat must process.
        filesPerDoc = 49
        # total lines or files that the master batch file m
        totalLines = 0
        for line in self.scenarioBatchFile:
            line = line.strip()
            if line:
                totalLines += 1
        self.scenarioBatchFile.close()
        return totalLines * filesPerDoc     
        
        
        