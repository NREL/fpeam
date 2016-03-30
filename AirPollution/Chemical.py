"""
Used to populate the newly created schema that stores emmision info.
Inserts data into cg_chem for emmisions from chemicals.
Created from pesticides.
"""

import SaveDataHelper


class Chemical(SaveDataHelper.SaveDataHelper):
    """
    @param pest_feed: Dictionary of the two feed stocks and weather they should
    run the pesticide code for them. dict(string) 
    """

    pcg, psg = 'CGP', 'SGP'  # @TODO: remove; doesn't seem to be necessary

    def __init__(self, cont, pest_feed):
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.document_file = "Chemical"
        # pesticides.
        self.pest_feed = pest_feed
        self.cont = cont
        self.kvals = cont.get('kvals')

    def set_chemical(self, feed):
        """
        Find the feedstock and add emmissions if it is switch grass or corn grain.
        @param feed: Feed stock.
        """
        # I think this is all horked up:
        #   self.pcg and self.psg are implicitly defined rather than explicity in __init__
        #       but not with numbers from the config or anywhere else, but what look like different acronyms
        #       those acronyms match the acronyms used in main.py (now in config.ini)
        #       I think that means each line is saying run query if the feedstock matches CG or SG and there are non-NaNs
        #   but defining query = '' means query is always
        query = None  # @TODO: remove;  extraneous definition
#        if feed == 'CG' or feed == 'SG':  # @TODO: remove;  extraneous check
        if feed == 'CG' and self.pest_feed['CGP'] is True:
            query = self.__corn_grain__()
        elif feed == 'SG' and self.pest_feed['SGP'] is True:
            query = self.__switchgrass__()
        # if a query was made, execute it.
        if query is not None:
            self._execute_query(query)

    def __corn_grain__(self):
        """
        emmisions = harvested acres * lbs/acre * Evaporation rate * VOC content (lbs VOC / lb active ingridient) * conversion from lbs to mt.
        emmisions = total VOC emmisions (lbs VOC).
        total_harv_ac = total harvested acres. (acres)
        pest.EF = lbs VOC/acre.
        .9 =  evaporation rate. (lbs active/lbs VOC)
        .835 = voc content. lbs VOC / lb active ingridient.
        (acres) * (lbs VOC/acre) * (lbs active/lbs VOC) * (lbs VOC/lbs active) * (mt/lbs) = mt VOC
        """

        chem_query = """INSERT INTO {scenario_name}.{cg_chem_table}
                        (
                        SELECT  cg.fips,
                                (2461850051) AS SCC,
                                ((cg.total_harv_ac * pest.EF * 0.9 * 0.835) * 0.907018474 / 2000.0) AS VOC,
                                ('Pesticide Emissions') AS Description
                        FROM {production_schema}.{cg_table} cg, {constants_schema}.CG_pest_app_factor pest
                        WHERE substr(fips, 1, 2) = pest.STFIPS
                        )""".format(**self.kvals)

        return chem_query

    def __switchgrass__(self):
        """
        Recieves several different fertilizers: Quinclorac, Attrazine, 2 and 4-D-Amine
        Multiply by .1 b/c it is switch grass on a ten year cycle.
        emmisions = .1 * harvested acres * lbs/acre * Evaporation rate * VOC content (lbs VOC / lb active ingridient) * conversion lbs to mt  VOC
        emmisions (mt VOC)
        """

        chem_query = """INSERT INTO {scenario_name}.{sg_chem_table}
                        (
                        SELECT sg.fips,
                                (2461850099) AS SCC,
                                (
                                (
                                 sg.total_harv_ac * 0.1 * (0.5) +
                                 sg.total_harv_ac * 0.1 * (1.0) +
                                 sg.total_harv_ac * 0.1 * (1.0) +
                                 sg.total_harv_ac * 0.1 * (1.5)
                                ) * 0.9 * 0.835
                                ) * 0.90718474 / 2000.0 AS VOC,
                                ('Establishment Year: quinclorac + Atrazine + 2-4-D-Amine') AS Description
                        FROM {production_schema}.{sg_table} sg
                        )""".format(**self.kvals)

        return chem_query
