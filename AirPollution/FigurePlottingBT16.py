# -*- coding: utf-8 -*-
"""
Created on Tue Apr 12 14:07:42 2016

Creates figures for the 2016 Billion Ton Study

@author: aeberle
"""

import matplotlib
import matplotlib.pyplot as plt
from utils import config, logger
from pylab import median, mean


class FigurePlottingBT16:
    def __init__(self, db):
        self.db = db

        self.f_color = ['r', 'b', 'g', 'k', 'c']
        self.f_marker = ['o', 'o', 'o', 'o', 'o']
        self.row_list = [0, 1, 0, 1, 0, 1]
        self.col_list = [0, 1, 2, 0, 1, 2]
        self.pol_list_label = ['$NO_x$', '$VOC$', '$PM_{2.5}$', '$CO$', '$PM_{10}$', '$SO_x$' ]
        self.pol_list = ['NOx', 'VOC', 'PM25', 'CO', 'PM10', 'SOx']

        self.feedstock_list = ['Corn Stover', 'Switchgrass', 'Wheat Straw', 'Corn Grain', 'Forest Residue']  # @TODO: remove hardcoded values
        self.f_list = ['CS']#, 'SG', 'WS', 'CS', 'FR']  # @TODO: remove hardcoded values

        self.etoh_vals = [89.6, 89.6, 89.6, 2.76/0.02756, 75.7,]  # gallons per dry short ton

    def compile_results(self):
        # initialize kvals dict for string formatting

        kvals = {'scenario_name': config.get('title'),
                 'year': config.get('year_dict')['all_crops'],
                 'yield': config.get('yield')}

        query_create_table = """ DROP TABLE IF EXISTS {scenario_name}.total_emissions;
                                 CREATE TABLE {scenario_name}.total_emissions (fips char(5),
                                                                              Year char(4),
                                                                              Yield char(2),
                                                                              NOx float,
                                                                              NH3 float,
                                                                              VOC float,
                                                                              PM10 float,
                                                                              PM25 float,
                                                                              SOx float,
                                                                              CO float,
                                                                              Source_Category varchar(255),
                                                                              NEI_Category char(2),
                                                                              Feedstock char(2))
                            """.format(**kvals)
        self.db.create(query_create_table)

        for feedstock in self.f_list:
            kvals['feed'] = feedstock.lower()
            logger.info('Inserting data for fertilizer and chemical emissions')
            query_fert_chem = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                  SELECT   fert.fips,
                                           '{year}' as 'Year',
                                           '{yield}' as 'Yield',
                                           fert.NOx as 'NOx',
                                           fert.NH3 as 'NH3',
                                           chem.VOC as 'VOC',
                                           0 as 'PM10',
                                           0 as 'PM25',
                                           0 as 'SOx',
                                           0 as 'CO',
                                           'Fertilizer and Chemical' as 'Source_Category',
                                           'NP' as 'NEI_Category',
                                           '{feed}' as 'Feedstock'
                                  FROM (SELECT fips, sum(NOx) as 'NOx', sum(NH3) as 'NH3'
                                        FROM reg2.cg_nfert
                                        GROUP BY fips) fert,
                                        (SELECT fips, sum(VOC) as 'VOC'
                                        FROM reg2.cg_chem
                                        GROUP BY fips) chem
                                  WHERE fert.fips = chem.fips
                             """.format(**kvals)
            self.db.input(query_fert_chem)

            logger.info('Inserting data for non-harvest emissions')
            query_non_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                    SELECT fips,
                                           '{year}' as 'Year',
                                           '{yield}' as 'Yield',
                                           sum(NOx) as 'NOx',
                                           sum(NH3) as 'NH3',
                                           sum(VOC) as 'VOC',
                                           sum(PM10) + sum(IFNULL(fug_pm10, 0)) as 'PM10',
                                           sum(PM25) + sum(IFNULL(fug_pm25, 0)) as 'PM25',
                                           sum(SOx) as 'SOx',
                                           sum(CO) as 'CO',
                                           'Non-Harvest' as 'Source_Category',
                                           'NR' as 'NEI_Category',
                                           '{feed}' as 'Feedstock'
                                    FROM {scenario_name}.{feed}_raw
                                    WHERE description LIKE '%Non-Harvest%'
                                    GROUP BY fips
                                """.format(**kvals)
            self.db.input(query_non_harvest)

            logger.info('Inserting data for harvest emissions')
            query_harvest = """ INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, NOx, NH3, VOC, PM10, PM25, SOx, CO, Source_Category, NEI_Category, Feedstock)
                                SELECT fips,
                                       '{year}' as 'Year',
                                       '{yield}' as 'Yield',
                                       sum(NOx) as 'NOx',
                                       sum(NH3) as 'NH3',
                                       sum(VOC) as 'VOC',
                                       sum(PM10) + sum(IFNULL(fug_pm10, 0)) as 'PM10',
                                       sum(PM25) + sum(IFNULL(fug_pm25, 0)) as 'PM25',
                                       sum(SOx) as 'SOx',
                                       sum(CO) as 'CO',
                                       'Harvest' as 'Source_Category',
                                       'NR' as 'NEI_Category',
                                       '{feed}' as 'Feedstock'
                                FROM {scenario_name}.{feed}_raw
                                WHERE (description LIKE '% Harvest%' OR description = 'Loading')
                                GROUP BY fips
                            """.format(**kvals)
            self.db.input(query_harvest)

            system_list = ['A', 'C']
            pol_list = ['NOx', 'PM10', 'PM25', 'SOx', 'VOC', 'CO', 'NH3']
            logistics = {'A': 'Advanced', 'C': 'Conventional'}

            for system in system_list:
                kvals['system'] = system
                for i, pollutant in enumerate(pol_list):
                    if pollutant == 'SOx':
                        kvals['pollutant'] = 'SO2'
                    else:
                        kvals['pollutant'] = pollutant
                    kvals['pollutant_name'] = pollutant
                    kvals['transport_cat'] = 'Transport, %s' % (logistics[system])
                    kvals['preprocess_cat'] = 'Pre-processing, %s' % (logistics[system])

                    logger.info('Inserting data {transport_cat}, pollutant: {pollutant}'.format(**kvals))
                    if i == 0:
                        query_transport = """   INSERT INTO {scenario_name}.total_emissions (fips, Year, Yield, {pollutant}, Source_Category, NEI_Category, Feedstock)
                                                SELECT fips,
                                                       '{year}' as 'Year',
                                                       '{yield}' as 'Yield',
                                                       total_emissions as '{pollutant_name}',
                                                       '{transport_cat}' as 'Source_Category',
                                                       'OR' as 'NEI_Category',
                                                       '{feed}' as 'Feedstock'
                                                FROM {scenario_name}.transportation
                                                WHERE  (logistics_type = '{system}' AND
                                                       yield_type = '{yield}' AND
                                                       feedstock = '{feed}' AND
                                                       pollutantID = '{pollutant_name}')
                                                GROUP BY fips;
                                            """.format(**kvals)
                        self.db.input(query_transport)
                    elif i > 0:
                        if not pollutant.startswith('PM'):
                            query_transport = """   UPDATE {scenario_name}.total_emissions tot
                                                    INNER JOIN {scenario_name}.transportation trans
                                                    ON trans.fips = tot.fips AND trans.yield_type = tot.Yield AND trans.feedstock = tot.feedstock
                                                    SET tot.{pollutant_name} = trans.total_emissions
                                                    WHERE trans.pollutantID = '{pollutant}' AND tot.Source_Category = '{transport_cat}' AND trans.logistics_type = '{system}';
                                              """.format(**kvals)
                        elif pollutant.startswith('PM'):
                            query_transport = """   UPDATE {scenario_name}.total_emissions tot
                                                    INNER JOIN {scenario_name}.transportation trans
                                                    ON trans.fips = tot.fips AND trans.yield_type = tot.Yield AND trans.feedstock = tot.feedstock
                                                    LEFT JOIN {scenario_name}.fugitive_dust fd
                                                    ON fd.fips = tot.fips AND fd.yield_type = tot.Yield AND fd.feedstock = tot.feedstock
                                                    SET tot.{pollutant_name} = IF(trans.total_emissions > 0.0, trans.total_emissions + fd.total_fd_emissions, 0)
                                                    WHERE trans.pollutantID = '{pollutant}' AND fd.pollutantID = '{pollutant}' AND tot.Source_Category = '{transport_cat}' AND trans.logistics_type = '{system}' AND fd.logistics_type = '{system}';
                                              """.format(**kvals)
                        self.db.input(query_transport)


    def plot_total_emissions(self):

        fig, axarr = plt.subplots(2, 3)
        matplotlib.rcParams.update({'font.size': 13})

        for f_num, feedstock in enumerate(self.f_list):
            for p_num, pollutant in enumerate(self.pol_list):
                logger.info('Collecting data for pollutant: %s, feedstock: %s' % (pollutant, feedstock, ))
                emissions_per_dt = self.collect_data(p_num=p_num, f_num=f_num)

                # compute statistics for emissions (in grams/dt -- must convert from metric tons pollutant to grams pollutant)
                mean_val = mean(emissions_per_dt)*1e6
                med_val = median(emissions_per_dt)*1e6
                max_val = max(emissions_per_dt)[0]*1e6
                min_val = min(emissions_per_dt)[0]*1e6

                row = self.row_list[p_num]
                col = self.col_list[p_num]
                ax1 = axarr[row, col]
                ax1.set_yscale('log')
                #ax1.set_ylim(bottom=1e1, top=1e3)

                ax1.set_title(self.pol_list_label[p_num])

                ax1.plot([f_num + 1], mean_val, 'b', marker='_', markersize=20)
                ax1.plot([f_num + 1], med_val, 'b', marker='_', markersize=7)

                # Plot the max/min values
                ax1.plot([f_num + 1] * 2, [max_val, min_val], 'b', marker=self.f_marker[f_num], markersize=2)

                # Set axis limits
                ax1.set_xlim([0, 9])

                ax2 = ax1.twinx()

                # compute statistics for emissions per gallon (in grams/galEtOH)
                mean_val /= self.etoh_vals[f_num]
                med_val /= self.etoh_vals[f_num]
                max_val /= self.etoh_vals[f_num]
                min_val /= self.etoh_vals[f_num]

                ax2.plot([f_num + 1], mean_val, 'r', marker='_', markersize=20)
                ax2.plot([f_num + 1], med_val, 'r', marker='_', markersize=7)

                # Plot the max/min values
                ax2.plot([f_num + 1] * 2, [max_val, min_val], 'r', marker=self.f_marker[f_num], markersize=2)

                ax2.set_xlim([0, 9])
                ax2.set_yscale('log')
                #ax2.set_ylim(bottom=1e-1, top=1e3)

                if col == 2:
                    ax2.set_ylabel('g/gge', color='r', fontsize=14)
                else:
                    plt.setp(ax2.get_yticklabels(), visible=False)

                for tl in ax2.get_yticklabels():
                    tl.set_color('r')

                for tl in ax1.get_yticklabels():
                    tl.set_color('b')
                ax1.set_xticklabels(([''] + self.f_list), rotation='vertical')

        # Fine-tune figure; hide x ticks for top plots and y ticks for right plots
        plt.setp([a.get_xticklabels() for a in axarr[0, :]], visible=False)
        # plt.setp([a.get_yticklabels() for a in axarr[:, 1]], visible=False)
        # plt.setp([a.get_yticklabels() for a in axarr[:, 2]], visible=False)

        axarr[0, 0].set_ylabel('g/dt', color='b', fontsize=14)
        axarr[1, 0].set_ylabel('g/dt', color='b', fontsize=14)

        fig.tight_layout()

        plt.show()

    def collect_data(self, p_num, f_num):
        """
        Collect data for one pollutant/feedstock combination
        Return the total emissions

        :param f_num: feedstock number
        :param p_num: pollutant number
        :return emissions_per_pollutant: emissions in (pollutant dt) / (total feedstock harvested dt)
        """

        kvals = {'feed_abr': self.f_list[f_num],
                 'feedstock': self.f_list[f_num],
                 'pollutant': self.pol_list[p_num],
                 'scenario_name': config.get('title'),
                 'production_schema': config.get('production_schema')}

        if self.pol_list[p_num].startswith('PM'):
            query_emissions_per_prod = """ SELECT (sum({pollutant})+ IFNULL(sum(fug_{pollutant}), 0))/prod.total_prod AS 'mt_{pollutant}_perdt'
                        FROM {scenario_name}.{feed_abr}_raw raw
                        LEFT JOIN {production_schema}.{feed_abr}_data prod ON raw.fips = prod.fips
                        GROUP BY raw.FIPS
                        ORDER BY raw.FIPS""".format(**kvals)
        else:
            query_emissions_per_prod = """ SELECT sum({pollutant})/prod.total_prod AS 'mt_{pollutant}_perdt'
                        FROM {scenario_name}.{feed_abr}_raw raw
                        LEFT JOIN {production_schema}.{feed_abr}_data prod ON raw.fips = prod.fips
                        GROUP BY raw.FIPS
                        ORDER BY raw.FIPS
                        """.format(**kvals)

        emissions_per_production = self.db.output(query_emissions_per_prod)

        return emissions_per_production
