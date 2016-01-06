"""
Determines the number of counties with unhealthy amounts of air pollutants.
Has lines on the graph indicating what percentage of air pollutants would be bad.
Saved as Figures/RatioToNEI_'+query_table+'.png.
X-axis: Air pollutants.
Y-axis: Ratio of feed stock emmisions to the NEI collected emmision invetory.
"""

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from pylab import *
import matplotlib.pyplot as plt
from scipy.stats import scoreatpercentile
import re


class RatioToNEIFig():
    
    def __init__(self, cont):
        """
        Create model.
        @param db: Database.
        @param path: Path to Directory.
        """
        self.db = cont.get('db')
        self.path = cont.get('path')
        self.document_file = "RatioToNEIFig"
    
        self.f = open(self.path + 'Figures' + os.sep + 'RatioToNEI_Numerical.csv', 'w')
        
        self.f.write('feedstock, pollutant, max, 95, 75, median, 25, 5, min \n')
        
        pollutant_list = ['NH3', 'NOX', 'VOC', 'PM25', 'PM10', 'CO', 'SOX']
        # define inputs/constants:
        data_labels = ['$NH_3$', '$NO_x$', '$VOC$', '$PM_{2.5}$', '$PM_{10}$', '$CO$', '$SO_x$']
        feedstock_list = ['corn grain', 'switchgrass', 'corn stover', 'wheat straw', 'forest residue', 'cellulosic']

        # return number arrays for plotting
        self.num_pollut = 6
        self.num_array = array([x for x in range(self.num_pollut + 1)]) + 1  # index starts at 1, not zero
        
        plot_title = ''
    
        for feedstock in range(6):
            # Model Corn Grain Scenario
            if feedstock == 0:
                query_table = "cg_neiratio"

            # Model Switchgrass scenario
            elif feedstock == 1:
                query_table = "sg_neiratio"
    
            # Model Corn Stover scenario
            elif feedstock == 2:
                query_table = "cs_neiratio"
            
            # Model Wheat Straw scenario
            elif feedstock == 3:
                query_table = "ws_neiratio"
                
            # Model Forest Residue scenario
            elif feedstock == 4:
                query_table = "fr_neiratio"
            # Model all cellulosic
            elif feedstock == 5:
                query_table = "cellulosic_neiratio"
                
            print query_table
            # Sets Y-Axis label to include (n) county totals---------
            query_count = 'SELECT COUNT(fips) FROM sgnew.%s' % (query_table,)
            county_num = self.db.output(query_count, self.db.schema)
            county_fix = ''.join(str(s) for s in str(county_num) if s not in "()L[],")
            axis_title = 'Ratio (R) of %s emissions to 2008 NEI\n (n = %s counties)' % (feedstock_list[feedstock], county_fix)
            # PART 1, EXTRACT DATA FROM THE DATABASE-----------------
            data_array = self.__collect_data__(query_table)
            self.__general_stats__(data_array, pollutant_list, feedstock_list, feedstock)
        
            # PART 2, PLOT DATA--------------------------------------
      
            # pretty plotting things
            fig = plt.figure(figsize=(8, 8))
            canvas = FigureCanvas(fig)        
            self.ax1 = fig.add_subplot(111)
        
            # adjust this value to change the plot size for the paper
            # ------------------------------------------------------
            # plt.subplots_adjust(left=0.3, right=0.93, top=0.95, bottom=0.25)
            # plt.subplots_adjust(left=0.3, right=0.93, top=0.95, bottom=0.35)
            plt.subplots_adjust(left=0.20, right=0.93, top=0.95, bottom=0.25)
            # -----------------------------------------------
            
            # -------create boxplot
            bp = plt.boxplot(data_array, notch=0, sym='', vert=1, whis=1000)
                
            plt.setp(bp['boxes'], color='black')
            plt.setp(bp['whiskers'], color='black', linestyle='-')
            plt.setp(bp['medians'], color='black')
            plt.yscale('log')
        
            # perc95 = self.__plot_interval__(data_array)
            self.__plot_interval__(data_array)
            
            # tT = self.__count_at_threshold__(query_table)
            self.__count_at_threshold__(query_table)
            
            self.__set_axis__(plot_title, axis_title, data_array, data_labels)    

            # show()
            fig.savefig(self.path + 'Figures' + os.sep + 'RatioToNEI_' + query_table + '.png', format='png')

    #        print figure to a .png file (small file size)
    #        canvas.print_figure(query_table + '.tiff')

    def __collect_data__(self, query_table):
        pollutants = ['nh3', 'nox', 'voc', 'pm25', 'pm10', 'co', 'sox']
        nei_data = {}
        for poll in pollutants:
            nei_data[poll] = self._make_query(poll, query_table)

        # query = """SELECT nh3, nox, voc, pm25, pm10, co, sox 
        #         FROM %s.%s 
        #         WHERE co > 0.0 AND sox > 0.0;"""  % (self.db.schema, query_table)
        # data = self.db.output(query, self.db.schema)
        # 
        # #create arrays for the data
        # data_matrix = matrix(data)
        # 
        # #store data in a plottable format
        # nh3 = array(data_matrix[:,0])
        # nox = array(data_matrix[:,1])
        # voc = array(data_matrix[:,2])
        # pm25 = array(data_matrix[:,3])
        # pm10 = array(data_matrix[:,4])
        # co = array(data_matrix[:,5])
        # sox = array(data_matrix[:,6])
        # 
        # return [nh3, nox, voc, pm25, pm10, co, sox]

        return [nei_data[p] for p in pollutants]

    def _make_query(self, pollutant, query_table):
        query = """SELECT """ + pollutant + """
                FROM """ + self.db.schema + """.""" + query_table + """
                WHERE """ + pollutant + """ > 0.0;"""  
        data = self.db.output(query, self.db.schema)
        return data

    def __general_stats__(self, data_array, pollutant_list, feedstock_list, feedstock):
        """
        function to capture confidence interfals for co. Because the input data has the
        same population (n), the counts between each interval will the the same. i.e.
        the count of counties > the 95% interval will the be same for co as for nox.
        Hence, these statistic calculated here will apply to all of the pollutants.
        """
        for pNum, pollutant in enumerate(pollutant_list):
            lines = [feedstock_list[feedstock], pollutant, max(data_array[pNum])[0],
                     scoreatpercentile(data_array[pNum], 95),
                     scoreatpercentile(data_array[pNum], 75),
                     median(data_array[pNum]),
                     scoreatpercentile(data_array[pNum], 25),
                     scoreatpercentile(data_array[pNum], 5),
                     min(data_array[pNum])[0]]
            
            self.f.write(str(lines) + '\n')

    def __plot_interval__(self, data_array):
        """
        function to calculate and plot the 95% intervals
        """
        # plot 95% interval
        perc95 = array([scoreatpercentile(data_array[0], 95), scoreatpercentile(data_array[1], 95),
                        scoreatpercentile(data_array[2], 95), scoreatpercentile(data_array[3], 95),
                        scoreatpercentile(data_array[4], 95), scoreatpercentile(data_array[5], 95),
                        scoreatpercentile(data_array[6], 95)])
        plt.plot(self.num_array, perc95, '_', markersize=10, color='k')

        # plot 5% interval
        perc5 = array([scoreatpercentile(data_array[0], 5), scoreatpercentile(data_array[1], 5),
                       scoreatpercentile(data_array[2], 5), scoreatpercentile(data_array[3], 5),
                       scoreatpercentile(data_array[4], 5), scoreatpercentile(data_array[5], 5),
                       scoreatpercentile(data_array[6], 5)])
                 
        plt.plot(self.num_array, perc5, '_', markersize=10, color='k')
        
        # calculate mean and plot it. Make sure there are no None elements when calculating mean. Means are not in boxplots, took out
        # means = [mean([data for data in data_array[0] if data[0] is not None]), mean([data for data in data_array[1] if data[0] is not None]),
        #          mean([data for data in data_array[2] if data[0] is not None]), mean([data for data in data_array[3] if data[0] is not None]),
        #          mean([data for data in data_array[4] if data[0] is not None]), mean([data for data in data_array[5] if data[0] is not None]),
        #          mean([data for data in data_array[6] if data[0] is not None])]
        # plt.plot((self.num_array), means, '_', markersize=75, color='b')

        return perc95

    def __set_axis__(self, plot_title, axis_title, data_array, data_labels):
        """
        function to set axis titles and plot titles
        """
        # Add a horizontal grid to the plot, but make it very light in color
        # so we can use it for reading data values but not be distracting
        self.ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.7)
        
        # Hide these grid behind plot objects
        self.ax1.set_axisbelow(True)
        # self.ax1.spines['bottom'].set_position(('axes', 0.1)) reposition the axis...I wasnt thinking clearly
    
        self.ax1.set_ylabel(axis_title, size=15, style='normal', multialignment='center')
        # manually enter axis tick labels because they need to be the same for all plots.
        self.ax1.set_yticklabels(['$10^{-6}$', '$10^{-5}$', '$10^{-4}$', '$10^{-3}$', '$10^{-2}$', '$10^{-1}$', '$1$'],
                                 size=15, weight='bold', style='normal')
        
        # self.ax1.set_xticklabels(data_labels, size=15, style='normal')
        self.ax1.set_xticklabels(' ', size=15, style='normal')

        # self.ax1.xaxis.labelpad = 20  # hopefully moves it downward

        # Set the axes ranges and axes labels    
        self.ax1.set_xlim(0.5, self.num_pollut * 1.15 + 1) 
        top = 3
        bottom = 10e-7
        self.ax1.set_ylim(bottom, top)

        # ----colored arrows--------------------------------------------------------------------
        self.ax1.text(8.28, 0.2, '0.2' + '       ', size=8, weight='bold', color='white', va="center", ha="center", rotation=0,
                      bbox=dict(boxstyle="larrow", color='red', alpha=0.5))
        self.ax1.text(8.28, 0.1, '0.1 ' + '      ', size=8, weight='bold', color='white', va="center", ha="center", rotation=0,
                      bbox=dict(boxstyle="larrow", color='green', alpha=0.5))
        self.ax1.text(8.28, 0.05, '0.05', size=8, weight='bold', color='white', va="center", ha="center", rotation=0,
                      bbox=dict(boxstyle="larrow", color='blue', alpha=0.5))
        # ax1.xaxis.set_visible(False)
        
        # Removed the number of counties that are used. Because alot of the NEI data does not use NH3 data which messes up this function.
        # self.ax1.annotate('N = '+str(shape(data_array)[1])+' counties', xy=(6.5, 1), xytext=(5.5, 1))
        # -------min located under the graph-----------------------------------------------------
        self.ax1.text(0.3, 0.5e-6, 'min = ', size=8, alpha=0.7)
        self.ax1.text(0.3, 0.45e-6, '_________________________________________________________________________', alpha=0.7)
        
        # -------x-axis labels--------------------------------------------------------------------
        for pNum, labels in enumerate(data_labels):
            self.ax1.text(int(pNum) + 0.7, 0.2e-6, labels, size=15, style='normal')
        # --------Legend--------------------------------------------------------------------------
        self.ax1.text(-0.7, 0.7e-7, 'No. counties\n     with R', rotation='vertical', size=11)
        self.ax1.text(-0.2, 0.7e-7, '> 0.2', color='red', size=11)
        self.ax1.text(-0.2, 0.4e-7, '> 0.1', color='green', size=11)
        self.ax1.text(-0.2, 0.22e-7, '> 0.05', color='blue', size=11)
        self.ax1.text(0.55, 1.8e-7, '__________', rotation='vertical', alpha=0.9) 
        # -------gets min value and plots below the graph----------------------------------------
        for x in range(7):
            min_val = round(min(data_array[x])[0], 15)
    
            if min_val < 1e-6:
                ticky_label = str(min_val)[0] + str(min_val)[-4:]
                # min
                self.ax1.annotate('min=', xy=(x + 1.3, 1.7e-7), size=9)
                # Value                 
                self.ax1.text(x + 0.9, 0.5e-6, ticky_label, size=8, alpha=0.7)
                # self.ax1.annotate(str(min_val)[0]+str(min_val)[-4:], xy=(x+1.3, 1.2e-6),size=9) 
                # arrow pointing down
                self.ax1.annotate('', xy=(x + 1.01, 1.0e-6),
                                  xytext=(x + 1.01, 1.7e-6), 
                                  arrowprops=dict(arrowstyle="->"))

    def __count_at_threshold__(self, query_table):
        """
        get count of values at a certain threshold
        """
        
        # plot threshold values 
        plt.plot(range(9), [0.2] * 9, color='red', alpha=0.8, linestyle='-.')
        plt.plot(range(9), [0.1] * 9, color='green', alpha=0.8, linestyle='--')
        plt.plot(range(9), [0.05] * 9, color='blue', alpha=0.8, linestyle=':')

        query1 = """
    WITH
        co02 AS (SELECT count(fips) AS x FROM %s where co > 0.2),
        co01 AS (SELECT count(fips) AS x FROM %s where co > 0.1),
        co005 AS (SELECT count(fips) AS x FROM %s where co > 0.05),
        
        nox02 AS (SELECT count(fips) AS x FROM %s where nox > 0.2),
        nox01 AS (SELECT count(fips) AS x FROM %s where nox > 0.1),
        nox005 AS (SELECT count(fips) AS x FROM %s where nox > 0.05),
        
        sox02 AS (SELECT count(fips) AS x FROM %s where sox > 0.2),
        sox01 AS (SELECT count(fips) AS x FROM %s where sox > 0.1),
        sox005 AS (SELECT count(fips) AS x FROM %s where sox > 0.05),
        
        voc02 AS (SELECT count(fips) AS x FROM %s where voc > 0.2),
        voc01 AS (SELECT count(fips) AS x FROM %s where voc > 0.1),
        voc005 AS (SELECT count(fips) AS x FROM %s where voc > 0.05),
        
        nh302 AS (SELECT count(fips) AS x FROM %s where nh3 > 0.2),
        nh301 AS (SELECT count(fips) AS x FROM %s where nh3 > 0.1),
        nh3005 AS (SELECT count(fips) AS x FROM %s where nh3 > 0.05),
        
        pm1002 AS (SELECT count(fips) AS x FROM %s where pm10 > 0.2),
        pm1001 AS (SELECT count(fips) AS x FROM %s where pm10 > 0.1),
        pm10005 AS (SELECT count(fips) AS x FROM %s where pm10 > 0.05),
        
        pm2502 AS (SELECT count(fips) AS x FROM %s where pm25 > 0.2),
        pm2501 AS (SELECT count(fips) AS x FROM %s where pm25 > 0.1),
        pm25005 AS (SELECT count(fips) AS x FROM %s where pm25 > 0.05)
    
    select nh302.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (query_table, query_table, query_table, 
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table, 
                                                                                query_table, query_table, query_table, 
                                                                                query_table, query_table, query_table, 
                                                                                query_table, query_table, query_table, 
                                                                                query_table, query_table, query_table)

        nh302_data = self.db.output(query1, self.db.schema)
        nh302_fix = ''.join(str(s) for s in str(nh302_data) if s not in "()L[],")
        self.ax1.text(0.8, 0.7e-7, nh302_fix, size=11, color='red')
        # plt.figtext(0.2, 0.2, nh302_fix)

        query2 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select nox02.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table)

        nox02_data = self.db.output(query2, self.db.schema)
        nox02_fix = ''.join(str(s) for s in str(nox02_data) if s not in "()L[],")
        self.ax1.text(1.8, 0.7e-7, nox02_fix, size=11, color='red')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query3 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)

    select voc02.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (query_table, query_table, query_table, 
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table, 
                                                                                query_table, query_table, query_table, 
                                                                                query_table, query_table, query_table, 
                                                                                query_table, query_table, query_table, 
                                                                                query_table, query_table, query_table)

        voc02_data = self.db.output(query3, self.db.schema)
        voc02_fix = ''.join(str(s) for s in str(voc02_data) if s not in "()L[],")
        self.ax1.text(2.8, 0.7e-7, voc02_fix, size=11, color='red')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query4 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select pm2502.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (query_table, query_table, query_table, 
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table, 
                                                                                 query_table, query_table, query_table, 
                                                                                 query_table, query_table, query_table, 
                                                                                 query_table, query_table, query_table, 
                                                                                 query_table, query_table, query_table)

        pm2502_data = self.db.output(query4, self.db.schema)
        pm2502_fix = ''.join(str(s) for s in str(pm2502_data) if s not in "()L[],")
        self.ax1.text(3.8, 0.7e-7, pm2502_fix, size=11, color='red')
        # plt.figtext(0.2, 0.1, pm2502_fix)

        query5 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select pm1002.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table)

        pm1002_data = self.db.output(query5, self.db.schema)
        pm1002_fix = ''.join(str(s) for s in str(pm1002_data) if s not in "()L[],")
        self.ax1.text(4.8, 0.7e-7, pm1002_fix, size=11, color='red')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query6 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select co02.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (query_table, query_table, query_table,
                                                                               query_table, query_table, query_table,
                                                                               query_table, query_table, query_table,
                                                                               query_table, query_table, query_table,
                                                                               query_table, query_table, query_table,
                                                                               query_table, query_table, query_table,
                                                                               query_table, query_table, query_table)

        co02_data = self.db.output(query6, self.db.schema)
        co02_fix = ''.join(str(s) for s in str(co02_data) if s not in "()L[],")
        self.ax1.text(5.8, 0.7e-7, co02_fix, size=11, color='red')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query7 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select sox02.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table)

        sox02_data = self.db.output(query7, self.db.schema)
        sox02_fix = ''.join(str(s) for s in str(sox02_data) if s not in "()L[],")
        self.ax1.text(6.8, 0.7e-7, sox02_fix, size=11, color='red')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query11 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select nh301.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table)

        nh301_data = self.db.output(query11, self.db.schema)
        nh301_fix = ''.join(str(s) for s in str(nh301_data) if s not in "()L[],")
        self.ax1.text(0.8, 0.4e-7, nh301_fix, size=11, color='green')
        # plt.figtext(0.2, 0.2, nh302_fix)

        query21 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select nox01.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table)

        nox01_data = self.db.output(query21, self.db.schema)
        nox01_fix = ''.join(str(s) for s in str(nox01_data) if s not in "()L[],")
        self.ax1.text(1.8, 0.4e-7, nox01_fix, size=11, color='green')
        # plt.figtext(0.2, 0.1, nox02_fix)
        
        query31 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select voc01.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table)

        voc01_data = self.db.output(query31, self.db.schema)
        voc01_fix = ''.join(str(s) for s in str(voc01_data) if s not in "()L[],")
        self.ax1.text(2.8, 0.4e-7, voc01_fix, size=11, color='green')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query41 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select pm2501.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table)

        pm2501_data = self.db.output(query41, self.db.schema)
        pm2501_fix = ''.join(str(s) for s in str(pm2501_data) if s not in "()L[],")
        self.ax1.text(3.8, 0.4e-7, pm2501_fix, size=11, color='green')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query51 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select pm1001.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table,
                                                                                 query_table, query_table, query_table)

        pm1001_data = self.db.output(query51, self.db.schema)
        pm1001_fix = ''.join(str(s) for s in str(pm1001_data) if s not in "()L[],")
        self.ax1.text(4.8, 0.4e-7, pm1001_fix, size=11, color='green')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query61 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select co01.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (query_table, query_table, query_table,
                                                                               query_table, query_table, query_table,
                                                                               query_table, query_table, query_table,
                                                                               query_table, query_table, query_table,
                                                                               query_table, query_table, query_table,
                                                                               query_table, query_table, query_table,
                                                                               query_table, query_table, query_table)

        co01_data = self.db.output(query61, self.db.schema)
        co01_fix = ''.join(str(s) for s in str(co01_data) if s not in "()L[],")
        self.ax1.text(5.8, 0.4e-7, co01_fix, size=11, color='green')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query71 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select sox01.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table,
                                                                                query_table, query_table, query_table)

        sox01_data = self.db.output(query71, self.db.schema)
        sox01_fix = ''.join(str(s) for s in str(sox01_data) if s not in "()L[],")
        self.ax1.text(6.8, 0.4e-7, sox01_fix, size=11, color='green')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query12 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select nh3005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table)

        nh3005_data = self.db.output(query12, self.db.schema)
        nh3005_fix = ''.join(str(s) for s in str(nh3005_data) if s not in "()L[],")
        self.ax1.text(0.8, 0.22e-7, nh3005_fix, size=11, color='blue')
        # plt.figtext(0.2, 0.2, nh302_fix)
        
        query22 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select nox005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table)

        nox005_data = self.db.output(query22, self.db.schema)
        nox005_fix = ''.join(str(s) for s in str(nox005_data) if s not in "()L[],")
        self.ax1.text(1.8, 0.22e-7, nox005_fix, size=11, color='blue')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query32 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select voc005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table)

        voc005_data = self.db.output(query32, self.db.schema)
        voc005_fix = ''.join(str(s) for s in str(voc005_data) if s not in "()L[],")
        self.ax1.text(2.8, 0.22e-7, voc005_fix, size=11, color='blue')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query42 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select pm25005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table)

        pm25005_data = self.db.output(query42, self.db.schema)
        pm25005_fix = ''.join(str(s) for s in str(pm25005_data) if s not in "()L[],")
        self.ax1.text(3.8, 0.22e-7, pm25005_fix, size=11, color='blue')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query52 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select pm10005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table,
                                                                                         query_table, query_table, query_table)

        pm10005_data = self.db.output(query52, self.db.schema)
        pm10005_fix = ''.join(str(s) for s in str(pm10005_data) if s not in "()L[],")
        self.ax1.text(4.8, 0.22e-7, pm10005_fix, size=11, color='blue')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query62 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select co005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (query_table, query_table, query_table,
                                                                                       query_table, query_table, query_table,
                                                                                       query_table, query_table, query_table,
                                                                                       query_table, query_table, query_table,
                                                                                       query_table, query_table, query_table,
                                                                                       query_table, query_table, query_table,
                                                                                       query_table, query_table, query_table)

        co005_data = self.db.output(query62, self.db.schema)
        co005_fix = ''.join(str(s) for s in str(co005_data) if s not in "()L[],")
        self.ax1.text(5.8, 0.22e-7, co005_fix, size=11, color='blue')
        # plt.figtext(0.2, 0.1, nox02_fix)

        query72 = """
    with
        co02 as (select count(fips) as x from %s where co > 0.2),
        co01 as (select count(fips) as x from %s where co > 0.1),
        co005 as (select count(fips) as x from %s where co > 0.05),
        
        nox02 as (select count(fips) as x from %s where nox > 0.2),
        nox01 as (select count(fips) as x from %s where nox > 0.1),
        nox005 as (select count(fips) as x from %s where nox > 0.05),
        
        sox02 as (select count(fips) as x from %s where sox > 0.2),
        sox01 as (select count(fips) as x from %s where sox > 0.1),
        sox005 as (select count(fips) as x from %s where sox > 0.05),
        
        voc02 as (select count(fips) as x from %s where voc > 0.2),
        voc01 as (select count(fips) as x from %s where voc > 0.1),
        voc005 as (select count(fips) as x from %s where voc > 0.05),
        
        nh302 as (select count(fips) as x from %s where nh3 > 0.2),
        nh301 as (select count(fips) as x from %s where nh3 > 0.1),
        nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
        
        pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
        pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
        pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
        
        pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
        pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
        pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    
    select sox005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table,
                                                                                        query_table, query_table, query_table)

        sox005_data = self.db.output(query72, self.db.schema)
        sox005_fix = ''.join(str(s) for s in str(sox005_data) if s not in "()L[],")
        self.ax1.text(6.8, 0.22e-7, sox005_fix, size=11, color='blue')
        # plt.figtext(0.2, 0.1, nox02_fix)
        
# ------------old piece of Jeremy's code-----------------------------------------------
# Matt took it out because of objects not moveable.

    #     query1 = """
    # with
    #     co02 as (select count(fips) as x from %s where co > 0.2),
    #     co01 as (select count(fips) as x from %s where co > 0.1),
    #     co005 as (select count(fips) as x from %s where co > 0.05),
    #
    #     nox02 as (select count(fips) as x from %s where nox > 0.2),
    #     nox01 as (select count(fips) as x from %s where nox > 0.1),
    #     nox005 as (select count(fips) as x from %s where nox > 0.05),
    #
    #     sox02 as (select count(fips) as x from %s where sox > 0.2),
    #     sox01 as (select count(fips) as x from %s where sox > 0.1),
    #     sox005 as (select count(fips) as x from %s where sox > 0.05),
    #
    #     voc02 as (select count(fips) as x from %s where voc > 0.2),
    #     voc01 as (select count(fips) as x from %s where voc > 0.1),
    #     voc005 as (select count(fips) as x from %s where voc > 0.05),
    #
    #     nh302 as (select count(fips) as x from %s where nh3 > 0.2),
    #     nh301 as (select count(fips) as x from %s where nh3 > 0.1),
    #     nh3005 as (select count(fips) as x from %s where nh3 > 0.05),
    #
    #     pm1002 as (select count(fips) as x from %s where pm10 > 0.2),
    #     pm1001 as (select count(fips) as x from %s where pm10 > 0.1),
    #     pm10005 as (select count(fips) as x from %s where pm10 > 0.05),
    #
    #     pm2502 as (select count(fips) as x from %s where pm25 > 0.2),
    #     pm2501 as (select count(fips) as x from %s where pm25 > 0.1),
    #     pm25005 as (select count(fips) as x from %s where pm25 > 0.05)
    #
    # select nh302.x, nox02.x, voc02.x, pm2502.x, pm1002.x, co02.x, sox02.x
    # from co02, nox02, sox02, voc02, nh302, pm1002, pm2502
    #
    # union all
    #
    # select nh301.x, nox01.x, voc01.x, pm2501.x, pm1001.x, co01.x, sox01.x
    # from co01, nox01, sox01, voc01, nh301, pm1001, pm2501
    #
    # union all
    #
    # select nh3005.x, nox005.x, voc005.x, pm25005.x, pm10005.x, co005.x, sox005.x
    # from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (
    #     query_table, query_table, query_table,
    #     query_table, query_table, query_table,
    #     query_table, query_table, query_table,
    #     query_table, query_table, query_table,
    #     query_table, query_table, query_table,
    #     query_table, query_table, query_table,
    #     query_table, query_table, query_table)
    #
    #
    #     cellTextList = self.db.output(query1, self.db.schema)
    #     print cellTextList
    
    #     rowLabels = [' # counties with R > 0.2',
    #                  '                              > 0.1',
    #                  '                                > 0.05']
    #     threshTable = table(cellText=cellTextList,rowLabels=rowLabels,
    #                         colLabels=['']*7,
    #                         rowColours=['red','green','blue'],
    #                          colLoc='center', rowLoc='center', loc= 'bottom')
    #     threshTable.set_fontsize(10)
    #
    # #    threshTable.set_alpha(.5)
    #
    #     table_props = threshTable.properties()
    #     table_cells = table_props['child_artists']
    #
    #     for cell in table_cells:
    #         cell.set_height(0.05)
    #         if not cell.get_text().get_text().startswith(' '):
    #
    #             cell.set_alpha(0.0)
    #             cell.PAD = 0.5
    #
    #         else:
    #             cell.PAD= 0.05
    #             cell.set_alpha(0.7)
    #
    #
    #     return threshTable

if __name__ == "__main__": 
    from Database import Database
    import Container
    
    title = 'sgNew'
    cont = Container.Container()
    cont.set('path', 'C:/Nonroad/%s/' % (title,))
    cont.set('db', Database(title))
    
    # Emissions per a production lb figure.
    print 'Creating NEI comparision figure.'
    RatioToNEIFig(cont)
