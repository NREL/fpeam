import SaveDataHelper

'''
Used to update database to account for single pass machines when harvesting corn.
Before one pass was for the corn itself and the next pass was to pick up the leftovers on the ground.
In the future this may occur with one pass.


The second query is never called.
The corn stover and wheat straw are being modeled for 2022. In that year
we predict a single pass system that will use a 540 hp vehicle to harvest
both the cs, ws, and corn grain. But we are only multiplying the cs and ws
by the single pass allocation because we are looking at corn grain data in
the year 2011. Data is being gathered for corn grain in 2022. When we get this data,
then we will let allocateCG = True and multiply the corn grain data by it's
single pass allocation.
'''
class SinglePassAllocation(SaveDataHelper.SaveDataHelper):
    
    def __init__(self, cont):
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.documentFile = "SinglePassAllocation"
        # 540 is the total energy allocation for the single pass allocation
        # 380 of it goes to the residue harvesting and 160 of it goes toward the corn harvesting.
        self.residueAllocation = str(380.0 / 540.0)
        self.cornGrainAllocation = str(160.0 / 540.0)
        '''
        @attention: allocateCG never gets called...
        so the second query is never made either...
        '''
        # weather to do corn grain or residue.
        # leave as is until corn grain data for 2022 is obtained.
        self.allocateCG = False
        
        residues = ['cs','ws']
        
        #define corn stover query - 380/540
        '''
        #########################
        @change: Fugitive dust was being calculated wrong. Causing fug_pm25 to appear to be fug_pm10
        old code: fug_pm25 = fug_pm10 * """+self.residueAllocation+"""
        new code: fug_pm25 = fug_pm25 * """+self.residueAllocation+"""
        #########################
        '''
        for r in residues: 
            query = """
                UPDATE """+r+"""_raw
                SET
                    fuel_consumption = fuel_consumption * """+self.residueAllocation+""",
                    thc = thc * """+self.residueAllocation+""",
                    voc = voc * """+self.residueAllocation+""",
                    co = co * """+self.residueAllocation+""",
                    nox = nox * """+self.residueAllocation+""",
                    co2 = co2 * """+self.residueAllocation+""",
                    sox = sox * """+self.residueAllocation+""",
                    pm10 = pm10 * """+self.residueAllocation+""",
                    pm25 = pm25 * """+self.residueAllocation+""",
                    nh3 = nh3 * """+self.residueAllocation+""",
                    fug_pm10 = fug_pm10 * """+self.residueAllocation+""",
                    fug_pm25 = fug_pm25 * """+self.residueAllocation+"""
                WHERE description ilike '%Harvest%';
            """             
            self._executeQuery(query)
            
        #define corn grain query - 160/540
        # do not use this until corn grain data for 2022 is obtained.
        if self.allocateCG:
            query = """
                UPDATE cs_raw
                SET
                    fuel_consumption = fuel_consumption * """+self.cornGrainAllocation+""",
                    thc = thc * """+self.cornGrainAllocation+""",
                    voc = voc * """+self.cornGrainAllocation+""",
                    co = co * """+self.cornGrainAllocation+""",
                    nox = nox * """+self.cornGrainAllocation+""",
                    co2 = co2 * """+self.cornGrainAllocation+""",
                    sox = sox * """+self.cornGrainAllocation+""",
                    pm10 = pm10 * """+self.cornGrainAllocation+""",
                    pm25 = pm25 * """+self.cornGrainAllocation+""",
                    nh3 = nh3 * """+self.cornGrainAllocation+""",
                    fug_pm10 = fug_pm10 * """+self.cornGrainAllocation+""",
                    fug_pm25 = fug_pm25 * """+self.cornGrainAllocation+"""
                WHERE 
                    description NOT ilike '%Conventional%' AND
                    description ilike '% Harvest%';
            """            
            self._executeQuery(query)
        
        
        
        
        
    