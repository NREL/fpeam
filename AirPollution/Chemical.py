import SaveDataHelper

'''
Used to populate the newly created schema that stores emmision info.
Inserts data into cg_chem for emmisions from chemicals.
Created from pesticides.
'''
class Chemical(SaveDataHelper.SaveDataHelper):
    
    pcg, psg = 'CGP', 'SGP'
    
    '''
    @param pestFeed: Dictionary of the two feed stocks and weather they should
    run the pesticide code for them. dict(string) 
    '''
    def __init__(self, cont, pestFeed):
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.documentFile = "Chemical"
        # pesticides.
        self.pestFeed = pestFeed
         
    '''
    Find the feedstock and add emmissions if it is switch grass or corn grain.
    @param feed: Feed stock.
    '''
    def setChemical(self, feed):
        query = ''
        if feed == 'CG' or feed == 'SG': 
            if feed == 'CG' and self.pestFeed[self.pcg]:
                query = self.__cornGrain__()
                
            elif feed == 'SG' and self.pestFeed[self.psg]:
                query = self.__switchgrass__()
            # if a query was made, execute it.
            if query: self._executeQuery(query)
            
        
        
    '''
    emmisions = harvested acres * lbs/acre * Evaporation rate * VOC content (lbs VOC / lb active ingridient) * conversion from lbs to mt.
    emmisions = total VOC emmisions (lbs VOC).
    total_harv_ac = total harvested acres. (acres)
    pest.EF = lbs VOC/acre.
    .9 =  evaporation rate. (lbs active/lbs VOC)
    .835 = voc content. lbs VOC / lb active ingridient.
    (acres) * (lbs VOC/acre) * (lbs active/lbs VOC) * (lbs VOC/lbs active) * (mt/lbs) = mt VOC
    '''
    def __cornGrain__(self):
        chemQuery = """
INSERT INTO cg_chem
    (

    SELECT cg.fips, (2461850051) AS "SCC", 

    ((cg.total_harv_ac * pest.EF * 0.9 * 0.835) * 0.907018474 / 2000.0) AS "VOC", 

    ('Pesticide Emissions') AS "Description"

    FROM """+self.db.productionSchema+""".cg_data cg, """ + self.db.constantsSchema + """.CG_pest_app_factor pest

    WHERE substr(fips, 1, 2) = pest.STFIPS
    )"""
        return chemQuery
    

    '''
    Recieves several different fertilizers: Quinclorac, Attrazine, 2 and 4-D-Amine
    Multiply by .1 b/c it is switch grass on a ten year cycle.
    emmisions = .1 * harvested acres * lbs/acre * Evaporation rate * VOC content (lbs VOC / lb active ingridient) * conversion lbs to mt  VOC
    emmisions (mt VOC)
    '''                                     
    def __switchgrass__(self):
        
        chemQuery = """
INSERT INTO sg_chem 
    (
        SELECT sg.fips, (2461850099) AS "SCC",  
        (
            (
            sg.harv_ac * 0.1 * (0.5) + 
            sg.harv_ac * 0.1 * (1.0) + 
            sg.harv_ac * 0.1 * (1.0) + 
            sg.harv_ac * 0.1 * (1.5)
            ) * 0.9 * 0.835
        ) * 0.90718474 / 2000.0 AS "VOC", 
     
        ('Establishment Year: quinclorac + Atrazine + 2-4-D-Amine') AS "Description"

        FROM """+self.db.productionSchema+""".sg_data sg
    )"""
        return chemQuery
          
        