import SaveDataHelper

'''
Used to populate the newly created schema that stores emmision info.
Inserts data into feed_nfert for emmisions from fertilizers.
Adds emmisions to N0X and NH3, which come from the production of fertilizers.
'''
class Fertilizer(SaveDataHelper.SaveDataHelper):
    
    # order of fertilizer list.
    faa, fan, fas, fur, fns = 0, 1, 2, 3, 4
    # order of feed stocks in the fertilizer list.
    fcs, fws, fcg, fsg = 'CSF', 'WSF', 'CGF', 'SGF'
    
    def __init__(self, cont, fertFeedStock, fertDist=False):
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        # gets used to save query to a text file for debugging purposes.
        self.documentFile = "Fertilizer"
        # add fert distributions here. List of fertilizers.
        self.fertDist = self.getFrtDistribution(fertDist)
        self.fertFeedStock = fertFeedStock
    
    '''
    Pick the correct feed stock and add fertilizer emmisions to the db.
    Only one not in use is forest residue b/c it is a forest and does not need fertilizer to grow.
    @param feed: feed stock. 
    '''    
    def setFertilizer(self, feed):
#table format in database        
#    FIPS    char(5)    ,
#    NOx    float    ,
#    NH3    float    ,
#    SCC    char(10)    ,
#    description    text   
        if feed != 'FR':
            # grab all of the queries.
            query = ''
            if feed == 'CS' and self.fertFeedStock[self.fcs]:
                query = self.__cornStover__(feed)
        
            elif feed == 'WS' and self.fertFeedStock[self.fws]:
                query = self.__wheatStraw__(feed)
                
            elif feed == 'CG' and self.fertFeedStock[self.fcg]:
                query = self.__cornGrain__()
                
            elif feed == 'SG' and self.fertFeedStock[self.fsg]:
                query = self.__switchgrass__(feed)
            # if a query was called execute it.
            if query: self._executeQuery(query)
    
    '''
    Get fertilizer distribution. The user can either input their own distribution, 
    or use the predefined distribution on the db.
    @param fertDistribution: Distribution of the the five different fertilizers. dict(string: list(string)
    @return: Distribution of the five different fertilizers as a percentage. Must sum up to 1.
    Order: annhydrous_amonia, ammonium_nitrate, ammonium_sulfate, urea, nsol. (list(string))
    '''    
    def getFrtDistribution(self, fertDistributions):
        fertFinal = {}
        for feed, fertDistribution in fertDistributions.items():
            if fertDistribution: 
                fertFinal[feed] = fertDistribution
            else:
                if feed is not 'SG':
                    query = """SELECT * 
                            FROM """ + self.db.constantsSchema + """.n_fert_distribution""" 
                    fertDist = self.db.output(query, self.db.constantsSchema)
                    # convert db data to usable strings.
                    fertDist = [str(f) for f in fertDist[0]]
                # switch grass only uses nitrogen solution nsol.
                else: fertDist = ['0', '0', '0', '0', '1']
                fertFinal[feed] = fertDist
        return fertFinal
                
    def __cornStover__(self, feed):
        '''
        NOX N_app data is in units of lbs of nox per ton of N nutirnent.
        NH3 N_app data is in units of % of N volatized as NH3.
        
        All for a specific fertilizer:
        Nitrogen application for feed stock (lbs fertilizer/lb feedstock) * % of fertilizer * Pollutant emmision * convert lbs to mt * Total feedstock harvested (lbs)
        (dt fertilizer/lb feedstock) * (lbs NOX / dt fertilizer) * (mt/lbs) * (lbs feedstock) = mt NOX
        
        (lbs fertilizer/lb feedstock) * (% NH3) * (mt/lbs) * (lbs feedstock) * (lbs NH3/lbs fertilizer) for (17.0/14.0)? = mt NH3
        '''
        fertQuery = """        
INSERT INTO """ + feed + """_nfert
    (
        --------------------------------------------------------------------------
        --This query returns the urea component 
        --------------------------------------------------------------------------
        SELECT feed.fips, 

        ((N_app.""" + feed + """ / 2000.0) * (""" + self.fertDist[feed][self.fur] + """ * nfert.nox_ur) * 0.90718474 / 2000.0 * feed.prod) AS "NOX", 

        ((N_app.""" + feed + """ * 0.90718474 / 2000.0) * (""" + self.fertDist[feed][self.fur] + """ * nfert.nh3_ur) * feed.prod * 17.0 / 14.0) AS "NH3",

        (2801700004) AS SCC,

        'Urea Fertilizer Emissions' AS "Description"

        FROM """ + self.db.productionSchema + '.' + feed + """_data feed, """ + self.db.constantsSchema + """.N_fert_EF nfert, 
        """ + self.db.constantsSchema + """.CS_WS_SG_Napp N_app

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

        ((N_app.""" + feed + """ / 2000.0) * (""" + self.fertDist[feed][self.fns] + """ * nfert.nox_nsol) * 0.90718474 / 2000.0 * feed.prod) AS "NOX", 

        ((N_app.""" + feed + """ * 0.90718474 / 2000.0) * (""" + self.fertDist[feed][self.fns] + """ * nfert.nh3_nsol) * feed.prod * 17.0 / 14.0) AS "NH3",

        (2801700003) AS SCC,

        'Nitrogen Solutions Fertilizer Emissions' AS "Description"

        FROM """ + self.db.productionSchema + '.' + feed + """_data feed, """ + self.db.constantsSchema + """.N_fert_EF nfert, 
        """ + self.db.constantsSchema + """.CS_WS_SG_Napp N_app

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

        ((N_app.""" + feed + """ / 2000.0) * (""" + self.fertDist[feed][self.faa] + """ * nfert.nox_aa) * 0.90718474 / 2000.0 * feed.prod) AS "NOX", 

        ((N_app.""" + feed + """ * 0.90718474 / 2000.0) * (""" + self.fertDist[feed][self.faa] + """ * nfert.nh3_aa) * feed.prod * 17.0 / 14.0) AS "NH3",

        (2801700001) AS SCC,

        'Anhydrous Ammonia Fertilizer Emissions' AS "Description"

        FROM """ + self.db.productionSchema + '.' + feed + """_data feed, """ + self.db.constantsSchema + """.N_fert_EF nfert, 
        """ + self.db.constantsSchema + """.CS_WS_SG_Napp N_app

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

        ((N_app.""" + feed + """ / 2000.0) * (""" + self.fertDist[feed][self.fan] + """ * nfert.nox_an) * 0.90718474 / 2000.0 * feed.prod) AS "NOX", 

        ((N_app.""" + feed + """ * 0.90718474 / 2000.0) * (""" + self.fertDist[feed][self.fan] + """ * nfert.nh3_an) * feed.prod * 17.0 / 14.0) AS "NH3",

        (2801700005) AS SCC,

        'Ammonium Nitrate Fertilizer Emissions' AS "Description"

        FROM """ + self.db.productionSchema + '.' + feed + """_data feed, """ + self.db.constantsSchema + """.N_fert_EF nfert, 
        """ + self.db.constantsSchema + """.CS_WS_SG_Napp N_app

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

        ((N_app.""" + feed + """ / 2000.0) * (""" + self.fertDist[feed][self.fas] + """ * nfert.nox_as) * 0.90718474 / 2000.0 * feed.prod) AS "NOX", 

        ((N_app.""" + feed + """ * 0.90718474 / 2000.0) * (""" + self.fertDist[feed][self.fas] + """ * nfert.nh3_as) * feed.prod * 17.0 / 14.0) AS "NH3",

        (2801700006) AS SCC,

        'Ammonium Sulfate Fertilizer Emissions' AS "Description"

        FROM """ + self.db.productionSchema + '.' + feed + """_data feed, """ + self.db.constantsSchema + """.N_fert_EF nfert, 
        """ + self.db.constantsSchema + """.CS_WS_SG_Napp N_app

        GROUP BY feed.fips, 
        nfert.nox_ur, nfert.nox_nsol, nfert.nox_as, nfert.nox_an, nfert.nox_aa,
        nfert.nh3_ur, nfert.nh3_nsol, nfert.nh3_as, nfert.nh3_an, nfert.nh3_aa,
        feed.prod, N_APP.""" + feed + """
    )"""
    
        return fertQuery
   
   
    
    def __wheatStraw__(self, feed):
        return self.__cornStover__(feed)
        
    
    '''
    TODO: is the GROUP BY correct? sg.fips is the only row that is being selected.
    sg.prod, nfert.nox_nsol, nfert.nh3_nsol, N_app.SG are not. Should not affect query.
    Nitrogen solution is the default fertilizer.
    '''
    def __switchgrass__(self, feed):
        '''
        Nitrogen application (lbs/ton of N nutrients) * harvested lbs * emmisions of nsol * lbs active / lbs fertilizer * evaporation rate
        
        (lbs fert/lbs active) * (feedstock lbs) * (pullontant lbs/ ?)? * (lbs active / lbs fert) * (lbs fert/lbs poll)
        lbs pollutant.
        '''
        fertQuery = """
    INSERT INTO sg_nfert 
    (
        --------------------------------------------------------------------------
        --This query contains the Nitrogen Solutions Component
        --------------------------------------------------------------------------
        
        SELECT sg.fips,  

        (N_app.""" + feed + """ / 2000.0 * sg.prod * (""" + self.fertDist[feed][self.fns] + """ * nfert.nox_nsol) * 0.907018474 / 2000.0 * 0.9) AS "NOx",

        (N_app.""" + feed + """ * sg.prod * (""" + self.fertDist[feed][self.fns] + """ * nfert.nh3_nsol) * 0.907018474 / 2000.0 * 17.0 / 14.0 * 0.9) AS "NH3",

        (2801700003) AS SCC,

        'Nitrogen Solutions Fertilizer Emissions' AS "Description"

        FROM  """ + self.db.productionSchema + """.sg_data sg, """ + self.db.constantsSchema + """.N_fert_EF nfert, """ + self.db.constantsSchema + """.CS_WS_SG_Napp N_app

        GROUP BY sg.fips, sg.prod,
        nfert.nox_nsol, nfert.nh3_nsol, N_app.SG
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Urea Component
        --------------------------------------------------------------------------
        
        SELECT sg.fips,  

        (N_app.""" + feed + """ / 2000.0 * sg.prod * (""" + self.fertDist[feed][self.fur] + """ * nfert.nox_ur) * 0.907018474 / 2000.0 * 0.9) AS "NOx",

        (N_app.""" + feed + """ * sg.prod * (""" + self.fertDist[feed][self.fur] + """ * nfert.nh3_ur) * 0.907018474 / 2000.0 * 17.0 / 14.0 * 0.9) AS "NH3",

        (2801700003) AS SCC,

        'Urea Fertilizer Emissions' AS "Description"

        FROM  """ + self.db.productionSchema + """.sg_data sg, """ + self.db.constantsSchema + """.N_fert_EF nfert, """ + self.db.constantsSchema + """.CS_WS_SG_Napp N_app

        GROUP BY sg.fips, sg.prod,
        nfert.nox_ur, nfert.nh3_ur, N_app.SG
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Ammonium Nitrate Component
        --------------------------------------------------------------------------
        
        SELECT sg.fips,  

        (N_app.""" + feed + """ / 2000.0 * sg.prod * (""" + self.fertDist[feed][self.fan] + """ * nfert.nox_an) * 0.907018474 / 2000.0 * 0.9) AS "NOx",

        (N_app.""" + feed + """ * sg.prod * (""" + self.fertDist[feed][self.fan] + """ * nfert.nh3_an) * 0.907018474 / 2000.0 * 17.0 / 14.0 * 0.9) AS "NH3",

        (2801700003) AS SCC,

        'Ammonium Nitrate Fertilizer Emissions' AS "Description"

        FROM  """ + self.db.productionSchema + """.sg_data sg, """ + self.db.constantsSchema + """.N_fert_EF nfert, """ + self.db.constantsSchema + """.CS_WS_SG_Napp N_app

        GROUP BY sg.fips, sg.prod,
        nfert.nox_an, nfert.nh3_an, N_app.SG
    )
    UNION
    (
        --------------------------------------------------------------------------
        --This query contains the Ammonium Sulfate Component
        --------------------------------------------------------------------------
        
        SELECT sg.fips,  

        (N_app.""" + feed + """ / 2000.0 * sg.prod * (""" + self.fertDist[feed][self.fas] + """ * nfert.nox_as) * 0.907018474 / 2000.0 * 0.9) AS "NOx",

        (N_app.""" + feed + """ * sg.prod * (""" + self.fertDist[feed][self.fas] + """ * nfert.nh3_as) * 0.907018474 / 2000.0 * 17.0 / 14.0 * 0.9) AS "NH3",

        (2801700003) AS SCC,

        'Amonium Sulfate Fertilizer Emissions' AS "Description"

        FROM  """ + self.db.productionSchema + """.sg_data sg, """ + self.db.constantsSchema + """.N_fert_EF nfert, """ + self.db.constantsSchema + """.CS_WS_SG_Napp N_app

        GROUP BY sg.fips, sg.prod,
        nfert.nox_as, nfert.nh3_as, N_app.SG
    )
    
"""
        return fertQuery


    '''
    ((dt fertilizer/acre feedstock) * acres feedstock) * (lbs NOX / dt fertilizer) * (mt/lbs) = mt NOX
        
    ((dt fertilizer/acre feedstock) * acres feedstock) * (% NH3) * (lbs NH3/lbs fertilizer)*2000->dt for (17.0/14.0) * (mt/lbs) = mt NH3
    '''
    def __cornGrain__(self):
        fertQuery = """
INSERT INTO cg_nfert
    (
        --------------------------------------------------------------------------
        --This query returns the urea component 
        --------------------------------------------------------------------------
        SELECT cd.fips, 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fertDist['CG'][self.fur] + """ * nfert.nox_ur) * 0.90718474 / 2000.0) AS "NOX", 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fertDist['CG'][self.fur] + """ * nfert.nh3_ur) * 0.90718474 * 17.0 / 14.0) AS "NH3",

        (2801700004) AS SCC,

        'Urea Fertilizer Emissions' AS "Description"

        FROM """ + self.db.constantsSchema + """.cg_napp n, """ + self.db.constantsSchema + """.N_fert_EF nfert, 
        """ + self.db.productionSchema + """.cg_data cd

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
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fertDist['CG'][self.fns] + """ * nfert.nox_nsol) * 0.90718474 / 2000.0) AS "NOX", 

        (((n.Conventional_N * cd.convtill_harv_ac +
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fertDist['CG'][self.fns] + """ * nfert.nh3_nsol) * 0.90718474 * 17.0 / 14.0) AS "NH3",

        (2801700003) AS SCC,

        'Nitrogen Solutions Fertilizer Emissions' AS "Description"

        FROM """ + self.db.constantsSchema + """.cg_napp n, """ + self.db.constantsSchema + """.N_fert_EF nfert,
        """ + self.db.productionSchema + """.cg_data cd

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
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fertDist['CG'][self.faa] + """ * nfert.nox_aa) * 0.90718474 / 2000.0) AS "NOX", 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fertDist['CG'][self.faa] + """ * nfert.nh3_aa) * 0.90718474 * 17.0 / 14.0) AS "NH3",

        (2801700001) AS SCC,

        'Anhydrous Ammonia Fertilizer Emissions' AS "Description"

        FROM """ + self.db.constantsSchema + """.cg_napp n, """ + self.db.constantsSchema + """.N_fert_EF nfert,
        """ + self.db.productionSchema + """.cg_data cd

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
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fertDist['CG'][self.fan] + """ * nfert.nox_an) * 0.90718474 / 2000.0) AS "NOX", 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fertDist['CG'][self.fan] + """ * nfert.nh3_an) * 0.90718474 * 17.0 / 14.0) AS "NH3",

        (2801700005) AS SCC,

        'Ammonium Nitrate Fertilizer Emissions' AS "Description"

        FROM """ + self.db.constantsSchema + """.cg_napp n, """ + self.db.constantsSchema + """.N_fert_EF nfert,
        """ + self.db.productionSchema + """.cg_data cd

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
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fertDist['CG'][self.fas] + """ * nfert.nox_as) * 0.90718474 / 2000.0) AS "NOX", 

        (((n.Conventional_N * cd.convtill_harv_ac + 
           n.Conventional_N * reducedtill_harv_ac + 
           n.NoTill_N * notill_harv_ac) / 2000.0) * (""" + self.fertDist['CG'][self.fas] + """ * nfert.nh3_as) * 0.90718474 * 17.0 / 14.0) AS "NH3",

        (2801700006) AS SCC,

        'Ammonium Sulfate Fertilizer Emissions' AS "Description"

        FROM """ + self.db.constantsSchema + """.cg_napp n, """ + self.db.constantsSchema + """.N_fert_EF nfert,
        """ + self.db.productionSchema + """.cg_data cd

        WHERE n.fips = cd.fips 

        GROUP BY cd.fips, n.polysys_region_id, 
        nfert.nox_as, nfert.nh3_as, cd.convtill_harv_ac, cd.reducedtill_harv_ac,
        cd.notill_harv_ac, n.Conventional_N, n.NoTill_N
    )
 """

        return fertQuery

