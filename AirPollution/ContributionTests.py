# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 09:18:49 2012
@author: nfisher
Chooses the sql to grab data for ContributionFigure graph.
"""


class ChooseSQL:

    def __doc__(self):
        return 'Create a structured query based on ( activity, pollutant, feedstock ) inputs'
    
    def __init__(self, activity, pollutant, feedstock, schema):
        self.schema = schema
        self.act = activity
        self.pol = pollutant
        self.feed = feedstock
        self.query_string = ''

        self.raw_table = feedstock.lower() + '_raw'
        
        if pollutant == 'NOx' or pollutant == 'NH3':
            self.fert_table = feedstock.lower() + '_nfert'

        if pollutant == 'VOC' and (feedstock == 'CG' or feedstock == 'SG'):
            self.chem_table = feedstock.lower() + '_chem'

    def get_query(self):
        """
        This method chooses which tables to query based on the inputs
        """

    # -- pre-define the test cases for which there are zero emissions   
        if self.feed == 'FR' and self.act == 'Harvest':
            return self.__return_fr_harv__()  # special case
        elif self.feed == 'FR':
            return self.__return_null__()

    # fertilizer only looks at nh3 and nox from fertilizer application
        elif self.act == 'Fertilizer' and (self.pol != 'NOx' and self.pol != 'NH3'):
            return self.__return_null__()
    
    # chemical only looks at voc from herbicide and pesticide
        elif self.act == 'Chemical' and self.pol != 'VOC':
            return self.__return_null__()

    # zero cases for CS and WS
        elif (self.feed == 'CS' or self.feed == 'WS') and (self.act == 'Non-Harvest' or self.act == 'Chemical'):     
            return self.__return_null__()

    # --- end of pre-defined cases for which there are zero emissions       
        # @TODO: refactor remaining elif atrocities
        elif( ( ( self.pol == 'CO' or self.pol.startswith('SO') ) 
                    and 
                ( self.act == 'Non-Harvest' or 
                self.act == 'Harvest' or 
                self.act == 'Transport' ) 
              )
                or 
              ( self.pol == 'VOC' 
                    and not
                ( self.feed == 'CG' or self.feed == 'SG' )
              )
            ): 
    
            # query raw table for sox and co. query raw table for voc only when feedstock
            # is not corn grain or switchgrass (_chem emissions occur here)
            return self.__query_raw__()            

        elif self.pol.startswith('PM') and (self.act == 'Non-Harvest' or self.act == 'Harvest' or self.act == 'Transport'):
            return self.__query_raw__()
        elif( (self.pol == 'NH3' or self.pol == 'NOx' ) ):
            return self.__queryRawFert__()
        elif( (self.pol == 'VOC' )
                and
                (self.feed == 'CG' or self.feed == 'SG' )
            ):
            return self.__query_raw_chem__()
        else:
            raise Exception('Error in test structure\nInputs were: %s, %s, %s' % (self.feed, self.pol, self.act))

    def __return_null__(self):
        """
        Handle cases where there are no values to return
        """
        self.query_string = 'No activity at this location'

    def __return_fr_harv__(self):
        """
        Special case for Forest Residue
        """
        self.query_string = 'FR Harvest'

    def __query_raw__(self):
        """
        Assemble queries that need only the '*_raw' tables. 
        """        
        
        if self.pol.startswith('PM'):
            sum_pollutant = "(sum(%s) + IFNULL(sum(fug_%s),0))" % (self.pol, self.pol)
        else:
            sum_pollutant = "sum(%s)" % (self.pol,)

        if self.act == 'Harvest':
            act = ' ' + self.act
        else:
            act = self.act

        kvals = {'pollutant': self.pol,
                 'scenario_name': self.schema,
                 'raw_table': self.raw_table,
                 'activity': act,
                 'sum_pollutant': sum_pollutant}

        self.query_string = """
                                SELECT (a.x / t.x) AS x
                                FROM (SELECT DISTINCT fips, {sum_pollutant} AS x
                                      FROM {scenario_name}.{raw_table}
                                      WHERE description LIKE '%{activity}%'
                                      GROUP BY fips
                                      ) a,
                                     (SELECT DISTINCT fips, {sum_pollutant} AS x
                                      FROM {scenario_name}.{raw_table}
                                      GROUP BY fips
                                      ) t
                                WHERE a.fips = t.fips AND t.x > 0.0 AND a.x > 0.0;
                            """.format(**kvals)

    def __queryRawFert__(self):
        """
        Assemble queries that need the '*_raw' and '*_fert' tables. 
        
        This part seems very odd.
        If you are not actually intersested in fertilizers, but are doing a calculation
        to get Nox and nh3, shouldnt you not care about fert.x for the ration in the first part?
        """

        kvals = {'pollutant': self.pol,
                 'scenario_name': self.schema,
                 'raw_table': self.raw_table,
                 'fert_table': self.fert_table,
                 'activity': self.act}

        if self.act != 'Fertilizer':
            ratio = "(act.x)/(raw.x + act.x)"
            conditions = """, (SELECT DISTINCT fips, sum({pollutant}) as x
                                      FROM {scenario_name}.{raw_table}
                                      WHERE description LIKE '%{activity}%'
                                      GROUP BY fips) act
                        WHERE act.fips = raw.fips and act.fips = fert.fips and act.x > 0.0""".format(**kvals)

        else:
            ratio = "(fert.x)/(raw.x+fert.x)"
            conditions = "WHERE raw.fips = fert.fips"

        kvals['ratio'] = ratio
        kvals['conditions'] = conditions

        self.query_string = """
                                SELECT {ratio} as x
                                FROM (SELECT DISTINCT r.fips, sum(r.{pollutant}) as x
                                      FROM {scenario_name}.{raw_table} r group by r.fips) raw,
                                     (SELECT DISTINCT fips, sum({pollutant}) as x
                                      FROM {scenario_name}.{fert_table}
                                      GROUP BY fips) fert
                                {conditions}
                                AND raw.x > 0.0 and fert.x > 0.0;
                            """.format(**kvals)

    def __query_raw_chem__(self):
        """
        Assemble queries that need the '*_raw' and '*_chem' tables.
        
        Almost identical code to queryRawFert(), kept separate for the sake of 
        being explicit 
        """
        kvals = {'pollutant': self.pol,
                 'scenario_name': self.schema,
                 'raw_table': self.raw_table,
                 'chem_table': self.chem_table,
                 'activity': self.act}

        if self.act != 'Chemical':
            ratio = "(act.x)/(raw.x + chem.x)"
            conditions = """, (SELECT DISTINCT fips, SUM({pollutant}) AS x
                               FROM {scenario_name}.{raw_table}
                               WHERE description LIKE '%% %{activity}%'
                               GROUP BY fips) act WHERE act.fips = raw.fips and act.fips = chem.fips and act.x > 0.0
                         """.format(**kvals)

        else:
            ratio = "(chem.x)/(raw.x+chem.x)"      
            conditions = "WHERE raw.fips = chem.fips"

        kvals['ratio'] = ratio
        kvals['conditions'] = conditions

        self.query_string = """
                                SELECT ({ratio}) AS x
                                FROM (SELECT DISTINCT r.fips, SUM(r.{pollutant}) AS x
                                      FROM {scenario_name}.{raw_table} r
                                      GROUP BY r.fips) raw,
                                     (SELECT DISTINCT fips, SUM({pollutant}) AS x
                                      FROM  {scenario_name}.{chem_table}
                                      GROUP BY fips) chem
                                {conditions}
                                AND raw.x > 0.0 AND chem.x > 0.0;
                            """.format(**kvals)