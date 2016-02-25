"""
The ScenarioOptions object is used to query production (harvested acres and production) from a database. 
It also contains other useful information such as a scenario title, path to write outputs, and the year
of interest for the data inputs. 
Can be broken into segments of datbase and DOS batching.
Creates the option input files for NONROAD.
"""

import os


class ScenarioOptions:

    def __init__(self, cont):
        # database
        self.db = cont.get('db')
        # query recorder.
        self.qr = cont.get('qr')
        # title of scenario. 
        self._model_run_title = cont.get(key='model_run_title')
        # run codes
        self.run_codes = cont.get('run_codes')
        # directory option file is saved to. Uses run title.
        self.path = cont.get('path')  # non-dev directory
        # break flag used to ensure switchgrass database query only happens once. (all other feedstocks need multiple pulls from the database).
        self.querySG = True
        self.document_file = "Options"
        self._create_dir()
        self.run_code = None
        self.data = None

    def _create_dir(self):        
        """
        Initialize the class by setting up file directory to store data.
        Also creates the batch file to store data.
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)       
            os.makedirs(self.path + "ALLOCATE/")
            os.makedirs(self.path + "POP/")
            os.makedirs(self.path + "OPT/")
            os.makedirs(self.path + "OUT/")
            os.makedirs(self.path + "FIGURES/")
            os.makedirs(self.path + "QUERIES/")

    def document_efs(self, query):
        """
        Executes query and records it to database. Should be emmission final? from constants though.
        @param query: sql query for selecting and recording.
        """        
        fileName = 'Emission Factors'
        for q in query: 
            data = self.db.output(q, self.db.constants_schema)
            self.qr.documentQuery(fileName, data)     

    def get_data(self, run_code):
        """
        Grabs data from the database.
        @param run_code: code to change the current scenario.
        """

        # keep track of current run code.
        self.run_code = run_code

        # query the data and collect it.
        query = self._get_query(run_code)
        if query:
            self.data = self._get_prod_data(query)

        # create output directories
        if not os.path.exists(self.path + '/OUT/' + run_code):
            os.makedirs(self.path + '/OPT/' + run_code)
            os.makedirs(self.path + '/OUT/' + run_code)

    def _get_prod_data(self, query):
        """
        execute the sql statments constructed in _get_query.
        @param query: query to be recorded. 
        """

        # the number of extracted data must be 3109 with no null (blank) returned results.
        # @TODO: add check to enforce expected number of returned records
        return self.db.output(query, self.db.production_schema)

    def _get_query(self, run_code):
        """
        query database for appropriate production data based on run_code
        @param run_code: current run code to know what data to query from the db. 
        @return: query to be executed.
        @attention: propbably do not need to be querying the state from county_attributes, maybe remove later.
        
        @change: Changed where the irrigation data is queried from. 
        Before from cg_irrigated_states.
        current from cg_irrigated_new. Updated data was added to this schema
        
        @change: Changed the query so that it can be used for the updated data.
        """

        query = None

        # corn grain.
        if run_code.startswith('CG'):
            # query conventional till data. For specific state and county.
            # fips, state, harv_ac, prod, yield
            if run_code.startswith('CG_C'):
                query = '''SELECT ca."fips", ca."st", dat."convtill_harv_ac", dat."convtill_prod", dat."convtill_yield"
                FROM "cg_data" dat, ''' + self.db.constants_schema + '''."county_attributes" ca WHERE dat."fips" = ca."fips" ORDER BY ca."fips" ASC;'''
             
            # query reduced till.
            elif run_code.startswith('CG_R'):
                query = '''SELECT ca."fips", ca."st", dat."reducedtill_harv_ac", dat."reducedtill_prod", dat."reducedtill_yield"
                FROM "cg_data" dat, ''' + self.db.constants_schema + '''."county_attributes" ca WHERE dat."fips" = ca."fips" ORDER BY ca."fips" ASC;'''
            
            # query no till data.
            elif run_code.startswith('CG_N'):
                query = '''SELECT ca."fips", ca."st", dat."notill_harv_ac", dat."notill_prod", dat."notill_yield"
                FROM "cg_data" dat, ''' + self.db.constants_schema + '''."county_attributes" ca WHERE dat."fips" = ca."fips" ORDER BY ca."fips" ASC;'''
            
            # grab data for irrigation.  
            elif run_code.startswith('CG_I'):

                # subprocess (WITH statment) is querried in the constant cg_irrigated_states. gets data for different
                # vehicles and their attributes (fuel, horse power.)

                fuel_types = {'D': 'diesel',
                              'G': 'gasoline',
                              'L': 'lpg',
                              'C': 'natgas'}

                fuel_type = fuel_types[run_code[-1]]

                # fuel_type = None
                # if run_code.endswith('D'):
                #     fuel_type = 'diesel'
                # elif run_code.endswith('G'):
                #     fuel_type = 'gasoline'
                # elif run_code.endswith('L'):
                #     fuel_type = 'lpg'
                # elif run_code.endswith('C'):
                #     fuel_type = 'natgas'

                # @TODO: convert config usage
                # @TODO: remove hardcoded schemas
                query = """
                WITH IRR AS (
                    SELECT 
                        "state", "fuel", "hp", "percent" AS "perc", "hrsperacre" AS "hpa"
                    FROM "constantvals"."cg_irrigated_new"
                    WHERE "cg_irrigated_new"."fuel" ILIKE '""" + fuel_type + """'
                )
                SELECT 
                    ca."fips", ca."st", dat."total_harv_ac" * irr."perc" AS "acres", dat."total_prod", irr."fuel", irr."hp", irr."perc", irr."hpa"
                FROM "constantvals"."county_attributes" ca
                LEFT JOIN "bts2dat_55"."cg_data" dat ON ca."fips" = dat."fips"
                LEFT JOIN irr ON irr."state" ILIKE ca."st"
                                
                WHERE ca."st" ILIKE irr."state"
                ORDER BY ca."fips" ASC;
                """  # @TODO: remove hardcoding of schema and tables

        elif run_code.startswith('CS'):
            
            if run_code == 'CS_RT':
                query = '''SELECT ca."fips", ca."st", dat."reducedtill_harv_ac", dat."reducedtill_prod", dat."reducedtill_yield"
                FROM "cs_data" dat, ''' + self.db.constants_schema + '''."county_attributes" ca WHERE dat."fips" = ca."fips" ORDER BY ca."fips" ASC;'''

            elif run_code == 'CS_NT':
                query = '''SELECT ca."fips", ca."st", dat."notill_harv_ac", dat."notill_prod", dat."notill_yield"
                FROM "cs_data" dat, ''' + self.db.constants_schema + '''."county_attributes" ca WHERE dat."fips" = ca."fips" ORDER BY ca."fips" ASC;'''

        elif run_code.startswith('WS'):
            '''
            ######################################################
            @change: 
            In the database there are rows that have produce = 0, while harvested acres and yield are non-zero.
            Need to skip over these faulty data points.
            new code: dat.prod  > 0.0
            ######################################################
            '''
            # @TODO: what is this var used for?
            self.queryTable = 'ws_data'
            
            if run_code == 'WS_RT':
                query = ''' SELECT ca."fips", ca."st", dat."reducedtill_harv_ac", dat."reducedtill_prod", dat."reducedtill_yield"
                            FROM "ws_data" dat, ''' + self.db.constants_schema + '''."county_attributes" ca
                            WHERE dat."fips" = ca."fips" AND dat."prod" > 0.0
                            ORDER BY ca."fips" ASC;'''

            elif run_code == 'WS_NT':
                query = ''' SELECT ca."fips", ca."st", dat."notill_harv_ac", dat."notill_prod", dat."notill_yield"
                            FROM "ws_data" dat, ''' + self.db.constants_schema + '''."county_attributes" ca
                            WHERE dat."fips" = ca."fips" AND dat."prod" > 0.0
                            ORDER BY ca."fips" ASC;'''

        elif run_code.startswith('SG'):
            if self.querySG:
                query = '''SELECT ca."fips", ca."st", dat."harv_ac", dat."prod"
                FROM "sg_data" dat, ''' + self.db.constants_schema + '''."county_attributes" ca WHERE dat."fips" = ca."fips" ORDER BY ca."fips" ASC;'''
                
                # we have 30 scenarios for SG to run, but only want one to query the database once
                self.querySG = False

        elif run_code.startswith('FR'):
            
            if run_code == 'FR':
                query = '''SELECT ca."fips", ca."st", dat."fed_minus_55"
                FROM ''' + self.db.constants_schema + '''."county_attributes" ca, "fr_data" dat WHERE dat."fips" = ca."fips" ORDER BY ca."fips" ASC;'''

        return query


class NROptionFile:
    """
    functions associated with nonroad input files (*.opt files)
    Used to create the .opt file for the NONROAD model to run.

    @note: NONROAD was not processing files with 10 in it so SG_H10, SG_N10, and SG_T10 inputs
    files were being made correct, but not porcessed and saved correctly with NONROAD. Hacked around
    this by saving SG_*10 in the same folder but using inputs from SG_*9. This works b/c SG_*9
    should be the same as SH_*10
    """

    def __init__(self, cont, state, fips, run_code, episode_year):
        """
        Grab important data to be put into the .opt files.
        @param state: state for file.
        @param fips: fips number, which tells you what county you are in.
        @attention: there was a parameter 'allocate' that i removed from init.
        """
        # run code.
        self.run_code = run_code
        # path to the .opt file that is saved.
        self.path = cont.get('path') + 'OPT/' + run_code + '/'  # @TODO: use string formatting and os.sep
        # removed not in use.
        #self.outPathNR = self.path.replace('/', '\\')
        # out path for NONROAD to read.
        self.out_path_pop_alo = cont.get('path').replace('/', '\\')  # @TODO: remove once os.sep usage is implemented
        self.episode_year = episode_year
        self.state = state
        self._model_run_title = cont.get('model_run_title')
        # temperatures.
        self.temp_min = 50.0  # @TODO: remove hardcoded values
        self.temp_max = 68.8  # @TODO: remove hardcoded values
        self.temp_mean = 60.0  # @TODO: remove hardcoded values
        # create .opt file
        self._nr_options(fips)

    def _nr_options(self, fips):
        """
        creates the .opt file.
        @param fips: Geographical Location
        ###############################
        @change: NONROAD was not processing files with 10 in it so SG_H10, SG_N10, and SG_T10 inputs
        files were being made correct, but not processing and saving correctly with NONROAD. Hacked around
        this by saving SG_*10 in the same folder but using inputs from SG_*9
        old code: self.run_code
        new code: run_code = self.run_code
                  if run_code.endswith('0'):
                    # remove the last character.
                    run_code = run_code[:-1]
                    # change the number from 1 to 9
                    split = list(run_code)
                    split[-1] = '9'
                    run_code = "".join(split)
        ###############################
        """
        run_code = self.run_code
        # run_code SG_*10, not working correctly.
        if run_code.endswith('0'):
            # remove the last character.
            run_code = run_code[:-1]
            # change the number from 1 to 9
            split = list(run_code)
            split[-1] = '9'
            run_code = "".join(split)
            
        self._add_opt(fips, run_code)

    def _add_opt(self, fips, new_run_code):
        """
            Add lines to .opt file.
            @param fips: County.
            @param new_run_code: To account for SG_*10 not working.

            @change: Changes made to run NONROAD with SG_*9 and save it as SG_*10.
            Leave folder for output to be the same. Change output file to be run_code given.
            old code: Population File    : ''' + self.out_path_pop_alo + 'POP\\' + self.state + '_' + self.run_code + '''.pop
                  Harvested acres    : ''' + self.out_path_pop_alo + 'ALLOCATE\\' + self.state + '_' + self.run_code + '''.alo
        new code: Population File    : ''' + self.out_path_pop_alo + 'POP\\' + self.state + '_' + new_run_code + '''.pop
                  Harvested acres    : ''' + self.out_path_pop_alo + 'ALLOCATE\\' + self.state + '_' + new_run_code + '''.alo

        """

        with open(self.path + self.state + ".opt", 'w') as self.opt_file:
        
            lines = """
------------------------------------------------------
                  PERIOD PACKET
1  - Char 10  - Period type for this simulation.
                  Valid responses are: ANNUAL, SEASONAL, and MONTHLY
2  - Char 10  - Type of inventory produced.
                  Valid responses are: TYPICAL DAY and PERIOD TOTAL
3  - Integer  - year of episode (4 digit year)
4  - Char 10  - Month of episode (use complete name of month)
5  - Char 10  - Type of day
                  Valid responses are: WEEKDAY and WEEKEND
------------------------------------------------------
/PERIOD/
Period type        : Annual
Summation type     : Period total
Year of episode    : """ + self.episode_year + """
Season of year     :
Month of year      :
Weekday or weekend : Weekday
Year of growth calc:
Year of tech sel   :
/END/

------------------------------------------------------
                  OPTIONS PACKET
1  -  Char 80  - First title on reports
2  -  Char 80  - Second title on reports
3  -  Real 10  - Fuel RVP of gasoline for this simulation
4  -  Real 10  - Oxygen weight percent of gasoline for simulation
5  -  Real 10  - Percent sulfur for gasoline
6  -  Real 10  - Percent sulfur for diesel
7  -  Real 10  - Percent sulfur for LPG/CNG
8  -  Real 10  - Minimum daily temperature (deg. F)
9  -  Real 10  - maximum daily temperature (deg. F)
10 -  Real 10  - Representative average daily temperature (deg. F)
11 -  Char 10  - Flag to determine if region is high altitude
                      Valid responses are: HIGH and LOW
12 -  Char 10  - Flag to determine if RFG adjustments are made
                      Valid responses are: YES and NO
------------------------------------------------------
/OPTIONS/
Title 1            : """ + self._model_run_title + """
Title 2            : All scripts written by Noah Fisher and Jeremy Bohrer
Fuel RVP for gas   : 8.0
Oxygen Weight %    : 2.62
Gas sulfur %       : 0.0339
Diesel sulfur %    : 0.0011
Marine Dsl sulfur %: 0.0435
CNG/LPG sulfur %   : 0.003
Minimum temper. (F): """ + str(self.temp_min) + """
Maximum temper. (F): """ + str(self.temp_max) + """
Average temper. (F): """ + str(self.temp_mean) + """
Altitude of region : LOW
EtOH Blend % Mkt   : 78.8
EtOH Vol %         : 9.5
/END/

------------------------------------------------------
                  REGION PACKET
US TOTAL   -  emissions are for entire USA without state
              breakout.

50STATE    -  emissions are for all 50 states
              and Washington D.C., by state.

STATE      -  emissions are for a select group of states
              and are state-level estimates

COUNTY     -  emissions are for a select group of counties
              and are county level estimates.  If necessary,
              allocation from state to county will be performed.

SUBCOUNTY  -  emissions are for the specified sub counties
              and are subcounty level estimates.  If necessary,
              county to subcounty allocation will be performed.

US TOTAL   -  Nothing needs to be specified.  The FIPS
              code 00000 is used automatically.

50STATE    -  Nothing needs to be specified.  The FIPS
              code 00000 is used automatically.

STATE      -  state FIPS codes

COUNTY     -  state or county FIPS codes.  State FIPS
              code means include all counties in the
              state.

SUBCOUNTY  -  county FIPS code and subregion code.
------------------------------------------------------
/REGION/
Region Level       : COUNTY
All STATE          : """ + fips[0:2] + """000
/END/

or use -
Region Level       : STATE
Michigan           : 26000
------------------------------------------------------

              SOURCE CATEGORY PACKET

This packet is used to tell the model which source
categories are to be processed.  It is optional.
If used, only those source categories list will
appear in the output data file.  If the packet is
not found, the model will process all source
categories in the population files.
------------------------------------------------------
/SOURCE CATEGORY/
                   :2260005000
                   :2265005000
                   :2267005000
                   :2268005000
                   :2270005000
                   :2270007015
/END/
------------------------------------------------------
/RUNFILES/
ALLOC XREF         : data\\allocate\\allocate.xrf
ACTIVITY           : c:\\nonroad\\data\\activity\\activity.dat
EXH TECHNOLOGY     : data\\tech\\tech-exh.dat
EVP TECHNOLOGY     : data\\tech\\tech-evp.dat
SEASONALITY        : data\\season\\season.dat
REGIONS            : data\\season\\season.dat
REGIONS            : data\\season\\season.dat
MESSAGE            : c:\\nonroad\\outputs\\""" + self.state + """.msg
OUTPUT DATA        : """ + self.out_path_pop_alo + 'OUT\\' + self.run_code + '\\' + self.state + """.out
EPS2 AMS           :
US COUNTIES FIPS   : data\\allocate\\fips.dat
RETROFIT           :
/END/

------------------------------------------------------
This is the packet that defines the equipment population
files read by the model.
------------------------------------------------------
/POP FILES/
Population File    : """ + self.out_path_pop_alo + 'POP\\' + self.state + '_' + new_run_code + """.pop
/END/

------------------------------------------------------
This is the packet that defines the growth files
files read by the model.
------------------------------------------------------
/GROWTH FILES/
National defaults  : data\\growth\\nation.grw
/END/


/ALLOC FILES/
Harvested acres    : """ + self.out_path_pop_alo + 'ALLOCATE\\' + self.state + '_' + new_run_code + """.alo
/END/
------------------------------------------------------
This is the packet that defines the emssions factors
files read by the model.
------------------------------------------------------
/EMFAC FILES/
THC exhaust        : data\\emsfac\\exhthc.emf
CO exhaust         : data\\emsfac\\exhco.emf
NOX exhaust        : data\\emsfac\\exhnox.emf
PM exhaust         : data\\emsfac\\exhpm.emf
BSFC               : data\\emsfac\\bsfc.emf
Crankcase          : data\\emsfac\\crank.emf
Spillage           : data\\emsfac\\spillage.emf
Diurnal            : data\\emsfac\\evdiu.emf
Tank Perm          : data\\emsfac\\evtank.emf
Non-RM Hose Perm   : data\\emsfac\\evhose.emf
RM Fill Neck Perm  : data\\emsfac\\evneck.emf
RM Supply/Return   : data\\emsfac\\evsupret.emf
RM Vent Perm       : data\\emsfac\\evvent.emf
Hot Soaks          : data\\emsfac\\evhotsk.emf
RuningLoss         : data\\emsfac\\evrunls.emf
/END/

------------------------------------------------------
This is the packet that defines the deterioration factors
files read by the model.
------------------------------------------------------
/DETERIORATE FILES/
THC exhaust        : data\\detfac\\exhthc.det
CO exhaust         : data\\detfac\\exhco.det
NOX exhaust        : data\\detfac\\exhnox.det
PM exhaust         : data\\detfac\\exhpm.det
Diurnal            : data\\detfac\\evdiu.det
Tank Perm          : data\\detfac\\evtank.det
Non-RM Hose Perm   : data\\detfac\\evhose.det
RM Fill Neck Perm  : data\\detfac\\evneck.det
RM Supply/Return   : data\\detfac\\evsupret.det
RM Vent Perm       : data\\detfac\\evvent.det
Hot Soaks          : data\\detfac\\evhotsk.det
RuningLoss         : data\\detfac\\evrunls.det
/END/

Optional Packets - Add initial slash "/" to activate

/STAGE II/
Control Factor     : 0.0
/END/
Enter percent control: 95 = 95% control = 0.05 x uncontrolled
Default should be zero control.

/MODELYEAR OUT/
EXHAUST BMY OUT    :
EVAP BMY OUT       :
/END/

SI REPORT/
SI report file-CSV :OUTPUTS\NRPOLLUT.CSV
/END/

/DAILY FILES/
DAILY TEMPS/RVP    :
/END/

PM Base Sulfur
 cols 1-10: dsl tech type;
 11-20: base sulfur wt%; or '1.0' means no-adjust (cert= in-use)
/PM BASE SULFUR/
T2        0.0350    0.02247
T3        0.2000    0.02247
T3B       0.0500    0.02247
T4A       0.0500    0.02247
T4B       0.0015    0.02247
T4        0.0015    0.30
T4N       0.0015    0.30
T2M       0.0350    0.02247
T3M       1.0       0.02247
T4M       1.0       0.02247
/END/
"""
            self.opt_file.writelines(lines)
            
            self.opt_file.close()
