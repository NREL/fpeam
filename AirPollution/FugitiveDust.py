import SaveDataHelper
from utils import config, logger


class FugitiveDust(SaveDataHelper.SaveDataHelper):
    """
    Create the fugitive dust emisisons based on the run code
    The run code tells you the feedstock, tillage, and operation
    (harvest/non-harvest/irrigation). 
    Fugitive dust occurs from vehicles such as tractors going over the field and creating lots of dust.

    Note: Emission factors are calculated on a spread sheet:

        https://docs.google.com/spreadsheet/ccc?key=0ArgAX3FKoio9dGdQcnRqRlZoS2FiZDVvODJHY3J0bHc#gid=1
    """

    def __init__(self, cont):
        """

        :param cont: Container object for global values
        :return:
        """

        SaveDataHelper.SaveDataHelper.__init__(self, cont)

        # init properties
        self.document_file = "FugitiveDust"
        self.pm_ratio = 0.20
        self.cont = cont
        self.silt_table = config.get('db_table_list')['silt_table']

    def set_emissions(self, run_code):
        """
        Add fugitive dust emissions for <run_code>. Combines pm10, and pm25 emissions.

        :param run_code: NONROAD run-code
        :return:
        """

        if run_code.startswith('FR'):
            self.__forest_res__()
        elif run_code.startswith('CG'):
            self.__corn_grain__(run_code)
        elif run_code.startswith('WS'):
            self.__wheat_straw__(run_code)
        elif run_code.startswith('CS'):
            self.__corn_stover__(run_code)
        elif run_code.startswith('SG'):
            pass

    def __forest_res__(self):
        """
        Calculate forest residue fugitive dust emissions.

        :return:
        """

        kvals = self.cont.get('kvals')
        kvals['pm_ratio'] = self.pm_ratio
        kvals['pm_fr'] = self.convert_lbs_to_mt(0.0)  # currently there are no pm emissions from FR operations

        query = """UPDATE {scenario_name}.fr_raw fr
                   LEFT JOIN {production_schema}.fr_data dat ON dat.fips = fr.fips
                   SET    fug_pm10 = ({pm_fr} * dat.total_prod),
                          fug_pm25 = ({pm_fr} * dat.total_prod * {pm_ratio})
                   ;""".format(**kvals)

        self._execute_query(query)

    def __corn_grain__(self, run_code):
        """
        Calculate orn grain fugitive dust emissions.

        Corn grain fugitive dust emissions = 1.7 lbs/acre (as reported by CARB in 2003 http://www.arb.ca.gov/ei/areasrc/fullpdf/full7-5.pdf)

        :param run_code:
        :return:
        """

        # emission factors
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
        if run_code.startswith('CG_T'):
            # pm10 = mt/acre * acre =  mt
            # pm2.5 = mt/acre * acre * constant = mt
            self.transport_query(run_code, tillage)

        # query for non-transport operations
        # pm10 = mt/acre * acre =  mt
        # pm2.5 = mt/acre * acre * constant = mt
        self.pm_query(run_code=run_code, ef=ef, till=table_till, activity=operation, till_type=tillage)

    def __corn_stover__(self, run_code):
        """
        Corn stover fugitive dust emissions.

        Corn stover fugitive dust emissions = 1.7 lbs/acre (assuming harvest activies are the same as for corn grain as reported by CARB in 2003 http://www.arb.ca.gov/ei/areasrc/fullpdf/full7-5.pdf)

        :param run_code:
        :return:
        """

        # emission factors
        pm_redu_till_harv = self.convert_lbs_to_mt(1.7)  # mt / acre
        pm_no_till_harv = self.convert_lbs_to_mt(1.7)  # mt / acre
        pm_conv_till_harv = self.convert_lbs_to_mt(1.7)  # mt / acre

        pm_conv_till_non_harv = self.convert_lbs_to_mt(0.8)  # mt / acre
        pm_redu_till_non_harv = self.convert_lbs_to_mt(0.8)  # mt / acre
        pm_no_till_non_harv = self.convert_lbs_to_mt(0.8)  # mt / acre

        # choose operation for reduced till
        if run_code.startswith('CS_R'):
            tillage = 'Reduced'
            table_till = 'reducedtill'
            if run_code.endswith('H'):
                operation = 'Harvest'
                ef = pm_redu_till_harv
            elif run_code.endswith('N'):
                operation = 'Non-Harvest'
                ef = pm_redu_till_non_harv

        # choose operation for no till                
        elif run_code.startswith('CS_N'):
            tillage = 'No Till'
            table_till = 'notill'
            if run_code.endswith('H'):
                operation = 'Harvest'
                ef = pm_no_till_harv
            elif run_code.endswith('N'):
                operation = 'Non-Harvest'
                ef = pm_no_till_non_harv

        elif run_code.startswith('CS_C'):
            tillage = 'Conventional Till'
            table_till = 'convtill'
            if run_code.endswith('H'):
                operation = 'Harvest'
                ef = pm_conv_till_harv
            elif run_code.endswith('N'):
                operation = 'Non-Harvest'
                ef = pm_conv_till_non_harv

        # execute query for transport emissions
        # pm10 = dt/acre * acre =  dt
        # pm2.5 = dt/acre * acre * constant = dt
        if run_code.startswith('CS_T'):
            self.transport_query(run_code, tillage)

        # non-transport emissions query
        self.pm_query(run_code=run_code, ef=ef, till=table_till, activity=operation, till_type=tillage)

    def __wheat_straw__(self, run_code):
        """
        Calculate wheat straw fugitive dust emissions.

        Wheat straw fugitive dust emissions = 5.8 lbs/acre (assuming harvest activies are the same as for wheat as reported by CARB in 2003 http://www.arb.ca.gov/ei/areasrc/fullpdf/full7-5.pdf)

        :param run_code:
        :return:
        """

        # emission factors:
        pm_redu_till_harv = self.convert_lbs_to_mt(5.8)  # mt / acre
        pm_no_till_harv = self.convert_lbs_to_mt(5.8)  # mt / acre

        pm_redu_till_non_harv = self.convert_lbs_to_mt(0.8)  # mt / acre
        pm_no_till_non_harv = self.convert_lbs_to_mt(0.8)  # mt / acre

        # choose operation for reduced till
        if run_code.startswith('WS_R'):
            tillage = 'Reduced'
            table_till = 'reducedtill'
            if run_code.endswith('H'):
                operation = 'Harvest'
                ef = pm_redu_till_harv
            elif run_code.endswith('N'):
                operation = 'Non-Harvest'
                ef = pm_redu_till_non_harv

        # choose operation for no till                
        elif run_code.startswith('WS_N'):
            tillage = 'No Till'
            table_till = 'notill'
            if run_code.endswith('H'):
                operation = 'Harvest'
                ef = pm_no_till_harv
            elif run_code.endswith('N'):
                operation = 'Non-Harvest'
                ef = pm_no_till_non_harv

        # execute query for transport emissions
        # pm10 = dt/acre * acre =  dt
        # pm2.5 = dt/acre * acre * constant = dt
        if run_code.startswith('WS_T'):
            self.transport_query(run_code=run_code, till_type=tillage)

        # non-transport emissions query
        self.pm_query(run_code=run_code, ef=ef, till=table_till, activity=operation, till_type=tillage)

    def pm_query(self, run_code, ef, till, activity, till_type):
        """
        Makes a query to update pm10 and pm2.5 from fugitive dust. Then executes that query. Calculates in units of metric tons.

        :param run_code: run code used to get type of feedstock.
        :param ef: Emission factor specific for each activity. In metric tons per acre.
        :param till: Type of till used.
        :param activity: Type of activity used to make emission.
        :param till_type: Type of till in description.
        :return:
        """

        # set dictionary values for string formatting
        kvals = self.cont.get('kvals')
        kvals['feed'] = run_code.lower()[0:2]
        kvals['ef'] = str(ef)
        kvals['till'] = str(till)
        kvals['pm_ratio'] = str(self.pm_ratio)
        kvals['activity'] = str("%" + activity + "%")
        kvals['till_type'] = str("%" + till_type + "%")
        kvals['description'] = str('%s - %s, Fugitive dust' % (till_type, activity, ))
        kvals['run_code'] = run_code

        query = """ INSERT INTO {scenario_name}.{feed}_raw (fips, scc, hp, thc, voc, co, nox, co2, sox, pm10, pm25, fuel_consumption, nh3, description, run_code)
                    SELECT cd.fips, 0, 0, 0, 0, 0, 0, 0, 0, ({ef} * cd.{till}_harv_AC), ({ef} * cd.{till}_harv_AC * {pm_ratio}), 0, 0, '{description}', '{run_code}'
                    FROM {production_schema}.{feed}_data cd
                    WHERE cd.{till}_harv_ac > 0
                """.format(**kvals)
        self._execute_query(query)

        # add additional emissions for lime application (corn grain only - varies by region)
        if run_code.startswith('CG') and run_code.endswith('N'):
            logger.info('Computing fugitive dust emissions from lime fertilizer application for CG')
            kvals['till_abr'] = '%sT' % (run_code[3], )
            kvals['lime_app_ef'] = self.convert_lbs_to_mt(0.8)
            kvals['description'] = str('%s - %s, Fugitive dust lime' % (till_type, activity, ))

            query_view = """ DROP VIEW IF EXISTS {scenario_name}.equip_lime;
                             CREATE VIEW {scenario_name}.equip_lime
                             AS (SELECT equip.fips, sum(equip.lime_lbac) AS 'lime_sum'
                             FROM {production_schema}.cg_equip_fips equip
                             LEFT JOIN {production_schema}.cg_data cd ON cd.fips = equip.fips
                             WHERE equip.tillage = '{till_abr}' AND cd.{till}_harv_ac > 0 AND oper_type = 'ESTC'
                             GROUP BY equip.fips)
                         """.format(**kvals)
            self._execute_query(query_view)

            query_lime = """ INSERT INTO {scenario_name}.{feed}_raw (fips, scc, hp, thc, voc, co, nox, co2, sox, pm10, pm25, fuel_consumption, nh3, description, run_code)
                             SELECT cd.fips, 0, 0, 0, 0, 0, 0, 0, 0, ({lime_app_ef} * cd.{till}_harv_AC), ({lime_app_ef} * cd.{till}_harv_AC * {pm_ratio}), 0, 0, '{description}', '{run_code}'
                             FROM {production_schema}.{feed}_data cd
                             LEFT JOIN {scenario_name}.equip_lime lime
                             ON lime.fips = cd.fips
                             WHERE lime.lime_sum > 0 AND cd.{till}_harv_ac > 0
                         """.format(**kvals)
            self._execute_query(query_lime)

    def transport_query(self, run_code, till_type):
        """
        Calculates pm10 and pm2.5 fugitive dust emissions from transportation on unpaved roads 
        Calculates in units of metric tons
        
        Equation for fugitive dust emissions generated by transportation on unpaved roads
        # equation comes from EPA 2006 http://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0202.pdf         
        Equation from EPA 2006 Section 13.2.2 Unpaved Roads on pg 3 at http://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0202.pdf     
        EPA equation is given in units of lbs of pollutant which must be converted to metric tons of pollutant.
        
        Final equation is given by
        E = prod / truck_cap [k * D (s/12)^a (W/3)^b] * 0.907/2000
        
        Where:    E = total emissions

                  D = distance traveled per load (vehicle miles traveled) (default 1 mile)
                  s = silt content (%)
                  W = mass of vehicle (short tons)
                  0.907/2000 converts from lbs to metric tons
                  
        :param run_code: Run code to get feed stock from
        :param till_type: Tillage type. Used to update correct row in feedstock_raw
        :return:
        """

        kvals = self.cont.get('kvals')
        kvals['feed'] = run_code.lower()[0:2]
        kvals['transport'] = 'transport'
        kvals['till_type'] = till_type
        kvals['onfarm_truck_capacity'] = config['onfarm_truck_capacity']
        kvals['convert_lb_to_mt'] = self.convert_lbs_to_mt(1)
        kvals['silt_table'] = self.silt_table

        # factors for equation.
        kvals['weight'] = 32.01  # short tons
        kvals['k25'] = 0.15
        kvals['k10'] = 1.5
        kvals['a25'] = 0.9
        kvals['a10'] = 0.9
        kvals['b25'] = 0.45
        kvals['b10'] = 0.45
        kvals['D'] = config.get('onfarm_default_distance')  # default value for distance traveled (in vehicle miles traveled)

        query = """ UPDATE {scenario_name}.{feed}_raw raw
                    LEFT JOIN {production_schema}.{feed}_data prod ON raw.fips = prod.fips
                    LEFT JOIN {constants_schema}.{silt_table} tfd ON
                            CASE
                                WHEN (length(prod.fips) = 5) THEN (LEFT(prod.fips, 2)     = LEFT(tfd.st_fips, 2))
                                WHEN (length(prod.fips) = 4) THEN (0 + LEFT(prod.fips, 1) = LEFT(tfd.st_fips, 2))
                            END
                    SET fug_pm25 = (prod.total_prod / {onfarm_truck_capacity} * ({k25} * {D} * ((tfd.uprsm_pct_silt / 12)^{a25}) * (({weight} / 3)^{b25})) * {convert_lb_to_mt}),
                        fug_pm10 = (prod.total_prod / {onfarm_truck_capacity} * ({k10} * {D} * ((tfd.uprsm_pct_silt / 12)^{a10}) * (({weight} / 3)^{b10})) * {convert_lb_to_mt})
                    WHERE (raw.description LIKE '%{till_type}%') AND
                          (raw.description LIKE '%{transport}%')""".format(**kvals)

        self._execute_query(query)

    def convert_lbs_to_mt(self, ef):
        """
        Convert from lbs to metric tons. 

        :param ef: Emission factor in lbs/acre
        :return Emission factor in mt/acre
        """

        return (ef * 0.907) / 2000.0  # metric tons.


class SG_FugitiveDust(SaveDataHelper.SaveDataHelper):

    def __init__(self, cont, run_code):
        """
        :param cont: Container class
        :param run_code:
        :return:
        """

        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.document_file = "SG_FugitiveDust"

        # to convert from PM10 to PM2.5, b/c PM2.5 is smaller.
        self.pm_ratio = 0.20
        self.cont = cont
        self.silt_table = config.get('db_table_list')['silt_table']
        self.run_code = run_code

        if run_code.startswith('SG_T'):
            # lbs/acre
            self.emission_factors = [1.2,  # year 1 transport emission factor
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
            if len(run_code) == 4:
                self.description = "Year %s - On-farm Transport, Fugitive dust" % (run_code[4])  # year 1-9
            else:
                self.description = "Year %s - On-farm Transport, Fugitive dust" % (run_code[4:6])  # year 10

        elif run_code.startswith('SG_H'):
            # Switchgrass fugitive dust emissions = 1.7 lbs/acre (assuming harvest activies are the same as for corn grain as reported by CARB in 2003
            # http://www.arb.ca.gov/ei/areasrc/fullpdf/full7-5.pdf)
            self.emission_factors = [1.7,  # year 1 harvest emission factor
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
            if len(run_code) == 4:
                self.description = "Year %s - Harvest, Fugitive dust" % (run_code[4])  # year 1-9
            else:
                self.description = "Year %s - Harvest, Fugitive dust" % (run_code[4:6])  # year 10

        elif run_code.startswith('SG_N'):
            # lbs/acre
            self.emission_factors = [7.6,  # year 1 non-harvest emission factor
                                     2.0,  # year 2
                                     0.8,  # year 3
                                     0.8,  # year 4
                                     1.6,  # year 5
                                     0.8,  # year 6
                                     0.8,  # year 7
                                     0.8,  # year 8
                                     0.8,  # year 9
                                     0.8  # year 10
                                    ]
            if len(run_code) == 4:
                self.description = "Year %s - Non-Harvest, Fugitive dust" % (run_code[4])  # year 1-9
            else:
                self.description = "Year %s - Non-Harvest, Fugitive dust" % (run_code[4:6])  # year 10

    def set_emissions(self):
        # initialize kvals dictionary for string formatting
        kvals = self.cont.get('kvals')
        kvals['rot_years'] = config.get('crop_budget_dict')['years']['SG']  # set number of rotation years to 10 for SG
        kvals['onfarm_truck_capacity'] = config['onfarm_truck_capacity']
        kvals['convert_lb_to_mt'] = self.convert_lbs_to_mt(1)
        kvals['silt_table'] = self.silt_table
        kvals['pm_ratio'] = self.pm_ratio
        kvals['feed'] = 'sg'
        kvals['till'] = 'notill'
        kvals['run_code'] = self.run_code

        year = int(self.run_code[-1])
        if year == 0:
            year = 10
        ef = self.emission_factors[year - 1]

        # return non-transport emissions query
        # pm10 = mt/acre * acre =  mt
        # pm2.5 = mt/acre * acre * constant = mt
        # switch grass on a 10 year basis.

        kvals['description'] = str(self.description)
        kvals['ef'] = self.convert_lbs_to_mt(ef)

        if self.run_code.startswith('SG_N') or self.run_code.startswith('SG_H'):
            query = """ INSERT INTO {scenario_name}.{feed}_raw (fips, scc, hp, thc, voc, co, nox, co2, sox, pm10, pm25, fuel_consumption, nh3, description, run_code)
                        SELECT      cd.fips,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0,
                                    0,
                                    ({ef} * cd.{till}_harv_AC),
                                    ({ef} * cd.{till}_harv_AC * {pm_ratio}),
                                    0,
                                    0,
                                    '{description}',
                                    '{run_code}'
                        FROM        {production_schema}.{feed}_data cd
                        WHERE       cd.{till}_harv_ac > 0
                        ;""".format(**kvals)

            self._execute_query(query)

        elif self.run_code.startswith('SG_T'):
            # Calculates pm10 and pm2.5 fugitive dust emissions from transportation on unpaved roads
            # Calculates in units of metric tons
            #
            # Equation for fugitive dust emissions generated by transportation on unpaved roads
            # # equation comes from EPA 2006 http://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0202.pdf
            # Equation from EPA 2006 Section 13.2.2 Unpaved Roads on pg 3 at http://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0202.pdf
            # EPA equation is given in units of lbs of pollutant per vehicle mile traveled which must be converted to metric tons of pollutant.
            #
            # Final equation is given by
            # E = [k * v (s/12)^a (W/3)^b]*0.907/2000
            #
            # Where:    v = vehicle miles traveled (default 10)
            #           s = silt content (%)
            #           W = mass of vehicle (short tons)
            #           0.907/2000 converts from lbs to metric tons

            # factors for equation.
            kvals['weight'] = 32.01  # short tons
            kvals['k25'] = 0.15
            kvals['k10'] = 1.5
            kvals['a25'] = 0.9
            kvals['a10'] = 0.9
            kvals['b25'] = 0.45
            kvals['b10'] = 0.45
            kvals['D'] = config.get('onfarm_default_distance')  # default value for distance traveled (in vehicle miles traveled)

            # @TODO: clean up FIPS app-wide (i.e., make them all numbers or all 0-padded strings in code and database
            # @TODO: change case statement to lpad()
            query = """ UPDATE    {scenario_name}.{feed}_raw raw
                        LEFT JOIN {production_schema}.{feed}_data prod
                               ON raw.fips = prod.fips
                        LEFT JOIN {constants_schema}.{silt_table} tfd
                               ON CASE
                                    WHEN (length(prod.fips) = 5) THEN (    LEFT(prod.fips, 2) = LEFT(tfd.st_fips, 2))
                                    WHEN (length(prod.fips) = 4) THEN (0 + LEFT(prod.fips, 1) = LEFT(tfd.st_fips, 2))
                                  END
                        SET       fug_pm25 = (prod.total_prod/{onfarm_truck_capacity} * ({k25} * {D} * ((tfd.uprsm_pct_silt / 12)^{a25}) * (({weight} / 3)^{b25})) * {convert_lb_to_mt}),
                                  fug_pm10 = (prod.total_prod/{onfarm_truck_capacity} * ({k10} * {D} * ((tfd.uprsm_pct_silt / 12)^{a10}) * (({weight} / 3)^{b10})) * {convert_lb_to_mt})
                        WHERE (raw.description = '{description}')
                        ;""".format(**kvals)

            self._execute_query(query)

        logger.info('Calculating fugitive dust emissions for %s, year %s' % (self.description, year, ))

    def convert_lbs_to_mt(self, ef):
        """
        Convert from lbs/acre to metric tons/acre.

        :param ef: Emission factor in lbs/acre. Converted to mt/acre.
        :return Emission factor in mt/acre
        """
        return (ef * 0.907) / 2000.0  # metric tons.


class MSFugitiveDust(SaveDataHelper.SaveDataHelper):

    def __init__(self, cont, run_code):
        """
        :param cont: Container class
        :param run_code:
        :return:
        """

        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.document_file = "MSFugitiveDust"

        # to convert from PM10 to PM2.5, b/c PM2.5 is smaller.
        self.pm_ratio = 0.20
        self.cont = cont
        self.silt_table = config.get('db_table_list')['silt_table']
        self.run_code = run_code

        if run_code.startswith('MS_T'):
            # lbs/acre
            self.emission_factors = [1.2,  # year 1 transport emission factor
                                     1.2,  # year 2
                                     1.2,  # year 3
                                     1.2,  # year 4
                                     1.2,  # year 5
                                     1.2,  # year 6
                                     1.2,  # year 7
                                     1.2,  # year 8
                                     1.2,  # year 9
                                     1.2,  # year 10
                                     1.2,  # year 11
                                     1.2,  # year 12
                                     1.2,  # year 13
                                     1.2,  # year 14
                                     1.2  # year 15
                                     ]
            if len(run_code) == 4:
                self.description = "Year %s - On-farm Transport, Fugitive dust" % (run_code[4])  # year 1-9
            else:
                self.description = "Year %s - On-farm Transport, Fugitive dust" % (run_code[4:6])  # year > 10

        elif run_code.startswith('MS_H'):
            # Switchgrass fugitive dust emissions = 1.7 lbs/acre (assuming harvest activies are the same as for corn grain as reported by CARB in 2003
            # http://www.arb.ca.gov/ei/areasrc/fullpdf/full7-5.pdf)
            self.emission_factors = [1.7,  # year 1 harvest emission factor
                                     1.7,  # year 2
                                     1.7,  # year 3
                                     1.7,  # year 4
                                     1.7,  # year 5
                                     1.7,  # year 6
                                     1.7,  # year 7
                                     1.7,  # year 8
                                     1.7,  # year 9
                                     1.7,  # year 10
                                     1.7,  # year 11
                                     1.7,  # year 12
                                     1.7,  # year 13
                                     1.7,  # year 14
                                     1.7  # year 15
                                     ]
            if len(run_code) == 4:
                self.description = "Year %s - Harvest, Fugitive dust" % (run_code[4])  # year 1-9
            else:
                self.description = "Year %s - Harvest, Fugitive dust" % (run_code[4:6])  # year > 10

        elif run_code.startswith('MS_N'):
            # lbs/acre
            self.emission_factors = [13,  # year 1 non-harvest emission factor
                                     1.6,  # year 2
                                     0.8,  # year 3
                                     0.8,  # year 4
                                     0.8,  # year 5
                                     0.8,  # year 6
                                     0.8,  # year 7
                                     0.8,  # year 8
                                     0.8,  # year 9
                                     0.8,  # year 10
                                     0.8,  # year 11
                                     0.8,  # year 12
                                     0.8,  # year 13
                                     0.8,  # year 14
                                     0.8,  # year 15
                                    ]

            if len(run_code) == 4:
                self.description = "Year %s - Non-Harvest, Fugitive dust" % (run_code[4])  # year 1-9
            else:
                self.description = "Year %s - Non-Harvest, Fugitive dust" % (run_code[4:6])  # year > 10

    def set_emissions(self):
        # initialize kvals dictionary for string formatting
        kvals = self.cont.get('kvals')
        kvals['rot_years'] = config.get('crop_budget_dict')['years']['MS']  # set number of rotation years to 15 for MS
        kvals['onfarm_truck_capacity'] = config['onfarm_truck_capacity']
        kvals['convert_lb_to_mt'] = self.convert_lbs_to_mt(1)
        kvals['silt_table'] = self.silt_table
        kvals['pm_ratio'] = self.pm_ratio
        kvals['feed'] = 'ms'
        kvals['till'] = 'convtill'
        kvals['run_code'] = self.run_code

        year = int(self.run_code[-1])
        if len(self.run_code) > 4:
            year = int(self.run_code[4:6])
        ef = self.emission_factors[year - 1]

        # return non-transport emissions query
        # pm10 = mt/acre * acre =  mt
        # pm2.5 = mt/acre * acre * constant = mt
        # switch grass on a 10 year basis.

        kvals['description'] = str(self.description)
        kvals['ef'] = self.convert_lbs_to_mt(ef)

        if self.run_code.startswith('MS_N') or self.run_code.startswith('MS_H'):
            query = """INSERT INTO {scenario_name}.{feed}_raw (fips, scc, hp, thc, voc, co, nox, co2, sox, pm10, pm25, fuel_consumption, nh3, description, run_code)
                       SELECT cd.fips, 0, 0, 0, 0, 0, 0, 0, 0, ({ef} * cd.{till}_harv_AC), ({ef} * cd.{till}_harv_AC * {pm_ratio}), 0, 0, '{description}', '{run_code}'
                       FROM   {production_schema}.{feed}_data cd
                       WHERE  cd.{till}_harv_ac > 0
                       ;""".format(**kvals)
            print query
            self._execute_query(query)

        elif self.description == 'MS_T':
            # Calculates pm10 and pm2.5 fugitive dust emissions from transportation on unpaved roads
            # Calculates in units of metric tons
            #
            # Equation for fugitive dust emissions generated by transportation on unpaved roads
            # # equation comes from EPA 2006 http://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0202.pdf
            # Equation from EPA 2006 Section 13.2.2 Unpaved Roads on pg 3 at http://www3.epa.gov/ttn/chief/ap42/ch13/final/c13s0202.pdf
            # EPA equation is given in units of lbs of pollutant per vehicle mile traveled which must be converted to metric tons of pollutant.
            #
            # Final equation is given by
            # E = [k * v (s/12)^a (W/3)^b]*0.907/2000
            #
            # Where:    v = vehicle miles traveled (default 10)
            #           s = silt content (%)
            #           W = mass of vehicle (short tons)
            #           0.907/2000 converts from lbs to metric tons

            # factors for equation.
            kvals['weight'] = 32.01  # short tons
            kvals['k25'] = 0.15
            kvals['k10'] = 1.5
            kvals['a25'] = 0.9
            kvals['a10'] = 0.9
            kvals['b25'] = 0.45
            kvals['b10'] = 0.45
            kvals['D'] = config.get('onfarm_default_distance')  # default value for distance traveled (in vehicle miles traveled)

            # @TODO: clean up FIPS app-wide (i.e., make them all numbers or all 0-padded strings in code and database
            query = """UPDATE {scenario_name}.{feed}_raw raw
                       LEFT JOIN {production_schema}.{feed}_data prod ON raw.fips = prod.fips
                       LEFT JOIN {constants_schema}.{silt_table} tfd
                              ON CASE
                                    WHEN (length(prod.fips) = 5) THEN (LEFT(prod.fips, 2) = LEFT(tfd.st_fips, 2))
                                    WHEN (length(prod.fips) = 4) THEN (0 + LEFT(prod.fips, 1) = LEFT(tfd.st_fips,2))
                                 END
                       SET       fug_pm25 = (prod.total_prod / {onfarm_truck_capacity} * ({k25} * {D} * ((tfd.uprsm_pct_silt / 12)^{a25}) * (({weight} / 3)^{b25})) * {convert_lb_to_mt}),
                                 fug_pm10 = (prod.total_prod / {onfarm_truck_capacity} * ({k10} * {D} * ((tfd.uprsm_pct_silt / 12)^{a10}) * (({weight} / 3)^{b10})) * {convert_lb_to_mt})
                       WHERE     raw.description = '{description}'
                       ;""".format(**kvals)

            self._execute_query(query)

        logger.info('Calculating fugitive dust emissions for %s, year %s' % (self.description, year, ))

    def convert_lbs_to_mt(self, ef):
        """
        Convert from lbs/acre to metric tons/acre.

        :param ef: Emission factor in lbs/acre. Converted to mt/acre.
        :return Emission factor in mt/acre
        """
        return (ef * 0.907) / 2000.0  # metric tons
