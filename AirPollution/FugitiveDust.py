import SaveDataHelper

"""
Create the fugitive dust emisisons based on the run code
The run code tells you the feedstock, tillage, and operation
(harvest/non-harvest/irrigation). 
Fugitive dust occurs from vehicles such as tractors going over the field and creating lots of dust.
******************
@note: Emission factors are calculated on a spread sheet. 
https://docs.google.com/spreadsheet/ccc?key=0ArgAX3FKoio9dGdQcnRqRlZoS2FiZDVvODJHY3J0bHc#gid=1 
*****************
"""
class FugitiveDust(SaveDataHelper.SaveDataHelper):
    def __init__(self, cont):
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.documentFile = "FugitiveDust"
        self.pmRatio = 0.20
    
    """
    loop through run_codes and call this method to create fugitive
    dust emissions in database.
    Adds pm10, and pm25 emissions.
    @param run_code: Specific run code with info on feedstock and operation. 
    TODO: why does it execute one query then returns another query?
    """                
    def setEmissions(self, run_code):
# Forest Residue fugitive dust emissions            
        if run_code.startswith('FR'):
            self.__forestRes__()  
# Corn Grain fugitivie dust emissions            
        elif run_code.startswith('CG'):
            self.__cornGrain__(run_code)     
# Wheat straw fugitive dust emissions            
        elif run_code.startswith('WS'):
            self.__wheatSraw__(run_code)
# Corn stover fugitive dust emissions            
        elif run_code.startswith('CS'):
            self.__cornStover__(run_code)
# switchgrass fugitive dust emissions            
        elif run_code.startswith('SG'):
            pass
 
    '''
    Forest residue fugitive dust emissions.
    '''
    def __forestRes__(self):
        pmFR = self.convertLbsToMt(0.0)
        # currently there are no pm emissions from FR operations
        query = """
            UPDATE fr_RAW fr
                SET 
                    fug_pm10 = (%s * dat.fed_minus_55),
                    fug_pm25 = (%s * dat.fed_minus_55 * %s)
                FROM %s.fr_data dat
                WHERE (dat.fips = fr.fips)
            """ % (pmFR, pmFR, self.pmRatio, self.db.productionSchema)
        self._executeQuery(query)
       
    
    '''
    Corn grain fugitive dust emissions
    '''    
    def __cornGrain__(self, run_code):
# --emission factors: 
        # 1.7 lbs/acre, convert to mt.        
        pmConvTillHarv = self.convertLbsToMt(2.4) # mt / acre
        pmReduTillHarv = self.convertLbsToMt(2.4) # mt / acre
        pmNoTillHarv = self.convertLbsToMt(2.4) # mt / acre
        
        pmConvTillNonHarv = self.convertLbsToMt(8.0) # mt / acre
        pmReduTillNonHarv = self.convertLbsToMt(7.2) # mt / acre
        pmNoTillNonHarv = self.convertLbsToMt(5.2) # mt / acre
        
        #irrigation emissions do not currently have PM emissions
        pmDieIrrigation = self.convertLbsToMt(0.0) # mt / acre
        pmGasIrrigation = self.convertLbsToMt(0.0) # mt / acre
        pmLPGIrrigation = self.convertLbsToMt(0.0) # mt / acre
        pmCNGIrrigation = self.convertLbsToMt(0.0) # mt / acre
        
        modelTransport = False
# --                
# choose operation for conventional till
        if run_code.startswith('CG_C'):
            tillage = 'Conventional'
            tableTill = 'convtill'
            
            if run_code.endswith('N'):
                operation = 'Non-Harvest'
                EF = pmConvTillNonHarv
                
            elif run_code.endswith('H'):
                operation = 'Harvest'
                EF = pmConvTillHarv
                modelTransport = True
                
# choose operation for reduced till
        elif run_code.startswith('CG_R'):
            tillage = 'Reduced'
            tableTill = 'reducedtill'
            
            if run_code.endswith('N'):
                operation = 'Non-Harvest'
                EF = pmReduTillNonHarv
                
            elif run_code.endswith('H'):
                operation = 'Harvest'
                EF = pmReduTillHarv
                modelTransport = True                        
                
# choose operation for no till                
        elif run_code.startswith('CG_N'):
            tillage = 'No Till'
            tableTill = 'notill'
            
            if run_code.endswith('N'):
                operation = 'Non-Harvest'
                EF = pmNoTillNonHarv
                
            elif run_code.endswith('H'):
                operation = 'Harvest'
                EF = pmNoTillHarv
                modelTransport = True                                                
              
# choose operation for irrigation
        elif run_code.startswith('CG_I'):
            tillage = 'Irrigation'
            tableTill = 'total'
            
            if run_code.endswith('D'):
                operation = 'Diesel'
                EF = pmDieIrrigation
                
            elif run_code.endswith('G'):
                operation = 'Gasoline'
                EF = pmGasIrrigation
                
            elif run_code.endswith('L'):
                operation = 'LPG'
                EF = pmLPGIrrigation
                                        
            elif run_code.endswith('C'):
                operation = 'CNG'
                EF = pmCNGIrrigation
 
        # execute query for transport operations
        if modelTransport: 
            # pm10 = mt/acre * acre =  mt
            # pm2.5 = mt/acre * acre * constant = mt
            self.transportQuery(run_code, tillage)
            
        # return query for non-transport operations
        # pm10 = mt/acre * acre =  mt
        # pm2.5 = mt/acre * acre * constant = mt
        self.pmQuery(run_code, EF, tableTill, operation, tillage)
            
    
    '''
    Corn stover fugitive dust emissions.
    '''
    def __cornStover__(self, run_code):
# --emission factors:         
        pmReduTillHarv = self.convertLbsToMt(1.8) # mt / acre 
        pmNoTillHarv = self.convertLbsToMt(1.8) # mt / acre 
# --     

# choose operation for reduced till
        if run_code.startswith('CS_R'):
            tillage = 'Reduced'
            tableTill = 'reducedtill'
            operation = 'Harvest'
            EF = pmReduTillHarv
            
# choose operation for no till                
        elif run_code.startswith('CS_N'):
            tillage = 'No Till'
            tableTill = 'notill'
            operation = 'Harvest'
            EF = pmNoTillHarv
        
        # execute query for transport emissions
        # pm10 = dt/acre * acre =  dt
        # pm2.5 = dt/acre * acre * constant = dt
        self.transportQuery(run_code, tillage)

        # return non-transport emissions query        
        self.pmQuery(run_code, EF, tableTill, operation, tillage)        
    
    
    '''
    Wheat straw fugitive dust emissions. 
    Bassically the same as corn stover...
    '''
    def __wheatSraw__(self, run_code):
# --emission factors:         
        pmReduTillHarv = self.convertLbsToMt(1.8) # mt / acre 
        pmNoTillHarv = self.convertLbsToMt(1.8) # mt / acre 
# --     

# choose operation for reduced till
        if run_code.startswith('WS_R'):
            tillage = 'Reduced'
            tableTill = 'reducedtill'
            operation = 'Harvest'
            EF = pmReduTillHarv
            
# choose operation for no till                
        elif run_code.startswith('WS_N'):
            tillage = 'No Till'
            tableTill = 'notill'
            operation = 'Harvest'
            EF = pmNoTillHarv
        
        # execute query for transport emissions
        # pm10 = dt/acre * acre =  dt
        # pm2.5 = dt/acre * acre * constant = dt
        self.transportQuery(run_code, tillage)
        # return non-transport emissions query        
        self.pmQuery(run_code, EF, tableTill, operation, tillage)  
    
    '''
    Makes a query to update pm10 and pm2.5 from fugitive dust. Then executes that query. Calculates in units of metric tons.
    @param run_code: run code used to get type of feedstock.
    @param ef: Emission factor specific for each activity. In metric tons per acre.
    @param till: Type of till used.
    @param activity: Type of activity used to make emission.
    @param tillType: Type of till in description.
    '''
    def pmQuery(self, run_code, ef, till, activity, tillType):
        feed = run_code.lower()[0:2]
        query = """
                UPDATE """ + feed + """_raw raw
                SET 
                    fug_pm10 = (""" + str(ef) + """ * cd.""" + str(till) + """_harv_AC),
                    fug_pm25 = (""" + str(ef) + """ * cd.""" + str(till) + """_harv_AC) * """ + str(self.pmRatio) + """
                FROM """ + str(self.db.productionSchema) + """.""" + str(feed) + """_data cd
                WHERE     (cd.fips = raw.fips) AND 
                          (raw.description ILIKE '""" + str("%" + activity + "%") + """') AND 
                          (raw.description ILIKE '""" + str("%" + tillType + "%") + """')"""
        self._executeQuery(query)
        
    '''
    Calculates pm10 and pm2.5 emissions from transportation and makes a query to update db. Calculates in units of metric tons.
    
    Equation from http://www.epa.gov/ttnchie1/ap42/ch13/final/c13s0202.pdf     13.2.2 Unpaved Roads pg 3.
    Gives units of lbs which must be converted to metric tons.
    E = [k * v (s/12)^a (W/3)^b] / (M/0.2)^c
    E converted = (E * 0.907) / 2000
    Where:    v = vehicle miles traveled (default 10)
              s = silt content (%)
              W = mass of vehicle (tons)
              M = moisture content (%)
              
    @param run_code: Run code to get feed stock from.
    @param tillType: Tillage type. Used to update correct row in feedstock_raw. 
    '''
    def transportQuery(self, run_code, tillType):
        feed = run_code.lower()[0:2]
        # factors for equation.
        weight = str(32.01)  # tons
        k25, k10 = str(0.38), str(2.6)    # constant
        a25, a10 = str(0.8), str(0.8)     # constant
        b25, b10 = str(0.4), str(0.4)     # constant
        c25, c10 = str(0.3), str(0.3)     # constant
        #TODO: convert from lbs to dt
        query = """
                UPDATE """ + feed + """_raw raw
                SET 
                    fug_pm10 = """ + str("("+k10+"*10*0.907*((tfd.silt/12)^"+a10+")*(("+weight+"/3)^"+b10+"))/(((tfd.moisture/0.2)^"+c10+")*2000)") + """,
                    fug_pm25 = """ + str("("+k25+"*10*0.907*((tfd.silt/12)^"+a25+")*(("+weight+"/3)^"+b25+"))/(((tfd.moisture/0.2)^"+c25+")*2000)") + """
                FROM """ + self.db.constantsSchema + """.transportfugitivedust tfd
                WHERE     (raw.fips ilike tfd.fips || '%') AND 
                          (raw.description ILIKE '""" + str("%transport%") + """') AND 
                          (raw.description ILIKE '""" + str("%" + tillType + "%") + """')"""
        self._executeQuery(query)
    
    '''
    Convert from lbs to metric tons. 
    @param ef: Emission factor in lbs/acre. Converted to mt/acre.  
    @return Emission factor in mt/acre
    '''
    def convertLbsToMt(self, ef):
        mt = (ef * 0.907) / 2000.0 # metric tons.
        return mt


#Data structure to hold SG emission factors
#   --structure is kept in the 'long-hand' format so users may easily change
#        EF's in the future
class SG_FugitiveDust(SaveDataHelper.SaveDataHelper):
    
    def __init__(self, cont, operation):
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.documentFile = "SG_FugitiveDust"
        # to convert from PM10 to PM2.5, b/c PM2.5 is smaller.
        self.pmRatio = 0.20
        
        if operation == 'Transport':
            # these emissions are not used any more for calculating emissions. Just tells code how long to loop for.
            emissionFactors = [     # lbs/acre
                                    1.2, #year 1 transport emission factor
                                    1.2, #year 2
                                    1.2, #year 3
                                    1.2, #year 4
                                    1.2, #year 5
                                    1.2, #year 6
                                    1.2, #year 7
                                    1.2, #year 8
                                    1.2, #year 9
                                    1.2 #year 10
                                    ]
            self.description = 'SG_T'
            
        elif operation == 'Harvest':
            emissionFactors = [     # lbs/acre
                                    2.4, #year 1 harvest emission factor
                                    2.4, #year 2
                                    2.4, #year 3
                                    2.4, #year 4
                                    2.4, #year 5
                                    2.4, #year 6
                                    2.4, #year 7
                                    2.4, #year 8
                                    2.4, #year 9
                                    2.4 #year 10
                                    ]
            self.description = 'SG_H'
            
        elif operation == 'Non-Harvest':
            emissionFactors = [     # lbs/acre
                                    7.6, #year 1 non-harvest emission factor
                                    2.0, #year 2
                                    0.8, #year 3
                                    0.8, #year 4
                                    1.6, #year 5
                                    0.8, #year 6
                                    0.8, #year 7
                                    0.8, #year 8
                                    0.8, #year 9
                                    0.0 #year 10
                                    ]
            self.description = 'SG_N'
        
        self.emissionFactors = (x * 0.907 / 2000.0 for x in emissionFactors) #convert from lbs to metric tons. mt / acre          
                        
                            
    def setEmissions(self):
        for year, EF in enumerate(self.emissionFactors):   
            # return non-transport emissions query      
            # pm10 = mt/acre * acre =  mt
            # pm2.5 = mt/acre * acre * constant = mt  
            # switch grass on a 10 year basis.
            if self.description == 'SG_N' or self.description == 'SG_H':
                query = """
                        UPDATE sg_raw raw
                        SET 
                            fug_pm10 = (%s * dat.harv_AC) / 10,
                            fug_pm25 = ((%s * dat.harv_AC) * %s) / 10
                        FROM %s.sg_data dat
                        WHERE     (dat.fips = raw.fips) AND 
                                  (raw.run_code ILIKE '%s');                     
                    """ % (EF, 
                           EF, self.pmRatio,
                           self.db.productionSchema,
                           str("%" + self.description + str(year+1) + "%")
                           )
            elif self.description == 'SG_T':
                # factors for equation.
                weight = str(32.01)  # tons
                k25, k10 = str(0.38), str(2.6)    # constant
                a25, a10 = str(0.8), str(0.8)     # constant
                b25, b10 = str(0.4), str(0.4)     # constant
                c25, c10 = str(0.3), str(0.3)     # constant
                #TODO: convert from lbs to dt
                query = """
                        UPDATE sg_raw raw                                                                  
                        SET 
                            fug_pm10 = """ + str("(("+k10+"*10*0.907*((tfd.silt/12)^"+a10+")*(("+weight+"/3)^"+b10+"))/(((tfd.moisture/0.2)^"+c10+")*2000.0))/10.0") + """,
                            fug_pm25 = """ + str("(("+k25+"*10*0.907*((tfd.silt/12)^"+a25+")*(("+weight+"/3)^"+b25+"))/(((tfd.moisture/0.2)^"+c25+")*2000.0))/10.0") + """
                        FROM """ + self.db.constantsSchema + """.transportfugitivedust tfd
                        WHERE     (raw.fips ilike tfd.fips || '%') AND 
                                  (raw.run_code ILIKE '""" + str("%" + self.description + str(year+1) + "%") + """')"""

            self._executeQuery(query)
            

        
