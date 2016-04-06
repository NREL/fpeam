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
        self.n_fert_app = config['n_fert_app']  # @TODO: change to DB query based FIPS
        self.cont = cont

    def set_fertilizer(self, feed):
        """
        Add fertilizer emissions to database tables.

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

            fert_query += """INSERT INTO {scenario_name}.{feed}_nfert
                             SELECT feed.fips,
                             feed.total_prod * {emissions_nox} AS NOX,
                             feed.total_prod * {emissions_nh3} AS NH3,
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

        for i, fert in enumerate(self.descrip_dict):

            # set additional values in dictionary for string formatting
            self.kvals['fert_dist'] = self.fert_dist['CG'][fert]
            self.kvals['fert_ef_nh3'] = self.n_fert_ef['NH3'][fert]
            self.kvals['fert_ef_nox'] = self.n_fert_ef['NOX'][fert]
            self.kvals['scc'] = self.scc_dict[fert]
            self.kvals['description'] = self.descrip_dict[fert]

            if i > 0:
                fert_query += """
                              UNION
                              """
            fert_query += """
                            (   SELECT cd.fips,

                                (((n.Conventional_N * cd.convtill_harv_ac +
                                   n.Conventional_N * cd.reducedtill_harv_ac +
                                   n.NoTill_N * cd.notill_harv_ac) / 2000.0) * ({fert_dist} * {fert_ef_nox} / 100) * 0.90718474 * 30.0 / 14.0) AS NOX,

                                (((n.Conventional_N * cd.convtill_harv_ac +
                                   n.Conventional_N * cd.reducedtill_harv_ac +
                                   n.NoTill_N * cd.notill_harv_ac) / 2000.0) * ({fert_dist} * {fert_ef_nh3} / 100) * 0.90718474 * 17.0 / 14.0) AS NH3,

                                ({scc}) AS SCC,

                                '{description}' AS Description

                                FROM {constants_schema}.cg_napp n, {production_schema}.cg_data cd

                                WHERE n.fips = cd.fips

                                GROUP BY cd.fips,
                                cd.convtill_harv_ac, cd.reducedtill_harv_ac,
                                cd.notill_harv_ac, n.Conventional_N, n.NoTill_N
                            )""".format(**self.kvals)

        return fert_query
