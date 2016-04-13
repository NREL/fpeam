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

        self.feedstock_list = ['Corn Grain']#, 'Switchgrass', 'Corn Stover', 'Wheat Straw', ]  # @TODO: remove hardcoded values
        self.f_list = ['CG']#, 'SG', 'CS', 'WS', ]  # @TODO: remove hardcoded values

        self.etoh_vals = [2.76/0.02756, 89.6, 89.6, 89.6, 75.7]  # gallons per dry short ton

    def total_emissions(self):

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
