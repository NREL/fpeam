import SaveDataHelper


class FugitiveDust(SaveDataHelper.SaveDataHelper):
    """
    Create the fugitive dust emisisons based on the run code
    The run code tells you the feedstock, tillage, and operation
    (harvest/non-harvest/irrigation). 
    Fugitive dust occurs from vehicles such as tractors going over the field and creating lots of dust.
    ******************
    @note: Emission factors are calculated on a spread sheet. 
    https://docs.google.com/spreadsheet/ccc?key=0ArgAX3FKoio9dGdQcnRqRlZoS2FiZDVvODJHY3J0bHc#gid=1 
    *****************
    """
    def __init__(self, cont):
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.document_file = "FugitiveDust"
        self.pm_ratio = 0.20

    def set_emissions(self, run_code):
        """
        loop through run_codes and call this method to create fugitive
        dust emissions in database.
        Adds pm10, and pm25 emissions.
        @param run_code: Specific run code with info on feedstock and operation.
        """
        # Forest Residue fugitive dust emissions
        if run_code.startswith('FR'):
            self.__forest_res__()
            # Corn Grain fugitivie dust emissions
        elif run_code.startswith('CG'):
            self.__corn_grain__(run_code)
            # Wheat straw fugitive dust emissions
        elif run_code.startswith('WS'):
            self.__wheat_straw__(run_code)
        # Corn stover fugitive dust emissions            
        elif run_code.startswith('CS'):
            self.__corn_stover__(run_code)
        # switchgrass fugitive dust emissions            
        elif run_code.startswith('SG'):
            pass

    def __forest_res__(self):
        """
        Forest residue fugitive dust emissions.
        """
        pm_fr = self.convert_lbs_to_mt(0.0)
        # currently there are no pm emissions from FR operations
        query = """
            UPDATE "fr_raw" fr
                SET 
                    "fug_pm10" = (%s * dat."fed_minus_55"),
                    "fug_pm25" = (%s * dat."fed_minus_55" * %s)
                FROM %s."fr_data" dat
                WHERE dat."fips" = fr."fips"
            """ % (pm_fr, pm_fr, self.pm_ratio, self.db.production_schema)
        self._execute_query(query)

    def __corn_grain__(self, run_code):
        """
        Corn grain fugitive dust emissions
        """
        # --emission factors: 
        # Corn grain fugitive dust emissions = 1.7 lbs/acre (as reported by CARB in 2003 http://www.arb.ca.gov/ei/areasrc/fullpdf/full7-5.pdf)
        # Need to convert from lbs to mt   
        pm_conv_till_harv = self.convert_lbs_to_mt(1.7)  # mt / acre
        pm_redu_till_harv = self.convert_lbs_to_mt(1.7)  # mt / acre
        pm_no_till_harv = self.convert_lbs_to_mt(1.7)  # mt / acre

        pm_conv_till_non_harv = self.convert_lbs_to_mt(8.0)  # mt / acre
        pm_redu_till_non_harv = self.convert_lbs_to_mt(7.2)  # mt / acre
        pm_no_till_non_harv = self.convert_lbs_to_mt(5.2)  # mt / acre

        # irrigation emissions do not currently have PM emissions
        pm_die_irrigation = self.convert_lbs_to_mt(0.0)  # mt / acre
        pm_gas_irrigation = self.convert_lbs_to_mt(0.0)  # mt / acre
        pm_lpg_irrigation = self.convert_lbs_to_mt(0.0)  # mt / acre
        pm_cng_irrigation = self.convert_lbs_to_mt(0.0)  # mt / acre

        model_transport = False
        # --                
        # choose operation for conventional till
        if run_code.startswith('CG_C'):
            tillage = 'Conventional'
            table_till = 'convtill'

            if run_code.endswith('N'):
                operation = 'Non-Harvest'
                ef = pm_conv_till_non_harv

            elif run_code.endswith('H'):
                operation = 'Harvest'
                ef = pm_conv_till_harv
                model_transport = True

                # choose operation for reduced till
        elif run_code.startswith('CG_R'):
            tillage = 'Reduced'
            table_till = 'reducedtill'

            if run_code.endswith('N'):
                operation = 'Non-Harvest'
                ef = pm_redu_till_non_harv

            elif run_code.endswith('H'):
                operation = 'Harvest'
                ef = pm_redu_till_harv
                model_transport = True

                # choose operation for no till                
        elif run_code.startswith('CG_N'):
            tillage = 'No Till'
            table_till = 'notill'

            if run_code.endswith('N'):
                operation = 'Non-Harvest'
                ef = pm_no_till_non_harv

            elif run_code.endswith('H'):
                operation = 'Harvest'
                ef = pm_no_till_harv
                model_transport = True

                # choose operation for irrigation
        elif run_code.startswith('CG_I'):
            tillage = 'Irrigation'
            table_till = 'total'

            if run_code.endswith('D'):
                operation = 'Diesel'
                ef = pm_die_irrigation

            elif run_code.endswith('G'):
                operation = 'Gasoline'
                ef = pm_gas_irrigation

            elif run_code.endswith('L'):
                operation = 'LPG'
                ef = pm_lpg_irrigation

            elif run_code.endswith('C'):
                operation = 'CNG'
                ef = pm_cng_irrigation

        # execute query for transport operations
        if model_transport:
            # pm10 = mt/acre * acre =  mt
            # pm2.5 = mt/acre * acre * constant = mt
            self.transport_query(run_code, tillage)

        # return query for non-transport operations
        # pm10 = mt/acre * acre =  mt
        # pm2.5 = mt/acre * acre * constant = mt
        self.pm_query(run_code=run_code, ef=ef, till=table_till, activity=operation, till_type=tillage)

    def __corn_stover__(self, run_code):
        """
        Corn stover fugitive dust emissions.
        """
        # --emission factors:
        # Corn stover fugitive dust emissions = 1.7 lbs/acre (assuming harvest activies are the same as for corn grain as reported by CARB in 2003 http://www.arb.ca.gov/ei/areasrc/fullpdf/full7-5.pdf)
        # Need to convert from lbs to mt
        pm_redu_till_harv = self.convert_lbs_to_mt(1.7)  # mt / acre 
        pm_no_till_harv = self.convert_lbs_to_mt(1.7)  # mt / acre 
        # --     

        # choose operation for reduced till
        if run_code.startswith('CS_R'):
            tillage = 'Reduced'
            table_till = 'reducedtill'
            operation = 'Harvest'
            ef = pm_redu_till_harv

        # choose operation for no till                
        elif run_code.startswith('CS_N'):
            tillage = 'No Till'
            table_till = 'notill'
            operation = 'Harvest'
            ef = pm_no_till_harv

        # execute query for transport emissions
        # pm10 = dt/acre * acre =  dt
        # pm2.5 = dt/acre * acre * constant = dt
        self.transport_query(run_code, tillage)

        # return non-transport emissions query        
        self.pm_query(run_code=run_code, ef=ef, till=table_till, activity=operation, till_type=tillage)

    def __wheat_straw__(self, run_code):
        """
        Wheat straw fugitive dust emissions. 
        Bassically the same as corn stover...
        """
        # --emission factors:
        # Wheat straw fugitive dust emissions = 5.6 lbs/acre (assuming harvest activies are the same as for wheat as reported by CARB in 2003 http://www.arb.ca.gov/ei/areasrc/fullpdf/full7-5.pdf)
        # Need to convert from lbs to mt
        pm_redu_till_harv = self.convert_lbs_to_mt(5.6)  # mt / acre 
        pm_no_till_harv = self.convert_lbs_to_mt(5.6)  # mt / acre 
        # --     

        # choose operation for reduced till
        if run_code.startswith('WS_R'):
            tillage = 'Reduced'
            table_till = 'reducedtill'
            operation = 'Harvest'
            ef = pm_redu_till_harv

        # choose operation for no till                
        elif run_code.startswith('WS_N'):
            tillage = 'No Till'
            table_till = 'notill'
            operation = 'Harvest'
            ef = pm_no_till_harv

        # execute query for transport emissions
        # pm10 = dt/acre * acre =  dt
        # pm2.5 = dt/acre * acre * constant = dt
        self.transport_query(run_code=run_code, till_type=tillage)
        # return non-transport emissions query        
        self.pm_query(run_code=run_code, ef=ef, till=table_till, activity=operation, till_type=tillage)

    def pm_query(self, run_code, ef, till, activity, till_type):
        """
        Makes a query to update pm10 and pm2.5 from fugitive dust. Then executes that query. Calculates in units of metric tons.
        @param run_code: run code used to get type of feedstock.
        @param ef: Emission factor specific for each activity. In metric tons per acre.
        @param till: Type of till used.
        @param activity: Type of activity used to make emission.
        @param tillType: Type of till in description.
        """
        feed = run_code.lower()[0:2]
        query = """
                UPDATE """ + feed + """_raw raw
                SET 
                    "fug_pm10" = (""" + str(ef) + """ * cd.""" + str(till) + """_harv_AC),
                    "fug_pm25" = (""" + str(ef) + """ * cd.""" + str(till) + """_harv_AC) * """ + str(self.pm_ratio) + """
                FROM """ + str(self.db.production_schema) + """.""" + str(feed) + """_data cd
                WHERE     (cd."fips" = raw."fips") AND 
                          (raw."description" ILIKE '""" + str("%" + activity + "%") + """') AND 
                          (raw."description" ILIKE '""" + str("%" + till_type + "%") + """')"""
        self._execute_query(query)

    def transport_query(self, run_code, till_type):
        """
        Calculates pm10 and pm2.5 fugitive dust emissions from transportation on unpaved roads 
        Calculates in units of metric tons
        
        Equation for fugitive dust emissions generated by transportation on unpaved roads
        # equation comes from EPA 2006 http://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0202.pdf         
        Equation from EPA 2006 Section 13.2.2 Unpaved Roads on pg 3 at http://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0202.pdf     
        EPA equation is given in units of lbs of pollutant per vehicle mile traveled which must be converted to metric tons of pollutant.
        
        Final equation is given by         
        E = [k * v (s/12)^a (W/3)^b]*0.907/2000
        
        Where:    v = vehicle miles traveled (default 10)
                  s = silt content (%)
                  W = mass of vehicle (short tons)
                  0.907/2000 converts from lbs to metric tons
                  
        @param run_code: Run code to get feed stock from.
        @param tillType: Tillage type. Used to update correct row in feedstock_raw. 
        """
        feed = run_code.lower()[0:2] 
        # factors for equation.
        weight = str(32.01)  # tons
        k25, k10 = str(0.38), str(2.6)    # constant
        a25, a10 = str(0.8), str(0.8)     # constant
        b25, b10 = str(0.4), str(0.4)     # constant
        c25, c10 = str(0.3), str(0.3)     # constant
        D = str(10) #default value for distance traveled (in vehicle miles traveled)
        # @TODO: convert from lbs to dt
        query = """
                UPDATE """ + feed + """_raw raw
                SET 
                    fug_pm10 = """ + str("(" + k10 + "* "+ D +" * 0.907/2000 * ((tfd.silt / 12)^" + a10 + ") * ((" + weight + "/3)^" + b10 + "))") + """,
                    fug_pm25 = """ + str("(" + k25 + "* "+ D +" * 0.907/2000 * ((tfd.silt / 12)^" + a25 + ") * ((" + weight + "/3)^" + b25 + "))") + """
                FROM """ + self.db.constants_schema + """.transportfugitivedust tfd
                WHERE     (raw.fips ilike tfd.fips || '%') AND 
                          (raw.description ILIKE '""" + str("%transport%") + """') AND 
                          (raw.description ILIKE '""" + str("%" + till_type + "%") + """')"""
        self._execute_query(query)

    def convert_lbs_to_mt(self, ef):
        """
        Convert from lbs to metric tons. 
        @param ef: Emission factor in lbs/acre. Converted to mt/acre.  
        @return Emission factor in mt/acre
        """
        mt = (ef * 0.907) / 2000.0  # metric tons.
        return mt


class SG_FugitiveDust(SaveDataHelper.SaveDataHelper):
    # Data structure to hold SG emission factors
    #   --structure is kept in the 'long-hand' format so users may easily change
    #        EF's in the future
    
    def __init__(self, cont, operation):
        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.document_file = "SG_FugitiveDust"
        # to convert from PM10 to PM2.5, b/c PM2.5 is smaller.
        self.pm_ratio = 0.20
        
        if operation == 'Transport':
            # these emissions are not used any more for calculating emissions. Just tells code how long to loop for.
            # lbs/acre
            emission_factors = [1.2,  # year 1 transport emission factor
                                1.2,  # year 2
                                1.2,  # year 3
                                1.2,  # year 4
                                1.2,  # year 5
                                1.2,  # year 6
                                1.2,  # year 7
                                1.2,  # year 8
                                1.2,  # year 9
                                1.2  # year 10
                                ]
            self.description = 'SG_T'
            
        elif operation == 'Harvest':
            # Switchgrass fugitive dust emissions = 1.7 lbs/acre (assuming harvest activies are the same as for corn grain as reported by CARB in 2003 http://www.arb.ca.gov/ei/areasrc/fullpdf/full7-5.pdf)        
            emission_factors = [1.7,  # year 1 harvest emission factor
                                1.7,  # year 2
                                1.7,  # year 3
                                1.7,  # year 4
                                1.7,  # year 5
                                1.7,  # year 6
                                1.7,  # year 7
                                1.7,  # year 8
                                1.7,  # year 9
                                1.7  # year 10
                                ]
            self.description = 'SG_H'
            
        elif operation == 'Non-Harvest':
            # lbs/acre
            emission_factors = [7.6,  # year 1 non-harvest emission factor
                                2.0,  # year 2
                                0.8,  # year 3
                                0.8,  # year 4
                                1.6,  # year 5
                                0.8,  # year 6
                                0.8,  # year 7
                                0.8,  # year 8
                                0.8,  # year 9
                                0.0  # year 10
                                ]
            self.description = 'SG_N'
        
        self.emission_factors = (x * 0.907 / 2000.0 for x in emission_factors)  # convert from lbs to metric tons. mt / acre

    def set_emissions(self):
        for year, ef in enumerate(self.emission_factors):   
            # return non-transport emissions query      
            # pm10 = mt/acre * acre =  mt
            # pm2.5 = mt/acre * acre * constant = mt  
            # switch grass on a 10 year basis.
            if self.description == 'SG_N' or self.description == 'SG_H':
                query = """
                        UPDATE sg_raw raw
                        SET 
                            "fug_pm10" = (%s * dat."harv_ac") / 10,
                            "fug_pm25" = ((%s * dat."harv_ac") * %s) / 10
                        FROM %s."sg_data" dat
                        WHERE     (dat."fips" = raw."fips") AND
                                  (raw."run_code" ILIKE '%s');
                    """ % (ef,
                           ef, self.pm_ratio,
                           self.db.production_schema,
                           str("%" + self.description + str(year + 1) + "%")
                           )
            elif self.description == 'SG_T':
                """
                Calculates pm10 and pm2.5 fugitive dust emissions from transportation on unpaved roads 
                Calculates in units of metric tons
                
                Equation for fugitive dust emissions generated by transportation on unpaved roads
                # equation comes from EPA 2006 http://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0202.pdf         
                Equation from EPA 2006 Section 13.2.2 Unpaved Roads on pg 3 at http://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0202.pdf     
                EPA equation is given in units of lbs of pollutant per vehicle mile traveled which must be converted to metric tons of pollutant.
                
                Final equation is given by         
                E = [k * v (s/12)^a (W/3)^b]*0.907/2000
                
                Where:    v = vehicle miles traveled (default 10)
                          s = silt content (%)
                          W = mass of vehicle (short tons)
                          0.907/2000 converts from lbs to metric tons
                          
                @param run_code: Run code to get feed stock from.
                @param tillType: Tillage type. Used to update correct row in feedstock_raw. 
                """           
                # factors for equation.
                weight = str(32.01)  # tons
                k25, k10 = str(0.38), str(2.6)    # constant
                a25, a10 = str(0.8), str(0.8)     # constant
                b25, b10 = str(0.4), str(0.4)     # constant
                c25, c10 = str(0.3), str(0.3)     # constant
                D = str(10) #default value for distance traveled (in vehicle miles traveled)
                rot = str(10) #number of years in switchgrass rotation 
                # @TODO: convert from lbs to dt
                query = """
                        UPDATE "sg_raw" raw
                        SET 
                            fug_pm10 = """ + str("(" + k10 + "* "+ D +" * 0.907/2000 * ((tfd.silt / 12)^" + a10 + ") * ((" + weight + "/3)^" + b10 + "))/"+ rot+"") + """,
                            fug_pm25 = """ + str("(" + k25 + "* "+ D +" * 0.907/2000 * ((tfd.silt / 12)^" + a25 + ") * ((" + weight + "/3)^" + b25 + "))/"+ rot+"") + """
                        FROM """ + self.db.constants_schema + """."transportfugitivedust" tfd
                        WHERE     (raw."fips" ILIKE tfd."fips" || '%') AND
                                  (raw."run_code" ILIKE '""" + str("%" + self.description + str(year + 1) + "%") + """')"""

            self._execute_query(query)
