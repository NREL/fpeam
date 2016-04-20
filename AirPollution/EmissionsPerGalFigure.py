"""
@comments: much of this plotting utility was taken from the following URL:
http://matplotlib.org/examples/pylab_examples/boxplot_demo2.html
"""

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from pylab import *
import matplotlib.pyplot as plt
from scipy.stats import scoreatpercentile
from matplotlib.ticker import FixedFormatter
import os


class EmissionsPerGallon():
    """
    Creates a graph for each air pollutant emmision.
    Saved as Figures/PerGalEtOH_'+pollutant+'.png
    Each graph has the total amount of air pollutants for each feedstock.
    X-axis: feedstock
    Y-axis: pollutant emmisions per gallon.
    """

    def __init__(self, cont):
        """
        Create emmision graphs.
        @param db: Database.
        @param path: Directory path.
        """
        self.path = cont.get('path')
        self.db = cont.get('db')
        self.document_file = "EmissionsPerGallon"
    
        self.f = open(os.path.join(self.path, 'FIGURES', 'PerGalEtOH_numerical.csv'), 'w')
        
        self.f.write('feedstock, pollutant, max, 95, 75, median, 25, 5, min, mean \n')
        
        # define inputs/constants:  
        pollutant_labels = ['$NO_x$', '$NH_3$', '$CO$', '$SO_x$', '$VOC$', '$PM_{10}$', '$PM_{2.5}$']

        feedstock_list = ['Corn Grain', 'Switchgrass', 'Corn Stover', 'Wheat Straw']#, 'Forest Residue']
        f_list = ['CG', 'SG', 'CS', 'WS']#, 'FR']
        pollutant_list = ['NOx', 'NH3', 'CO', 'SOx', 'VOC', 'PM10', 'PM25']
        etoh_vals = [2.76, 89.6, 89.6, 89.6, 75.7]  # gallons per production (bu for CG, dry short ton for everything else)    

        query_table = 'summedemissions'
    
        for p_num, pollutant in enumerate(pollutant_list):
            # -----------------EXTRACT DATA FROM THE DATABASE-----------------    
            data_array = self.__collect_data__(query_table, feedstock_list, pollutant, etoh_vals)
            # -----------------PART 2, PLOT DATA----------------------------------
            # pretty plotting things
            fig = plt.figure(figsize=(8, 6))
            canvas = FigureCanvas(fig)        
            self.ax1 = fig.add_subplot(111)
            # adjust this value to change the plot size
            # ----------------------------------------------------------------
            plt.subplots_adjust(left=0.15, right=0.99, top=0.95, bottom=0.1)
            # ---------------------------------------------------------------- 

            # -------create boxplot
            bp = plt.boxplot(data_array, notch=0, sym='', vert=1, whis=1000)
                
            plt.setp(bp['boxes'], color='black')
            plt.setp(bp['whiskers'], color='black', linestyle='-')
            plt.setp(bp['medians'], color='black')
            # plt.yscale('log')
            plt.semilogy()
            self.ax1.yaxis.set_major_formatter(FixedFormatter([0.001, 0.01, 0.1, 1, 10, 100]))  # for above y-axis
            # self.ax1.yaxis.set_major_formatter(FixedFormatter([0.00001, 0.0001, 0.001]))#for below y-axis
            self.ax1.tick_params(axis='y', labelsize=15)  # changes font size of y-axis
            plot_title = pollutant_labels[p_num]
            axis_title = '%s emissions  (g/gal EtOH)' % (pollutant_labels[p_num])

            self.__set_axis__(plot_title, axis_title, data_array, f_list)    
            # plot 95% intervals 
            # perc95 = self.__plot_interval__(data_array)
            self.__plot_interval__(data_array)

            fig.savefig(self.path + 'Figures' + os.sep + 'PerGalEtOH_' + pollutant + '.png', format='png')

            print pollutant

        self.f.close()

    def __collect_data__(self, query_table, feedstock_list, pollutant, etoh_vals):
        data = []
        for fNum, feedstock in enumerate(feedstock_list):
            # query_table = summedemissions
            # emmisions = (pollutant mt) / ( (feed stock dt) * (gallons / feed stock lb) )
            # emmisions = (pollutant mt / gallons)
            # SELECT (%s) / (prod * %s * 1e-6) FROM %s.%s WHERE prod > 0.0 AND feedstock ilike '%s';
            # % (pollutant, etoh_vals[fNum], self.db.schema, query_table, feedstock)
            # 
            # emmissions per acre = (pollutant lbs) / (total acres)
            # emmissions = pollutant / harv_ac
            # SELECT (%s) / (harv_ac) FROM %s.%s WHERE harv_ac > 0.0 AND feedstock ilike '%s';
            # % (pollutant,  self.db.schema, query_table, feedstock)
            
            query = """
                    SELECT (%s) / (prod * %s * 1e-6) FROM %s.%s WHERE prod > 0.0 AND feedstock LIKE '%s';
                    """ % (pollutant, etoh_vals[fNum], self.db.schema, query_table, feedstock)
            emmisions = self.db.output(query)
            data.append(emmisions)

        self.__write_data__(data, feedstock_list, pollutant)

        return data

    def __plot_interval__(self, data_array):

        num_feed = 5
        num_array = array([x for x in range(num_feed)]) + 1  # index starts at 1, not zero

        # plot 95% interval
        perc95 = array([scoreatpercentile(data_array[0], 95), scoreatpercentile(data_array[1], 95),
                        scoreatpercentile(data_array[2], 95), scoreatpercentile(data_array[3], 95), 
                        scoreatpercentile(data_array[4], 95)])

        # plot 5% interval
        perc5 = array([scoreatpercentile(data_array[0], 5), scoreatpercentile(data_array[1], 5),
                       scoreatpercentile(data_array[2], 5), scoreatpercentile(data_array[3], 5), 
                       scoreatpercentile(data_array[4], 5)])

        plt.plot(num_array, perc95, '_', markersize=15, color='k')
        plt.plot(num_array, perc5, '_', markersize=15, color='k')

        # calculate mean and plot it.  Means are not used in box plots
        # means = [mean(data_array[0]), mean(data_array[1]), mean(data_array[2]), mean(data_array[3]), mean(data_array[4])]
        # plt.plot((num_array), means, '_', markersize=75, color='b')

    def __set_axis__(self, plot_title, axis_title, data_array, data_labels):
        """
        function to set axis titles and plot titles
        """
        # Add a horizontal grid to the plot
        self.ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.7)

        # determine limits of axis
        # self.ax1.set_ylim(bottom=1e-03, top=1e02)  # old Jeremy way
        self.ax1.set_ylim(bottom=0.001, top=100)  # for above 0.001 y axis
        # self.ax1.set_ylim(bottom=0.00001, top=0.001)  # for below 0.001 y axis

        # Hide these grid behind plot objects
        self.ax1.set_axisbelow(True)

        self.ax1.set_ylabel(axis_title, size=25, style='normal')

        self.ax1.set_xticklabels(data_labels, size=25, style='normal')
        #    ax1.set_title(plot_title+' Mg per gallon of EtOH', size=20, style='normal')

        # -------------------------------------------------------------------------------
        # This section plots the smallest values that do not show up on the graph
        # Labeled with an arrow, and the max/min values.
        position_list = [0, 2, 3, 4, 5]
        position_data = []
        for p_num, position in enumerate(position_list):
            min_val = min(data_array[p_num])[0]
            if min_val < 1e-3:
                min_string = '%.0e' % (min_val,)
                max_string = '%.0e' % (max(data_array[p_num])[0],)

                # Annotates the max and min on the boxplot value            
                self.ax1.annotate(' min=' + min_string, xy=(position - 0.25, 2.5e-3), size=12)
                self.ax1.annotate('max=' + max_string, xy=(position - 0.25, 4.0e-3), size=12)
                # arrow pointing down where the value is located
                self.ax1.annotate('', xy=(position, 1.0e-3),
                                  xytext=(position, 1.9e-3),
                                  arrowprops=dict(arrowstyle="->"))
                position_data.append(p_num)

    def __write_data__(self, data_array, feedstock_list, pollutant):

        for fNum, feedstock in enumerate(feedstock_list):
            lines = [feedstock, pollutant, max(data_array[fNum])[0],
                     scoreatpercentile(data_array[fNum], 95), 
                     scoreatpercentile(data_array[fNum], 75),
                     median(data_array[fNum]),
                     scoreatpercentile(data_array[fNum], 25), 
                     scoreatpercentile(data_array[fNum], 5),
                     min(data_array[fNum])[0],
                     mean(data_array[fNum])]             

            self.f.write(str(lines) + '\n')
