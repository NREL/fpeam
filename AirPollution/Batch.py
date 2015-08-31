"""
Batches files for running.
Keeps track of the master batch file, which runs the smaller batch files
for each run code.
"""

from subprocess import Popen


class Batch:

    def __init__(self, cont):
        """
        Initiate Batch class by recording batch paths and creating the Document.
        @param cont: dictionary containing title, path, etc
        """
        # run title.
        self.model_run_title = cont.get('model_run_title')
        # path to batch directory.
        self.path = cont.get(key='path') + 'OPT/'
        # path to batch to be used in a batch file.
        self.batch_path = self.path.replace('/', '\\') 
        # master path to the batch file that keeps track of all the run_code batch files.
        self.master_path = self.path + cont.get(key='model_run_title') + '.bat'
        # create scenario level batch file. Needs the file directory to be created before creating.
        self.scenario_batch_file = None
        # current batch file being made.
        self.batch_file = None
    
    def get_master(self, mode):
        """
        Create master batch file.
        @param mode: weather to read or write.
        w - write
        r - read
        """
        self.scenario_batch_file = open(self.master_path, mode)
            
    def initialize(self, run_code):
        """
        Create Batch File for each run_code. 
        @param run_code: Name of new batch file.
        """
        self.scenario_batch_file.write('\n')
        self.batch_file = open(self.path + run_code + '.bat', 'w')
        self.batch_file.write("cd C:\\NonRoad\n")  # @TODO: remove hardcoding

    def append(self, state, run_code):
        """
        Add states to the batch file.
        To run a batch file in DOS for this model, type:
        >NONROAD.exe C:\\NONROAD\\NewModel\\OPT\\<run_code>\\<option_file.opt>
        @param state: state the batch file is running.
        @param run_code: run code. 
        """
        lines = "NONROAD.exe " + self.batch_path + run_code + '\\' + state + ".opt\n"
        self.batch_file.writelines(lines) 
    
    def finish(self, run_code):
        """
        finish the batch file and add the finished batch file to the full 'Scenario' batch file.
        @param run_code: run code.  
        """
        self.batch_file.close()        
        self.scenario_batch_file.write("CALL " + "\"" + self.batch_path + run_code + '.bat\"\n')
    
    def run(self, qprocess):
        """
        ****************************************
        **    Acess point to NONROAD model    **
        ****************************************
        Call master batch file.
        Runs NONROAD model through function.
        
        @deprecated: deprecated subprocess.
        p = Popen(self.master_path)
        p.wait()
         
        @param qprocess: sub process controller from  controller.Controller.
        * uses PyQt4.QtCore.QProcess.startDetached('file.exe') to run batch.
        Runs the NONROAD program in the background.
        When finished it will send a signal to the controller.
        """ 
        # start subprocess.
        if qprocess:
            qprocess.start(self.master_path)
        else:
            p = Popen(self.master_path)
            p.wait()
    
    def get_batch_files(self):
        """
        Get the total number of files that will be run through the subprocess.
        @return: total number of files.
        """
        self.get_master('r')
        # number of files that each sub .bat must process.
        files_per_doc = 49
        # total lines or files that the master batch file m
        total_lines = 0
        for line in self.scenario_batch_file:
            line = line.strip()
            if line:
                total_lines += 1
        self.scenario_batch_file.close()
        return total_lines * files_per_doc
