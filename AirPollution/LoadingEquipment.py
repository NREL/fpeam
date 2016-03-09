from src.AirPollution.utils import config, logger


class LoadingEquipment:
    """
    Calculates loading equipment populations and add them to .pop file.
    Includes loader and chipper for forest residues and tractor for other crops
    """

    def __init__(self, cont, episode_year, run_code):
        # loading equipment dictionary
        self.loading_equip_dict = config.get('loading_equip')
        # nonroad equipment dictionary
        self.nonroad_equip_dict = config.get('nonroad_equip_dict')
        # loading equipment for specific feedstock
        self.loading_equip = self.loading_equip_dict[run_code[0:2]]
        # set values for string formatting
        self.kvals = dict()
        self.kvals['year'] = episode_year

    def create_lines(self, fips, dat):
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

            # calculate required population using production, processing rate, and annual hours of operation
            self.kvals['pop'] = round(float(self.kvals['hrs_per_dt']) * float(self.kvals['prod']) / float(annual_hrs_operation), 10)

            # determine range for horsepower (match to NONROAD range) and evaluate useful life
            for hp_range in self.nonroad_equip_dict['power_range']:
                if self.nonroad_equip_dict['power_range'][hp_range][0] < self.kvals['hp'] <= self.nonroad_equip_dict['power_range'][hp_range][1]:
                    self.kvals['hp_min'] = self.nonroad_equip_dict['power_range'][hp_range][0]
                    self.kvals['hp_max'] = self.nonroad_equip_dict['power_range'][hp_range][1]
                    self.kvals['useful_life'] = self.nonroad_equip_dict['useful_life'][hp_range]

            # append equipment information to string for population file
            lines += """{fips} \t {year} \t {scc} \t {equip_name} \t {hp_min} \t {hp_max} \t {hp} \t {useful_life} \t DEFAULT \t {pop} \n""".format(**self.kvals)

        return lines
