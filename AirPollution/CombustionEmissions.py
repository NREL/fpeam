import SaveDataHelper
import csv
import os

"""
Writes raw data for emmisions to a .csv file that can be opened with excel.
Then saves the data to the db with name <run_code>_raw.

Transform the data from the default Nonroad output to a useful format. 
Update database with emissions as well as copy emissions to static files
for quick debugging and error checking.  
Combustion emmisions associated with harvest and non-harvest methods that use non-road vehicles.
"""
class CombustionEmissions(SaveDataHelper.SaveDataHelper):
    
    '''
    @param operationDict: dictionary containing 3 feedstocks that have harvest, non-harvest, and transport.
    Each feedstock contains another dictionary of the harvest methods and weather to do the run with them.
    dict(dict(boolean))
    {'CS': {'H': True, 'N': True, 'T': True}, 
    'WS': {'H': True, 'N': True, 'T': True},
    'CG': {'H': True, 'N': True, 'T': True}}
    @param alloc: Amount of non harvest emmisions to allocate to cg, cs, and ws. dict(string: int)
    {'CG': .9, 'CS': .1, 'WS': .1}
    '''
    def __init__(self, cont, operationDict, alloc): 
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.documentFile = "CombustionEmissions"
        # not used here?
        self.pmRatio = 0.20
        self.basePath = cont.get('path')
        # operations and feedstock dictionary.
        self.operationDict = operationDict
        self.alloc = alloc

    def populateTables(self, run_codes, modelRunTitle):
        
        # short ton = 0.90718474 metric tonn
        convert_tonne = 0.9071847  # metric ton / dry ton
        
        # DOE conversion from BTU/gal of diesel, LHV: light heat value.
        # also part of GREET Argonne model for conversion.
        self.LHV = 128450.0 / 1e6  # mmBTU / gallon --> default for diesel fuel, changed for other fuel types
                
        # SF2 impact analysis NH3 emission factor
        self.NH3_EF = 0.68  # gNH3 / mmBTU --> default for diesel fuel, changed for other fuel types
        
        # From EPA NONROAD Conversion Factors for Hydrocarbon Emission Components.
        # Convert THC to VOC
        self.vocConversion = 1.053  # --> default for diesel fuel
        
        # Convert PM10 to PM2.5
        # not used at the moment...
        self.pm10toPM25 = 0.97  # --> default for diesel fuel
        # convert from gallons to btu.
        gal_to_btu = 128450 # Btu/gallon
        #-------Inputs End
        
        for run_code in run_codes:
            
            print run_code
            # path to results
            path = self.basePath + 'OUT/%s/' % (run_code)
            listing = os.listdir(path)
        
            feedstock = run_code[0:2] 
            
            
            # write data to static files for debugging purposes
            f = open(self.basePath + 'OUT/' + run_code + '.csv', 'wb')
            writer = csv.writer(f)
            writer.writerow(('FIPS', 'SCC', 'HP', 'FuelCons_gal/yr', 'THC_exh', 'VOC_exh', 'CO_exh', 'NOx_exh',
                            'CO2_exh', 'SO2_exh', 'PM10_exh', 'PM25_exh', 'NH3_exh', 'Description'))
        
            queries = []
            for cur_file in listing:
                # use for debugging
                # print "Current file is: %s -- %s" % (run_code, cur_file)
                reader = csv.reader(open(path + cur_file))
         
                # account for headers in file, skip the first 10 lines.
                for i in range(10): reader.next()
                        
                for row in reader:
                    # row[4] is the vehicle population.
                    if float(row[4]) > 0.0:    
                
                        # _getDescription updates the vocConversion, NH3_EF and LHV for each fuel type    
                        SCC = row[2]
                        HP = row[3]   
                        description, operation = self._getDescription(run_code, SCC, HP) 
                        # check if it is a feedstock and operation that should be recorded.
                        if feedstock == 'FR' or self.operationDict[feedstock][operation[0]]:  
                            # all emissions are recorder in metric tons.         
                            # dry ton * metric ton / dry ton = metric ton
                            THC = float(row[5]) * convert_tonne
                            CO = float(row[6]) * convert_tonne
                            NOx = float(row[7]) * convert_tonne
                            CO2 = float(row[8]) * convert_tonne
                            SO2 = float(row[9]) * convert_tonne
                            PM10 = float(row[10]) * convert_tonne
                            PM25 = float(row[10]) * self.pm10toPM25 * convert_tonne
                            '''
                            fuel consumption
                            NONROAD README 5-10
                            CNG is a gaseous fuel, and its fuel consumption is reported in gallons at 
                            standard temperature and pressure. This can be misleading if this very large number
                            is viewed together with the fuel consumption of the other (liquid) fuels
                            dt/year
                            '''
                            FuelCons = float(row[19])  # gal/year
                            
                            VOC = THC * self.vocConversion                    
                            NH3 = FuelCons * self.LHV * self.NH3_EF / (1e6)  # gal * mmBTU/gal * gNH3/mmBTU = g NH3
                            
                            
                            # allocate non harvest emmisions from cg to cs and ws.
                            if operation and operation[0] == 'N' and feedstock == 'CG': 
                                # add to cs.
                                if self.operationDict['CS'][operation[0]] and self.alloc['CS'] != 0:
                                    self._record('CS', row[0], SCC, HP, FuelCons, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, NH3, description, run_code, writer, queries, self.alloc)
                                # add to ws. 
                                if self.operationDict['WS'][operation[0]] and self.alloc['WS'] != 0:  
                                    self._record('WS', row[0], SCC, HP, FuelCons, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, NH3, description, run_code, writer, queries, self.alloc)
                                # add to corn grain.
                                self._record(feedstock, row[0], SCC, HP, FuelCons, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, NH3, description, run_code, writer, queries, self.alloc)
                            # don't change allocation.
                            else: 
                                self._record(feedstock, row[0], SCC, HP, FuelCons, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, NH3, description, run_code, writer, queries)
                            
                            # change constants back to normal, b/c they can be changes in _getDescription()
                            self.LHV = 128450.0 / 1e6  
                            self.NH3_EF = 0.68
                            self.vocConversion = 1.053
                            self.pm10toPM25 = 0.97
                        
            self.db.input(queries)
        
        print "Finished populating table for " + run_code            

    '''
    write data to static files and the database
    @param feed: Feed stock. string
    @param alloc: Allocation of non-harvest emmissions between cg, cs, and ws. dict(string: int)
    @param emmissions: Emmissions from various pollutants. int  
    '''
    def _record(self, feed, row, SCC, HP, FuelCons, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, NH3, description, run_code, writer, queries, alloc=None):
        # multiply the emmissions by allocation constant.
        if alloc:
            FuelCons, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, NH3 = FuelCons * alloc[feed], THC * alloc[feed], VOC * alloc[feed], CO * alloc[feed], NOx * alloc[feed], CO2 * alloc[feed], SO2 * alloc[feed], PM10 * alloc[feed], PM25 * alloc[feed], NH3 * alloc[feed]
        writer.writerow((row, SCC, HP, FuelCons, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, NH3, run_code,))
                            
        q = """INSERT INTO %s.%s_raw (FIPS, SCC, HP, THC, VOC, CO, NOX, CO2, SOx, PM10, PM25, fuel_consumption, NH3, description, run_code) 
                                            VALUES ('%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '%s', '%s')""" % (self.db.schema, feed, row, SCC, HP, THC, VOC, CO, NOx, CO2, SO2, PM10, PM25, FuelCons, NH3, description, run_code)
        queries.append(q)

    '''
    Switch grass harvest and non-harvest uses two different machines that are 60 and 130 hp.
    This creates multiple rows in the db for each operation year. To remove the duplicate columns,
    for each fips and for each operation year, add all the same ones and make a single row.
    '''
    def updateSG(self):
        # insert added data to sg_raw.
        self._insertSGData()
        # delete old data from sg_raw.
        self._deleteSGData()
    
    '''
    Switch grass harvest and non-harvest uses two different machines that are 60 and 130 hp.
    This creates multiple rows in the db for each operation year. This function creates a single column for each run_code,
    by adding together multiple entries from the different hp's. Adds data to sg_raw.
    '''
    def _insertSGData(self):
        # when inserting, leave some of the slots blank that do not matter.
        query = """
            INSERT into """ + self.db.schema + """.sg_raw
            WITH 
                Raw as 
                (
                    SELECT DISTINCT fips, run_code, description,
                        sum(nox) AS nox,
                        sum(nh3) AS nh3,
                        sum(sox) AS sox,
                        sum(voc) AS voc,
                        sum(pm10) AS pm10, 
                        sum(pm25) AS pm25,
                        sum(co) AS co,
                        sum(fuel_consumption) AS fuel_consumption
                    FROM sgnew.sg_raw
                    GROUP BY fips, run_code, description
                )
                (
                SELECT 
                    dat.fips as fips, 
                    '' as scc, 0 as hp, (raw.fuel_consumption) as fuel_consumption, 0 as thc,
                    (raw.voc) as voc,
                    (raw.co) as co,
                    (raw.nox) as nox, 
                    0 as co2,
                    (raw.sox) as sox,
                    (raw.pm10) as pm10, 
                    (raw.pm25) as pm25,
                    (raw.nh3) as nh3,  
                    raw.description as description,
                    raw.run_code as run_code, 
                    0 as fug_pm10, 0 as fug_pm25    
                FROM """ + self.db.productionSchema + """.sg_data dat
                LEFT JOIN Raw ON raw.fips = dat.fips
                ) """
        self.db.input(query)
    
    '''
    Deletes unwanted data in sg_raw. b/c of multiple entries for each run_code.
    '''    
    def _deleteSGData(self):
        query = """
            DELETE FROM """ + self.db.schema + """.sg_raw
            WHERE sg_raw.hp != 0 or sg_raw.run_code IS NULL  
            """
        self.db.input(query)

    def _getDescription(self, run_code, SCC, HP):
        # cast HP as a number
        HP = int(HP)
        # in case operation does not get defined.
        operation = ''
        description = ''
        
# Switchgrass        
        if run_code.startswith('SG_H'):
            if len(run_code) == 4: 
                description = "Year %s - Harvest" % (run_code[4])  # year 1-9
            else:
                description = "Year %s - Harvest" % (run_code[4:6])  # year 10
            operation = 'Harvest'

        elif run_code.startswith('SG_N'):
            if len(run_code) == 4: 
                description = "Year %s - Non-Harvest" % (run_code[4])  # year 1-9
            else:
                description = "Year %s - Non-Harvest" % (run_code[4:6])  # year 10
            operation = 'Non-Harvest'
                
        elif run_code.startswith('SG_T'):
            if len(run_code) == 4: 
                description = "Year %s - Transport" % (run_code[4])  # year 1-9
            else:
                description = "Year %s - Transport" % (run_code[4:6])  # year 10
            operation = 'Transport'
                        
# Forest Residue            
        elif run_code.startswith('FR'):
            if HP == 600:
                description = "Loader Emissions"
            elif HP == 175:
                description = "Chipper Emissions"
        
# Corn Stover and Wheat Straw        
        elif run_code.startswith('CS') or run_code.startswith('WS'):
        
        # get tillage    
            if run_code.endswith('RT'):
                tillage = 'Reduced Till'
            elif run_code.endswith('NT'):
                tillage = 'No Till'    
            
            if SCC.endswith('5020'):
                operation = 'Harvest'
            elif SCC.endswith('5015'):
                operation = 'Transport'
            
            description = tillage + ' - ' + operation
            
        # Corn Grain
        elif run_code.startswith('CG'):
            
        # get tillage    
            if run_code.startswith('CG_R'): tillage = 'Reduced Till'
                
            elif run_code.startswith('CG_N'): tillage = 'No Till'    
                
            elif run_code.startswith('CG_C'): tillage = 'Conventional Till'
        
        # special case for irrigation    
            elif run_code.startswith('CG_I'):
        
                if run_code.endswith('D'):
                    tillage = 'Diesel Irrigation'
                    self.LHV = 128450.0 / 1e6  
                    self.NH3_EF = 0.68  
                    self.vocConversion = 1.053
                    self.pm10toPM25 = 0.97 
                                 
                elif run_code.endswith('L'):
                    tillage = 'LPG Irrigation'
                    self.LHV = 84950.0 / 1e6
                    self.NH3_EF = 0.0  # data not available
                    self.vocConversion = 0.995
                    self.pm10toPM25 = 1.0
                               
                elif run_code.endswith('C'):
                    tillage = 'CNG Irrigation'
                    # 983 btu/ft3 at 1atm and 32F, standard temperature and pressure.
                    self.LHV = 20268.0 / 1e6
                    self.NH3_EF = 0.0  # data not available
                    self.vocConversion = 0.004
                    self.pm10toPM25 = 1.0
                                        
                elif run_code.endswith('G'):
                    tillage = 'Gasoline Irrigation'
                    self.LHV = 116090.0 / 1e6
                    self.NH3_EF = 1.01        
                    self.vocConversion = 0.933         
                    self.pm10toPM25 = 0.92
            
            # get operation (harvest or non-harvest)                                                    
            if run_code.endswith('N') or run_code.startswith('CG_I'):
                operation = 'Non-Harvest'
                
            elif run_code.endswith('H'):
                # get operation (harvest or transport)
                if SCC.endswith('5020'):
                    operation = 'Harvest'
                elif SCC.endswith('5015'):
                    operation = 'Transport'
            
   
            description = tillage + ' - ' + operation    
         
        return description, operation 
    
    
    
