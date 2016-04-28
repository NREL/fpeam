"""
functions associated with population
"""

from utils import config, logger
import os


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

        self.path = os.path.join(cont.get(key='path'), 'POP')

        self.run_code = run_code

        # get dictionary for NONROAD equipment
        self.nonroad_equip_dict = config.get('nonroad_equip_dict')

        # get dictionary for crop budget
        self.crop_budget_dict = config.get('crop_budget_dict')

        # Used in all agricultural feedstocks (i.e. not FR)
        self.activity_tractor = float(self.nonroad_equip_dict['annual_hrs_operation']['tractor'])              # hr / year (NonRoad default value)
        # Corn Grain
        self.activity_combine = float(self.nonroad_equip_dict['annual_hrs_operation']['combine'])              # hr / year (NonRoad default values)
        self.activity_gas = float(self.nonroad_equip_dict['annual_hrs_operation']['ir_gas'])                  # hr / year (NonRoad default values)
        self.activity_diesel = float(self.nonroad_equip_dict['annual_hrs_operation']['ir_diesel'])               # hr / year (NonRoad default values)
        self.activity_lpg = float(self.nonroad_equip_dict['annual_hrs_operation']['ir_lpg'])                  # hr / year (NonRoad default values)
        self.activity_cng = float(self.nonroad_equip_dict['annual_hrs_operation']['ir_cng'])                  # hr / year (NonRoad default values)

        # data from personal communication with Anthony Turhollow for SG.
        # It is assumed that the transport time for one bale of SG is the same as for one bale of CS or WS)
        self.transport_bales = 20.0                   # dt/hr

        self.pop_file = None

    def initialize_pop(self, dat):
        """
        This function creates the .POP file with the correct syntax and population estimates
        :param dat: data from the db containing harvested acres, fips, yield, etc. list(string)
        :return: A file is created containing a nonroad appropriate population file
        """
        state = dat[1]
        path = os.path.join(self.path, '%s_%s.pop' % (state, self.run_code))
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

    def _create_pop_line(self, fips, subregion_code, year, scc_code, equip_desc, min_hp, max_hp, avg_hp, life, flag, pop):
        """
        Generate population file line

        :param fips: FIPS code
        :param subregion_code: subregion code (used for subcounty estimates)
        :param year: year of population estimates
        :param scc_code: SCC code (no globals accepted)
        :param equip_desc: equipment description (ignored)
        :param min_hp: minimum HP range
        :param max_hp: maximum HP range (ranges must match those internal to model)
        :param avg_hp: average HP in range (if blank model uses midpoint)
        :param life: expected useful life (in hours of use)
        :param flag: flag for scrappage distribution curve (DEFAULT = standard curve)
        :param pop: population estimate
        :return: String
        """

        kvals = {'fips': fips,
                 'sub_reg': subregion_code,
                 'year': year,
                 'scc_code': scc_code,
                 'equip_desc': equip_desc,
                 'min_hp': min_hp,
                 'max_hp': max_hp,
                 'avg_hp': avg_hp,
                 'life': life,
                 'flag': flag,
                 'pop': pop
                 }

        return '{fips:0>5} {sub_reg:>5} {year:>4} {scc_code:>10} {equip_desc:<40} {min_hp:>5} {max_hp:>5} {avg_hp:>5.1f} {life:>5} {flag:<10} {pop:>17.7f} \n'.format(**kvals)

    def append_pop(self, fips, indicator1):
        """

        :param fips:
        :param indicator1:
        :return:
        """

        raise NotImplementedError()

    def finish_pop(self):
        """
        This function finishes the POP_file.  It closes the file and appends the '/END/' data label to the file.

        :return:
        """

        lines = '/END/'

        self.pop_file.writelines(lines)

        self.pop_file.close()

    def _get_combine_hours_per_acre(self, scenario_yield):
        """
        Find machinery hours based on yield.

        :param scenario_yield: Yield from feed stock in lbs/acre
        :return: Combine hours per acre. hrs/acre
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


class RegionalEquipment(Population):
    """
    Calculates equipment populations for agricultural crops using regional crop budgets
    :return:
    """

    def __init__(self, cont, episode_year, run_code):
        Population.__init__(self, cont, episode_year, run_code)

        # get database object
        self.db = cont.get('db')

        # set run_code
        self.run_code = run_code

        # initialize kvals dictionary
        self.cont = cont

    def append_pop(self, fips, dat):
        """
        Calculate the equipment populations for NONROAD using regional crop budgets
        Then write them to a population file

        :param fips: fips county code. (string)
        :param dat: Data from the db containing harvested acres and the yield from the residues. list(string)
            harv_ac = dat[2]: Harvested acres
        """
        # set feedstock from run code
        feed = self.run_code[0:2]

        kvals = self.cont.get('kvals')
        # set other values in kvals dictionary
        kvals['feed'] = feed.lower()  # feedstock
        kvals['fips'] = fips  # fips code

        # set tillage type
        if not (self.run_code.startswith('SG') or self.run_code.startswith('MS')):
            if self.run_code[3] == 'R':
                kvals['tillage'] = 'CT'  # reduced tillage equipment is the same as conventional tillage
            else:
                kvals['tillage'] = '%sT' % (self.run_code[3])
        elif self.run_code.startswith('SG'):
            kvals['tillage'] = 'NT'
        elif self.run_code.startswith('MS'):
            kvals['tillage'] = 'CT'

        # set operation type and activity type from run code
        kvals['oper_type'] = self.crop_budget_dict['type'][feed]
        if self.run_code.startswith('SG') or self.run_code.startswith('MS'):
            kvals['activity'] = self.run_code[3]
        else:
            kvals['activity'] = self.run_code[4]

        # get equipment list from crop budget
        if self.run_code.startswith('SG') or self.run_code.startswith('MS'):
            kvals['budget_year'] = self.run_code[4]
            query = """
                        SELECT equip_type, hp, activity_rate
                        FROM {production_schema}.{feed}_equip_fips
                        WHERE fips = {fips} AND tillage = '{tillage}' AND oper_type LIKE '%{oper_type}' AND activity LIKE '{activity}%' AND bdgtyr = '{budget_year}'
                    """.format(**kvals)

        else:
            query = """SELECT equip_type, hp, activity_rate
                        FROM {production_schema}.{feed}_equip_fips
                        WHERE fips = {fips} AND tillage = '{tillage}' AND oper_type LIKE '%{oper_type}' AND activity LIKE '{activity}%'
                    """.format(**kvals)
        # return data from query
        equip_list = self.db.output(query)

        # if data is not empty
        if len(equip_list) >= 1:
            equip_list = equip_list[0]
            # get harvested acreage from production data
            harv_ac = dat[2]

            # loop through equipment in equipment list
            for equip in equip_list:
                # set equipment type, hp and activity rate using data returned from equipment budget query
                equip_type = equip[0]
                hp = equip[1]
                activity_rate = equip[2]

                # only evaluate non-road activity for equipment other than airplanes (aerial emissions are calculated during post-processing under CombustionEmissions.py)
                if equip_type != 'aerial':
                    # get annual activity for equipment type
                    annual_activity = float(self.nonroad_equip_dict['annual_hrs_operation'][equip_type])  # hr / year (NonRoad default value)

                    # compute population of equipment using activity rate, harvested acreage, and annual activity
                    pop = round(activity_rate * harv_ac / annual_activity, 7)  # population in years of operation

                    # get hp and useful life dictionaries for NONROAD data
                    hp_list = self.nonroad_equip_dict['power_range']
                    useful_life_dict = self.nonroad_equip_dict['useful_life']

                    # loop through hp_ranges in hp dictionary
                    for hp_range_type in hp_list:
                        # check if hp falls in range
                        hp_range = hp_list[hp_range_type]
                        if float(hp_range[0]) <= float(hp) < float(hp_range[1]):
                            # if so, set min and max hp and useful life for this hp range
                            hp_min = hp_range[0]
                            hp_max = hp_range[1]
                            life = useful_life_dict[hp_range_type]
                            break

                    # initialize population line values
                    kvals = {'fips': fips,
                             'subregion_code': '',
                             'year': self.episode_year,
                             'scc_code': self.nonroad_equip_dict['scc'][equip_type],
                             'equip_desc': self.nonroad_equip_dict['name'][equip_type],
                             'min_hp': hp_min,
                             'max_hp': hp_max,
                             'avg_hp': hp,
                             'life': life,
                             'flag': 'DEFAULT',
                             'pop': pop,
                             }

                    line = self._create_pop_line(**kvals)
                    self.pop_file.writelines(line)


class ResiduePop(Population):
    """
    Calculates equipment populations for corn stover and wheat straw residue collection using national crop budgets
    CS, WS
    Residues have harvest and transports emissions, but none for non-harvest.
    Because these are residues, so the emissions are going to corn grain.
    """

    def __init__(self, cont, episode_year, run_code):
        Population.__init__(self, cont, episode_year, run_code)

    def append_pop(self, fips, dat):
        """
        Calculates the population of combines and tractors needed.
        Then writes them to a population file.

        :param fips: fips county code. (string)
        :param dat: Data from the db containing harvested acres and the yield from the residues. list(string)
            harv_ac = dat[2]: Harvested acres. acrs
            scenario_yield = dat[4]: Yield. lbs
        """

        harv_ac = dat[2]  # acre
        scenario_yield = dat[4]  # lbs

        # get activity
        hours_per_acre_combine = self._get_combine_hours_per_acre(scenario_yield=scenario_yield)  # hrs/acre

        # calculate population of combine for harvest.
        # pop = (hr/acre * acre) / (hr/yr) = yr
        pop_comb = round(hours_per_acre_combine * harv_ac / self.activity_combine, 7)  # yr

        # init population line values
        kvals = {'fips': fips,
                 'subregion_code': '',
                 'year': self.episode_year,
                 'scc_code': 2270005020,
                 'equip_desc': 'Dsl - Combines',
                 'min_hp': 300,
                 'max_hp': 600,
                 'avg_hp': 345.8,
                 'life': 7000,
                 'flag': 'DEFAULT',
                 'pop': pop_comb,
                 }

        line = self._create_pop_line(**kvals)
        self.pop_file.writelines(line)

        # calculate population of tractors for transport.
        # pop = [(lbs/acre / dt/hr) * acre] / hr/yr = yr
        pop_bale_mover = round((scenario_yield / self.transport_bales) * harv_ac / self.activity_tractor, 7)  # yr
        # init population line values
        kvals_bale = {'fips': fips,
                      'subregion_code': '',
                      'year': self.episode_year,
                      'scc_code': 2270005020,
                      'equip_desc': 'Dsl - Combines',
                      'min_hp': 100,
                      'max_hp': 175,
                      'avg_hp': 133.6,
                      'life': 4667,
                      'flag': 'DEFAULT',
                      'pop': pop_bale_mover,
                      }
        line = self._create_pop_line(**kvals_bale)
        self.pop_file.writelines(line)


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
        """

        :param cont: Container object
        :param episode_year: year of interest
        :param run_code: current run code
        :return:
        """

        Population.__init__(self, cont, episode_year, run_code)

        # Harvest hours per acre
        # @TODO: what is 29.5? Where did it come from? Appears to be 3x the value specified in SI table S9 (13 dry short tons/hr, which works out to about 525 bu/hr)
        self.transport_tractor = 29.5 * 60  # bu/min * 60 min/hr = bu/hr

        # Non-Harvest hours per acre, from UT database
        self.hrs_per_acre_conv_till = 1.255  # hrs/acre conventional till with moldboard plow
        self.hrs_per_acre_red_till = 0.7377  # hrs/acre limited till
        self.hrs_per_acre_no_till = 0.5884  # hrs/acre no till

    def append_pop(self, fips, dat):
        """
        Calculates a vehicle population for corn grain and adds population to .pop file.
        :param fips: Fips code
        :param dat: Data from Billion ton study in the db on corn grain
            harv_ac = dat[2]: Harvested acres. acres
            prod = dat[3]: Produce. lbs
        :return:
        """

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
        Calculates tractor and combine populations for transport and harvest and writes population lines to .pop file

        :param fips: county FIPS code
        :param harv_ac: acres harvested
        :param prod: production
        :return:
        """

        # convert from bu/acre to dt/acre
        # lbs/acre
        scenario_yield = 0
        if harv_ac > 0:
            # dt_to_bu = 56.0 * (1.0 - 0.155) / 2000.0
            scenario_yield = (prod / harv_ac)

        # hrs/acre
        hours_per_acre_combine = self._get_combine_hours_per_acre(scenario_yield=scenario_yield)

        # calculate population for combine
        # EDIT 12.07.12 - REDUCED COMBINE HRS/ACRE BY 10% DUE TO TRANSPORT CART
        # (hrs/acre * acre) / (hrs/yr) = yr
        # init population line values

        pop_combine = round((hours_per_acre_combine * 0.9) * harv_ac / self.activity_combine, 7)
        kvals = {'fips': fips,
                 'subregion_code': '',
                 'year': self.episode_year,
                 'scc_code': 2270005020,
                 'equip_desc': 'Dsl - Combines',
                 'min_hp': 300,
                 'max_hp': 600,
                 'avg_hp': 345.8,
                 'life': 7000,
                 'flag': 'DEFAULT',
                 'pop': pop_combine,
                 }
        # create line for combine
        line = self._create_pop_line(**kvals)
        self.pop_file.writelines(line)

        # calculate population for transport
        # to convert to dt, if needed
        # bu_to_dt = 39.3680  # agric.gov.ab.ca/app19/calc/crop/bushel2tonne.jsp
        pop_transport = round((scenario_yield / self.transport_tractor) * harv_ac / self.activity_tractor, 7)
        kvals = {'fips': fips,
                 'subregion_code': '',
                 'year': self.episode_year,
                 'scc_code': 2270005015,
                 'equip_desc': 'Dsl - Agricultural Tractors',
                 'min_hp': 100,
                 'max_hp': 175,
                 'avg_hp': 133.6,
                 'life': 4667,
                 'flag': 'DEFAULT',
                 'pop': pop_transport,
                 }
        # create line for transport
        line = self._create_pop_line(**kvals)
        self.pop_file.writelines(line)

    def __set_non_harv_pop_file__(self, fips, harv_ac):
        """
        Calculates tractors for non-harvest.
        Either conventional, reduced, and non till.

        :param fips:
        :param harv_ac:
        :return:
        """

        if self.run_code.endswith('CN'):
            #  pop = (hrs/acre) * (acre) / (hrs/yr) = yr
            pop_conv_till = round(self.hrs_per_acre_conv_till * harv_ac / self.activity_tractor, 7)  # yr
            kvals = {'fips': fips,
                     'subregion_code': '',
                     'year': self.episode_year,
                     'scc_code': 2270005015,
                     'equip_desc': 'Dsl - Agricultural Tractors',
                     'min_hp': 175,
                     'max_hp': 300,
                     'avg_hp': 236.5,
                     'life': 4667,
                     'flag': 'DEFAULT',
                     'pop': pop_conv_till,
                     }

            # create line for conventional till
            line = self._create_pop_line(**kvals)
            self.pop_file.writelines(line)

        elif self.run_code.endswith('RN'):
            # pop = (hrs/acre * acre) / (hrs/yr) = yr
            pop_reduced_till = round(self.hrs_per_acre_red_till * harv_ac / self.activity_tractor, 7)  # yr
            kvals = {'fips': fips,
                     'subregion_code': '',
                     'year': self.episode_year,
                     'scc_code': 2270005015,
                     'equip_desc': 'Dsl - Agricultural Tractors',
                     'min_hp': 100,
                     'max_hp': 175,
                     'avg_hp': 133.6,
                     'life': 4667,
                     'flag': 'DEFAULT',
                     'pop': pop_reduced_till,
                     }
            # create line for reduced till
            line = self._create_pop_line(**kvals)
            self.pop_file.writelines(line)

        elif self.run_code.endswith('NN'):
            # pop = (hrs/acre * acre) / (hrs/yr) = yr
            pop_conventional_till = round(self.hrs_per_acre_no_till * harv_ac / self.activity_tractor, 7)  # yr
            kvals = {'fips': fips,
                     'subregion_code': '',
                     'year': self.episode_year,
                     'scc_code': 2270005015,
                     'equip_desc': 'Dsl - Agricultural Tractors',
                     'min_hp': 100,
                     'max_hp': 175,
                     'avg_hp': 133.6,
                     'life': 4667,
                     'flag': 'DEFAULT',
                     'pop': pop_conventional_till,
                     }
            # create line for transport
            line = self._create_pop_line(**kvals)
            self.pop_file.writelines(line)


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
        """

        :param cont:
        :param episode_year:
        :param run_code:
        :return:
        """
        Population.__init__(self, cont, episode_year, run_code)
        self.hp_list = self.nonroad_equip_dict['power_range']

    def initialize_pop(self, dat):
        """
        :param dat: All of the data. Saved for later.
        0 fips: fips
        1 st: state
        2 (total_harv_ac * perc): harvested acres * percentage of land irrigated.
        3 total_prod: total produce.
        4 fuel: fuel type, Diesel, Gasoline, LPG, CNG
        5 hp: horsepower.
        6 perc: percent of land use.
        7 hpa: irrigation hrs/acre

        :return:
        """

        Population.initialize_pop(self, dat)

    def append_pop(self, fips, dat):
        """

        :param fips:
        :param dat:
        :return:
        """

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

        :param hp: Horse power.
        :param hpa: Hours per acre.
        :param max_hp: Max hp NONROAD can take.
        :return: Horse power and hourse per acre changed.
        """

        while hp >= max_hp:
            hp /= 2.0
            hpa *= 2.0

        return hp, hpa

    def _diesel(self, fips, hp, hpa, indicator):
        """
        Create diesel population.

        :param fips:
        :param hp:
        :param hpa:
        :param indicator:
        :return:
        """

        hp, hpa = self.hp_check(hp, hpa, 750)
        # pop = (acres * hrs/acre) / (hrs/yr) = yr
        pop = round(indicator * hpa / self.activity_diesel, 7)

        for hp_range_type in self.hp_list:
            # check if hp falls in range
            hp_range = self.hp_list[hp_range_type]
            if float(hp_range[0]) <= float(hp) < float(hp_range[1]):
                # if so, set min and max hp and useful life for this hp range
                hp_min = hp_range[0]
                hp_max = hp_range[1]
                life = self.nonroad_equip_dict['useful_life'][hp_range_type]
                break

        # set kvals dictionary for string formatting
        kvals = {'fips': fips,
                 'subregion_code': '',
                 'year': self.episode_year,
                 'scc_code': 2270005060,
                 'equip_desc': 'Dsl - Irrigation Sets',
                 'min_hp': hp_min,
                 'max_hp': hp_max,
                 'avg_hp': hp,
                 'life': life,
                 'flag': 'DEFAULT',
                 'pop': pop,
                 }

        # create line in population file
        line = self._create_pop_line(**kvals)
        self.pop_file.writelines(line)

    def _gasoline(self, fips, hp, hpa, indicator):
        """
        Create gasoline population.

        :param fips:
        :param hp:
        :param hpa:
        :param indicator:
        :return:
        """

        hp, hpa = self.hp_check(hp, hpa, 300)

        # pop = (acres * hrs/acre) / (hrs/yr) = yr
        pop = round(indicator * hpa / self.activity_gas, 7)

        for hp_range_type in self.hp_list:
            # check if hp falls in range
            hp_range = self.hp_list[hp_range_type]
            if float(hp_range[0]) <= float(hp) < float(hp_range[1]):
                # if so, set min and max hp and useful life for this hp range
                hp_min = hp_range[0]
                hp_max = hp_range[1]
                break

        if hp < 6:
            life = 200
        elif hp < 11:
            life = 400
        elif hp < 25:
            life = 750
        elif 25 <= hp < 300:
            life = 3000

        # set kvals dictionary for string formatting
        kvals = {'fips': fips,
                 'subregion_code': '',
                 'year': self.episode_year,
                 'scc_code': 2265005060,
                 'equip_desc': '4-Str Irrigation Sets',
                 'min_hp': hp_min,
                 'max_hp': hp_max,
                 'avg_hp': hp,
                 'life': life,
                 'flag': 'DEFAULT',
                 'pop': pop,
                 }

        # create line in population file
        line = self._create_pop_line(**kvals)
        self.pop_file.writelines(line)

    def _lpg(self, fips, hp, hpa, indicator):
        """
        Create liquid propane population.

        :param fips:
        :param hp:
        :param hpa:
        :param indicator:
        :return:
        """

        hp, hpa = self.hp_check(hp, hpa, 175)

        # pop = (acres * hrs/acre) / (hrs/yr) = yr
        pop = round(indicator * hpa / self.activity_lpg, 7)

        # set kvals dictionary for string formatting
        kvals = {'fips': fips,
                 'subregion_code': '',
                 'year': self.episode_year,
                 'scc_code': 2267005060,
                 'equip_desc': 'LPG - Irrigation Sets',
                 'min_hp': 100,
                 'max_hp': 175,
                 'avg_hp': 113,
                 'life': 3000,
                 'flag': 'DEFAULT',
                 'pop': pop,
                 }

        # create line in population file
        line = self._create_pop_line(**kvals)
        self.pop_file.writelines(line)

    def _cng(self, fips, hp, hpa, indicator):
        """
        Created compressed natural gas population.

        :param fips:
        :param hp:
        :param hpa:
        :param indicator:
        :return:
        """

        hp, hpa = self.hp_check(hp, hpa, 600)

        # pop = (acres * hrs/acre) / (hrs/yr) = yr
        pop = round(indicator * hpa / self.activity_cng, 7)

        for hp_range_type in self.hp_list:
            # check if hp falls in range
            hp_range = self.hp_list[hp_range_type]
            if float(hp_range[0]) <= float(hp) < float(hp_range[1]):
                # if so, set min and max hp and useful life for this hp range
                hp_min = hp_range[0]
                hp_max = hp_range[1]
                break

        if hp < 40:
            life = 1500
        elif 40 <= hp < 600:
            life = 3000

        # set kvals dictionary for string formatting
        kvals = {'fips': fips,
                 'subregion_code': '',
                 'year': self.episode_year,
                 'scc_code': 2268005060,
                 'equip_desc': 'CNG - Irrigation Sets',
                 'min_hp': hp_min,
                 'max_hp': hp_max,
                 'avg_hp': hp,
                 'life': life,
                 'flag': 'DEFAULT',
                 'pop': pop,
                 }

        # create line in population file
        line = self._create_pop_line(**kvals)
        self.pop_file.writelines(line)


class SwitchgrassPop(Population):
    """
    Calculates equipment populations for a perennial (10 year) switchgrass model run.
    """

    def __init__(self, cont, episode_year, run_code):
        """

        :param cont: Container object
        :param episode_year:
        :param run_code:
        :return:
        """

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
        """

        :param fips:
        :param dat:
        :return:
        """
        prod = dat[3] * 0.1  # 10% of acres in each year of the 10-yr production cycle

        # case where there is no production
        if prod == 0.0:
            self.pop_60 = 0.0
            self.pop_130 = 0.0
        else:
            harv_ac = dat[2] * 0.1  # 10% of acres in each year of the 10-yr production cycle
            if self.run_code.startswith('SG_N'):
                self.__get_non_harv_hrs_per_acre__(harv_ac=harv_ac)
            elif self.run_code.startswith('SG_H'):
                self.__get_harv_hrs_per_acre__(harv_ac=harv_ac, prod=prod)
            else:
                self.__get_transport_hrs_per_acre__(prod=prod)

        # set kvals dictionary for string formatting for 60 hp tractor
        kvals = {'fips': fips,
                 'subregion_code': '',
                 'year': self.episode_year,
                 'scc_code': 2270005015,
                 'equip_desc': 'Dsl - Agricultural Tractors',
                 'min_hp': 50,
                 'max_hp': 75,
                 'avg_hp': 62.18,
                 'life': 4667,
                 'flag': 'DEFAULT',
                 'pop': self.pop_60,
                 }

        # create line in population file
        line = self._create_pop_line(**kvals)
        self.pop_file.writelines(line)

        # set kvals dictionary for string formatting for 130 hp tractor
        kvals = {'fips': fips,
                 'subregion_code': '',
                 'year': self.episode_year,
                 'scc_code': 2270005015,
                 'equip_desc': 'Dsl - Agricultural Tractors',
                 'min_hp': 100,
                 'max_hp': 175,
                 'avg_hp': 133.6,
                 'life': 4667,
                 'flag': 'DEFAULT',
                 'pop': self.pop_130,
                 }

        # create line in population file
        line = self._create_pop_line(**kvals)
        self.pop_file.writelines(line)

    def __get_non_harv_hrs_per_acre__(self, harv_ac):
        """

        :param harv_ac:
        :return:
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
        self.pop_60 = round((harv_ac * self.hrs_per_ac_60hp) / self.activity_tractor, 7)
        self.pop_130 = round((harv_ac * self.hrs_per_ac_130hp) / self.activity_tractor, 7)

    def __get_harv_hrs_per_acre__(self, harv_ac, prod):
        """

        :param harv_ac:
        :param prod:
        :return:
        """

        scenario_yield = (prod / harv_ac) * self.yield_factor  # lb/acre

        if scenario_yield < 20.0:
            baler = 0.169 * 1.1  # hrs/acre
        else:
            baler = (scenario_yield / 20.0) * 1.1  # hrs/acre

        mower = 0.138 * 1.1  # hrs/acre
        rake = 0.191 * 1.1  # hrs/acre

        # (hrs/acre * acres) / (hrs/yr) = yr
        self.pop_60 = round((rake * harv_ac) / self.activity_tractor, 7)
        self.pop_130 = round(((mower + baler) * harv_ac) / self.activity_tractor, 7)

    def __get_transport_hrs_per_acre__(self, prod):
        """
        Get the transport populations in years.

        :param prod:
        :return:
        """

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
        self.pop_130 = round((scenario_prod / (self.transport_bales * self.activity_tractor)) * 1.1, 7)  # yr


class LoadingEquipment(Population):
    """
    Calculates loading equipment populations and add them to .pop file.
    Includes loader and chipper for forest residues and tractor for other crops
    """

    def __init__(self, cont, episode_year, run_code):
        """

        :param cont:
        :param episode_year:
        :param run_code:
        :return:
        """

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

        :param fips: Fips county code. string
        :param dat: Db data for production. list(string)
            dat[2]: production (dry tons)
        :return:
        """

        # get production data
        prod = float(dat[2])

        # loop through equipment in loading equipment list
        for i in range(0, len(self.loading_equip['type'])):
            # get equipment information in equipment list
            equip_type = self.loading_equip['type'][i]  # type(e.g., tractor)

            kvals = dict()
            kvals['fips'] = fips
            kvals['subregion_code'] = ''
            kvals['year'] = self.episode_year
            kvals['avg_hp'] = float(self.loading_equip['power'][i])
            kvals['flag'] = 'DEFAULT'

            # find information needed for NONROAD population file
            kvals['scc_code'] = self.nonroad_equip_dict['scc'][equip_type]  # scc code
            kvals['equip_desc'] = self.nonroad_equip_dict['name'][equip_type]

            # calculate population
            annual_hrs_operation = float(self.nonroad_equip_dict['annual_hrs_operation'][equip_type])  # annual hours of operation
            hrs_per_dt = float(self.loading_equip['process_rate'][i])  # processing rate (hr/dt)
            kvals['pop'] = round(hrs_per_dt * prod / annual_hrs_operation, 7)  # population (years)

            # determine range for horsepower (match to NONROAD range) and evaluate useful life
            for hp_range in self.nonroad_equip_dict['power_range']:
                if float(self.nonroad_equip_dict['power_range'][hp_range][0]) < kvals['avg_hp'] <= float(self.nonroad_equip_dict['power_range'][hp_range][1]):
                    kvals['min_hp'] = float(self.nonroad_equip_dict['power_range'][hp_range][0])
                    kvals['max_hp'] = float(self.nonroad_equip_dict['power_range'][hp_range][1])
                    kvals['life'] = self.nonroad_equip_dict['useful_life'][hp_range]

            # create line in population file
            line = self._create_pop_line(**kvals)
            self.pop_file.writelines(line)
