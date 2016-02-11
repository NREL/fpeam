import SaveDataHelper
from src.AirPollution.utils import config

class Fertilizer(SaveDataHelper.SaveDataHelper):
    """
    Used to populate the newly created schema that stores emmision info.
    Inserts data into feed_nfert for emmisions from fertilizers.
    Adds emmisions to N0X and NH3, which come from the production of fertilizers.
    """

    # order of fertilizer list.
    faa, fan, fas, fur, fns = 0, 1, 2, 3, 4  # @TODO: refactor to remove implicit ordering
    # order of feed stocks in the fertilizer list.
    fcs, fws, fcg, fsg = 'CSF', 'WSF', 'CGF', 'SGF'  # @TODO: remove; what is this? Why define these instead of using the strings directly? The strings map to keys that were definied in main.py but now ultimately come from config.ini. Doesn't seem to be used anywhere else.

    def __init__(self, cont, fert_feed_stock, fert_dist=None):
        SaveDataHelper.SaveDataHelper.__init__(self, cont=cont)
        # gets used to save query to a text file for debugging purposes.
        self.document_file = "Fertilizer"
        # add fert distributions here. List of fertilizers.
        self.fert_dist = self.get_frt_distribution(fert_distributions=fert_dist)
        self.fert_feed_stock = fert_feed_stock
        self.n_fert_ef = config['n_fert_ef'] 
        self.cs_ws_sg_napp = config['cs_ws_sg_napp']
        self.kvals = {}

    def set_fertilizer(self, feed):
        """
        Pick the correct feed stock and add fertilizer emmisions to the db.
        Only one not in use is forest residue b/c it is a forest and does not need fertilizer to grow.
        @param feed: feed stock. 
        """    
        # table format in database
        #    FIPS    char(5)    ,
        #    NOx    float    ,
        #    NH3    float    ,
        #    SCC    char(10)    ,
        #    description    text   
        if feed != 'FR':
            # grab all of the queries.
            query = None
            if feed == 'CS' and self.fert_feed_stock['CSF'] is True:
                query = self.__corn_stover__(feed)
            elif feed == 'WS' and self.fert_feed_stock['WSF'] is True:
                query = self.__wheat_straw__(feed)
            elif feed == 'CG' and self.fert_feed_stock['CGF'] is True:
                query = self.__corn_grain__()
            elif feed == 'SG' and self.fert_feed_stock['SGF'] is True:
                query = self.__switchgrass__(feed)
            # if a query was created, execute it.
            if query is not None:
                self._execute_query(query)

    def get_frt_distribution(self, fert_distributions):
        """
        Get fertilizer distribution. The user can either input their own distribution, 
        or use the predefined distribution on the db.
        @param fert_distributions: Distribution of the the five different fertilizers. dict(string: list(string)
        @return: Distribution of the five different fertilizers as a percentage. Must sum up to 1.
        Order: annhydrous_amonia, ammonium_nitrate, ammonium_sulfate, urea, nsol. (list(string))
        """    
        fert_final = {}
        for feed, fert_distribution in fert_distributions.items():
            if fert_distribution: 
                fert_final[feed] = fert_distribution
            else:
                if feed is not 'SG':
                    query = """SELECT * 
                            FROM """ + self.db.constants_schema + """.n_fert_distribution""" 
                    fert_dist = self.db.output(query, self.db.constants_schema)
                    # convert db data to usable strings.
                    fert_dist = [str(f) for f in fert_dist[0]]
                # switch grass only uses nitrogen solution nsol.
                else:
                    fert_dist = ['0', '0', '0', '0', '1']
                fert_final[feed] = fert_dist
        return fert_final
                
    def __corn_stover__(self, feed):
        """
        NOX N_app data is in units of % of N volatilized as NO
        NH3 N_app data is in units of % of N volatilized as NH3
        
        For a specific pollutant (NO or NH3), feedstock, and fertilizer type:
        Emissions (mt pollutant/county/year)  = Prod (dt feedstock/county/year) * N_applied for feedstock (lb N/dt feedstock) * nitrogen share by fertilizer type (lb N in AA/lb N) * 1/100 * emission factor (amount volatized as pollutant by fertilizer type %; lb N/lb fert) * conversion factor to convert from N to pollutant (i.e., 30/14 for NO and 17/14 for NH3; lb pollutant/lb N) * convert lbs to mt 

        Total emissions are then given by: 
        
        E_NO  = sum(Prod * N_app * N_share * N_fert_percent_ef/100 * 30/14 * 0.90718474 / 2000.0) over all fertilizer types 
        E_NH3 = sum(Prod * N_app * N_share * N_fert_percent_ef/100 * 17/14 * 0.90718474 / 2000.0) over all fertilizer types 
        
        """
        # @TODO: rewrite to use string formatting and make more readable
        # @TODO: remove feed var. isn't it always the same in each of these 'make query' functions?

        ef_nox = 0
        ef_nh3 = 0
        for numfert in range(0,5):
           ef_nox = ef_nox + float(self.cs_ws_sg_napp[feed])*float(self.fert_dist[feed][numfert])*float(self.n_fert_ef['NOX'][numfert])/100 * 30/14 * 0.90718474 / 2000.0 # emission factor: total mt NO per dt feedstock
           ef_nh3 = ef_nh3 + float(self.cs_ws_sg_napp[feed])*float(self.fert_dist[feed][numfert])*float(self.n_fert_ef['NH3'][numfert])/100 * 17/14 * 0.90718474 / 2000.0 # emission factor: total mt NH3 per dt feedstock 
        
        kvals = {}        
        kvals['nox']=ef_nox
        kvals['nh3']=ef_nh3
        
        fert_query =("""INSERT INTO """ + feed + """_nfert
        SELECT feed.fips, 
        feed.prod * {nox} AS "NOX",
        feed.prod * {nh3} AS "NH3",
        (2801700004) AS SCC,
        'Fertilizer Emissions' AS "Description"
        FROM """ + self.db.production_schema + '.' + feed + """_data feed
        GROUP BY feed.fips;""").format(**kvals)
        
        return fert_query 
        

    def __wheat_straw__(self, feed):
        return self.__corn_stover__(feed)

   
    def __switchgrass__(self, feed):
       return self.__corn_stover__(feed)
   
   
    def __corn_grain__(self):
        fert_query = """
INSERT INTO cg_nfert
    (
        --------------------------------------------------------------------------
        --This query returns the urea component 
        --------------------------------------------------------------------------
        SELECT cd.fips, 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fert_dist['CG'][self.fur] + """ * nfert.nox_ur) * 0.90718474 / 2000.0) AS "NOX", 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fert_dist['CG'][self.fur] + """ * nfert.nh3_ur) * 0.90718474 * 17.0 / 14.0) AS "NH3",

        (2801700004) AS SCC,

        'Urea Fertilizer Emissions' AS "Description"

        FROM """ + self.db.constants_schema + """.cg_napp n, """ + self.db.constants_schema + """.N_fert_EF nfert, 
        """ + self.db.production_schema + """.cg_data cd

        WHERE n.fips = cd.fips 

        GROUP BY cd.fips, 
        nfert.nox_ur, nfert.nh3_ur, cd.convtill_harv_ac, cd.reducedtill_harv_ac, 
        cd.notill_harv_ac, n.Conventional_N, n.NoTill_N
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Nitrogen Solutions Component
        --------------------------------------------------------------------------

        SELECT cd.fips, 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fert_dist['CG'][self.fns] + """ * nfert.nox_nsol) * 0.90718474 / 2000.0) AS "NOX", 

        (((n.Conventional_N * cd.convtill_harv_ac +
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fert_dist['CG'][self.fns] + """ * nfert.nh3_nsol) * 0.90718474 * 17.0 / 14.0) AS "NH3",

        (2801700003) AS SCC,

        'Nitrogen Solutions Fertilizer Emissions' AS "Description"

        FROM """ + self.db.constants_schema + """.cg_napp n, """ + self.db.constants_schema + """.N_fert_EF nfert,
        """ + self.db.production_schema + """.cg_data cd

        WHERE n.fips = cd.fips 

        GROUP BY cd.fips, n.polysys_region_id, 
        nfert.nox_nsol, nfert.nh3_nsol, cd.convtill_harv_ac, cd.reducedtill_harv_ac, 
        cd.notill_harv_ac, n.Conventional_N, n.NoTill_N
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Anhydrous Ammonia Component
        --------------------------------------------------------------------------

        SELECT cd.fips, 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fert_dist['CG'][self.faa] + """ * nfert.nox_aa) * 0.90718474 / 2000.0) AS "NOX", 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fert_dist['CG'][self.faa] + """ * nfert.nh3_aa) * 0.90718474 * 17.0 / 14.0) AS "NH3",

        (2801700001) AS SCC,

        'Anhydrous Ammonia Fertilizer Emissions' AS "Description"

        FROM """ + self.db.constants_schema + """.cg_napp n, """ + self.db.constants_schema + """.N_fert_EF nfert,
        """ + self.db.production_schema + """.cg_data cd

        WHERE n.fips = cd.fips 

        GROUP BY cd.fips, n.polysys_region_id, 
        nfert.nox_aa, nfert.nh3_aa, cd.convtill_harv_ac, cd.reducedtill_harv_ac, 
        cd.notill_harv_ac, n.Conventional_N, n.NoTill_N
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Ammonium Nitrate component
        --------------------------------------------------------------------------

        SELECT cd.fips, 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fert_dist['CG'][self.fan] + """ * nfert.nox_an) * 0.90718474 / 2000.0) AS "NOX", 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fert_dist['CG'][self.fan] + """ * nfert.nh3_an) * 0.90718474 * 17.0 / 14.0) AS "NH3",

        (2801700005) AS SCC,

        'Ammonium Nitrate Fertilizer Emissions' AS "Description"

        FROM """ + self.db.constants_schema + """.cg_napp n, """ + self.db.constants_schema + """.N_fert_EF nfert,
        """ + self.db.production_schema + """.cg_data cd

        WHERE n.fips = cd.fips 

        GROUP BY cd.fips, n.polysys_region_id, 
        nfert.nox_an, nfert.nh3_an, cd.convtill_harv_ac, cd.reducedtill_harv_ac,
        cd.notill_harv_ac, n.Conventional_N, n.NoTill_N
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Ammonium Sulfate component
        --------------------------------------------------------------------------

        SELECT cd.fips, 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fert_dist['CG'][self.fas] + """ * nfert.nox_as) * 0.90718474 / 2000.0) AS "NOX", 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fert_dist['CG'][self.fas] + """ * nfert.nh3_as) * 0.90718474 * 17.0 / 14.0) AS "NH3",

        (2801700006) AS SCC,

        'Ammonium Sulfate Fertilizer Emissions' AS "Description"

        FROM """ + self.db.constants_schema + """.cg_napp n, """ + self.db.constants_schema + """.N_fert_EF nfert,
        """ + self.db.production_schema + """.cg_data cd

        WHERE n.fips = cd.fips 

        GROUP BY cd.fips, n.polysys_region_id, 
        nfert.nox_as, nfert.nh3_as, cd.convtill_harv_ac, cd.reducedtill_harv_ac,
        cd.notill_harv_ac, n.Conventional_N, n.NoTill_N
    )
 """

        return fert_query
