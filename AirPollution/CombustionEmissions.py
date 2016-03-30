import SaveDataHelper
import csv
import os
from utils import config, logger

# @TODO: refactor to match PEP8 standards
# @TODO: refactor to use string formatting
# @TODO: fill out docstrings


class CombustionEmissions(SaveDataHelper.SaveDataHelper):
    """
    Writes raw data for emmisions to a .csv file that can be opened with excel.
    Then saves the data to the db with name <run_code>_raw.
    
    Transform the data from the default Nonroad output to a useful format. 
    Update database with emissions as well as copy emissions to static files
    for quick debugging and error checking.  
    Combustion emmisions associated with harvest and non-harvest methods that use non-road vehicles.
    """

    def __init__(self, cont, operation_dict, alloc):
        """

        Each feedstock contains another dictionary of the harvest methods and weather to do the run with them.
        dict(dict(boolean))
        {'CS': {'H': True, 'N': True, 'T': True},
        'WS': {'H': True, 'N': True, 'T': True},
        'CG': {'H': True, 'N': True, 'T': True}}

        :param cont:
        :param operation_dict: dictionary containing 3 feedstocks that have harvest, non-harvest, and transport
        :param alloc: Amount of non harvest emmisions to allocate to cg, cs, and ws. dict(string: int)
            {'CG': .9, 'CS': .1, 'WS': .1}
        :return:

        """

        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.document_file = "CombustionEmissions"
        # not used here?
        self.pm_ratio = 0.20  # @TODO: remove hardcoded values
        self.base_path = cont.get('path')
        # operations and feedstock dictionary.
        self.operation_dict = operation_dict
        self.alloc = alloc
        
        self.lhv = None  
        self.nh3_ef = None
        self.voc_conversion = None
        self.pm10topm25 = None

        self.cont = cont

    def populate_tables(self, run_codes):
        """

        :param run_codes: list of codes for NONROAD runs
        :return:
        """
        
        # short ton = 0.90718474 metric tonn
        convert_tonne = 0.9071847  # metric ton / dry ton
        
        # DOE conversion from BTU/gal of diesel, lhv: light heat value.
        # also part of GREET Argonne model for conversion.
        self.lhv = 128450.0 / 1e6  # mmBTU / gallon --> default for diesel fuel, changed for other fuel types
                
        # SF2 impact analysis nh3 emission factor
        self.nh3_ef = 0.68  # gnh3 / mmBTU --> default for diesel fuel, changed for other fuel types
        
        # From EPA NONROAD Conversion Factors for Hydrocarbon Emission Components.
        # Convert thc to voc
        self.voc_conversion = 1.053  # --> default for diesel fuel
        
        # Convert pm10 to PM2.5
        # not used at the moment...
        self.pm10topm25 = 0.97  # --> default for diesel fuel
        # convert from gallons to btu.
        # gal_to_btu = 128450  # Btu/gallon
        # -------Inputs End
        
        for run_code in run_codes:
            
            logger.info('Populating NONROAD combustion emissions table for %s' % (run_code, ))
            # path to results
            path = os.path.join(self.base_path, 'OUT', run_code)
            listing = os.listdir(path)

            feedstock = run_code[0:2] 

            # write data to static files for debugging purposes
            f = open(os.path.join(self.base_path, 'OUT', run_code + '.csv'), 'wb')
            writer = csv.writer(f)
            writer.writerow(('FIPS', 'scc', 'hp', 'fuel_cons_gal/yr', 'thc_exh', 'voc_exh', 'co_exh', 'nox_exh',
                            'co2_exh', 'so2_exh', 'pm10_exh', 'pm25_exh', 'nh3_exh', 'Description'))

            queries = []
            for cur_file in listing:
                # use for debugging
                # print "Current file is: %s -- %s" % (run_code, cur_file)
                reader = csv.reader(open(os.path.join(path, cur_file)))

                for i, row in enumerate(reader):
                    # account for headers in file, skip the first 10 lines
                    if i > 9:
                        # row[4] is the vehicle population.
                        if float(row[4]) > 0.0:

                            # _get_description updates the voc_conversion, nh3_ef and lhv for each fuel type
                            scc = row[2]
                            hp = row[3]
                            description, operation = self._get_description(run_code, scc)
                            # check if it is a feedstock and operation that should be recorded.
                            if feedstock == 'FR' or self.operation_dict[feedstock][operation[0]]:
                                # all emissions are recorder in metric tons.
                                # dry ton * metric ton / dry ton = metric ton
                                thc = float(row[5]) * convert_tonne
                                co = float(row[6]) * convert_tonne
                                nox = float(row[7]) * convert_tonne
                                co2 = float(row[8]) * convert_tonne
                                so2 = float(row[9]) * convert_tonne
                                pm10 = float(row[10]) * convert_tonne
                                pm25 = float(row[10]) * self.pm10topm25 * convert_tonne

                                # fuel consumption
                                # NONROAD README 5-10
                                # CNG is a gaseous fuel, and its fuel consumption is reported in gallons at
                                # standard temperature and pressure. This can be misleading if this very large number
                                # is viewed together with the fuel consumption of the other (liquid) fuels
                                # dt/year

                                fuel_cons = float(row[19])  # gal/year

                                voc = thc * self.voc_conversion
                                nh3 = fuel_cons * self.lhv * self.nh3_ef / 1e6  # gal * mmBTU/gal * gnh3/mmBTU = g nh3

                                # allocate non harvest emmisions from cg to cs and ws.
                                if operation and operation[0] == 'N' and feedstock == 'CG':
                                    # add to cs.
                                    if self.operation_dict['CS'][operation[0]] and self.alloc['CS'] != 0:
                                        self._record(feed='CS', row=row[0], scc=scc, hp=hp, fuel_cons=fuel_cons, thc=thc, voc=voc, co=co, nox=nox, co2=co2, so2=so2, pm10=pm10,
                                                     pm25=pm25, nh3=nh3, description=description, run_code=run_code, writer=writer, queries=queries, alloc=self.alloc)
                                    # add to ws.
                                    if self.operation_dict['WS'][operation[0]] and self.alloc['WS'] != 0:
                                        self._record(feed='WS', row=row[0], scc=scc, hp=hp, fuel_cons=fuel_cons, thc=thc, voc=voc, co=co, nox=nox, co2=co2, so2=so2, pm10=pm10,
                                                     pm25=pm25, nh3=nh3, description=description, run_code=run_code, writer=writer, queries=queries, alloc=self.alloc)
                                    # add to corn grain.
                                    self._record(feed=feedstock, row=row[0], scc=scc, hp=hp, fuel_cons=fuel_cons, thc=thc, voc=voc, co=co, nox=nox, co2=co2, so2=so2, pm10=pm10,
                                                 pm25=pm25, nh3=nh3, description=description, run_code=run_code, writer=writer, queries=queries, alloc=self.alloc)
                                # don't change allocation.
                                else:
                                    self._record(feed=feedstock, row=row[0], scc=scc, hp=hp, fuel_cons=fuel_cons, thc=thc, voc=voc, co=co, nox=nox, co2=co2, so2=so2, pm10=pm10,
                                                 pm25=pm25, nh3=nh3, description=description, run_code=run_code, writer=writer, queries=queries, alloc=None)

                                # change constants back to normal, b/c they can be changes in _get_description()
                                self.lhv = 128450.0 / 1e6
                                self.nh3_ef = 0.68
                                self.voc_conversion = 1.053
                                self.pm10topm25 = 0.97

            self.db.input(queries)

            logger.info('Finished populating NONROAD combustion emissions table for %s' % (run_code, ))

    def _record(self, feed, row, scc, hp, fuel_cons, thc, voc, co, nox, co2, so2, pm10, pm25, nh3, description, run_code, writer, queries, alloc=None):
        """
        write data to static files and the database

        :param feed: STRING Feed stock
        :param row:
        :param scc:
        :param hp:
        :param fuel_cons:
        :param thc:
        :param voc:
        :param co:
        :param nox:
        :param co2:
        :param so2:
        :param pm10:
        :param pm25:
        :param nh3:
        :param description:
        :param run_code:
        :param writer:
        :param queries:
        :param alloc:
        :return:
        @param feed:
        @param alloc: dict(string: int) Allocation of non-harvest emissions between cg, cs, and ws
        """

        # multiply the emissions by allocation constant.
        if alloc is not None:
            self.kvals = {'fuel_cons': fuel_cons * alloc[feed],
                          'thc': thc * alloc[feed],
                          'voc': voc * alloc[feed],
                          'co': co * alloc[feed],
                          'nox': nox * alloc[feed],
                          'co2': co2 * alloc[feed],
                          'so2': so2 * alloc[feed],
                          'pm10': pm10 * alloc[feed],
                          'pm25': pm25 * alloc[feed],
                          'nh3': nh3 * alloc[feed],
                          'description': description,
                          'row': row,
                          'scc': scc,
                          'hp': hp,
                          'run_code': run_code,
                          'scenario_name': self.cont.get('model_run_title'),
                          'feed': feed}
        else:
            self.kvals = {'fuel_cons': fuel_cons,
                          'thc': thc,
                          'voc': voc,
                          'co': co,
                          'nox': nox,
                          'co2': co2,
                          'so2': so2,
                          'pm10': pm10,
                          'pm25': pm25,
                          'nh3': nh3,
                          'description': description,
                          'row': row,
                          'scc': scc,
                          'hp': hp,
                          'run_code': run_code,
                          'scenario_name': self.cont.get('model_run_title'),
                          'feed': feed}

        writer.writerow((self.kvals['row'], self.kvals['scc'], self.kvals['hp'], self.kvals['fuel_cons'], self.kvals['thc'], self.kvals['voc'], self.kvals['co'], self.kvals['nox'],
                         self.kvals['co2'], self.kvals['so2'], self.kvals['pm10'], self.kvals['pm25'], self.kvals['nh3'], self.kvals['run_code'],))

        q = """INSERT INTO {scenario_name}.{feed}_raw (fips, scc, hp, thc, voc, co, nox, co2, sox, pm10, pm25, fuel_consumption, nh3, description, run_code)
               VALUES ( {row},
                        {scc},
                        {hp},
                        {thc},
                        {voc},
                        {co},
                        {nox},
                        {co2},
                        {so2},
                        {pm10},
                        {pm25},
                        {fuel_cons},
                        {nh3},
                        '{description}',
                        '{run_code}')""".format(**self.kvals)
        queries.append(q)

    def update_sg(self, run_code):
        """
        Switch grass harvest and non-harvest uses two different machines that are 60 and 130 hp.
        This creates multiple rows in the db for each operation year. To remove the duplicate columns,
        for each fips and for each operation year, add all the same ones and make a single row.
        :param run_code: run code for NONROAD
        """
        # @TODO: what is going on here? why insert and then delete? this doesn't make any sense
        # insert added data to sg_raw.
        logger.info('Inserting data for run code: %s' % (run_code, ))
        self._insert_sg_data()
        # delete old data from sg_raw.
        logger.info('Deleting old SG data for run %s' % (run_code, ))
        self._delete_sg_data()
    
    def _insert_sg_data(self):
        """
        Switch grass harvest and non-harvest uses two different machines that are 60 and 130 hp.
        This creates multiple rows in the db for each operation year. This function creates a single column for each run_code,
        by adding together multiple entries from the different hp's. Adds data to sg_raw.
        """
        # when inserting, leave some of the slots blank that do not matter.
        # @TODO: not sure we should be using 0s for 'blanks'; maybe should use NULL

        self.kvals = self.cont.get('kvals')

        query = """
                INSERT INTO {scenario_name}.sg_raw
                SELECT
                    dat.fips AS fips,
                    '' AS scc,
                    0 AS hp,
                    (raw.fuel_consumption) AS fuel_consumption,
                    0 AS thc,
                    (raw.voc) AS voc,
                    (raw.co) AS co,
                    (raw.nox) AS nox,
                    0 AS co2,
                    (raw.sox) AS sox,
                    (raw.pm10) AS pm10,
                    (raw.pm25) AS pm25,
                    (raw.nh3) AS nh3,
                    raw.description AS description,
                    raw.run_code AS run_code,
                    0 AS fug_pm10,
                    0 AS fug_pm25
                FROM {production_schema}.sg_data dat
                LEFT JOIN (SELECT   DISTINCT fips, run_code, description,
                                    sum(nox)  AS nox,
                                    sum(nh3)  AS nh3,
                                    sum(sox)  AS sox,
                                    sum(voc)  AS voc,
                                    sum(pm10) AS pm10,
                                    sum(pm25) AS pm25,
                                    sum(co)   AS co,
                                    sum(fuel_consumption) AS fuel_consumption
                           FROM {scenario_name}.sg_raw
                           GROUP BY fips, run_code, description) raw ON raw.fips = dat.fips;""".format(**self.kvals)

        self.db.input(query)
    
    def _delete_sg_data(self):
        """
        Deletes unwanted data in sg_raw. b/c of multiple entries for each run_code.
        """
        self.kvals = self.cont.get('kvals')

        query = """
            DELETE FROM {scenario_name}.sg_raw
            WHERE sg_raw.hp != 0 or sg_raw.run_code IS NULL;
            """.format(**self.kvals)

        self.db.input(query)

    def _get_description(self, run_code, scc):
        """

        :param run_code: run code for NONROAD run
        :param scc: source category code for equipment
        :return:
        """

        # in case operation does not get defined.
        operation = ''
        description = ''
        tillage = ''

        # Loading
        if run_code.endswith('L'):
            if run_code.startswith('SG'):
                if len(run_code) == 4:
                    description = "Year %s - Loading" % (run_code[3])  # year 1-9
                else:
                    description = "Year %s - Loading" % (run_code[3:5])  # year 10
                operation = 'Loading'
            else:
                description = 'Loading'
                operation = 'Loading'

        # Switchgrass
        elif run_code.startswith('SG_H'):
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
            # currently no equipment allocated to FR harvest, non-harvest, or on-farm transport
            pass

        # Corn Stover and Wheat Straw
        elif run_code.startswith('CS') or run_code.startswith('WS'):
        
            # get tillage
            if run_code.endswith('RT'):
                tillage = 'Reduced Till'
            elif run_code.endswith('NT'):
                tillage = 'No Till'    
            
            if scc.endswith('5020'):
                operation = 'Harvest'
            elif scc.endswith('5015'):
                operation = 'Transport'
            
            description = tillage + ' - ' + operation
            
        # Corn Grain
        elif run_code.startswith('CG'):
            
            # get tillage
            if run_code.startswith('CG_R'):
                tillage = 'Reduced Till'
                
            elif run_code.startswith('CG_N'):
                tillage = 'No Till'
                
            elif run_code.startswith('CG_C'):
                tillage = 'Conventional Till'
        
            # special case for irrigation
            elif run_code.startswith('CG_I'):
        
                if run_code.endswith('D'):
                    tillage = 'Diesel Irrigation'
                    self.lhv = 128450.0 / 1e6  
                    self.nh3_ef = 0.68  
                    self.voc_conversion = 1.053
                    self.pm10topm25 = 0.97 
                                 
                elif run_code.endswith('L'):
                    tillage = 'LPG Irrigation'
                    self.lhv = 84950.0 / 1e6
                    self.nh3_ef = 0.0  # data not available
                    self.voc_conversion = 0.995
                    self.pm10topm25 = 1.0
                               
                elif run_code.endswith('C'):
                    tillage = 'CNG Irrigation'
                    # 983 btu/ft3 at 1atm and 32F, standard temperature and pressure.
                    self.lhv = 20268.0 / 1e6
                    self.nh3_ef = 0.0  # data not available
                    self.voc_conversion = 0.004
                    self.pm10topm25 = 1.0
                                        
                elif run_code.endswith('G'):
                    tillage = 'Gasoline Irrigation'
                    self.lhv = 116090.0 / 1e6
                    self.nh3_ef = 1.01        
                    self.voc_conversion = 0.933         
                    self.pm10topm25 = 0.92
            
            # get operation (harvest or non-harvest)                                                    
            if run_code.endswith('N') or run_code.startswith('CG_I'):
                operation = 'Non-Harvest'
                
            elif run_code.endswith('H'):
                # get operation (harvest or transport)
                if scc.endswith('5020'):
                    operation = 'Harvest'
                elif scc.endswith('5015'):
                    operation = 'Transport'

            description = tillage + ' - ' + operation    
         
        return description, operation 

if __name__ == '__main__':
    raise NotImplementedError
