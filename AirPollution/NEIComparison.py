import SaveDataHelper

'''
What is NEI?
'''
class NEIComparison(SaveDataHelper.SaveDataHelper):
    
    def __init__(self, cont):
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.documentFile = "NEIComparison"
        
        query = """
CREATE TABLE summedEmissions
(
fips    char(5)    ,
feedstock    text    ,
prod    float    ,
harv_Ac    float    ,
NOX    float    DEFAULT 0.0,
NH3    float    DEFAULT 0.0,
SOX    float    DEFAULT 0.0,
VOC    float    DEFAULT 0.0,
PM10    float    DEFAULT 0.0,
PM25    float    DEFAULT 0.0,
CO    float    DEFAULT 0.0);"""

        self._executeQuery(query)



    def __setNEIRatioTable__(self, feedstock):
        query = """
CREATE TABLE """+feedstock+"""_NEIRatio
(
fips    char(5) ,
nox    float    ,
sox    float    ,
co    float    ,
pm10    float    ,
pm25    float    ,
voc    float    ,
nh3    float);"""
        self._executeQuery(query)
        
        
    '''
    Create summed dimmensions table in the db.
    TODO: fr should have a harv_ac.

    select ca.fips, ca.st, dat.fed_minus_55 
    from constantsSchema.county_attributes ca, fr_data dat where dat.fips = ca.fips"""
    ''' 
    def createSummedEmissionsTable(self, feedstock):
        
        if feedstock == 'CG':
            f = "Corn Grain"
            prod = "dat.total_prod, dat.total_harv_ac"
        elif feedstock == 'SG':
            f = "Switchgrass"
            prod = "dat.prod, dat.harv_ac"
        elif feedstock == 'WS':
            f = "Wheat Straw"
            prod = "dat.prod, dat.harv_ac"
        elif feedstock == 'CS':
            f = "Corn Stover"
            prod = "dat.prod, dat.harv_ac"
        elif feedstock == 'FR':
            f = "Forest Residue"
            prod = "dat.fed_minus_55, 0"
        
    
        query = """
    INSERT INTO summedEmissions 
    WITH
    """
        #populate tables that have fertilizer emissions
    #    if feedstock == 'CG' or feedstock == 'SG':
        if feedstock != 'FR':    
            query += """
    Fert as (SELECT DISTINCT fips,
                    sum(nox) as nox,
                    sum(nh3) as nh3
        FROM %s_nfert
        GROUP BY fips),
    ---------------------------------------------------------------------------------------------
    """ % (feedstock)
    
        # populate table that have pesticides.
        if feedstock == 'CG' or feedstock == 'SG':
            query += """
    Chem as (SELECT DISTINCT fips,
                    sum(voc) as voc
        FROM %s_chem
        GROUP BY fips),
    ---------------------------------------------------------------------------------------------
    """ % (feedstock)
    
        # populate everything else.
        '''
        ########################
        @change: Not adding fug_pm10
        old code: (sum(pm10) + sum(fug_pm10)) AS pm10, 
                  (sum(pm25) + sum(fug_pm25)) AS pm25,
        new code: (sum(pm10) + 0.0) AS pm10, 
                  (sum(pm25) + 0.0) AS pm25,
        ########################
        '''
        query +="""
            Raw as (SELECT DISTINCT fips,
                    sum(nox) AS nox,
                    sum(nh3) AS nh3,
                    sum(sox) AS sox,
                    sum(voc) AS voc,
                    (sum(pm10) + sum(fug_pm10)) AS pm10, 
                    (sum(pm25) + sum(fug_pm25)) AS pm25,
                    (sum(co)) AS co
            FROM %s_raw
            GROUP BY fips)
    ---------------------------------------------------------------------------------------------
    """ % (feedstock)
    
    
        if feedstock == 'CG' or feedstock == 'SG': 
            query +="""
    (SELECT dat.fips, %s, %s,
        (raw.nox + fert.nox) as nox, 
        (raw.nh3 + fert.nh3) as nh3,
        (raw.sox) as sox,
        (raw.voc + chem.voc) as voc,
        (raw.pm10) as pm10,
        (raw.pm25) as pm25,
        (raw.co) as co    
        
    FROM %s dat
    
    LEFT JOIN Fert ON fert.fips = dat.fips
    LEFT JOIN Chem ON chem.fips = dat.fips
    LEFT JOIN Raw ON raw.fips = dat.fips
    )
    ;""" % ("'"+f+"'", prod, 
            self.db.productionSchema +'.'+ feedstock + "_data")


        elif feedstock == 'CS' or feedstock == 'WS':
            query +="""
    (SELECT dat.fips, %s, %s,
        (raw.nox + fert.nox) as nox, 
        (raw.nh3 + fert.nh3) as nh3,
        (raw.sox) as sox,
        (raw.voc) as voc,
        (raw.pm10) as pm10,
        (raw.pm25) as pm25,
        (raw.co) as co    
        
    FROM %s dat
    
    LEFT JOIN Fert ON fert.fips = dat.fips
    LEFT JOIN Raw ON raw.fips = dat.fips
    )
    ;""" % ("'"+f+"'", prod, 
            self.db.productionSchema +'.'+ feedstock + "_data")    
    
    
        elif feedstock == 'FR':
            query +="""
    (SELECT dat.fips, %s, %s,
        (raw.nox) as nox, 
        (raw.nh3) as nh3,
        (raw.sox) as sox,
        (raw.voc) as voc,
        (raw.pm10) as pm10,
        (raw.pm25) as pm25,
        (raw.co) as co    
        
    FROM %s dat
    
    LEFT JOIN Raw ON raw.fips = dat.fips
    )
    ;""" % ("'"+f+"'", prod, 
            self.db.productionSchema +'.'+ feedstock + "_data")            


        self._executeQuery(query)
    
 
    
    def createNEIComparison(self, feedstock):
        
        # Old NEI data from Noah.
        #self.nei_data_by_county = self.db.constantsSchema + ".nei_data_by_county"
        # new NEI data from Jeremy.
        # nei_nonroad_nonpoint and nei_total
        self.nei_data_by_county = "full2008nei.nei_total"
        # @change: Change allocation. Allocation is the amount of the feedstock that actually get's used to produce ethanol.
        # 9/3
        # old code:     self.cellulosicAllocation = 0.34
        #               self.cornGrainAllocation = 0.54
        # new code:     allocation = 0.52
        # @change: convert NEI data from short tons to metric tons.
        # 9/11
        # old code:     nei.nox
        # new code:     nei.nox * 0.907185
        allocation = str(0.52)
            
        self.__setNEIRatioTable__(feedstock)
        
        if feedstock == 'CG':
            f = 'Corn Grain'
        elif feedstock == 'SG':
            f = 'Switchgrass'
        elif feedstock == 'CS':
            f = 'Corn Stover'
        elif feedstock == 'WS':
            f = 'Wheat Straw'
        elif feedstock == 'FR':
            f = 'Forest Residue' 
        elif feedstock == 'cellulosic':
            f = 'cellulosic'
        
        
        if f is not 'cellulosic': 
            # For the NEI data convert from short ton to metric ton by multiplying nei data by 0.907185
            query = """
    INSERT INTO """+feedstock+"""_NEIRatio
    WITH
       nrel AS (select distinct fips,  sum(nox) as nox,
                       sum(sox) as sox,
                       sum(co) as co,
                       sum(pm10) as pm10,
                       sum(pm25) as pm25,
                       sum(voc) as voc,
                       sum(nh3) as nh3 
                from sgnew.summedemissions 
                where feedstock ilike '%"""+f+"""%' 
                GROUP BY fips),
       nei as (select fips, nox, sox, co, pm10, pm25, voc, nh3 
               from """+self.nei_data_by_county+""")
    
       select   nrel.fips,
                (nrel.nox * """+allocation+""") / (nei.nox * 0.907185) as nox, 
                (nrel.sox * """+allocation+""") / (nei.sox * 0.907185) as sox,
                (nrel.co * """+allocation+""") / (nei.co * 0.907185) as co,
                (nrel.pm10 * """+allocation+""") / (nei.pm10 * 0.907185) as PM10,
                (nrel.pm25 * """+allocation+""") / (nei.pm25 * 0.907185) as PM25,
                (nrel.voc * """+allocation+""") / (nei.voc* 0.907185) as VOC,
                CASE WHEN nei.nh3 > 0 THEN     (nrel.nh3 * """+allocation+""") / (nei.nh3 * 0.907185)
                     ELSE 0.0    
                END as NH3
    
        FROM nrel
        LEFT JOIN nei ON nrel.fips = nei.fips    
        WHERE nrel.nh3 > 0 and nei.nox > 0
                """
        
        else:   
            # query everything 
            query = """
    INSERT INTO """+feedstock+"""_NEIRatio
    WITH
       nrel AS (select distinct fips,  sum(nox) as nox,
                       sum(sox) as sox,
                       sum(co) as co,
                       sum(pm10) as pm10,
                       sum(pm25) as pm25,
                       sum(voc) as voc,
                       sum(nh3) as nh3 
                from sgnew.summedemissions 
                GROUP BY fips),
       nei as (select fips, nox, sox, co, pm10, pm25, voc, nh3 
               from """+self.nei_data_by_county+""")
    
       select   nrel.fips,
                (nrel.nox  * """+allocation+""") / (nei.nox * 0.907185) as nox, 
                (nrel.sox * """+allocation+""") / (nei.sox * 0.907185) as sox,
                (nrel.co * """+allocation+""") / (nei.co * 0.907185) as co,
                (nrel.pm10 * """+allocation+""") / (nei.pm10 * 0.907185) as PM10,
                (nrel.pm25 * """+allocation+""") / (nei.pm25 * 0.907185) as PM25,
                (nrel.voc * """+allocation+""") / (nei.voc * 0.907185) as VOC,
                CASE WHEN nei.nh3 > 0 THEN     (nrel.nh3 * """+allocation+""") / (nei.nh3 * 0.907185) 
                     ELSE 0.0    
                END as NH3
    
        FROM nrel
        LEFT JOIN nei ON nrel.fips = nei.fips    
        WHERE nrel.nh3 > 0 and nei.nox > 0
                """

        self._executeQuery(query)
        
        




