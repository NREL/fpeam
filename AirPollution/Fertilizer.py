import SaveDataHelper


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
#        self.n_fert_ef = n_fert_ef 
#        self.cs_ws_sg_napp = cs_ws_sg_napp

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
        NOX N_app data is in units of lbs of nox per ton of N nutirnent.
        NH3 N_app data is in units of % of N volatized as NH3.
        
        All for a specific fertilizer:
        Nitrogen application for feed stock (lbs fertilizer/lb feedstock) * % of fertilizer * Pollutant emmision * convert lbs to mt * Total feedstock harvested (lbs)
        (dt fertilizer/lb feedstock) * (lbs NOX / dt fertilizer) * (mt/lbs) * (lbs feedstock) = mt NOX
        
        (lbs fertilizer/lb feedstock) * (% NH3) * (mt/lbs) * (lbs feedstock) * (lbs NH3/lbs fertilizer) for (17.0/14.0)? = mt NH3
        """
        # @TODO: rewrite to use string formatting and make more readable
        # @TODO: remove feed var. isn't it always the same in each of these 'make query' functions?
        fert_query = """        
INSERT INTO """ + feed + """_nfert
    (
        --------------------------------------------------------------------------
        --This query returns the urea component 
        --------------------------------------------------------------------------
        SELECT feed.fips, 

        ((N_app.""" + feed + """ / 2000.0) * (""" + self.fert_dist[feed][self.fur] + """ * nfert.nox_ur) * 0.90718474 / 2000.0 * feed.prod) AS "NOX", 

        ((N_app.""" + feed + """ * 0.90718474 / 2000.0) * (""" + self.fert_dist[feed][self.fur] + """ * nfert.nh3_ur) * feed.prod * 17.0 / 14.0) AS "NH3",

        (2801700004) AS SCC,

        'Urea Fertilizer Emissions' AS "Description"

        FROM """ + self.db.production_schema + '.' + feed + """_data feed, """ + self.db.constants_schema + """.N_fert_EF nfert, 
        """ + self.db.constants_schema + """.CS_WS_SG_Napp N_app

        GROUP BY feed.fips, 
        nfert.nox_ur, nfert.nox_nsol, nfert.nox_as, nfert.nox_an, nfert.nox_aa,
        nfert.nh3_ur, nfert.nh3_nsol, nfert.nh3_as, nfert.nh3_an, nfert.nh3_aa,
        feed.prod, N_APP.""" + feed + """
    )
    UNION 
    (
        --------------------------------------------------------------------------
        --This query contains the Nitrogen Solutions Component
        --------------------------------------------------------------------------

        SELECT feed.fips, 

        ((N_app.""" + feed + """ / 2000.0) * (""" + self.fert_dist[feed][self.fns] + """ * nfert.nox_nsol) * 0.90718474 / 2000.0 * feed.prod) AS "NOX", 

        ((N_app.""" + feed + """ * 0.90718474 / 2000.0) * (""" + self.fert_dist[feed][self.fns] + """ * nfert.nh3_nsol) * feed.prod * 17.0 / 14.0) AS "NH3",

        (2801700003) AS SCC,

        'Nitrogen Solutions Fertilizer Emissions' AS "Description"

        FROM """ + self.db.production_schema + '.' + feed + """_data feed, """ + self.db.constants_schema + """.N_fert_EF nfert, 
        """ + self.db.constants_schema + """.CS_WS_SG_Napp N_app

        GROUP BY feed.fips, 
        nfert.nox_ur, nfert.nox_nsol, nfert.nox_as, nfert.nox_an, nfert.nox_aa,
        nfert.nh3_ur, nfert.nh3_nsol, nfert.nh3_as, nfert.nh3_an, nfert.nh3_aa,
        feed.prod, N_APP.""" + feed + """
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Anhydrous Ammonia Component
        --------------------------------------------------------------------------

        SELECT feed.fips, 

        ((N_app.""" + feed + """ / 2000.0) * (""" + self.fert_dist[feed][self.faa] + """ * nfert.nox_aa) * 0.90718474 / 2000.0 * feed.prod) AS "NOX", 

        ((N_app.""" + feed + """ * 0.90718474 / 2000.0) * (""" + self.fert_dist[feed][self.faa] + """ * nfert.nh3_aa) * feed.prod * 17.0 / 14.0) AS "NH3",

        (2801700001) AS SCC,

        'Anhydrous Ammonia Fertilizer Emissions' AS "Description"

        FROM """ + self.db.production_schema + '.' + feed + """_data feed, """ + self.db.constants_schema + """.N_fert_EF nfert, 
        """ + self.db.constants_schema + """.CS_WS_SG_Napp N_app

        GROUP BY feed.fips, 
        nfert.nox_ur, nfert.nox_nsol, nfert.nox_as, nfert.nox_an, nfert.nox_aa,
        nfert.nh3_ur, nfert.nh3_nsol, nfert.nh3_as, nfert.nh3_an, nfert.nh3_aa,
        feed.prod, N_APP.""" + feed + """
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Ammonium Nitrate component
        --------------------------------------------------------------------------

        SELECT feed.fips, 

        ((N_app.""" + feed + """ / 2000.0) * (""" + self.fert_dist[feed][self.fan] + """ * nfert.nox_an) * 0.90718474 / 2000.0 * feed.prod) AS "NOX", 

        ((N_app.""" + feed + """ * 0.90718474 / 2000.0) * (""" + self.fert_dist[feed][self.fan] + """ * nfert.nh3_an) * feed.prod * 17.0 / 14.0) AS "NH3",

        (2801700005) AS SCC,

        'Ammonium Nitrate Fertilizer Emissions' AS "Description"

        FROM """ + self.db.production_schema + '.' + feed + """_data feed, """ + self.db.constants_schema + """.N_fert_EF nfert, 
        """ + self.db.constants_schema + """.CS_WS_SG_Napp N_app

        GROUP BY feed.fips, 
        nfert.nox_ur, nfert.nox_nsol, nfert.nox_as, nfert.nox_an, nfert.nox_aa,
        nfert.nh3_ur, nfert.nh3_nsol, nfert.nh3_as, nfert.nh3_an, nfert.nh3_aa,
        feed.prod, N_APP.""" + feed + """
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Ammonium Sulfate component
        --------------------------------------------------------------------------

        SELECT feed.fips,

        ((N_app.""" + feed + """ / 2000.0) * (""" + self.fert_dist[feed][self.fas] + """ * nfert.nox_as) * 0.90718474 / 2000.0 * feed.prod) AS "NOX", 

        ((N_app.""" + feed + """ * 0.90718474 / 2000.0) * (""" + self.fert_dist[feed][self.fas] + """ * nfert.nh3_as) * feed.prod * 17.0 / 14.0) AS "NH3",

        (2801700006) AS SCC,

        'Ammonium Sulfate Fertilizer Emissions' AS "Description"

        FROM """ + self.db.production_schema + '.' + feed + """_data feed, """ + self.db.constants_schema + """.N_fert_EF nfert, 
        """ + self.db.constants_schema + """.CS_WS_SG_Napp N_app

        GROUP BY feed.fips, 
        nfert.nox_ur, nfert.nox_nsol, nfert.nox_as, nfert.nox_an, nfert.nox_aa,
        nfert.nh3_ur, nfert.nh3_nsol, nfert.nh3_as, nfert.nh3_an, nfert.nh3_aa,
        feed.prod, N_APP.""" + feed + """
    )"""
    
        return fert_query
    
    def __wheat_straw__(self, feed):
        return self.__corn_stover__(feed)

    """
    @TODO: is the GROUP BY correct? sg.fips is the only row that is being selected.
    sg.prod, nfert.nox_nsol, nfert.nh3_nsol, N_app.SG are not. Should not affect query.
    Nitrogen solution is the default fertilizer.
    """
    def __switchgrass__(self, feed):
        """
        Nitrogen application (lbs/ton of N nutrients) * harvested lbs * emmisions of nsol * lbs active / lbs fertilizer * evaporation rate
        
        (lbs fert/lbs active) * (feedstock lbs) * (pullontant lbs/ ?)? * (lbs active / lbs fert) * (lbs fert/lbs poll)
        lbs pollutant.
        """
        fert_query = """
    INSERT INTO sg_nfert 
    (
        --------------------------------------------------------------------------
        --This query contains the Nitrogen Solutions Component
        --------------------------------------------------------------------------
        
        SELECT sg.fips,  

        (N_app.""" + feed + """ / 2000.0 * sg.prod * (""" + self.fert_dist[feed][self.fns] + """ * nfert.nox_nsol) * 0.907018474 / 2000.0 * 0.9) AS "NOx",

        (N_app.""" + feed + """ * sg.prod * (""" + self.fert_dist[feed][self.fns] + """ * nfert.nh3_nsol) * 0.907018474 / 2000.0 * 17.0 / 14.0 * 0.9) AS "NH3",

        (2801700003) AS SCC,

        'Nitrogen Solutions Fertilizer Emissions' AS "Description"

        FROM  """ + self.db.production_schema + """.sg_data sg, """ + self.db.constants_schema + """.N_fert_EF nfert, """ + self.db.constants_schema + """.CS_WS_SG_Napp N_app

        GROUP BY sg.fips, sg.prod,
        nfert.nox_nsol, nfert.nh3_nsol, N_app.SG
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Urea Component
        --------------------------------------------------------------------------
        
        SELECT sg.fips,  

        (N_app.""" + feed + """ / 2000.0 * sg.prod * (""" + self.fert_dist[feed][self.fur] + """ * nfert.nox_ur) * 0.907018474 / 2000.0 * 0.9) AS "NOx",

        (N_app.""" + feed + """ * sg.prod * (""" + self.fert_dist[feed][self.fur] + """ * nfert.nh3_ur) * 0.907018474 / 2000.0 * 17.0 / 14.0 * 0.9) AS "NH3",

        (2801700003) AS SCC,

        'Urea Fertilizer Emissions' AS "Description"

        FROM  """ + self.db.production_schema + """.sg_data sg, """ + self.db.constants_schema + """.N_fert_EF nfert, """ + self.db.constants_schema + """.CS_WS_SG_Napp N_app

        GROUP BY sg.fips, sg.prod,
        nfert.nox_ur, nfert.nh3_ur, N_app.SG
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Ammonium Nitrate Component
        --------------------------------------------------------------------------
        
        SELECT sg.fips,  

        (N_app.""" + feed + """ / 2000.0 * sg.prod * (""" + self.fert_dist[feed][self.fan] + """ * nfert.nox_an) * 0.907018474 / 2000.0 * 0.9) AS "NOx",

        (N_app.""" + feed + """ * sg.prod * (""" + self.fert_dist[feed][self.fan] + """ * nfert.nh3_an) * 0.907018474 / 2000.0 * 17.0 / 14.0 * 0.9) AS "NH3",

        (2801700003) AS SCC,

        'Ammonium Nitrate Fertilizer Emissions' AS "Description"

        FROM  """ + self.db.production_schema + """.sg_data sg, """ + self.db.constants_schema + """.N_fert_EF nfert, """ + self.db.constants_schema + """.CS_WS_SG_Napp N_app

        GROUP BY sg.fips, sg.prod,
        nfert.nox_an, nfert.nh3_an, N_app.SG
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Ammonium Sulfate Component
        --------------------------------------------------------------------------
        
        SELECT sg.fips,  

        (N_app.""" + feed + """ / 2000.0 * sg.prod * (""" + self.fert_dist[feed][self.fas] + """ * nfert.nox_as) * 0.907018474 / 2000.0 * 0.9) AS "NOx",

        (N_app.""" + feed + """ * sg.prod * (""" + self.fert_dist[feed][self.fas] + """ * nfert.nh3_as) * 0.907018474 / 2000.0 * 17.0 / 14.0 * 0.9) AS "NH3",

        (2801700003) AS SCC,

        'Amonium Sulfate Fertilizer Emissions' AS "Description"

        FROM  """ + self.db.production_schema + """.sg_data sg, """ + self.db.constants_schema + """.N_fert_EF nfert, """ + self.db.constants_schema + """.CS_WS_SG_Napp N_app

        GROUP BY sg.fips, sg.prod,
        nfert.nox_as, nfert.nh3_as, N_app.SG
    )
    
"""
        return fert_query

    """
    ((dt fertilizer/acre feedstock) * acres feedstock) * (lbs NOX / dt fertilizer) * (mt/lbs) = mt NOX
        
    ((dt fertilizer/acre feedstock) * acres feedstock) * (% NH3) * (lbs NH3/lbs fertilizer)*2000->dt for (17.0/14.0) * (mt/lbs) = mt NH3
    """
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
