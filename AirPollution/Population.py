"""
functions associated with population
"""

# import abc
# from _pyio import __metaclass__
from src.AirPollution.utils import config, logger


class Population(object):
    """
    The 'Population' class is used to write the .pop files for the nonroad program.
    The 'append_pop' is an abstract method determines writes the equipment lists
    and population to the .pop file. It is defined in each of the feedstockPOP
    classes.
    """

    def __init__(self, cont, episode_year, run_code):
        """
        Include key variables for creating population files.
        @param cont: container
        @param episode_year: Year for modeling.
        @param run_code: run code. Determines which subclass to make.
        """

        self.episode_year = episode_year

        self.path = cont.get(key='path') + 'POP/'

        self.run_code = run_code

        # Used in all agricultural feedstocks (i.e. not FR)
        self.activity_tractor = float(config.get('nonroad_equip_dict')['annual_hrs_operation']['tractor'])              # hr / year (NonRoad default value)
        # Corn Grain
        self.activity_combine = float(config.get('nonroad_equip_dict')['annual_hrs_operation']['combine'])              # hr / year (NonRoad default values)
        self.activity_gas = 716.0                  # hr / year (NonRoad default values)
        self.activity_diesel = 749.0               # hr / year (NonRoad default values)
        self.activity_lpg = 716.0                  # hr / year (NonRoad default values)
        self.activity_cng = 716.0                  # hr / year (NonRoad default values)

        # data from personal communication with Anthony Turhollow for SG.
        # It is assumed that the transport time for one bale of SG is the same as for one bale of CS or WS)
        self.transport_bales = 20.0                   # dt/hr

        self.pop_file = None

    def initialize_pop(self, dat):
        """
        This function creates the .POP file with the correct syntax and population estimates
        Inputs: State FIPS number (string), state abbreviation (string), and population estimate by SCC (float)
        Output: A file is created containing a nonroad appropriate population file
        """
        state = dat[1]
        path = self.path + '%s_%s.pop' % (state, self.run_code)
        self.pop_file = open(path, 'w')
        lines = """
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
        self.pop_file.writelines(lines)

    # __metaclass__ = abc.ABCMeta
    # @abc.abstractmethod
    def append_pop(self, fips, indicator1):
        """
        Inputs: data list read from psycopg2 table query
        Output: calculate equpipment population for each county
        """
        raise NotImplementedError("Should have implemented this")

    def finish_pop(self):
        """
        This function finishes the POP_file.  It closes the file and appends the '/END/'
            data label to the file.
        Inputs: POP_file to close
        Outputs: finishes file with '/END/' and closes the file.
        """
        lines = """/END/"""
        self.pop_file.writelines(lines)
        self.pop_file.close()

    def _get_combine_hours_per_acre(self, scenario_yield):
        """
        Find machinery hours based on yield.
        @param scenario_yield: Yield from feed stock. lbs/acre
        @return: Combine hours per acre. hrs/acre
        """
        # find machinery hours based on yield
        hours_per_acre_comb = None
        if scenario_yield <= 0.5:
            hours_per_acre_comb = 0.076388889
        elif scenario_yield <= 1.0:
            hours_per_acre_comb = 0.076388889
        elif scenario_yield <= 1.5:
            hours_per_acre_comb = 0.101626016
        elif scenario_yield <= 2.0:
            hours_per_acre_comb = 0.135501355
        elif scenario_yield <= 2.5:
            hours_per_acre_comb = 0.169376694
        elif scenario_yield <= 3.0:
            hours_per_acre_comb = 0.203252033
        elif scenario_yield <= 3.5:
            hours_per_acre_comb = 0.237127371
        elif scenario_yield <= 4.0:
            hours_per_acre_comb = 0.27100271
        elif scenario_yield <= 4.5:
            hours_per_acre_comb = 0.304878049
        elif scenario_yield > 4.5:
            hours_per_acre_comb = 0.338753388

        return hours_per_acre_comb

# Sub classes of population for each unique crop.
# @TODO: Should try to standarize what is in the dat[] array with a variable for each index. ex. state = dat[1]


class ResiduePop(Population):
    """
    Calculates equipment populations for corn stover and wheat straw residue collection.
    CS, WS
    Residues have harvest and transports emmisions, but none for non-harvest.
    Because these are residues, so the emmisions are going to corn grain.
    """

    def __init__(self, cont, episode_year, run_code):
        Population.__init__(self, cont, episode_year, run_code)

    def append_pop(self, fips, dat):
        """
        Calulates the population of combines and tractors needed.
        Then writes them to a population file.
        @param fips: fips county code. (string)
        @param dat: Data from the db containing harvested acres and the yield from the residues. list(string)
            harv_ac = dat[2]: Harvested acres. acrs
            scenario_yield = dat[4]: Yield. lbs
        """
        harv_ac = dat[2]  # acre
        scenario_yield = dat[4]  # lbs
        # @TODO: replace with db queries by FIPs
        hours_per_acre_combine = self._get_combine_hours_per_acre(scenario_yield=scenario_yield)  # hrs/acre
        # calculate population of combine for harvest.
        # pop = (hr/acre * acre) / (hr/yr) = yr
        pop_comb = round(hours_per_acre_combine * harv_ac / self.activity_combine, 10)  # yr
        # calculate population of tractors for transport.
        # pop = [(lbs/acre / dt/hr) * acre] / hr/yr = yr
        pop_bale_mover = round((scenario_yield / self.transport_bales) * harv_ac / self.activity_tractor, 10)  # yr

        lines = """%s       %s 2270005020 Dsl - Combines                             300   600 345.8  7000  DEFAULT         %s
%s       %s 2270005015 Dsl - Agricultural Tractors                100   175 133.6  4667  DEFAULT         %s
""" % (fips, self.episode_year, pop_comb, fips, self.episode_year, pop_bale_mover)

        self.pop_file.writelines(lines)


class ForestPop(Population):
    """
    Calculates equipment populations for forest residues
    Currently only loading equipment allocated to forest residue production, which is computed separately so no values here
    """
    def __init__(self, cont, episode_year, run_code):
        Population.__init__(self, cont, episode_year, run_code)

    def append_pop(self, fips, dat):
        pass


class CornGrainPop(Population):
    """
    Calculate corn grain populations. Irrigation gets calculated in another class.
    Non-harvest: Different tractors.
    Harvest: Combine.
    Transport: Tractor.
    """

    def __init__(self, cont, episode_year, run_code):
        Population.__init__(self, cont, episode_year, run_code)

        # Harvest hours per acre
        self.transport_tractor = 29.5 * 60  # bu/min * 60 min/hr = bu/hr

        # Non-Harvest hours per acre, from UT database
        self.hrs_per_acre_convTill = 1.255  # hrs/acre conventional till with moldboard plow
        self.hrs_per_acre_redTill = 0.7377  # hrs/acre limited till
        self.hrs_per_acre_noTill = 0.5884  # hrs/acre no till

    def append_pop(self, fips, dat):
        """
        Calculates a vehicle population for corn grain and adds population to .pop file.
        @param fips: Fips code.
        @param dat: Data from Billion ton study in the db on corn grain.
            harv_ac = dat[2]: Harvested acres. acres
            prod = dat[3]: Produce. lbs
        ############################
        @deprecated: this is not a 10 year cycle!
        harv_ac = dat[2] * 0.1    #10% of acres in each year of the 10-yr production cycle
        prod = dat[3] / 10.0
        ############################
        """
        # @TODO: CASE WHEN POP = 0.0, NOAH
        harv_ac = dat[2]
        prod = dat[3]
        # non harvest model.
        if self.run_code.endswith('N'):
            self.__set_non_harv_pop_file__(fips=fips, harv_ac=harv_ac)
            pass
        # model harvest
        else:
            self.__set_harv_pop_file__(fips=fips, harv_ac=harv_ac, prod=prod)
            pass

    def __set_harv_pop_file__(self, fips, harv_ac, prod):
        """
        Calculates tractor and combine populations for transport and harvest.
        ############################################
        @deprecated: Changed scenario yield = harv_ac * constant,
        to (prod / harv_ac) * constant.
        Also has to make sure not dividing by 0.
        ############################################
        """
        # convert from bu/acre to dt/acre
        # lbs/acre
        scenario_yield = 0
        if harv_ac > 0:
            scenario_yield = (prod / harv_ac) * 56.0 * (1.0 - 0.155) / 2000.0
        # hrs/acre
        hours_per_acre_combine = self._get_combine_hours_per_acre(scenario_yield=scenario_yield)

        # calculate population
        # EDIT 12.07.12 - REDUCED COMBINE HRS/ACRE BY 10% DUE TO TRANSPORT CART
        # (hrs/acre * acre) / (hrs/yr) = yr
        pop_combine = round((hours_per_acre_combine * 0.9) * harv_ac / self.activity_combine, 10)
        # [(lbs/acre) / (bu/hr)] * (acre) / (hr/yr) = yr
        pop_transport = (scenario_yield / self.transport_tractor) * harv_ac / self.activity_tractor

        lines = """%s       %s 2270005015 Dsl - Agricultural Tractors                100   175 133.6  4667  DEFAULT        %s
%s       %s 2270005020 Dsl - Combines                             300   600 345.8  7000  DEFAULT        %s
""" % (fips, self.episode_year, pop_transport, fips, self.episode_year, pop_combine)

        self.pop_file.writelines(lines)

    def __set_non_harv_pop_file__(self, fips, harv_ac):
        """
        Calculates tractors for non-harvest.
        Either conventional, reduced, and non till.
        """
        lines = None
        if self.run_code.endswith('CN'):
            #  pop = (hrs/acre) * (acre) / (hrs/yr) = yr
            pop_conv_till = self.hrs_per_acre_convTill * harv_ac / self.activity_tractor  # yr
            lines = """%s       %s 2270005015 Dsl - Agricultural Tractors                175   300 236.5  4667  DEFAULT        %s
""" % (fips, self.episode_year, pop_conv_till)

        elif self.run_code.endswith('RN'):
            # pop = (hrs/acre * acre) / (hrs/yr) = yr
            pop_reduced_till = self.hrs_per_acre_redTill * harv_ac / self.activity_tractor  # yr
            lines = """%s       %s 2270005015 Dsl - Agricultural Tractors                100   175 133.6  4667  DEFAULT        %s
""" % (fips, self.episode_year, pop_reduced_till)

        elif self.run_code.endswith('NN'):
            # pop = (hrs/acre * acre) / (hrs/yr) = yr
            pop_conventional_till = self.hrs_per_acre_noTill * harv_ac / self.activity_tractor  # yr
            lines = """%s       %s 2270005015 Dsl - Agricultural Tractors                100   175 133.6  4667  DEFAULT        %s
""" % (fips, self.episode_year, pop_conventional_till)

        self.pop_file.writelines(lines)


class CornGrainIrrigationPop(Population):
    """
    Calculates the population of irrigation machines for harvesting corn grain.
    Use multiple inheritance to get the total harvested acres from the allocate file to calculate population.

    Override the 'initialize_harvest' method to get the data
    Implement the 'append_harvest' method to 'pass' i.e. do not calculate population on a county level basis.
    Override the 'finish_pop' method to create a state level population.

    In the 'append_harvest' method, call 'pass' in order to have a common interface for the Population class.

    line[0] - fips
        [1] - state
        [2] - total harv ac * percent of acres
        [3] - total prod (in bu)
        [4] - fuel identifier (diesel, gasoline, lpg, or cng)
        [5] - horsepower (hp)
        [6] - percent of acres
        [7] - hours per acre (hpa)
    """

    def __init__(self, cont, episode_year, run_code):
        Population.__init__(self, cont, episode_year, run_code)

    def initialize_pop(self, dat):
        """
        @param dat: All of the data. Saved for later.
        0 fips: fips
        1 st: state
        2 (total_harv_ac * perc): harvested acres * percentage of land irrigated.
        3 total_prod: total produce.
        4 fuel: fuel type, Diesel, Gasoline, LPG, CNG
        5 hp: horsepower.
        6 perc: percent of land use.
        7 hpa: irrigation hrs/acre
        """
        Population.initialize_pop(self, dat)

    def append_pop(self, fips, dat):
        # hp
        hp = dat[5]
        # hrs/acre
        hpa = dat[7]
        # irrigated acres
        indicator = dat[2]
        # Gasoline Irrigation
        if self.run_code.endswith('G'):
            self._gasoline(fips=fips, hp=hp, hpa=hpa, indicator=indicator)
        # LPG Irrigation, only one hp range is modeled in Nonroad
        if self.run_code.endswith('L'):
            self._lpg(fips=fips, hp=hp, hpa=hpa, indicator=indicator)
        # CNG Irrigation
        if self.run_code.endswith('C'):
            self._cng(fips=fips, hp=hp, hpa=hpa, indicator=indicator)
        # Diesel Irrigation
        if self.run_code.endswith('D'):
            self._diesel(fips=fips, hp=hp, hpa=hpa, indicator=indicator)

    def hp_check(self, hp, hpa, max_hp):
        """
        Used to make sure hp is in the correct ranges for NONROAD. If it is too high, the hp is halved
        and the hours per acre is doubled.
        @param hp: Horse power.
        @param hpa: Hours per acre.
        @param max_hp: Max hp NONROAD can take.
        @return: Horse power and hourse per acre changed.
        """
        while hp >= max_hp:
            hp /= 2.0
            hpa *= 2.0
        return hp, hpa

    def _diesel(self, fips, hp, hpa, indicator):
        """
        Create diesel population.
        """
        hp, hpa = self.hp_check(hp, hpa, 750)
        # pop = (acres * hrs/acre) / (hrs/yr) = yr
        pop = round(indicator * hpa / self.activity_diesel, 10)
        lines = ""
        if hp < 11:
            lines = """%s       %s 2270005060 Dsl - Irrigation Sets                        6    11     8  2500  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 16:
            lines = """%s       %s 2270005060 Dsl - Irrigation Sets                       11    16  15.6  2500  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 25:
            lines = """%s       %s 2270005060 Dsl - Irrigation Sets                       16    25 21.88  2500  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 40:
            lines = """%s       %s 2270005060 Dsl - Irrigation Sets                       25    40    33  2500  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 50:
            lines = """%s       %s 2270005060 Dsl - Irrigation Sets                       40    50 45.08  2500  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 75:
            lines = """%s       %s 2270005060 Dsl - Irrigation Sets                       50    75 60.24  4667  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 100:
            lines = """%s       %s 2270005060 Dsl - Irrigation Sets                       75   100 85.87  4667  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 175:
            lines = """%s       %s 2270005060 Dsl - Irrigation Sets                      100   175 136.3  4667  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 300:
            lines = """%s       %s 2270005060 Dsl - Irrigation Sets                      175   300 224.5  4667  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 600:
            lines = """%s       %s 2270005060 Dsl - Irrigation Sets                      300   600   390  7000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 750:
            lines = """%s       %s 2270005060 Dsl - Irrigation Sets                      600   750 704.7  7000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        self.pop_file.writelines(lines)

    def _gasoline(self, fips, hp, hpa, indicator):
        """
        Create gasoline population.
        """
        hp, hpa = self.hp_check(hp, hpa, 300)
        # pop = (acres * hrs/acre) / (hrs/yr) = yr
        pop = round(indicator * hpa / self.activity_gas, 10)
        lines = ""
        if hp < 6:
            lines = """%s       %s 2265005060 4-Str Irrigation Sets                        3     6 4.692   200  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 11:
            lines = """%s       %s 2265005060 4-Str Irrigation Sets                        6    11 8.918   400  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 25:
            lines = """%s       %s 2265005060 4-Str Irrigation Sets                       16    25    18   750  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 75:
            lines = """%s       %s 2265005060 4-Str Irrigation Sets                       50    75  59.7  3000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 100:
            lines = """%s       %s 2265005060 4-Str Irrigation Sets                       75   100 80.25  3000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 175:
            lines = """%s       %s 2265005060 4-Str Irrigation Sets                      100   175 120.5  3000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 300:
            lines = """%s       %s 2265005060 4-Str Irrigation Sets                      175   300 210.2  3000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        self.pop_file.writelines(lines)

    def _lpg(self, fips, hp, hpa, indicator):
        """
        Create liquid propane population.
        """
        # pop = (acres * hrs/acre) / (hrs/yr) = yr
        hp, hpa = self.hp_check(hp, hpa, 175)
        pop = round(indicator * hpa / self.activity_lpg, 10)
        lines = """%s       %s 2267005060 LPG - Irrigation Sets                      100   175   113  3000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        self.pop_file.writelines(lines)

    def _cng(self, fips, hp, hpa, indicator):
        """
        Created compressed natraul gas population.
        """
        hp, hpa = self.hp_check(hp, hpa, 600)
        # pop = (acres * hrs/acre) / (hrs/yr) = yr
        pop = round(indicator * hpa / self.activity_cng, 10)
        lines = ""
        if hp < 40:
            lines = """%s       %s 2268005060 CNG - Irrigation Sets                       25    40    32  1500  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 75:
            lines = """%s       %s 2268005060 CNG - Irrigation Sets                       50    75 72.78  3000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 100:
            lines = """%s       %s 2268005060 CNG - Irrigation Sets                       75   100 96.19  3000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 175:
            lines = """%s       %s 2268005060 CNG - Irrigation Sets                      100   175 138.9  3000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 300:
            lines = """%s       %s 2268005060 CNG - Irrigation Sets                      175   300 233.3  3000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        elif hp < 600:
            lines = """%s       %s 2268005060 CNG - Irrigation Sets                      300   600 384.4  3000  DEFAULT        %s
""" % (fips, self.episode_year, pop)
        self.pop_file.writelines(lines)


class SwitchgrassPop(Population):
    """
    Calculates equipment populations for a perennial (10 year) switchgrass model run.
    """

    def __init__(self, cont, episode_year, run_code):
        Population.__init__(self, cont, episode_year, run_code)

        self.pop_60 = None
        self.pop_130 = None

        # Yield assumptions for switchgrass (fractions are compared to 'mature yields')
        if self.run_code.endswith('H1'):
            self.yield_factor = 1 / 3.0
        elif self.run_code.endswith('H2'):
            self.yield_factor = 2 / 3.0
        else:
            self.yield_factor = 1.0

    def append_pop(self, fips, dat):
        # case where there is no production
        if dat[3] == 0.0:
            self.pop_60 = 0.0
            self.pop_130 = 0.0
        else:
            harv_ac = dat[2] * 0.1  # 10% of acres in each year of the 10-yr production cycle
            prod = dat[3] / 10.0  # Production at maturity
            if self.run_code.startswith('SG_N'):
                self.__get_non_harv_hrs_per_acre__(harv_ac=harv_ac)
            elif self.run_code.startswith('SG_H'):
                self.__get_harv_hrs_per_acre__(harv_ac=harv_ac, prod=prod)
            else:
                self.__get_transport_hrs_per_acre__(prod=prod)

        self.__set_pop_file__(fips=fips)

    def __set_pop_file__(self, fips):
        lines = """%s       %s 2270005015 Dsl - Agricultural Tractors                 50    75 62.18  4667  DEFAULT         %s
%s       %s 2270005015 Dsl - Agricultural Tractors                100   175 133.6  4667  DEFAULT         %s
""" % (fips, self.episode_year, self.pop_60, fips, self.episode_year, self.pop_130)

        self.pop_file.writelines(lines)

    def __get_non_harv_hrs_per_acre__(self, harv_ac):
        """
        ##############################
        @deprecated: Should be N1, not NH1
        old code: if self.run_code.endswith('NH1'):
        new code: if self.run_code.endswith('N1'):
        ##############################
        """

        # year 1, establishment year, non-harvest activities
        if self.run_code.endswith('N1'):
            self.hrs_per_ac_60hp = 0.2211
            self.hrs_per_ac_130hp = 0.5159

        # year 2, maintenance year, non-harvest activities
        elif self.run_code.endswith('N2'):
            self.hrs_per_ac_60hp = 0.04620
            self.hrs_per_ac_130hp = 0.0

        # year 5, additional pesticide applications
        elif self.run_code.endswith('N5'):
            self.hrs_per_ac_60hp = 0.0891  # pesticides are applied in addition to other activities
            self.hrs_per_ac_130hp = 0.0

        # years 3-4 & 6-10 all have the same non-harvest activities
        else:
            self.hrs_per_ac_60hp = 0.04620
            self.hrs_per_ac_130hp = 0.0

        # (acres * hrs/acre) / (hr/year) = year
        self.pop_60 = round((harv_ac * self.hrs_per_ac_60hp) / self.activity_tractor, 10)
        self.pop_130 = round((harv_ac * self.hrs_per_ac_130hp) / self.activity_tractor, 10)

    def __get_harv_hrs_per_acre__(self, harv_ac, prod):

        scenario_yield = (prod / harv_ac) * self.yield_factor  # lb/acre

        if scenario_yield < 20.0:
            baler = 0.169 * 1.1  # hrs/acre
        else:
            baler = (scenario_yield / 20.0) * 1.1  # hrs/acre

        mower = 0.138 * 1.1  # hrs/acre
        rake = 0.191 * 1.1  # hrs/acre

        # (hrs/acre * acres) / (hrs/yr) = yr
        self.pop_60 = (rake * harv_ac) / self.activity_tractor
        self.pop_130 = ((mower + baler) * harv_ac) / self.activity_tractor

    def __get_transport_hrs_per_acre__(self, prod):
        """
        Get the transport populations in years.
        #################################
        @deprecated: pop_130 was calculated incorrectly. Units did not make sense.
        old code: self.pop_130 = ((scenario_yield * self.transport_bales) / self.activity_tractor) * 1.1
        new code: self.pop_130 = ((scenario_yield) / (self.transport_bales * self.activity_tractor) * 1.1
        machine hours = (scenario_yield / self.transport_bales) * 1.1
        @deprecated: Changed population equation to use produce instead of yield. Allows population to be in units of yr.
        old code: scenario_yield = (prod/harv_acre) * self.yield_factor
        new code: scenario_prod = prod * self.yield_factor
                  self.pop_130 = (scenario_prod / (self.transport_bales * self.activity_tractor)) * 1.1 # yr
        ###################################
        """
        # @TODO: transport pop calculation

        if self.run_code.endswith('T1'):
            self.yield_factor = 1.0 / 3.0
        elif self.run_code.endswith('T2'):
            self.yield_factor = 2.0 / 3.0
        else:
            self.yield_factor = 1.0

        # years 1-10, transport activities
        scenario_prod = prod * self.yield_factor  # lbs
        self.pop_60 = 0.0
        # lbs / (dt/hr * hr/yr) = yr
        self.pop_130 = (scenario_prod / (self.transport_bales * self.activity_tractor)) * 1.1  # yr


class LoadingEquipment(Population):
    """
    Calculates loading equipment populations and add them to .pop file.
    Includes loader and chipper for forest residues and tractor for other crops
    """

    def __init__(self, cont, episode_year, run_code):
        Population.__init__(self, cont, episode_year, run_code)

        # loading equipment dictionary
        self.loading_equip_dict = config.get('loading_equip')
        # nonroad equipment dictionary
        self.nonroad_equip_dict = config.get('nonroad_equip_dict')
        # loading equipment for specific feedstock
        self.loading_equip = self.loading_equip_dict[run_code[0:2]]
        # set values for string formatting
        self.kvals = dict()
        self.kvals['year'] = episode_year

    def append_pop(self, fips, dat):
        """
        Calculate populations for each fips code.
        @param fips: Fips county code. string
        @param dat: Db data for production. list(string)
            dat[2]: production (dry tons)
        """

        # get production data
        self.kvals['prod'] = dat[2]

        # set other values for string formatting
        self.kvals['fips'] = fips

        # initialize lines for file
        lines = ''
        # loop through equipment in loading equipment list
        for i in range(0, len(self.loading_equip['type'])):
            # get equipment information in equipment list
            equip_type = self.loading_equip['type'][i]  # type(e.g., tractor)
            self.kvals['hrs_per_dt'] = self.loading_equip['process_rate'][i]  # processing rate (hr/dt)
            self.kvals['hp'] = self.loading_equip['power'][i]  # power

            # find information needed for NONROAD population file
            self.kvals['scc'] = self.nonroad_equip_dict['scc'][equip_type]  # scc code
            annual_hrs_operation = self.nonroad_equip_dict['annual_hrs_operation'][equip_type]  # annual hours of operation
            self.kvals['equip_name'] = self.nonroad_equip_dict['name'][equip_type]

            pop = round(float(self.kvals['hrs_per_dt']) * float(self.kvals['prod']) / float(annual_hrs_operation), 10)

            # calculate required population using production, processing rate, and annual hours of operation
            self.kvals['pop'] = pop

            # determine range for horsepower (match to NONROAD range) and evaluate useful life
            for hp_range in self.nonroad_equip_dict['power_range']:
                if self.nonroad_equip_dict['power_range'][hp_range][0] < self.kvals['hp'] <= self.nonroad_equip_dict['power_range'][hp_range][1]:
                    self.kvals['hp_min'] = self.nonroad_equip_dict['power_range'][hp_range][0]
                    self.kvals['hp_max'] = self.nonroad_equip_dict['power_range'][hp_range][1]
                    self.kvals['useful_life'] = self.nonroad_equip_dict['useful_life'][hp_range]

            # append equipment information to string for population file
            lines += """{fips}       {year} {scc}                                           {hp_min}   {hp_max}   {hp}   {useful_life} DEFAULT     {pop} \n""".format(**self.kvals)

        self.pop_file.writelines(lines)
