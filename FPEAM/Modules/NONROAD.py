import os
import pymysql
import pandas as pd
import numpy as np

from .Module import Module
from FPEAM import utils

LOGGER = utils.logger(name=__name__)


class NONROAD(Module):
    
    def __init__(self, config, production, equipment, year,
                 region_nonroad_fips_map, nonroad_equipment, **kvals):

        # init parent
        super(NONROAD, self).__init__(config=config)

        # store input arguments in self
        self.production = production
        self.equipment = equipment
        self.year = year

        # add year as an extra column in production
        self.production['year'] = self.year

        # @TODO update to match the correct name in the config file
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
        # @note this is a dataframe of equipment names matching the
        # equipment input and SCC codes from nonroad, pulled in from csv
        self.nonroad_equipment = nonroad_equipment
        self.region_nonroad_fips_map = region_nonroad_fips_map


        # moves database parameters
        self.moves_database = config.get('moves_database')

        # open connection to MOVES default database for input/output
        self.moves_con = pymysql.connect(host=config.get('moves_db_host'),
                                         user=config.get('moves_db_user'),
                                         password=config.get('moves_db_pass'),
                                         db=config.get('moves_database'),
                                         local_infile=True)

        # create dirs in the project path (which includes the scenario name)
        #  if the directories do not already exist
        _nr_folders = [self.project_path,
                       os.path.join(self.project_path, 'MESSAGES'),
                       os.path.join(self.project_path, 'ALLOCATE'),
                       os.path.join(self.project_path, 'POP'),
                       os.path.join(self.project_path, 'OPT'),
                       os.path.join(self.project_path, 'OUT'),
                       os.path.join(self.project_path, 'FIGURES'),
                       os.path.join(self.project_path, 'QUERIES')]
        for _folder in _nr_folders:
            if not os.path.exists(_folder):
                os.makedirs(_folder)


    def create_allocate_files(self):
        """
        write spatial indicators to .alo file for the NonRoad program to
        use. File are written on a state-level basis.
        :return: None
        """
        
        # @todo verify that NONROAD needs the allocation file to run,
        # and what it does if so


    def create_options_files(self, fips):
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
                 # @note changed dir name from runcode to fips
                 # @todo use fips-feedstock(-tillage-activitytype?) combination
                 'OUTPUT_DATA': os.path.join(self.project_path, 'OUT',
                                             fips, '%s.out' % (_state,)),
                 'EPS2_AMS': '',
                 'US_COUNTIES_FIPS': os.path.join(self.nonroad_path, 'data',
                                                  'allocate', 'fips.dat'),
                 'RETROFIT': '',
                 'Population_File': os.path.join(self.project_path,
                                                 'POP', '%s_%s.pop' % (fips)),
                 'National_defaults': os.path.join(self.nonroad_path, 'data',
                                                   'growth', 'nation.grw'),
                 'Harvested_acres': os.path.join(self.project_path,
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


    def write_population_file_line(self, df):
        """
        Function for applying over the rows of a dataframe containing all
        relevant NONROAD equipment population data
        :return: None
        """

        kvals = {'fips': df.NONROAD_fips,
                 'sub_reg': '',
                 'year': self.year,
                 'scc_code': df.SCC,
                 'equip_desc': df.equipment_description,
                 'min_hp': df.hpMin,
                 'max_hp': df.hpMax,
                 'avg_hp': df.hpAvg,
                 'life': df.equipment_lifetime,
                 'flag': 'DEFAULT',
                 'pop': df.equipment_population}

        _string_to_write = '{fips:0>5} {sub_reg:>5} {year:>4} {scc_code:>10} {equip_desc:<40} {min_hp:>5} {max_hp:>5} {avg_hp:>5.1f} {life:>5} {flag:<10} {pop:>17.7f} \n'.format(**kvals)

        self.pop_file.writelines(_string_to_write)

        return None


    def create_population_files(self):
        """
        Calculates [level?] populations of all equipment from
        operation-hours found in the equipment input and the annual hours of
        operation from the MOVES database
        :return: None
        """

        ## preprocess and merge equipment and production dfs

        # filter down production and equipment to nonroad-relevant values
        _prod_filter = self.production.feedstock_measure == \
                      self.nonroad_feedstock_measure
        _equip_filter = self.equipment.resource == self.time_resource_name

        # apply filter to production and equipment
        _prod_filtered = self.production[_prod_filter]
        _equip_filtered = self.equipment[_equip_filter]

        # merge production with the region_production-fips map for NONROAD fips
        _prod_nr_fips = _prod_filtered.merge(self.region_nonroad_fips_map,
                                             how='inner',
                                             on='region_production')

        # add column with state derived from NONROAD fips column
        _prod_nr_fips['state'] = _prod_nr_fips.NONROAD_fips.str.slice(stop=2)

        # sum resource rates over rotation year to prep for calculating
        # average rates
        _equip_grouped = _equip_filtered.groupby(['feedstock',
                                                  'state', 'tillage_type',
                                                  'equipment_group',
                                                  'activity', 'equipment_name',
                                                  'equipment_horsepower'],
                                                 as_index=False).sum()

        # find the maximum rotation year within groups for calculating
        # average rates
        _max_year = _equip_filtered.groupby(['feedstock', 'tillage_type',
                                             'equipment_group'],
                                            as_index=False).max()[[
            'feedstock', 'tillage_type', 'equipment_group', 'rotation_year']]

        # rename rotation year to max rotation year to avoid confusion
        _max_year.rename(index=str, columns={'rotation_year':
                                                 'max_rotation_year'},
                         inplace=True)

        # rename rate column to total rate
        _equip_grouped.rename(index=str,
                              columns={'rate': 'total_rotation_rate'},
                              inplace=True)

        # remove rotation_year column so it can be replaced with the maximum
        #  rotation year
        del _equip_grouped['rotation_year']

        # combine the total rate df with the maximum rotation year df
        _equip_avg = _equip_grouped.merge(_max_year, how='left',
                                          on=['feedstock', 'tillage_type',
                                              'equipment_group'])

        # calculate average rate from total rotation rate and max rotation year
        _equip_avg.eval('average_rate = total_rotation_rate / '
                        'max_rotation_year',
                        inplace=True)

        # merge prod and the equip with average rates on feedstock, tillage
        # type and equipment group
        # note that how='left' and how='inner' produce the same merged df in
        #  this step
        _prod_equip_merge = _prod_nr_fips.merge(_equip_avg,
                                                how='inner',
                                                on=['feedstock',
                                                    'tillage_type',
                                                    'equipment_group'])

        # calculate total hours for each equipment type - activity type combo
        _prod_equip_merge.eval('total_annual_rate = feedstock_amount * '
                               'average_rate',
                               inplace=True)

        # assemble kvals for sql statement formatting
        kvals = {}
        kvals['moves_database'] = self.moves_database

        # read in nrsourceusetype table to get the hp range IDs, hp averages,
        # and hours used per year (annual activity used to calculate
        # population) by SCC
        _nrsourceusetype_sql = """SELECT SCC, NRHPRangeBinID, 
            medianLifeFullLoad, hoursUsedPerYear, hpAvg
            FROM {moves_database}.nrsourceusetype;""".format(**kvals)

        _nrsourceusetype = pd.read_sql(_nrsourceusetype_sql, self.moves_con)

        # rename the equipment lifetime column
        _nrsourceusetype.rename(index=str,
                                columns={'medianLifeFullLoad':
                                             'equipment_lifetime'},
                                inplace=True)

        # filter down the nrsourceusetype table based on the list of
        # equipment in user-provided nonroad_equipment
        _scc_filter = _nrsourceusetype.SCC.isin(
            self.nonroad_equipment.nonroad_equipment_scc)

        _nrsourceusetype_filtered = _nrsourceusetype[_scc_filter]

        # read in nrhprangebin that matches hp range IDs to hp min and max
        # values
        _nrhprangebin_sql = """SELECT NRHPRangeBinID, hpMin, hpMax
                        FROM {moves_database}.nrhprangebin""".format(**kvals)

        _nrhprangebin = pd.read_sql(_nrhprangebin_sql, self.moves_con)

        # merge the nonroad_equipment, nrsourceusetype and nrhprangebin
        # together to generate a df of information needed in the population
        # file
        # the dropna is because the default nonroad_equipment file has many
        # missing values; it won't impact a file with no missing values
        _nr_pop_info = self.nonroad_equipment.dropna().merge(_nrsourceusetype,
                                                             how='inner',
                                                             left_on='nonroad_equipment_scc',
                                                             right_on='SCC').merge(
                                                        _nrhprangebin,
                                                        how='inner',
                                                        on='NRHPRangeBinID')

        _nr_equip_filter = _equip_avg[['equipment_name',
                                       'equipment_horsepower']].drop_duplicates()

        _nr_pop_info_filtered = _nr_pop_info.merge(_nr_equip_filter,
                                                   how='inner',
                                                   on='equipment_name')

        # create horsepower filter based on comparing the equipment hp to hp
        #  bins - this is to avoid multiple entries with different hp
        # ranges for each piece of equipment
        _hp_filter = ((_nr_pop_info_filtered.equipment_horsepower >=
                       _nr_pop_info_filtered.hpMin) & (
                _nr_pop_info_filtered.equipment_horsepower <=
                _nr_pop_info_filtered.hpMax))

        _nr_pop_info_filtered = _nr_pop_info_filtered[_hp_filter]

        # merge the nr population info with equipment before calculating equipment
        # population from actual activity hours and hours-per-year from nonroad
        _nr_pop_equip_merge = _prod_equip_merge.merge(_nr_pop_info_filtered,
                                                      how='left',
                                                      on=['equipment_name',
                                                          'equipment_horsepower'])

        # calculate the equipment population from the annual rate (from the
        # equipment input data) and the hours used per year (from nonroad
        # defaults)
        _nr_pop_equip_merge.eval('equipment_population = total_annual_rate / '
                                 'hoursUsedPerYear', inplace=True)

        # keep only the columns relevant to either the population file name
        # or file contents
        _nr_pop = _nr_pop_equip_merge[['state', 'feedstock', 'tillage_type',
                                       'activity', 'NONROAD_fips', 'year',
                                       'SCC', 'equipment_description',
                                       'hpMin', 'hpMax', 'hpAvg',
                                       'equipment_lifetime']]

        ## use population info to construct population files

        # set path to population file for this scenario
        # project_path already contains the scenario name
        _pop_dir = os.path.join(self.project_path, 'POP')

        _pop_files = _nr_pop[['state', 'feedstock', 'tillage_type',
                              'activity']].drop_duplicates()

        # open, create and close all population files for a scenario
        for _file in np.arange(_pop_files.shape[0]):
            _nr_pop_filter = (_nr_pop.state == _pop_files.state[_file]) & (
                _nr_pop.feedstock == _pop_files.feedstock[_file]) & (
                _nr_pop.tillage_type == _pop_files.tillage_type[_file]) & (
                _nr_pop.activity == _pop_files.activity[_file])

            _nr_pop_sub = _nr_pop[_nr_pop_filter]

            _state = _pop_files.state[_file]
            _feedstock = _pop_files.feedstock[_file]
            _tillage_type = _pop_files.tillage_type[_file]
            _activity = _pop_files.activity[_file]

            path = os.path.join(_pop_dir, '%s_%s_%s_%s.pop' % (_state,
                                                               _feedstock,
                                                               _tillage_type,
                                                               _activity))

            self.pop_file = open(path, 'w')

            _opening_lines = """
            ------------------------------------------------------------------------------
              1 -   5   FIPS code
              7 -  11   subregion code (used for subcounty estimates)
             13 -  16   year of population estimates
             18 -  27   SCC code (no globals accepted)
             29 -  68   equipment description (ignored)
             70 -  74   minimum HP range
             76 -  80   maximum HP range (ranges must match those internal to model)
             82 -  86   average HP in range (if blank model uses midpoint)
             88 -  92   expected useful life (in hours of use)
             93 - 102   flag for scrappage distribution curve (DEFAULT = standard curve)
            106 - 122   population estimate

            FIPS       Year  SCC        Equipment Description                    HPmn  HPmx HPavg  Life ScrapFlag     Population
            ------------------------------------------------------------------------------
            /POPULATION/
            """
            self.pop_file.writelines(_opening_lines)

            # @todo apply_along_axis to write data lines
            # ignore the output, file lines are written within the function
            # being applied along the rows of _nr_pop_sub
            _output = np.apply_along_axis(self.write_population_file_line, 0,
                                          _nr_pop_sub)

            _ending_line = '/END/'

            self.pop_file.writelines(_ending_line)

            self.pop_file.close()








