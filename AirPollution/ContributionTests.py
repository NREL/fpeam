# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 09:18:49 2012
@author: nfisher
Chooses the sql to grab data for ContributionFigure graph.
"""
class ChooseSQL:

    def __doc__(self):
        return 'Create a structured query based on ( activity, pollutant, feedstock ) inputs'
    
    def __init__(self, activity, pollutant, feedstock, schema):
        self.schema = schema
        self.act = activity
        self.pol = pollutant
        self.feed = feedstock
        self.queryString = ''

        self.rawTable = feedstock + '_raw'
        
        if( pollutant == 'NOx' or pollutant == 'NH3' ):
            self.fertTable = feedstock + '_nfert'

        if( (pollutant == 'VOC') and
            (feedstock == 'CG' or feedstock == 'SG') ):

            self.chemTable = feedstock + '_chem'
                
                
  
    """
    This method chooses which tables to query based on the inputs
    """
    def getQuery(self):
         
    #-- pre-define the test cases for which there are zero emissions   
        if self.feed == 'FR' and self.act == 'Harvest':
            return self.__returnFRHarv__() #special case
    
        elif self.feed == 'FR':
            return self.__returnNull__()
            
    #fertilizer only looks at nh3 and nox from fertilizer application
        elif( ( self.act == 'Fertilizer' ) and 
                ( self.pol != 'NOx' and self.pol != 'NH3' ) ):
            return self.__returnNull__()
    
    #chemical only looks at voc from herbicide and pesticide
        elif( self.act == 'Chemical' and self.pol != 'VOC'):
            return self.__returnNull__()
             
    #zero cases for CS and WS
        elif( ( self.feed == 'CS' or self.feed == 'WS')
            and 
            (self.act == 'Non-Harvest' or 
            self.act == 'Chemical')):     
            return self.__returnNull__()
            
            
    #--- end of pre-defined cases for which there are zero emissions       

        elif( ( ( self.pol == 'CO' or self.pol.startswith('SO') ) 
                    and 
                ( self.act == 'Non-Harvest' or 
                self.act == 'Harvest' or 
                self.act == 'Transport' ) 
              )
                or 
              ( self.pol == 'VOC' 
                    and not
                ( self.feed == 'CG' or self.feed == 'SG' )
              )
            ): 
    
            #query raw table for sox and co. query raw table for voc only when feedstock
            #is not corn grain or switchgrass (_chem emissions occur here)
            return self.__queryRaw__()            

    
        elif( (self.pol.startswith('PM') )
                and 
                (self.act == 'Non-Harvest' or 
                self.act == 'Harvest' or 
                self.act == 'Transport')): 
                    
            return self.__queryRaw__()
            

        elif( (self.pol == 'NH3' or self.pol == 'NOx' ) ):
            return self.__queryRawFert__()
       
        
        elif( (self.pol == 'VOC' )
                and 
                (self.feed == 'CG' or self.feed == 'SG' ) 
            ): 
        
            return self.__queryRawChem__()
    

        else:
            
            raise Exception('Error in test structure\nInputs were: %s, %s, %s'%(self.feed, self.pol, self.act))
        

    
    """
    Handle cases where there are no values to return
    """    
    def __returnNull__(self):
        self.queryString = 'No activity at this location'
        
       
       
    """
    Special case for Forest Residue
    """
    def __returnFRHarv__(self):
        self.queryString = 'FR Harvest'
       
       
        
    """
    Assemble queries that need only the '*_raw' tables. 
    """        
    def __queryRaw__(self):
        
        if self.pol.startswith('PM'):
            sumPollutant = "(sum(%s) + sum(fug_%s))" % (self.pol, self.pol)

        else: 
            sumPollutant = "sum(%s)" % (self.pol)
        
        if self.act == 'Harvest':
            act = ' ' + self.act
        else:
            act = self.act
            
        self.queryString = """
with
    activitySum as (select distinct fips, %s as x 
		from %s.%s where description ilike '%% %s' group by fips),

    totalSum as (select distinct fips, %s as x 
		from %s.%s group by fips)
        
select (a.x/t.x) as x from activitySum a, totalSum t 
where a.fips = t.fips and t.x > 0.0 and a.x > 0.0;

""" % (sumPollutant, 
       self.schema, self.rawTable, '%'+act+'%',
       sumPollutant, 
       self.schema, self.rawTable)   

#        if self.feed == 'CG' and (self.pol == 'CO' or self.pol == 'SO2'):
#            print self.queryString



    '''
    Assemble queries that need the '*_raw' and '*_fert' tables. 
    
    This part seems very odd.
    If you are not actually intersested in fertilizers, but are doing a calculation
    to get Nox and nh3, shouldnt you not care about fert.x for the ration in the first part?
    '''
    def __queryRawFert__(self):
        if self.act != 'Fertilizer':
            ratio = "(act.x)/(raw.x + fert.x)"
            conditions = ", activitySum act where act.fips = raw.fips and act.fips = fert.fips and act.x > 0.0"

        else:
            ratio = "(fert.x)/(raw.x+fert.x)"
            conditions = "where raw.fips = fert.fips"
            
        self.queryString = """
            WITH

                activitySum as (select distinct fips, sum(%s) as x
                from %s.%s where description ilike '%s' group by fips),
                
                rawSum as (select distinct r.fips, sum(r.%s) as x
                from %s.%s r group by r.fips),

                fertSum as (select distinct fips, sum(%s) as x
                from %s.%s group by fips)
                
                select (%s) as x
                FROM rawSum raw, fertSum fert %s 
                and raw.x > 0.0 and fert.x > 0.0;


            """ % (self.pol, self.schema, self.rawTable, '%'+self.act+'%',
                   self.pol, self.schema, self.rawTable,
                   self.pol, self.schema, self.fertTable,
                   ratio,
                   conditions)       
                   
          
    """
    Assemble queries that need the '*_raw' and '*_chem' tables.
    
    Almost identical code to queryRawFert(), kept separate for the sake of 
    being explicit 
    """
    def __queryRawChem__(self):


        if self.act != 'Chemical':
            ratio = "(act.x)/(raw.x + chem.x)"
            conditions = ", activitySum act where act.fips = raw.fips and act.fips = chem.fips and act.x > 0.0"

        else:
            ratio = "(chem.x)/(raw.x+chem.x)"      
            conditions = "where raw.fips = chem.fips"
            
        self.queryString = """
WITH

    activitySum as (select distinct fips, sum(%s) as x 
		from %s.%s where description ilike '%% %s' group by fips),
   
    rawSum as (select distinct r.fips, sum(r.%s) as x 
		from %s.%s r group by r.fips),

    chemSum as (select distinct fips, sum(%s) as x 
		from %s.%s group by fips)
  
select (%s) as x 
		from rawSum raw, chemSum chem %s and raw.x > 0.0 and chem.x > 0.0;

 

""" % (self.pol, self.schema, self.rawTable, '%'+self.act+'%',
       self.pol, self.schema, self.rawTable,
       self.pol, self.schema, self.chemTable,
       ratio,
       conditions)   
       
       

 
