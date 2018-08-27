import os
import pandas as pd
import numpy as np

from Module import Module
from FPEAM import utils

LOGGER = utils.logger(name=__name__)

class NONROAD(Module):
    
    def __init__(self, config, production, equipment, year,
                 nonroad_equipment, **kvals):

        # init parent
        super(NONROAD, self).__init__(config=config)

        # store input arguments in self
        self.production = production
        self.equipment = equipment
        self.year = year
        self.model_run_title = config.get('scenario_name')
        self.project_path = os.path.join(config.get('project_path'),
                                         self.model_run_title)

        # store nonroad parameters in self
        self.temp_min = config.get('nonroad_temp_min')
        self.temp_mean = config.get('nonroad_temp_mean')
        self.temp_max = config.get('nonroad_temp_max')
        self.nonroad_path = config.get('nonroad_path')
        self.time_resource_name = config.get('time_resource_name')
        self.nonroad_feedstock_measure = config.get(
            'nonroad_feedstock_measure')
        # @todo this is a dataframe of equipment names matching the
        # equipment input and SCC codes from nonroad, pulled in from csv
        self.nonroad_equipment = config.get('nonroad_equipment')

        # @todo create dirs if they do not exist


    # def __enter__(self):
    #     return self
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     # process exceptions
    #     if exc_type is not None:
    #         LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
    #         return False
    #     else:
    #         return self

    def create_allocate_file(self):
        """
        write spatial indicators to .alo file for the NonRoad program to
        use. File are written on a state-level basis.
        :return: None
        """





    def create_options_file(self, fips):
        """
        creates options file by filling in a template with values from
        config, production and equipment
        :return: None
        """

        _state = str(fips)[0:2]

        kvals = {'episode_year': self.year,
                 'state_fips': '{fips:0<5}'.format(fips=fips[0:2]),
                 'model_run_title': self.model_run_title,
                 'temp_min': self.temp_min,
                 'temp_max': self.temp_max,
                 'temp_mean': self.temp_mean,
                 # @todo check that the alloc_xref is OK, it comes from an
                 # old code version
                 'ALLOC_XREF': os.path.join(self.nonroad_path, 'data',
                                            'allocate', 'allocate.xrf'),
                 'ACTIVITY': os.path.join(self.nonroad_path,
                                          'data', 'activity', 'activity.dat'),
                 'EXH_TECHNOLOGY': os.path.join(self.nonroad_path,
                                                'data', 'tech',
                                                'tech-exh.dat'),
                 'EVP_TECHNOLOGY': os.path.join(self.nonroad_path,
                                                'data', 'tech',
                                                'tech-evp.dat'),
                 'SEASONALITY': os.path.join(self.nonroad_path,
                                             'data', 'season', 'season.dat'),
                 'REGIONS': os.path.join(self.nonroad_path,
                                         'data', 'season', 'season.dat'),
                 'MESSAGE': os.path.join(self.project_path, 'MESSAGES',
                                         '%s.msg' % (_state,)),
                 # @todo changed dir name from runcode to fips
                 'OUTPUT_DATA': os.path.join(self.out_path_pop_alo, 'OUT',
                                             fips, '%s.out' % (_state,)),
                 'EPS2_AMS': '',
                 'US_COUNTIES_FIPS': os.path.join(self.nonroad_path, 'data',
                                                  'allocate', 'fips.dat'),
                 'RETROFIT': '',
                 'Population_File': os.path.join(self.out_path_pop_alo,
                                                 'POP', '%s_%s.pop' % (fips)),
                 'National_defaults': os.path.join(self.nonroad_path, 'data',
                                                   'growth', 'nation.grw'),
                 'Harvested_acres': os.path.join(self.out_path_pop_alo,
                                                 'ALLOCATE',
                                                 '%s_%s.alo' % (fips)),
                 'EMFAC_THC_exhaust': os.path.join(self.nonroad_path, 'data',
                                                   'emsfac', 'exhthc.emf'),
                 'EMFAC_CO_exhaust': os.path.join(self.nonroad_path, 'data',
                                                  'emsfac', 'exhco.emf'),
                 'EMFAC_NOX_exhaust': os.path.join(self.nonroad_path, 'data',
                                                   'emsfac', 'exhnox.emf'),
                 'EMFAC_PM_exhaust': os.path.join(self.nonroad_path, 'data',
                                                  'emsfac', 'exhpm.emf'),
                 'EMFAC_BSFC': os.path.join(self.nonroad_path, 'data',
                                            'emsfac', 'bsfc.emf'),
                 'EMFAC_Crankcase': os.path.join(self.nonroad_path, 'data',
                                                 'emsfac', 'crank.emf'),
                 'EMFAC_Spillage': os.path.join(self.nonroad_path, 'data',
                                                'emsfac', 'spillage.emf'),
                 'EMFAC_Diurnal': os.path.join(self.nonroad_path, 'data',
                                               'emsfac', 'evdiu.emf'),
                 'EMFAC_Tank_Perm': os.path.join( self.nonroad_path, 'data',
                                                  'emsfac', 'evtank.emf'),
                 'EMFAC_Non_RM_Hose_Perm': os.path.join( self.nonroad_path,
                                                         'data', 'emsfac',
                                                         'evhose.emf'),
                 'EMFAC_RM_Fill_Neck_Perm': os.path.join(self.nonroad_path,
                                                         'data', 'emsfac',
                                                         'evneck.emf'),
                 'EMFAC_RM_Supply_Return': os.path.join(self.nonroad_path,
                                                        'data', 'emsfac',
                                                        'evsupret.emf'),
                 'EMFAC_RM_Vent_Perm': os.path.join(self.nonroad_path, 'data',
                                                    'emsfac', 'evvent.emf'),
                 'EMFAC_Hot_Soaks': os.path.join(self.nonroad_path, 'data',
                                                 'emsfac', 'evhotsk.emf'),
                 'EMFAC_RuningLoss': os.path.join(self.nonroad_path,
                                                  'data', 'emsfac',
                                                  'evrunls.emf'),
                 'DETERIORATE_THC_exhaust': os.path.join(self.nonroad_path,
                                                         'data', 'detfac',
                                                         'exhthc.det'),
                 'DETERIORATE_CO_exhaust': os.path.join(self.nonroad_path,
                                                        'data', 'detfac',
                                                        'exhco.det'),
                 'DETERIORATE_NOX_exhaust': os.path.join(self.nonroad_path,
                                                         'data', 'detfac',
                                                         'exhnox.det'),
                 'DETERIORATE_PM_exhaust': os.path.join(self.nonroad_path,
                                                        'data', 'detfac',
                                                        'exhpm.det'),
                 'DETERIORATE_Diurnal': os.path.join(self.nonroad_path,
                                                     'data', 'detfac',
                                                     'evdiu.det'),
                 'DETERIORATE_Tank_Perm': os.path.join(self.nonroad_path,
                                                       'data', 'detfac',
                                                       'evtank.det'),
                 'DETERIORATE_Non_RM_Hose_Perm': os.path.join(
                     self.nonroad_path, 'data', 'detfac', 'evhose.det'),
                 'DETERIORATE_RM_Fill_Neck_Perm': os.path.join(
                     self.nonroad_path, 'data', 'detfac', 'evneck.det'),
                 'DETERIORATE_RM_Supply_Return': os.path.join(
                     self.nonroad_path, 'data', 'detfac', 'evsupret.det'),
                 'DETERIORATE_RM_Vent_Perm': os.path.join(self.nonroad_path,
                                                          'data', 'detfac',
                                                          'evvent.det'),
                 'DETERIORATE_Hot_Soaks': os.path.join(self.nonroad_path,
                                                       'data', 'detfac',
                                                       'evhotsk.det'),
                 'DETERIORATE_RuningLoss': os.path.join(self.nonroad_path,
                                                        'data', 'detfac',
                                                        'evrunls.det'),
                 'EXHAUST_BMY_OUT': '',
                 'EVAP_BMY_OUT': '',
                 'SI_report_file_CSV': os.path.join(self.project_path,
                                                    'MESSAGES',
                                                    'NRPOLLUT.csv'),
                 'DAILY_TEMPS_RVP': ''
                 }

        f = os.path.join(self.project_path, 'OPT', fips, '%s.opt' % (_state,))
        with open(f, 'w') as _opt_file:
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
        Title 1            : {model_run_title}
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

        _opt_file.writelines(lines)

        _opt_file.close()

    def create_population_file(self):
        """
        Calculates [level?] populations of all equipment from
        operation-hours found in the equipment input and the annual hours of
        operation from the MOVES database
        :return: None
        """




