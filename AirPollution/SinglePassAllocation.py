"""
Used to update database to account for single pass machines when harvesting corn.
Before one pass was for the corn itself and the next pass was to pick up the leftovers on the ground.
In the future this may occur with one pass.


The second query is never called.
The corn stover and wheat straw are being modeled for 2022. In that year
we predict a single pass system that will use a 540 hp vehicle to harvest
both the cs, ws, and corn grain. But we are only multiplying the cs and ws
by the single pass allocation because we are looking at corn grain data in
the year 2011. Data is being gathered for corn grain in 2022. When we get this data,
then we will let allocate_cg = True and multiply the corn grain data by it's
single pass allocation.
"""

import SaveDataHelper
from utils import config, logger


class SinglePassAllocation(SaveDataHelper.SaveDataHelper):
    
    def __init__(self, cont):
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.document_file = "SinglePassAllocation"
        # 540 is the total energy allocation for the single pass allocation
        # 380 of it goes to the residue harvesting and 160 of it goes toward the corn harvesting.
        self.residue_allocation = str(380.0 / 540.0)
        self.corn_grain_allocation = str(160.0 / 540.0)

        scenario_name = config['title']
        # @attention: allocate_cg never gets called...
        # so the second query is never made either...

        # whether to do corn grain or residue.
        # leave as is until corn grain data for 2022 is obtained.
        self.allocate_cg = True

        residues = ['cs', 'ws']

        # define corn stover query - 380/540

        # #########################
        # @change: Fugitive dust was being calculated wrong. Causing fug_pm25 to appear to be fug_pm10
        # old code: fug_pm25 = fug_pm10 * """+self.residue_allocation+"""
        # new code: fug_pm25 = fug_pm25 * """+self.residue_allocation+"""
        # #########################
        
        for r in residues: 
            query = """
                UPDATE """ + scenario_name + """.""" + r + """_raw
                SET
                    fuel_consumption = fuel_consumption * """ + self.residue_allocation + """,
                    thc = thc * """ + self.residue_allocation + """,
                    voc = voc * """ + self.residue_allocation + """,
                    co = co * """ + self.residue_allocation + """,
                    nox = nox * """ + self.residue_allocation + """,
                    co2 = co2 * """ + self.residue_allocation + """,
                    sox = sox * """ + self.residue_allocation + """,
                    pm10 = pm10 * """ + self.residue_allocation + """,
                    pm25 = pm25 * """ + self.residue_allocation + """,
                    nh3 = nh3 * """ + self.residue_allocation + """,
                    fug_pm10 = fug_pm10 * """ + self.residue_allocation + """,
                    fug_pm25 = fug_pm25 * """ + self.residue_allocation + """
                WHERE description LIKE '% Harvest%';
            """
            self._execute_query(query)
            
        # define corn grain query - 160/540
        # do not use this until corn grain data for 2022 is obtained.
        if self.allocate_cg:
            query = """
                UPDATE """ + scenario_name + """.cg_raw
                SET
                    fuel_consumption = fuel_consumption * """ + self.corn_grain_allocation + """,
                    thc = thc * """ + self.corn_grain_allocation + """,
                    voc = voc * """ + self.corn_grain_allocation + """,
                    co = co * """ + self.corn_grain_allocation + """,
                    nox = nox * """ + self.corn_grain_allocation + """,
                    co2 = co2 * """ + self.corn_grain_allocation + """,
                    sox = sox * """ + self.corn_grain_allocation + """,
                    pm10 = pm10 * """ + self.corn_grain_allocation + """,
                    pm25 = pm25 * """ + self.corn_grain_allocation + """,
                    nh3 = nh3 * """ + self.corn_grain_allocation + """,
                    fug_pm10 = fug_pm10 * """ + self.corn_grain_allocation + """,
                    fug_pm25 = fug_pm25 * """ + self.corn_grain_allocation + """
                WHERE 
                    description NOT LIKE '%Conventional%' AND
                    description LIKE '% Harvest%';
            """
            self._execute_query(query)
