"""
The ScenarioOptions object is used to query production (harvested acres and production) from a database. 
It also contains other useful information such as a scenario title, path to write outputs, and the year
of interest for the data inputs. 
Can be broken into segments of datbase and DOS batching.
Creates the option input files for NONROAD.
"""

import os
from utils import config


class ScenarioOptions:

    def __init__(self, cont):
        """

        :param cont:
        :return:
        """

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

        # # break flag used to ensure switchgrass and miscanthus database queries only happens once. (all other feedstocks need multiple pulls from the database).
        # self.query_sg = True
        # self.query_ms = True

        self.document_file = 'Options'
        self._create_dir()
        self.run_code = None
        self.data = None

        self.kvals = cont.get('kvals')

    def _create_dir(self):        
        """
        Initialize the class by setting up file directory to store data.
        Also creates the batch file to store data.
        """

        folders = (self.path,
                   os.path.join(self.path, 'MESSAGES'),
                   os.path.join(self.path, 'ALLOCATE'),
                   os.path.join(self.path, 'POP'),
                   os.path.join(self.path, 'OPT'),
                   os.path.join(self.path, 'OUT'),
                   os.path.join(self.path, 'FIGURES'),
                   os.path.join(self.path, 'QUERIES'))
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)

    def get_data(self, run_code, regional_crop_budget):
        """
        Grabs data from the database

        :param run_code: code to change the current scenario
        :param regional_crop_budget: BOOLEAN process as regional data
        :return:
        """

        # keep track of current run code
        self.run_code = run_code

        # query the data and collect it
        query = self._get_query(run_code, regional_crop_budget)
        if query is not None:
            self.data = self._get_prod_data(query)

    def create_output_dir(self, run_code):
        """
        Create output directories for the given run_code
        :param run_code: code for run type
        :return:
        """

        folders = ('OUT', 'OPT')
        for folder in folders:
            path = os.path.join(self.path, folder, run_code)
            if not os.path.exists(path):
                os.makedirs(path)

    def _get_prod_data(self, query):
        """
        Execute sql statement and return results

        :param query: query to extract data
        :return: list of result rows
        """
        return self.db.output(query)

    def _get_query(self, run_code, regional_crop_budget):
        """
        query database for appropriate production data based on run_code

        :param run_code: STRING current run code to know what data to query from the db
        :param regional_crop_budget: BOOLEAN process as regional data
        :return: STRING query to be executed
        """

        query = None  # must return, in order: county FIPS, state fips, harvested acreage for <tillage>, production for <tillage>, hours_per_year, hp, equipment_type

        # create tillage dictionary
        till_dict = {'C': 'convtill', 'R': 'reducedtill', 'N': 'notill'}

        self.kvals['feed'] = run_code[0:2].lower()
        self.kvals['feed_table'] = self.kvals['feed_tables'][self.kvals['feed']]

        # get CG irrigation data
        if run_code.startswith('CG_I'):

            # dictionary for irrigation fuel types
            fuel_types = {'D': 'diesel',
                          'G': 'gasoline',
                          'L': 'lpg',
                          'C': 'natgas'}

            # set fuel type
            self.kvals['fuel_type'] = fuel_types[run_code[-1]]

            # create query for irrigation data
            query = '''SELECT      ca.fips
                                 , ca.st
                                 , dat.total_harv_ac * irr.perc AS acres
                                 , dat.total_prod
                                 , irr.fuel
                                 , irr.hp
                                 , irr.perc
                                 , irr.hpa
                       FROM      {constants_schema}.county_attributes ca
                       LEFT JOIN {production_schema}.{feed_table}     dat ON ca.fips = dat.fips
                       LEFT JOIN (SELECT   state
                                         , fuel
                                         , hp
                                         , percent    AS perc
                                         , hrsperacre AS hpa
                                  FROM   {constants_schema}.cg_irrigated_states
                                  WHERE  cg_irrigated_states.fuel LIKE '{fuel_type}'
                                 ) irr
                           ON irr.state LIKE ca.st
                       WHERE ca.st LIKE irr.state
                       ORDER BY ca.fips ASC;
            '''.format(**self.kvals)

        else:
            # set tillage type
            if not (self.run_code.startswith('SG') or self.run_code.startswith('MS')):
                if self.run_code[3] == 'R':
                    self.kvals['tillage'] = 'CT'  # reduced tillage equipment is the same as conventional tillage for equipment budgets
                    self.kvals['till_type'] = 'reducedtill'  # till type is for production data so this remains reduced till
                else:
                    self.kvals['tillage'] = '%sT' % (self.run_code[3], )
                    self.kvals['till_type'] = till_dict[run_code[3]]
            elif self.run_code.startswith('SG'):
                self.kvals['till_type'] = 'notill'
                self.kvals['tillage'] = 'NT'
            elif self.run_code.startswith('MS'):
                self.kvals['till_type'] = 'convtill'
                self.kvals['tillage'] = 'CT'

            # @TODO: rewrite run_code parsing; at least MS loading data is not parsed correctly
            # @TODO: even if parsed well, source tables are not loaded with loading data because loading data is not included in agricultural crop budgets (and is subsumed as harvest in forestry)
            # set operation type and activity type from run code
            if self.run_code.startswith('SG') or self.run_code.startswith('MS'):
                self.kvals['activity'] = self.run_code[3]
                if len(self.run_code) > 5:
                    self.kvals['budget_year'] = self.run_code[4:6]
                else:
                    self.kvals['budget_year'] = self.run_code[4]
            else:
                self.kvals['activity'] = self.run_code[4]
                self.kvals['budget_year'] = '1'

            if regional_crop_budget is True:
                # make sql for regional crop budget queries
                query = '''
                           SELECT   fe.fips
                                  , ca.st
                                  , fd.{till_type}_harv_ac
                                  , fd.{till_type}_prod
                                  , fe.equip_type
                                  , fe.hp
                                  , SUM(IFNULL(fe.activity_rate_hrperac * fd.{till_type}_harv_ac, fe.activity_rate_hrperdt * fd.{till_type}_prod)) AS hrs_per_year
                           FROM      {production_schema}.{feed}_equip_fips fe
                           LEFT JOIN {constants_schema}.county_attributes  ca ON  ca.fips = fe.fips
                           LEFT JOIN {production_schema}.{feed_table}      fd ON (fe.fips = fd.fips AND fe.bdgt_id = fd.bdgt)
                           WHERE fe.bdgtyr              = '{budget_year}'
                             AND fe.tillage             = '{tillage}'
                             AND fe.activity         LIKE '{activity}%'
                             AND fe.equip_type         != 'NULL'
                             AND fd.{till_type}_prod    > 0
                           GROUP BY fe.fips, fe.activity, fe.tillage, fe.bdgtyr, fe.equip_type, fe.hp
                        ;'''.format(**self.kvals)
            else:
                raise NotImplementedError('Non-regional crop budgets are deprecated')
                # create query for production data
                # if not (run_code.startswith('SG') or run_code.startswith('MS')) or (self.query_sg is True or self.query_ms is True):
                #     query = '''SELECT ca.fips, ca.st, dat.{till_type}_harv_ac, dat.{till_type}_prod, dat.{till_type}_yield, dat.bdgt
                #                FROM {production_schema}.{feed_table} dat, {constants_schema}.county_attributes ca
                #                WHERE dat.fips = ca.fips  AND dat.{till_type}_prod > 0.0
                #                ORDER BY ca.fips ASC;'''.format(**self.kvals)

                # if run_code.startswith('SG'):
                #     # we have 30 scenarios for SG to run, but only want one to query the database once
                #     self.query_sg = False
                #
                # if run_code.startswith('MS'):
                #     # we have 45 scenarios for MS to run, but only want one to query the database once
                #     self.query_ms = False

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

        :param cont:
        :param state:
        :param fips:
        :param run_code:
        :param episode_year:
        :return:
        """

        # run code
        self.run_code = run_code

        # path to the .opt file that is saved
        self.path = cont.get('path')

        # out path for NONROAD to read
        self.out_path_pop_alo = cont.get('path')

        self.episode_year = episode_year
        self.state = state
        self._model_run_title = cont.get('model_run_title')

        # temperatures
        self.temp_min = config.as_float('nonroad_temp_min')
        self.temp_max = config.as_float('nonroad_temp_max')
        self.temp_mean = config.as_float('nonroad_temp_min')

        # create .opt file
        self._nr_options(fips)

    def _nr_options(self, fips):
        """
        creates the .opt file.

        :param fips: Geographical Location
        :return:

        """
        # ###############################
        # @change: NONROAD was not processing files with 10 in it so SG_H10, SG_N10, and SG_T10 inputs
        # files were being made correct, but not processing and saving correctly with NONROAD. Hacked around
        # this by saving SG_*10 in the same folder but using inputs from SG_*9
        # old code: self.run_code
        # new code: run_code = self.run_code
        #           if run_code.endswith('0'):
        #             # remove the last character.
        #             run_code = run_code[:-1]
        #             # change the number from 1 to 9
        #             split = list(run_code)
        #             split[-1] = '9'
        #             run_code = "".join(split)
        # ###############################

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

    def _add_opt(self, fips, run_code):
        """
        Add lines to .opt file.

        :param fips: county FIPS
        :param run_code: Hack for SQ_*10 run code issues in NONROAD
        :return:
        """

        # @change: Changes made to run NONROAD with SG_*9 and save it as SG_*10.
        # Leave folder for output to be the same. Change output file to be run_code given.
        # old code: Population File    : ''' + self.out_path_pop_alo + 'POP\\' + self.state + '_' + self.run_code + '''.pop
        #       Harvested acres    : ''' + self.out_path_pop_alo + 'ALLOCATE\\' + self.state + '_' + self.run_code + '''.alo
        # new code: Population File    : ''' + self.out_path_pop_alo + 'POP\\' + self.state + '_' + new_run_code + '''.pop
        #           Harvested acres    : ''' + self.out_path_pop_alo + 'ALLOCATE\\' + self.state + '_' + new_run_code + '''.alo

        kvals = {'episode_year': self.episode_year,
                 'state_fips': '{fips:0<5}'.format(fips=fips[0:2]),
                 '_model_run_title': self._model_run_title,
                 'temp_min': self.temp_min,
                 'temp_max': self.temp_max,
                 'temp_mean': self.temp_mean,
                 'ALLOC_XREF': os.path.join(config.get('nonroad_path'), 'data', 'allocate', 'allocate.xrf'),
                 'ACTIVITY': os.path.join(config.get('nonroad_path'), 'data', 'activity', 'activity.dat'),
                 'EXH_TECHNOLOGY': os.path.join(config.get('nonroad_path'), 'data', 'tech', 'tech-exh.dat'),
                 'EVP_TECHNOLOGY': os.path.join(config.get('nonroad_path'), 'data', 'tech', 'tech-evp.dat'),
                 'SEASONALITY': os.path.join(config.get('nonroad_path'), 'data', 'season', 'season.dat'),
                 'REGIONS': os.path.join(config.get('nonroad_path'), 'data', 'season', 'season.dat'),
                 'MESSAGE': os.path.join(self.path, 'MESSAGES', '%s.msg' % (self.state, )),
                 'OUTPUT_DATA': os.path.join(self.out_path_pop_alo, 'OUT', self.run_code, '%s.out' % (self.state, )),
                 'EPS2_AMS': '',
                 'US_COUNTIES_FIPS': os.path.join(config.get('nonroad_path'), 'data', 'allocate', 'fips.dat'),
                 'RETROFIT': '',
                 'Population_File': os.path.join(self.out_path_pop_alo, 'POP', '%s_%s.pop' % (self.state, run_code)),
                 'National_defaults': os.path.join(config.get('nonroad_path'), 'data', 'growth', 'nation.grw'),
                 'Harvested_acres': os.path.join(self.out_path_pop_alo, 'ALLOCATE', '%s_%s.alo' % (self.state, run_code)),
                 'EMFAC_THC_exhaust': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'exhthc.emf'),
                 'EMFAC_CO_exhaust': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'exhco.emf'),
                 'EMFAC_NOX_exhaust': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'exhnox.emf'),
                 'EMFAC_PM_exhaust': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'exhpm.emf'),
                 'EMFAC_BSFC': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'bsfc.emf'),
                 'EMFAC_Crankcase': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'crank.emf'),
                 'EMFAC_Spillage': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'spillage.emf'),
                 'EMFAC_Diurnal': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'evdiu.emf'),
                 'EMFAC_Tank_Perm': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'evtank.emf'),
                 'EMFAC_Non_RM_Hose_Perm': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'evhose.emf'),
                 'EMFAC_RM_Fill_Neck_Perm': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'evneck.emf'),
                 'EMFAC_RM_Supply_Return': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'evsupret.emf'),
                 'EMFAC_RM_Vent_Perm': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'evvent.emf'),
                 'EMFAC_Hot_Soaks': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'evhotsk.emf'),
                 'EMFAC_RuningLoss': os.path.join(config.get('nonroad_path'), 'data', 'emsfac', 'evrunls.emf'),
                 'DETERIORATE_THC_exhaust': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'exhthc.det'),
                 'DETERIORATE_CO_exhaust': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'exhco.det'),
                 'DETERIORATE_NOX_exhaust': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'exhnox.det'),
                 'DETERIORATE_PM_exhaust': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'exhpm.det'),
                 'DETERIORATE_Diurnal': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'evdiu.det'),
                 'DETERIORATE_Tank_Perm': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'evtank.det'),
                 'DETERIORATE_Non_RM_Hose_Perm': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'evhose.det'),
                 'DETERIORATE_RM_Fill_Neck_Perm': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'evneck.det'),
                 'DETERIORATE_RM_Supply_Return': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'evsupret.det'),
                 'DETERIORATE_RM_Vent_Perm': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'evvent.det'),
                 'DETERIORATE_Hot_Soaks': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'evhotsk.det'),
                 'DETERIORATE_RuningLoss': os.path.join(config.get('nonroad_path'), 'data', 'detfac', 'evrunls.det'),
                 'EXHAUST_BMY_OUT': '',
                 'EVAP_BMY_OUT': '',
                 'SI_report_file_CSV': os.path.join(self.path, 'MESSAGES', 'NRPOLLUT.csv'),
                 'DAILY_TEMPS_RVP': ''
                 }

        f = os.path.join(self.path, 'OPT', run_code, '%s.opt' % (self.state,))
        with open(f, 'w') as self.opt_file:

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
Year of episode    : {episode_year}
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
Title 1            : {_model_run_title}
Title 2            :
Fuel RVP for gas   : 8.0
Oxygen Weight %    : 2.62
Gas sulfur %       : 0.0339
Diesel sulfur %    : 0.0011
Marine Dsl sulfur %: 0.0435
CNG/LPG sulfur %   : 0.003
Minimum temper. (F): {temp_min}
Maximum temper. (F): {temp_max}
Average temper. (F): {temp_mean}
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
All STATE          : {state_fips}
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
                   :2270002069
                   :2270004066
                   :2270004020
/END/

------------------------------------------------------
/RUNFILES/
ALLOC XREF         : {ALLOC_XREF}
ACTIVITY           : {ACTIVITY}
EXH TECHNOLOGY     : {EXH_TECHNOLOGY}
EVP TECHNOLOGY     : {EVP_TECHNOLOGY}
SEASONALITY        : {SEASONALITY}
REGIONS            : {REGIONS}
MESSAGE            : {MESSAGE}
OUTPUT DATA        : {OUTPUT_DATA}
EPS2 AMS           : {EPS2_AMS}
US COUNTIES FIPS   : {US_COUNTIES_FIPS}
RETROFIT           : {RETROFIT}
/END/

------------------------------------------------------
This is the packet that defines the equipment population
files read by the model.
------------------------------------------------------
/POP FILES/
Population File    : {Population_File}
/END/

------------------------------------------------------
This is the packet that defines the growth files
files read by the model.
------------------------------------------------------
/GROWTH FILES/
National defaults  : {National_defaults}
/END/

/ALLOC FILES/
Harvested acres    : {Harvested_acres}
/END/

------------------------------------------------------
This is the packet that defines the emssions factors
files read by the model.
------------------------------------------------------
/EMFAC FILES/
THC exhaust        : {EMFAC_THC_exhaust}
CO exhaust         : {EMFAC_CO_exhaust}
NOX exhaust        : {EMFAC_NOX_exhaust}
PM exhaust         : {EMFAC_PM_exhaust}
BSFC               : {EMFAC_BSFC}
Crankcase          : {EMFAC_Crankcase}
Spillage           : {EMFAC_Spillage}
Diurnal            : {EMFAC_Diurnal}
Tank Perm          : {EMFAC_Tank_Perm}
Non-RM Hose Perm   : {EMFAC_Non_RM_Hose_Perm}
RM Fill Neck Perm  : {EMFAC_RM_Fill_Neck_Perm}
RM Supply/Return   : {EMFAC_RM_Supply_Return}
RM Vent Perm       : {EMFAC_RM_Vent_Perm}
Hot Soaks          : {EMFAC_Hot_Soaks}
RuningLoss         : {EMFAC_RuningLoss}
/END/

------------------------------------------------------
This is the packet that defines the deterioration factors
files read by the model.
------------------------------------------------------
/DETERIORATE FILES/
THC exhaust        : {DETERIORATE_THC_exhaust}
CO exhaust         : {DETERIORATE_CO_exhaust}
NOX exhaust        : {DETERIORATE_NOX_exhaust}
PM exhaust         : {DETERIORATE_PM_exhaust}
Diurnal            : {DETERIORATE_Diurnal}
Tank Perm          : {DETERIORATE_Tank_Perm}
Non-RM Hose Perm   : {DETERIORATE_Non_RM_Hose_Perm}
RM Fill Neck Perm  : {DETERIORATE_RM_Fill_Neck_Perm}
RM Supply/Return   : {DETERIORATE_RM_Supply_Return}
RM Vent Perm       : {DETERIORATE_RM_Vent_Perm}
Hot Soaks          : {DETERIORATE_Hot_Soaks}
RuningLoss         : {DETERIORATE_RuningLoss}
/END/

Optional Packets - Add initial slash "/" to activate

/STAGE II/
Control Factor     : 0.0
/END/
Enter percent control: 95 = 95% control = 0.05 x uncontrolled
Default should be zero control.

/MODELYEAR OUT/
EXHAUST BMY OUT    : {EXHAUST_BMY_OUT}
EVAP BMY OUT       : {EVAP_BMY_OUT}
/END/

SI REPORT/
SI report file-CSV : {SI_report_file_CSV}
/END/

/DAILY FILES/
DAILY TEMPS/RVP    : {DAILY_TEMPS_RVP}
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
""".format(**kvals)

            self.opt_file.writelines(lines)

            self.opt_file.close()
