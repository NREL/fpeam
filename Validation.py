from PyQt4 import QtGui

'''
Used for validating user inputs.
'''
class Validation:
    
    # string containing the error.
    errors = []
    
    '''
    Called when ever a error is made. Adds the error message to a list.
    @param msg: Error message. string
    @return: False, indicating a error occured. boolean
    '''
    def error(self, msg):
        self.errors.append(msg)
        return False
    
    '''
    Used to get the errors from validation.
    When it is called it destroys the old errors and returns them.
    @return: list of errors. list(string)
    '''
    def getErrors(self):
        oldErrors = self.errors
        self.errors = []
        return oldErrors
    
    '''
    Validate title.
    @param title: Title to validate. Must be less then or equal to 8 characters. string
    @return: True if no errors, false if title is greater then 8 characters, 
    first character is not a letter, or the title has spaces. boolean
    '''
    def title(self, title):
        alphabetL = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        alphabetU = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        if not title:
            return self.error('Must enter a run title.')
        elif len(title) > 8:
            return self.error('Title must be less than 9 characters.')
        elif title[0] not in alphabetL and title[0] not in alphabetU:
            return self.error('Title`s first character must be letter.')
        elif ' ' in title:
            return self.error('Title cannot contain spaces.')
        else:
            return True
    
    '''
    Validate run codes. Make sure they selecetd a feed stock and harvest activity.
    @param run_codes: run codes to validate. list(string)
    @return: True if more then 0 run codes, false if no run codes were submitted. boolean
    '''
    def runCodes(self, run_codes):
        if len(run_codes) > 0:
            return True
        else:
            return self.error('Must select a feed stock and activity.') 
    
    '''
    Validate fertilizer distribution.
    Must all be numbers and must sum up to 1.
    Or they can leave all the slots blank.
    @param fertDist: Fertilizer distribution the user enterd for 4 feedstocks. dict(string: list(string))
    @return: True if criteria are met, false otherwise. boolean
    '''
    def fertDist(self, fertDists):
        # if they don't enter anything, then return true.
        if all(fertDist == None for fertDist in fertDists.values()):
            return True
        for fertDist in fertDists.values():
            # if the current fertilization distribution is blank.
            if not fertDist:
                continue
            # make sure all of the entries are numbers and sum to 1.
            sumDist = 0.0
            try:
                for fert in fertDist:
                    sumDist += float(fert)
            except: 
                return self.error('Must enter a number for fertilizer distributions.') 
            if sumDist != 1:
                return self.error('Distribion must sum to 1.') 
        return True
    
    '''
    Fertilizer validation. Should validate on it's own. Would only be set off
    it a bug occurs in the making of the fertilizer dictionary.
    @param fert: Dictionary of the four feedstocks and weather the model will account
    for them using fertilizers. dict(boolean)
    @return: True if all conditions are met, false otherswise. boolean.
    '''
    def ferts(self, ferts):
        if len(ferts.values()) >= 5:
            return self.error('Fertilizer Error.') 
        else: return True
     
    '''
    Pesticide validation. Only to make sure pesticide dictionary was created.
    @param pestFeed: Pesticides name and weather it was clicked. dict(string)
    @return: True if conditions are met, false otherwise. boolean 
    '''       
    def pest(self, pestFeed):
        if len(pestFeed.values()) >= 3:
            return self.error('Pesticide Error.') 
        else: return True
            
            
        
        
    