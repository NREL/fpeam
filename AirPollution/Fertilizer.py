import SaveDataHelper
from src.AirPollution.utils import config


class Fertilizer(SaveDataHelper.SaveDataHelper):
    """
    Used to populate the newly created schema that stores emmision info.
    Inserts data into feed_nfert for emmisions from fertilizers.
    Adds emmisions to N0X and NH3, which come from the production of fertilizers.
    """

    def __init__(self, cont):
        """

        :param cont: container object
        :return:
        """

        SaveDataHelper.SaveDataHelper.__init__(self, cont=cont)
        # gets used to save query to a text file for debugging purposes.
        self.document_file = "Fertilizer"

        # add fert distributions here. List of fertilizers.
        self.fert_dist = config['fert_dist']
        self.n_fert_ef = config['n_fert_ef']  # dictionary of fertilizer emission factor
        self.scc_dict = config['scc_dict']  # dictionary of fertilizer source category codes
        self.descrip_dict = config['descrip_dict']  # dictionary of fertilizer descriptions
        self.n_fert_app = config['n_fert_app']  # amount of nitrogen fertilizer applied for national crop budget
        self.cont = cont
        self.col_dict = {'cg': 'n_lbac',
                         'cs': 'n_lbdt',
                         'ws': 'n_lbdt',
                         'sg_yr1': 'n_lbac',
                         'sg_yr2to10': 'n_lbdt',
                         'ms_yr1': 'n_lbac',
                         'ms_yr2to10': 'n_lbdt', }

        self.kvals = self.cont.get('kvals')

    def regional_fert(self, feed, yr):
        """
        Add fertilizer emissions to database tables using regional crop budget

        For a specific pollutant (NOx or NH3), feedstock, and fertilizer type:
        Emissions (mt pollutant/county/year)  = ( Prod or acreage (dt or acres feedstock/county/year) *
                                                  amount of nitrogen fertilizer applied to feedstock (lb N fert/dt or lb N fert/ac feedstock) *
                                                  nitrogen share by fertilizer type (lb fert/lb N fert)
                                                  emission factor (amount nitrogen in fertilizer volatilized by fertilizer type; lb N/lb fert = % N / 100) *
                                                  conversion factor to convert from N to pollutant (i.e., 30/14 for NO and 17/14 for NH3; lb pollutant/lb N) *
                                                  convert lbs to mt)

        For N_app in lb/dt:

        E_NO_fert_type  = (Prod * N_app * N_share * N_fert_percent_ef / 100.0 * 30.0 / 14.0 * 0.90718474 / 2000.0) over all fertilizer types
        E_NH3_fert_type = (Prod * N_app * N_share * N_fert_percent_ef / 100.0 * 17.0 / 14.0 * 0.90718474 / 2000.0) over all fertilizer types

        For N_app in lb/ac:

        E_NO_fert_type  = (Harv_ac * N_app * N_share * N_fert_percent_ef / 100.0 * 30.0 / 14.0 * 0.90718474 / 2000.0) over all fertilizer types
        E_NH3_fert_type = (Harv_ac * N_app * N_share * N_fert_percent_ef / 100.0 * 17.0 / 14.0 * 0.90718474 / 2000.0) over all fertilizer types

        :param feed: feedstock
        :param yr: budget year (for energy crops)
        :return:
        """
        # set feedstock
        self.kvals['feed'] = feed.lower()

        # set column name for N fertilizer data
        if feed != 'SG' and feed != 'MS':
            self.kvals['n_column'] = self.col_dict[feed.lower()]
        else:
            if yr == 1:
                name = '%s_yr1' % (feed.lower(), )
                self.kvals['n_column'] = self.col_dict[name]
            elif yr > 1:
                name = '%s_yr2to10' % (feed.lower(), )
                self.kvals['n_column'] = self.col_dict[name]

        # set year for crop budget
        self.kvals['yr'] = yr

        for fert in self.descrip_dict:
            self.kvals['scc'] = self.scc_dict[fert]
            self.kvals['description'] = self.descrip_dict[fert]

            # emission factor: total mt NO per dt feedstock
            self.kvals['emissions_nox'] = float(self.fert_dist[feed][fert]) * float(self.n_fert_ef['NOX'][fert]) / 100.0 * 30.0 / 14.0 * 0.90718474 / 2000.0
            # emission factor: total mt NH3 per dt feedstock
            self.kvals['emissions_nh3'] = float(self.fert_dist[feed][fert]) * float(self.n_fert_ef['NH3'][fert]) / 100.0 * 17.0 / 14.0 * 0.90718474 / 2000.0

            if feed == 'SG':
                till_dict = {'NT': 'notill'}
            elif feed == 'MS':
                till_dict = {'CT': 'convtill'}
            else:
                till_dict = {'CT': 'convtill',
                             'RT': 'reducedtill',
                             'NT': 'notill'}

            for tillage in till_dict:
                self.kvals['tillage'] = tillage
                self.kvals['tillage_name'] = till_dict[tillage]

                # set tillage selection for data (if RT then same as CT)
                if tillage == 'RT':
                    self.kvals['tillage_select'] = 'CT'
                else:
                    self.kvals['tillage_select'] = tillage

                if self.kvals['n_column'].endswith('dt'):
                    fert_query = """INSERT INTO {scenario_name}.{feed}_nfert
                                     SELECT  feed.fips,
                                             '{tillage}',
                                             '{yr}',
                                             feed.{tillage_name}_prod * nfert.n_app * {emissions_nox} AS NOX,
                                             feed.{tillage_name}_prod * nfert.n_app * {emissions_nh3} AS NH3,
                                             ({scc}) AS SCC,
                                             '{description}' AS Description
                                     FROM {production_schema}.{feed}_data feed
                                     LEFT JOIN (SELECT fips, sum({n_column}) as n_app
                                                FROM {production_schema}.{feed}_equip_fips
                                                WHERE tillage = '{tillage_select}' AND bdgtyr = '{yr}'
                                                GROUP BY fips) nfert
                                     ON nfert.fips = feed.fips
                                     GROUP BY feed.fips;""".format(**self.kvals)
                    self._execute_query(fert_query)
                elif self.kvals['n_column'].endswith('ac'):
                    fert_query = """INSERT INTO {scenario_name}.{feed}_nfert
                                     SELECT  feed.fips,
                                             '{tillage}',
                                             '{yr}',
                                             feed.{tillage_name}_harv_ac * nfert.n_app * {emissions_nox} AS NOX,
                                             feed.{tillage_name}_harv_ac * nfert.n_app * {emissions_nh3} AS NH3,
                                             ({scc}) AS SCC,
                                             '{description}' AS Description
                                     FROM {production_schema}.{feed}_data feed
                                     LEFT JOIN (SELECT fips, sum({n_column}) as n_app
                                                FROM {production_schema}.{feed}_equip_fips
                                                WHERE tillage = '{tillage_select}' AND bdgtyr = '{yr}'
                                                GROUP BY fips) nfert
                                     ON nfert.fips = feed.fips
                                     GROUP BY feed.fips;""".format(**self.kvals)
                    self._execute_query(fert_query)

    def set_fertilizer(self, feed):
        """
        Add fertilizer emissions to database tables using national crop budget

        :param feed: feedstock
        :return:

        """

        query = None

        if feed == 'CS':
            query = self.__corn_stover__(feed)
        elif feed == 'WS':
            query = self.__wheat_straw__(feed)
        elif feed == 'CG':
            query = self.__corn_grain__()
        elif feed == 'SG':
            query = self.__switchgrass__(feed)

        if query is not None:
            self._execute_query(query)

    def __corn_stover__(self, feed):
        """
        NOX N_app data is in units of % of N volatilized as NO
        NH3 N_app data is in units of % of N volatilized as NH3
        
        For a specific pollutant (NO or NH3), feedstock, and fertilizer type:
        Emissions (mt pollutant/county/year)  = Prod (dt feedstock/county/year) * N_applied for feedstock (lb N/dt feedstock) * nitrogen share by fertilizer type (lb N in AA/lb N) * 1/100 * emission factor (amount volatized as pollutant by fertilizer type %; lb N/lb fert) * conversion factor to convert from N to pollutant (i.e., 30/14 for NO and 17/14 for NH3; lb pollutant/lb N) * convert lbs to mt 

        Total emissions are then given by: 
        
        E_NO  = sum(Prod * N_app * N_share * N_fert_percent_ef / 100.0 * 30.0 / 14.0 * 0.90718474 / 2000.0) over all fertilizer types 
        E_NH3 = sum(Prod * N_app * N_share * N_fert_percent_ef / 100.0 * 17.0 / 14.0 * 0.90718474 / 2000.0) over all fertilizer types 

        :param feed: feedstock
        :return: string

        """

        self.kvals = self.cont.get('kvals')

        fert_query = ''

        for fert in self.descrip_dict:
            self.kvals['scc'] = self.scc_dict[fert]
            self.kvals['description'] = self.descrip_dict[fert]

            # emission factor: total mt NO per dt feedstock
            self.kvals['emissions_nox'] = float(self.n_fert_app[feed]) * float(self.fert_dist[feed][fert]) * float(self.n_fert_ef['NOX'][fert]) / 100.0 * 30.0 / 14.0 * 0.90718474 / 2000.0
            # emission factor: total mt NH3 per dt feedstock
            self.kvals['emissions_nh3'] = float(self.n_fert_app[feed]) * float(self.fert_dist[feed][fert]) * float(self.n_fert_ef['NH3'][fert]) / 100.0 * 17.0 / 14.0 * 0.90718474 / 2000.0

            till_dict = {'CT': 'convtill',
                         'RT': 'reducedtill',
                         'NT': 'notill'}

            for till in till_dict:
                self.kvals['tillage'] = till_dict[till]
                self.kvals['till'] = till
                fert_query += """INSERT INTO {scenario_name}.{feed}_nfert
                                 SELECT feed.fips,
                                 '{till}',
                                 '1',
                                 feed.{tillage}_prod * {emissions_nox} AS NOX,
                                 feed.{tillage}_prod * {emissions_nh3} AS NH3,
                                 ({scc}) AS SCC,
                                 '{description}' AS Description
                                 FROM {production_schema}.{feed}_data feed
                                 GROUP BY feed.fips;\n""".format(**self.kvals)

        if fert_query == '':
            fert_query = None

        return fert_query

    def __wheat_straw__(self, feed):
        return self.__corn_stover__(feed)
   
    def __switchgrass__(self, feed):
        return self.__corn_stover__(feed)

    def __corn_grain__(self):

        self.kvals = self.cont.get('kvals')

        fert_query = """INSERT INTO {scenario_name}.cg_nfert""".format(**self.kvals)

        till_dict = {'CT': 'convtill',
                     'RT': 'reducedtill',
                     'NT': 'notill'}

        n_till_dict = {'CT': 'Conventional_N ',
                         'RT': 'Conventional_N ',
                         'NT': 'NoTill_N'}

        i = 0
        for till in till_dict:
            self.kvals['till']
            self.kvals['tillage'] = till_dict[till]
            self.kvals['n_till'] = n_till_dict[till]
            for fert in self.descrip_dict:
                if i > 0:
                    fert_query += """
                                  UNION
                                  """
                # set additional values in dictionary for string formatting
                self.kvals['fert_dist'] = self.fert_dist['CG'][fert]
                self.kvals['fert_ef_nh3'] = self.n_fert_ef['NH3'][fert]
                self.kvals['fert_ef_nox'] = self.n_fert_ef['NOX'][fert]
                self.kvals['scc'] = self.scc_dict[fert]
                self.kvals['description'] = self.descrip_dict[fert]

                fert_query += """
                                    (   SELECT cd.fips,
                                                '{till}',
                                                '1',

                                        (((n.{n_till} * cd.{tillage}_harv_ac) / 2000.0) * ({fert_dist} * {fert_ef_nox} / 100) * 0.90718474 * 30.0 / 14.0) AS NOX,

                                        (((n.{n_till} * cd.{tillage}_harv_ac) / 2000.0) * ({fert_dist} * {fert_ef_nh3} / 100) * 0.90718474 * 17.0 / 14.0) AS NH3,

                                        ({scc}) AS SCC,

                                        '{description}' AS Description

                                        FROM {constants_schema}.cg_napp n, {production_schema}.cg_data cd

                                        WHERE n.fips = cd.fips

                                        GROUP BY cd.fips,
                                        cd.{tillage}_harv_ac, n.{n_till}
                                    )""".format(**self.kvals)

                i += 1

        return fert_query
