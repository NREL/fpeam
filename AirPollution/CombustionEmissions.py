import csv
import os

import SaveDataHelper
from utils import logger, config


# @TODO: fill out docstrings


class CombustionEmissions(SaveDataHelper.SaveDataHelper):
    """
    Writes raw data for emissions to a .csv file that can be opened with excel.
    Then saves the data to the db with name <run_code>_raw.
    
    Transform the data from the default Nonroad output to a useful format. 
    Update database with emissions as well as copy emissions to static files
    for quick debugging and error checking.  
    Combustion emissions associated with harvest and non-harvest methods that use non-road vehicles.
    """

    def __init__(self, cont, operation_dict, alloc, regional_crop_budget):
        """

        Each feedstock contains another dictionary of the harvest methods and weather to do the run with them.
        dict(dict(boolean))
        {'CS': {'H': True, 'N': True, 'T': True},
        'WS': {'H': True, 'N': True, 'T': True},
        'CG': {'H': True, 'N': True, 'T': True}}

        :param cont:
        :param operation_dict: dictionary containing 3 feedstocks that have harvest, non-harvest, and transport
        :param alloc: Amount of non harvest emissions to allocate to cg, cs, and ws. dict(string: int)
            {'CG': .9, 'CS': .1, 'WS': .1}
        :return:
        """

        SaveDataHelper.SaveDataHelper.__init__(self, cont)
        self.document_file = "CombustionEmissions"
        # not used here?
        self.pm_ratio = 0.20
        self.base_path = cont.get('path')
        # operations and feedstock dictionary.
        self.operation_dict = operation_dict
        self.alloc = alloc
        
        self.lhv = None  
        self.nh3_ef = None
        self.voc_conversion = None
        self.pm10topm25 = None

        self.cont = cont

        self.regional_crop_budget = regional_crop_budget

        self.ef_crop_dust_dict = config.get('ef_crop_dust_dict')

    def populate_tables(self, run_codes):
        """

        :param run_codes: list of codes for NONROAD runs
        :return:
        """
        
        # short ton = 0.90718474 metric tonn
        convert_tonne = 0.9071847  # metric ton / dry ton
        
        # DOE conversion from BTU/gal of diesel, lhv: light heat value.
        # also part of GREET Argonne model for conversion.
        self.lhv = 128450.0 / 1e6  # mmBTU / gallon --> default for diesel fuel, changed for other fuel types
                
        # SF2 impact analysis nh3 emission factor
        self.nh3_ef = 0.68  # gnh3 / mmBTU --> default for diesel fuel, changed for other fuel types
        
        # From EPA NONROAD Conversion Factors for Hydrocarbon Emission Components.
        # Convert thc to voc
        self.voc_conversion = 1.053  # --> default for diesel fuel
        
        # Convert pm10 to PM2.5
        # not used at the moment...
        self.pm10topm25 = 0.97  # --> default for diesel fuel
        # convert from gallons to btu.
        # gal_to_btu = 128450  # Btu/gallon
        # -------Inputs End
        
        for run_code in run_codes:
            
            logger.info('Populating NONROAD combustion emissions table for %s' % (run_code, ))
            # path to results
            path = os.path.join(self.base_path, 'OUT', run_code)
            listing = os.listdir(path)  # @TODO: grabbing all files in the directory is probably not a good idea, should be more specific

            feedstock = run_code[0:2] 

            # write data to static files for debugging purposes
            f = open(os.path.join(self.base_path, 'OUT', '%s.csv' % (run_code, )), 'wb')
            writer = csv.writer(f)
            writer.writerow(('FIPS', 'scc', 'hp', 'fuel_cons_gal/yr', 'thc_exh', 'voc_exh', 'co_exh', 'nox_exh',
                             'co2_exh', 'so2_exh', 'pm10_exh', 'pm25_exh', 'nh3_exh', 'Description'))

            queries = []
            for cur_file in listing:
                # use for debugging
                # print "Current file is: %s -- %s" % (run_code, cur_file)
                reader = csv.reader(open(os.path.join(path, cur_file)))

                for i, row in enumerate(reader):
                    # account for headers in file, skip the first 10 lines
                    if i > 9:
                        # row[4] is the vehicle population.
                        if float(row[4]) > 0.0:

                            scc = row[2]
                            hp = row[3]

                            # _get_description updates the voc_conversion, nh3_ef and lhv for each fuel type
                            description, operation = self._get_description(run_code)

                            # check if it is a feedstock and operation that should be recorded.
                            if feedstock.startswith('F') or self.operation_dict[feedstock][operation[0]]:
                                # all emissions are recorder in metric tons.
                                # dry ton * metric ton / dry ton = metric ton
                                thc = float(row[5]) * convert_tonne
                                co = float(row[6]) * convert_tonne
                                nox = float(row[7]) * convert_tonne
                                co2 = float(row[8]) * convert_tonne
                                so2 = float(row[9]) * convert_tonne
                                pm10 = float(row[10]) * convert_tonne
                                pm25 = float(row[10]) * self.pm10topm25 * convert_tonne

                                # fuel consumption
                                # NONROAD README 5-10
                                # CNG is a gaseous fuel, and its fuel consumption is reported in gallons at
                                # standard temperature and pressure. This can be misleading if this very large number
                                # is viewed together with the fuel consumption of the other (liquid) fuels
                                # dt/year

                                fuel_cons = float(row[19])  # gal/year

                                voc = thc * self.voc_conversion
                                nh3 = fuel_cons * self.lhv * self.nh3_ef / 1e6  # gal * mmBTU/gal * gnh3/mmBTU = g nh3

                                # allocate non harvest emissions from cg to cs and ws.
                                if operation and operation[0] == 'N' and feedstock == 'CG' and self.regional_crop_budget is False:
                                    # add to cs.
                                    if self.operation_dict['CS'][operation[0]] and self.alloc['CS'] != 0:
                                        self._record(feed='CS', row=row[0], scc=scc, hp=hp, fuel_cons=fuel_cons, thc=thc, voc=voc, co=co, nox=nox, co2=co2, so2=so2, pm10=pm10,
                                                     pm25=pm25, nh3=nh3, description=description, run_code=run_code, writer=writer, queries=queries, alloc=self.alloc)
                                    # add to ws.
                                    if self.operation_dict['WS'][operation[0]] and self.alloc['WS'] != 0:
                                        self._record(feed='WS', row=row[0], scc=scc, hp=hp, fuel_cons=fuel_cons, thc=thc, voc=voc, co=co, nox=nox, co2=co2, so2=so2, pm10=pm10,
                                                     pm25=pm25, nh3=nh3, description=description, run_code=run_code, writer=writer, queries=queries, alloc=self.alloc)
                                    # add to corn grain.
                                    self._record(feed=feedstock, row=row[0], scc=scc, hp=hp, fuel_cons=fuel_cons, thc=thc, voc=voc, co=co, nox=nox, co2=co2, so2=so2, pm10=pm10,
                                                 pm25=pm25, nh3=nh3, description=description, run_code=run_code, writer=writer, queries=queries, alloc=self.alloc)
                                # don't change allocation.
                                else:
                                    self._record(feed=feedstock, row=row[0], scc=scc, hp=hp, fuel_cons=fuel_cons, thc=thc, voc=voc, co=co, nox=nox, co2=co2, so2=so2, pm10=pm10,
                                                 pm25=pm25, nh3=nh3, description=description, run_code=run_code, writer=writer, queries=queries, alloc=None)

                                # change constants back to normal, b/c they can be changed in _get_description()
                                self.lhv = 128450.0 / 1e6
                                self.nh3_ef = 0.68
                                self.voc_conversion = 1.053
                                self.pm10topm25 = 0.97

            self.db.input(queries)

            logger.info('Finished populating NONROAD combustion emissions table for %s' % (run_code, ))

    def _record(self, feed, row, scc, hp, fuel_cons, thc, voc, co, nox, co2, so2, pm10, pm25, nh3, description, run_code, writer, queries, alloc=None):
        """
        write data to static files and the database

        :param feed: STRING Feed stock
        :param row:
        :param scc:
        :param hp:
        :param fuel_cons:
        :param thc:
        :param voc:
        :param co:
        :param nox:
        :param co2:
        :param so2:
        :param pm10:
        :param pm25:
        :param nh3:
        :param description:
        :param run_code:
        :param writer:
        :param queries:
        :param alloc: dict(string: int) Allocation of non-harvest emissions between cg, cs, and ws
        :return:
        """

        self.kvals = {'fuel_cons': fuel_cons,
                      'thc': thc,
                      'voc': voc,
                      'co': co,
                      'nox': nox,
                      'co2': co2,
                      'so2': so2,
                      'pm10': pm10,
                      'pm25': pm25,
                      'nh3': nh3,
                      'description': description,
                      'row': row,
                      'scc': scc,
                      'hp': hp,
                      'run_code': run_code,
                      'scenario_name': self.cont.get('model_run_title'),
                      'feed': feed.lower()}

        # multiply the emissions by allocation constant
        if alloc is not None:
            pollutants = ('thc', 'voc', 'co', 'nox', 'co2', 'so2', 'pm10', 'pm25', 'nh3')
            for pollutant in pollutants:
                self.kvals[pollutant] *= alloc[feed] 

        writer.writerow((self.kvals['row'], self.kvals['scc'], self.kvals['hp'], self.kvals['fuel_cons'], self.kvals['thc'], self.kvals['voc'], self.kvals['co'], self.kvals['nox'],
                         self.kvals['co2'], self.kvals['so2'], self.kvals['pm10'], self.kvals['pm25'], self.kvals['nh3'], self.kvals['run_code']))

        q = """INSERT INTO {scenario_name}.{feed}_raw (fips, scc, hp, thc, voc, co, nox, co2, sox, pm10, pm25, fuel_consumption, nh3, description, run_code)
               VALUES ( {row},
                        {scc},
                        {hp},
                        {thc},
                        {voc},
                        {co},
                        {nox},
                        {co2},
                        {so2},
                        {pm10},
                        {pm25},
                        {fuel_cons},
                        {nh3},
                        '{description}',
                        '{run_code}')""".format(**self.kvals)
        queries.append(q)

    def airplane_emission(self, run_code):
        """
        Calculates emissions generated by aerial application of fertilizer/chemicals (i.e., crop dusting)

        Emission factors are based on data from the San Joaquin Valley Air Pollution Control District
        http://www.valleyair.org/air_quality_plans/EmissionsMethods/MethodForms/Current/CivilianAircraft2012.pdf

        :param run_code: run code specifying feedstock type, activity type, and tillage type
        :return:
        """
        pol_list = ['voc', 'co', 'nox', 'sox', 'pm10', 'pm25']
        till_dict = {'R': 'reducedtill',
                     'C': 'convtill',
                     'N': 'notill'}

        kvals = {'scenario_name': config.get('title'),
                 'constants_schema': config.get('constants_schema'),
                 'production_schema': config.get('production_schema')}

        if run_code.startswith('CG'):
            kvals['tillage'] = till_dict[run_code[4]]
            kvals['feed'] = 'cg'
            kvals['run_code'] = run_code
            kvals['conv_ton_to_mt'] = 0.90718474

            if run_code[4] == 'R':
                kvals['till_type'] = 'Reduced Till'
            elif run_code[4] == 'C':
                kvals['till_type'] = 'Conventional Till'
            elif run_code[4] == 'N':
                kvals['till_type'] = 'No Till'

            logger.info('Computing aerial emissions from crop dusting for CG for pollutant for run code: %s' % (run_code, ))

            for i, pollutant in enumerate(pol_list):
                kvals['ef_ton_per_ac'] = self.ef_crop_dust_dict[pollutant]
                kvals['pollutant'] = pollutant
                # @TODO: query_airplane will need to be revised to allow for equipment budgets outside region 13
                if i == 0:
                    query_airplane = """ INSERT INTO {scenario_name}.{feed}_raw (fips, scc, hp, thc, co2, fuel_consumption, nh3, {pollutant}, description, run_code)
                                         SELECT cd.fips, 0, 0, 0, 0, 0, 0, cd.{tillage}_planted_ac * {ef_ton_per_ac} * {conv_ton_to_mt}, '{till_type} - Non-Harvest, aerial', '{run_code}'
                                         FROM {production_schema}.cg_data cd
                                         LEFT JOIN {constants_schema}.fips_region fp ON fp.fips = cd.fips
                                         WHERE fp.polyfrr = 13 AND cd.{tillage}_prod > 0
                                     """.format(**kvals)
                else:
                    query_airplane = """ UPDATE {scenario_name}.{feed}_raw aerial
                                         LEFT JOIN {production_schema}.cg_data cd
                                         ON cd.fips = aerial.fips
                                         LEFT JOIN {constants_schema}.fips_region fp
                                         ON fp.fips = cd.fips
                                         SET {pollutant} = cd.{tillage}_planted_ac * {ef_ton_per_ac} * {conv_ton_to_mt}
                                         WHERE fp.polyfrr = 13 AND cd.{tillage}_prod > 0 AND description LIKE '{till_type} - Non-Harvest, aerial' AND run_code = '{run_code}'
                                     """.format(**kvals)
                self.db.input(query_airplane)

    def _parse_run_code(self, run_code):
        """
        Parse run_code to determine feedstock, tillage type, activity type, and year and fuel if applicable
        :param run_code: STRING
        :return: DICTIONARY {run_code: STRING, feedstock: STRING, tillage: STRING, year: STRING, activity: STRING, fuel: STRING}
        """

        feed = run_code[0:2]

        # fuel is only relevant for irrigation run_codes (which currently only occur for CG)
        # year is only relevant for crops with rotation, currently MS and SG
        fuel = None
        year = None

        # the default pattern for run_codes is: FF_TA where FF = feedstock, T = tillage type, and A = activity type
        activity = run_code[4]
        tillage = run_code[3]

        # CG (and currently only CG) may have irrigation, in which case 'I' replaces tillage type and activity becomes a fuel type
        # therefore, the pattern becomes: FF_AFu where FF = feedstock, A = activity type, and Fu = fuel and a big FU to future developers
        if feed == 'CG' and run_code[3] == 'I':
            activity = 'I'
            tillage = None
            fuel = run_code[4]

        # MS and SG are managed over several years and without tillage. Therefore, the pattern becomes: FF_AY where
        # FF = feedstock, A = activity, and Y = rotation year, which may be 1 or 2 digits
        if feed in ('MS', 'SG'):
            activity = run_code[3]
            tillage = None
            year = run_code[4:]

        # init kvals for string formatting
        kvals = {'run_code': run_code,
                 'feedstock': feed,
                 'tillage': tillage,
                 'year': year,
                 'activity': activity,
                 'fuel': fuel}

        logger.debug('{run_code:6}: crop: {feedstock:4} year: {year:4} tillage: {tillage:4} activity: {activity:4} fuel: {fuel:4}'.format(**kvals))

        return kvals

    def _set_factors(self, fuel):
        """
        Set lhv, nh3_ef, voc_conversion, and pm10topm25 factors based on fuel type.

        :param fuel: STRING one of D, L, C, G
        :return:
        """

        if fuel == 'D':
            self.lhv = 128450.0 / 1e6
            self.nh3_ef = 0.68
            self.voc_conversion = 1.053
            self.pm10topm25 = 0.97
        elif fuel == 'L':
            self.lhv = 84950.0 / 1e6
            self.nh3_ef = 0.0  # data not available
            self.voc_conversion = 0.995
            self.pm10topm25 = 1.0
        elif fuel == 'C':
            # 983 btu/ft3 at 1atm and 32F, standard temperature and pressure.
            self.lhv = 20268.0 / 1e6
            self.nh3_ef = 0.0  # data not available
            self.voc_conversion = 0.004
            self.pm10topm25 = 1.0
        elif fuel == 'G':
            self.lhv = 116090.0 / 1e6
            self.nh3_ef = 1.01
            self.voc_conversion = 0.933
            self.pm10topm25 = 0.92

    def _get_description(self, run_code):
        """

        :param run_code: run code for NONROAD run
        :param scc: source category code for equipment
        :return: (STRING, STRING) description, activity
        """

        # set defaults
        activity = None
        description = None

        # define lookups
        activity_lk = {'N': 'Non-Harvest',
                       'H': 'Harvest',
                       'I': 'Irrigation',
                       'L': 'Loading',
                       'T': 'On-farm Transport'}

        tillage_lk = {'R': 'Reduced Till',
                      'N': 'No Till',
                      'C': 'Conventional Till'}

        fuel_lk = {'D': 'Diesel Irrigation',
                   'L': 'LPG Irrigation',
                   'C': 'CNG Irrigation',
                   'G': 'Gasoline Irrigation'}

        # parse run code
        run_code_values = self._parse_run_code(run_code)

        # split parsing for ease of use
        year = run_code_values['year']
        feedstock = run_code_values['feedstock']
        tillage = run_code_values['tillage']
        activity = run_code_values['activity']
        fuel = run_code_values['fuel']  # set to None already if activity != 'I'
        irrigation = fuel_lk[fuel] if fuel is not None else None

        # set activity to non-harvest for irrigation
        if activity == 'I':
            activity = 'N'

        # expand activity
        activity = activity_lk[activity]

        # init kvals for string formatting, swapping for descriptive values if necessary
        kvals = {'activity': activity,
                 'tillage': tillage_lk[tillage] if tillage is not None else None,
                 'irrigation': irrigation,
                 'year': year}

        if year is not None:  # MS and SG are caught here
            description = 'Year {year} - {activity}'
        if feedstock in ('FR', 'FW'):
            description = '{activity} - {activity}'  # I don't know why it's done this way
        if feedstock in ('CS', 'WS', 'SS', 'CG'):
            description = '{tillage} - {activity}'
        if irrigation is not None:
            description = '{irrigation} - {activity}'

        description = description.format(**kvals)

        # set emission factors and conversion rates
        self._set_factors(fuel=fuel)  # this is here because that's where it originally was and requires parsing the run_code to collect the fuel type; it obviously should be somewhere else. May god be with you if you try to move it.

        return description, activity

if __name__ == '__main__':
    raise NotImplementedError
