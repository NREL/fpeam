'''
Creates run codes.
'''
class Inputs:
    
    # variables that can be accesed.
    title, run_codes, ferts, pestFeed, fertDist = None, None, None, None, None
    
    '''
    @param inputs: Input parameters to model. dict(string: vars)
    '''
    def __init__(self, inputs=False):
        if inputs: self.sortInputs(inputs)
        
    '''
    Go through a dictionary of values that map a category to input parameters 
    to the air model.
    @param inputs: Input parameters to model. dict(string: vars)
    title => run title.
    checkBoxes => run codes, and fertilizers.
    fertilizers => fertilizers distribution.
    operations => operations on feedstocks: harvest, non-harvest, transport.
    alloc => allocating non-harvest distribution from corn grain to corn stover and wheat straw.
    @return: run codes, title, fertilizers, fertilizer distribution.
    '''
    def sortInputs(self, inputs):
        for key, value in inputs.items():
            if key == 'title':
                self.title = value
            elif key == 'checkBoxes':
                self.run_codes, self.ferts, self.pestFeed = self.createRunCodes(value)
            elif key == 'fertilizers':
                self.fertDist = self.createFertilizerDistribution(value)
            elif key == 'operations':
                self.operations = self.createOperations(value)
            elif key == 'alloc':
                self.alloc = self.createAllocation(value)
    
    '''
    Create the allocation redistribution from corn grain non-harvest
    to corn stover and wheat straw.
    @param value: Allocation percent to corn grain.
    @return: Dictionary of the percent allocations for cg, cs, and ws.
    alloc = {'CG': 1, 'CS': 0, 'WS': 0} dict(string: float)
    '''
    def createAllocation(self, value):
        alloc = {}
        # if value was entered.
        if value:
            value = float(value)
            diff = 1 - value
            alloc['CG'] = value
            alloc['CS'] = diff
            alloc['WS'] = diff 
        # default values.
        else:
            alloc['CG'] = 1
            alloc['CS'] = 0
            alloc['WS'] = 0 
        return alloc
    
    '''
    Create a operation dictionary of 4 feed stocks for Harvest,
    Non-harvest, and transport.
    @param operations: Dict of feedstocks and operations partially fillded out.
    @return: Operation dictionary. dict(dict(boolean))
    '''
    def createOperations(self, operations):
        operationDict = {'CS': {'H': True, 'N': True, 'T': True}, 
                         'WS': {'H': True, 'N': True, 'T': True},
                         'CG': {'H': True, 'N': True, 'T': True},
                         'SG': {'H': True, 'N': True, 'T': True}}
        for feedStock, oper in operations.items():
            if 'H' not in oper:
                operationDict[feedStock]['H'] = False
            if 'N' not in oper:
                operationDict[feedStock]['N'] = False
            if 'T' not in oper:
                operationDict[feedStock]['T'] = False
        return operationDict
            
    '''
    Create run codes from the check boxes in the NewModel view.
    @param checkBoxes: A list of checkboxes. Each element is a tuple
    containing the name of the variable, which is used to determine
    the feed stock and harvest activity; and the checkbox variable
    to check weather it was checked or not.
    @return: The run codes used in the air model. list(string)
    @return: Dictinary of each fertilizer and weather it was checked. dict(boolean)
    @return: Pesticides and weather to use them in the model. dict(boolean)
    '''           
    def createRunCodes(self, checkBoxes):
        # list to save run codes to.
        run_codes = []
        # weather or not a feed stock uses fertilizers.
        ferts = {'CSF': False, 'WSF': False, 'CGF': False, 'SGF': False}
        # weather or not a feed stock uses persicides. 
        pestFeed = {'CGP': False, 'SGP': False}
        # get the feedstocks that were clicked.
        feedStock = self._getCheckedFeed(checkBoxes, run_codes)
        # go through every check box.
        for checkBox in checkBoxes:
            # get name and variable of check box.
            name, var = checkBox[0], checkBox[1]  
            # make a run_code or operation code from the check box.
            run_code = self._makeRunCode(name, var, feedStock)
            # add run_code to the correct bin.
            run_codes, ferts, pestFeed = self._addRunCode(run_code, var, run_codes, ferts, pestFeed)
        return run_codes, ferts, pestFeed
    
    '''
    Add a run code to the run_codes list.
    Or add a operation to ferts and pestFeed.
    @param run_code: Current run_code that has been created. string
    @param var: Check button varibale.Used to see if it was clicked or not. PyQTCheckBox
    @param run_codes: run_codes to save the rurrent run code to. list(string)
    @param ferts: Save fertilizer operation to. dict(boolean)
    @param pestFeed: Save pesticide operation to. dict(boolean)
    @return: Saved data for run_codes, fertilizers, and pesticides. list(string), dict(boolean), dict(boolean)  
    '''
    def _addRunCode(self, run_code, var, run_codes, ferts, pestFeed):
        if run_code:
            # if it is a normal run_code. FR, CS, WS, CG
            if run_code[2] == '_':
                if 'SG' not in run_code:
                    # Might be multiple run codes for irrigation.
                    if run_code[3] != 'I':
                        run_codes.append(run_code)
                    else:
                        # only put the corn grain irrigation run codes into the final list.
                        if run_code[0:1] != 'CG':
                            # replace sg and cs with cg.
                            run_codeList = list(run_code)
                            run_codeList[0], run_codeList[1] = 'C', 'G'
                            run_code = ''.join(run_codeList)
                            # make sure run_code is not allready in the list.
                            if run_code not in run_codes:
                                run_codes.append(run_code)
                # switch grass.
                else:
                    [run_codes.append(run_code + str(i)) for i in range(1, 11)]
            # if it is a fertilizer or pesticide..
            elif run_code[-1] == 'F':
                if var.checkState() == 2: ferts[run_code] = True
                else: ferts[run_code] = False
            elif run_code[-1] == 'P':
                if var.checkState() == 2: pestFeed[run_code] = True
                else: pestFeed[run_code] = False
        return run_codes, ferts, pestFeed
    
    '''
    Get all of the checked feed stocks.
    @param checkBoxes: Check boxes from the NewModel GUI.
    @param run_codes: List that contains all of the run_codes that have been checked.
    Needed to add FR to it.
    @return: A list of all the checked feedstocks. list(string)
    '''
    def _getCheckedFeed(self, checkBoxes, run_codes):
        feedStock = []
        for checkBox in checkBoxes:
            name, var = checkBox[0], checkBox[1]
            if len(name) == 4 and var.checkState() == 2:
                # get the last two letters of the string.
                name = name[-2:]
                if name == 'FR':
                    run_codes.append(name) 
                else:
                    feedStock.append(name)
                    checkBoxes.remove(checkBox)
        return feedStock
    
    '''
    Make a run code. 
    Returns run_code if to make a traditional run_code. returns name of input var 
    if for fertilizer and pesticide.
    @param name: Name of the variable.
    @param var: Compute memory of the variable to use.
    @param feedStock: The feed stock.
    @return: run_code. Or operation such as pesticide and fertilizers. string
    '''
    def _makeRunCode(self, name, var, feedStock):
        # check every check box to make sure that it's feed stock has been chosen.
        for feed in feedStock:
            # create name from var.
            oper = name[-3:]
            # create run code.
            run_code = feed + oper
            # if the box has been check.
            if feed in name and var.checkState() == 2: 
                # check if it is not sg.
                if 'SG' not in name and (name[-1] != 'F' and name[-1] != 'P'): 
                    return run_code
                elif 'SG' not in name and (name[-1] == 'F' or name[-1] == 'P'):
                    return oper
                # turn SG input code into a run code.
                elif 'SG' in name and (name[-1] == 'H' or name[-1] == 'N' or name[-1] == 'T'): 
                    # SG_H1, SG_N1, SG_T1
                    run_code = feed + '_' + name[-1]
                    return run_code
                # return name if it is a pesticide or 
                elif 'SG' in name and (name[-1] == 'F' or name[-1] == 'P'): return oper
            # if the box has not been checked, but it is a fertilizer.
            elif len(name) == 5:
                if name[-1] == 'F': return oper
                # if the box has not been checked, but is a pesticide.
                elif name[-1] == 'P': return oper
        # else return nothing.
        return None
    
    '''
    Create fertilizer distribution. Needs to be ordered exactly for later.
    aa, an, as, ur, ns
    @param fertilizers: Feritlizers name and variable from NewModel.
    @return: fertilizer distribution the user entered or False if they did not enter anything. list(string)
    '''
    def createFertilizerDistribution(self, fertelizers):
        fertDist = {'CG': [None for i in range(0,5)], 'CS': [None for i in range(0,5)],
                    'WS': [None for i in range(0,5)], 'SG': [None for i in range(0,5)]}
        for feed, ferts in fertelizers.items():
            for fert in ferts:
                name, var = fert[0], fert[1]
                # order correctly.
                if name.endswith('aa')   and var.text(): fertDist[feed][0] = str(var.text())
                elif name.endswith('an') and var.text(): fertDist[feed][1] = str(var.text())
                elif name.endswith('as') and var.text(): fertDist[feed][2] = str(var.text())
                elif name.endswith('ur') and var.text(): fertDist[feed][3] = str(var.text())
                elif name.endswith('ns') and var.text(): fertDist[feed][4] = str(var.text())
            # sg does not have a 'aa' fertilizer input. But it is always 0.
            if feed == 'SG': fertDist[feed][0] = str(0)
            # check if nothing was entered.
            if all(v == None or v == '0' for v in fertDist[feed]):
                fertDist[feed] = None
        return fertDist
            

            
            