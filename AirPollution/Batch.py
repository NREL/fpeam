"""
Batches files for running.
Keeps track of the master batch file, which runs the smaller batch files
for each run code.
"""

from subprocess import Popen

from utils import config
import os


class Batch:

    def __init__(self, cont):
        """
        Initiate Batch class by recording batch paths and creating the Document.

        :param cont: dictionary containing title, path, etc
        """

        # run title
        self.model_run_title = cont.get(key='model_run_title')

        # path to batch directory
        self.path = '%sOPT%s' % (cont.get(key='path'), os.sep)

        # path to batch to be used in a batch file
        # self.batch_path = self.path.replace('/', '\\')  # @QUESTION: is this necessary now (with os.sep usage)? Commenting out and replacing self.batch_path usages to self.path

        # master path to the batch file that keeps track of all the run_code batch files
        self.master_path = '%s%s.bat' % (self.path, cont.get(key='model_run_title'))

        # create scenario level batch file. Needs the file directory to be created before creating.
        self.scenario_batch_file = None

        # current batch file being made
        self.batch_file = None

    def get_master(self, mode):
        """
        Create master batch file.

        :param mode: Open mode ([w]rite or [r]ead)
        :return:
        """

        mode = mode.lower()

        self.scenario_batch_file = open(self.master_path, mode)

    def initialize(self, run_code):
        """
        Create Batch file for a given run_code.

        :param run_code: run code of interest
        """

        self.scenario_batch_file.write('\n')  # this is janky, but the whole app is janky so I'm not sure where the best place for this is

        f = '%s%s.bat' % (self.path, run_code)
        self.batch_file = open(f, 'w')
        self.batch_file.write("cd %s\n" % (config.get('project_path'), ))

    def append(self, state, run_code):
        """
        Add states to the batch file.

        To run a batch file in DOS for this model, type:

        >NONROAD.exe C:\\NONROAD\\NewModel\\OPT\\<run_code>\\<option_file.opt>

        :param state: state the batch file is running
        :param run_code: run code
        :return:
        """

        lines = '{nr_path} {batch_path}{run_code}{sep}{state}.opt\n'.format(nr_path=config.get('nonroad_path'),
                                                                            batch_path=self.path,
                                                                            run_code=run_code,
                                                                            sep=os.sep,
                                                                            state=state)

        self.batch_file.writelines(lines)

    def finish(self, run_code):
        """
        finish the batch file and add the finished batch file to the full 'Scenario' batch file.

        :param run_code: run codE
        :return:
        """

        self.batch_file.close()

        self.scenario_batch_file.write("CALL %s%s" % (os.sep, os.path.join(self.path, '%s.bat' % (run_code, ))))
    
    def run(self, qprocess):
        """
        ****************************************
        **    Access point to NONROAD model   **
        ****************************************

        Call master batch file

        :param qprocess: Optional. sub process controller from  controller.Controller.
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

    # appears to be unused
    # def get_batch_files(self):
    #     """
    #     Get the total number of files that will be run through the subprocess.
    #     :return: total number of files
    #     """
    #
    #     # open master batch fle
    #     self.get_master('r')
    #
    #     # number of files that each sub .bat must process
    #     files_per_doc = 49  # @QUESTION: why does this have to be 49?
    #
    #     # total lines or files that the master batch file m
    #     total_lines = 0
    #     for line in self.scenario_batch_file:
    #         line = line.strip()
    #         if line:
    #             total_lines += 1
    #
    #     self.scenario_batch_file.close()
    #
    #     return total_lines * files_per_doc
