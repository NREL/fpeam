from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from pylab import *
import matplotlib.pyplot as plt
from scipy.stats import scoreatpercentile
import re

"""
Determines the number of counties with unhealthy amounts of air pollutants.
Has lines on the graph indicating what percentage of air pollutants would be bad.
Saved as Figures/RatioToNEI_'+queryTable+'.png.
X-axis: Air pollutants.
Y-axis: Ratio of feed stock emmisions to the NEI collected emmision invetory.
"""
class RatioToNEIFig():
    
    '''
    Create model.
    @param db: Database.
    @param path: Path to Directory.
    '''
    def __init__(self, cont):
        self.db = cont.get('db')
        self.path = cont.get('path')
        self.documentFile = "RatioToNEIFig"
    
        self.f = open(self.path + 'Figures/RatioToNEI_Numerical.csv','w')
        
        self.f.write('feedstock, pollutant, max, 95, 75, median, 25, 5, min \n')
        
        pollutantList = ['NH3','NOX','VOC','PM25','PM10','CO','SOX']
    #define inputs/constants:  
        data_labels = ['$NH_3$','$NO_x$','$VOC$','$PM_{2.5}$','$PM_{10}$','$CO$','$SO_x$'] 
        feedstockList = ['corn grain', 'switchgrass','corn stover','wheat straw','forest residue', 'cellulosic']
    
     
    #return number arrays for plotting   
        self.numPollut = 6
        self.numArray = array([x for x in range(self.numPollut+1)]) + 1 #index starts at 1, not zero
        
        plotTitle=''
    
        for feedstock in range(6):
            if feedstock == 0:
    #-----------------Model Corn Grain Scenario    
                queryTable = "cg_neiratio" 
    
            elif feedstock == 1:
    #-----------------Model Switchgrass scenario
                queryTable = "sg_neiratio"
    
            elif feedstock == 2:
    #-----------------Model Corn Stover scenario
                queryTable = "cs_neiratio"
            
            elif feedstock == 3:
    #-----------------Model Wheat Straw scenario
                queryTable = "ws_neiratio"
                
            elif feedstock == 4:
    #-----------------Model Forest Residue scenario
                queryTable = "fr_neiratio"    
            elif feedstock == 5:
    #-----------------Model all cellulosic
                queryTable = "cellulosic_neiratio"    
                
            print queryTable
    #-----------------Sets Y-Axis label to include (n) county totals---------
            queryCount = 'SELECT COUNT(fips) FROM sgnew.%s' % (queryTable)
            countyNum = self.db.output(queryCount, self.db.schema)
            countyFix = ''.join(str(s) for s in str(countyNum) if s not in "()L[],")
            axisTitle = 'Ratio (R) of %s emissions to 2008 NEI\n (n = %s counties)' % (feedstockList[feedstock], countyFix)
    #-----------------PART 1, EXTRACT DATA FROM THE DATABASE-----------------    
            data_array = self.__collectData__(queryTable)
            self.__generalStats__(data_array, pollutantList, feedstockList, feedstock)
        
    #-----------------PART 2, PLOT DATA--------------------------------------
      
            #pretty plotting things
            fig = plt.figure(figsize=(8,8))
            canvas = FigureCanvas(fig)        
            self.ax1 = fig.add_subplot(111)
        
    #adjust this value to change the plot size for the paper    
    #-----------------------------------------------------------------------
            #plt.subplots_adjust(left=0.3, right=0.93, top=0.95, bottom=0.25)
            #plt.subplots_adjust(left=0.3, right=0.93, top=0.95, bottom=0.35)
            plt.subplots_adjust(left=0.20, right=0.93, top=0.95, bottom=0.25)
    #---------------------------------------------------------------- 
            
    #-------create boxplot
            bp = plt.boxplot(data_array, notch=0, sym='', vert=1, whis=1000)
                
            plt.setp(bp['boxes'], color='black')
            plt.setp(bp['whiskers'], color='black', linestyle='-')
            plt.setp(bp['medians'], color='black')
            plt.yscale('log')
        
            perc95 = self.__plotInterval__(data_array)
            
            tT = self.__countAtThreshold__(queryTable)
            
            self.__setAxis__(plotTitle, axisTitle, data_array, data_labels)    
            
    
                         
        #    show()
            fig.savefig(self.path + 'Figures/RatioToNEI_'+queryTable+'.png', format = 'png')
    
    #        print figure to a .png file (small file size)
    #        canvas.print_figure(queryTable + '.tiff')
        
            
        
    def __collectData__(self, queryTable):
        pollutants = ['nh3', 'nox', 'voc', 'pm25', 'pm10', 'co', 'sox']
        neiData = {}
        for poll in pollutants:
            neiData[poll] = self._makeQuery(poll, queryTable)
            
        
        '''
        query = """SELECT nh3, nox, voc, pm25, pm10, co, sox 
                FROM %s.%s 
                WHERE co > 0.0 AND sox > 0.0;"""  % (self.db.schema, queryTable)
        data = self.db.output(query, self.db.schema)
        
        #create arrays for the data
        data_matrix = matrix(data)
        
        #store data in a plottable format
        nh3 = array(data_matrix[:,0])
        nox = array(data_matrix[:,1])
        voc = array(data_matrix[:,2])
        pm25 = array(data_matrix[:,3])
        pm10 = array(data_matrix[:,4])
        co = array(data_matrix[:,5])
        sox = array(data_matrix[:,6])
        
        return [nh3, nox, voc, pm25, pm10, co, sox]
        '''
        return [neiData[p] for p in pollutants]

    def _makeQuery(self, pollutant, queryTable):
        query = """SELECT """ + pollutant + """
                FROM """ + self.db.schema + """.""" + queryTable + """
                WHERE """ + pollutant + """ > 0.0;"""  
        data = self.db.output(query, self.db.schema)
        return data
        
    
    """
    function to capture confidence interfals for co. Because the input data has the 
    same population (n), the counts between each interval will the the same. i.e. 
    the count of counties > the 95% interval will the be same for co as for nox. 
    Hence, these statistic calculated here will apply to all of the pollutants. 
    """
    def __generalStats__(self, data_array, pollutantList, feedstockList, feedstock):
        for pNum, pollutant in enumerate(pollutantList):
            lines=[ feedstockList[feedstock], pollutant, max(data_array[pNum])[0],
                 scoreatpercentile(data_array[pNum],95), 
                 scoreatpercentile(data_array[pNum],75),
                 median(data_array[pNum]),
                 scoreatpercentile(data_array[pNum],25), 
                 scoreatpercentile(data_array[pNum],5),
                 min(data_array[pNum])[0] ]
            
            self.f.write(str(lines) + '\n')
                      
        
    """
    function to calculate and plot the 95% intervals
    """
    def __plotInterval__(self, data_array):
        #plot 95% interval
        perc95 = array([scoreatpercentile(data_array[0],95), scoreatpercentile(data_array[1],95),
                        scoreatpercentile(data_array[2],95), scoreatpercentile(data_array[3],95), 
                        scoreatpercentile(data_array[4],95), scoreatpercentile(data_array[5],95),
                        scoreatpercentile(data_array[6],95)])
        plt.plot((self.numArray), perc95, '_', markersize=10, color='k')
    
        
    #    plot 5% interval
        perc5 = array([scoreatpercentile(data_array[0],5), scoreatpercentile(data_array[1],5),
                        scoreatpercentile(data_array[2],5), scoreatpercentile(data_array[3],5), 
                        scoreatpercentile(data_array[4],5), scoreatpercentile(data_array[5],5),
                        scoreatpercentile(data_array[6],5)])
                 
        plt.plot((self.numArray), perc5, '_', markersize=10, color='k')
        
        # calculate mean and plot it. Make sure there are no None elements when calculating mean. Means are not in boxplots, took out
        #means = [mean([data for data in data_array[0] if data[0] is not None]), mean([data for data in data_array[1] if data[0] is not None]),
        #          mean([data for data in data_array[2] if data[0] is not None]), mean([data for data in data_array[3] if data[0] is not None]),
        #          mean([data for data in data_array[4] if data[0] is not None]), mean([data for data in data_array[5] if data[0] is not None]),
        #          mean([data for data in data_array[6] if data[0] is not None])]
        #plt.plot((self.numArray), means, '_', markersize=75, color='b')
        
        return perc95
        
        
        
    """
    function to set axis titles and plot titles
    """
    def __setAxis__(self, plotTitle, axisTitle, data_array, data_labels):
    # Add a horizontal grid to the plot, but make it very light in color
    # so we can use it for reading data values but not be distracting
        self.ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey',
                      alpha=0.7)
        
        # Hide these grid behind plot objects
        self.ax1.set_axisbelow(True)
        #self.ax1.spines['bottom'].set_position(('axes',0.1)) reposition the axis...I wasnt thinking clearly
    
        self.ax1.set_ylabel(axisTitle, size=15, style='normal', multialignment = 'center')    
    #manually enter axis tick labels because they need to be the same for all plots.     
        self.ax1.set_yticklabels(['$10^{-6}$','$10^{-5}$','$10^{-4}$','$10^{-3}$','$10^{-2}$','$10^{-1}$','$1$'],
                             size=15,weight='bold', style='normal')
        
        #self.ax1.set_xticklabels(data_labels, size=15, style='normal')
        self.ax1.set_xticklabels(' ', size=15, style='normal')
        
        #self.ax1.xaxis.labelpad = 20 #hopefully moves it downward
    
        # Set the axes ranges and axes labels    
        self.ax1.set_xlim(0.5, self.numPollut*1.15+1) 
        top = 3
        bottom = 10e-7
        self.ax1.set_ylim(bottom, top)

#---------------------colored arrows--------------------------------------------------------------------        
        self.ax1.text(8.28, 0.2, '0.2' + '       ', size=8, weight = 'bold', color = 'white', va="center", ha="center", rotation=0,
                bbox=dict(boxstyle="larrow", color = 'red', alpha=0.5))
        self.ax1.text(8.28, 0.1, '0.1 ' + '      ', size=8, weight = 'bold', color = 'white', va="center", ha="center", rotation=0,
                bbox=dict(boxstyle="larrow", color = 'green', alpha=0.5))
        self.ax1.text(8.28, 0.05, '0.05', size=8, weight = 'bold', color = 'white', va="center", ha="center", rotation=0,
                bbox=dict(boxstyle="larrow", color = 'blue', alpha=0.5))
    #    ax1.xaxis.set_visible(False)
        
        # Removed the number of counties that are used. Because alot of the NEI data does not use NH3 data which messes up this function.
        #self.ax1.annotate('N = '+str(shape(data_array)[1])+' counties', xy=(6.5, 1), xytext=(5.5, 1))
#------------------------min located under the graph-----------------------------------------------------
        self.ax1.text(0.3, 0.5e-6, 'min = ', size = 8, alpha=0.7)
        self.ax1.text(0.3, 0.45e-6, '_________________________________________________________________________', alpha=0.7)
        
#------------------------x-axis labels--------------------------------------------------------------------
        for pNum, labels in enumerate(data_labels):
            self.ax1.text(int(pNum) + 0.7, 0.2e-6, labels, size = 15, style = 'normal')
#-------------------------Legend--------------------------------------------------------------------------
        self.ax1.text(-0.7, 0.7e-7, 'No. counties\n     with R', rotation='vertical', size = 11)
        self.ax1.text(-0.2, 0.7e-7, '> 0.2', color = 'red', size = 11)
        self.ax1.text(-0.2, 0.4e-7, '> 0.1', color = 'green', size = 11)
        self.ax1.text(-0.2, 0.22e-7, '> 0.05', color = 'blue', size = 11)
        self.ax1.text(0.55, 1.8e-7, '__________', rotation='vertical', alpha=0.9) 
#------------------------gets min value and plots below the graph----------------------------------------
        for x in range(7):
            minVal = round(min(data_array[x])[0],15)
    
            if minVal < 1e-6:
                tickyLabel = str(minVal)[0]+str(minVal)[-4:]
    #min
                self.ax1.annotate('min=', xy=(x + 1.3, 1.7e-7),size=9)
    #Value                 
                self.ax1.text(x + 0.9, 0.5e-6, tickyLabel, size = 8, alpha=0.7)
                #self.ax1.annotate(str(minVal)[0]+str(minVal)[-4:], xy=(x+1.3, 1.2e-6),size=9) 
    #arrow pointing down
                self.ax1.annotate('', xy=(x+1.01, 1.0e-6),
                             xytext=(x+1.01,1.7e-6), 
                             arrowprops=dict(arrowstyle="->"))   
        

     
    """
    get count of values at a certain threshold
    """
    def __countAtThreshold__(self, queryTable):
        
        #plot threshold values 
        plt.plot(range(9),[0.2]*9,color='red',alpha=0.8,linestyle='-.')
        plt.plot(range(9),[0.1]*9,color='green',alpha=0.8,linestyle='--')
        plt.plot(range(9),[0.05]*9,color='blue',alpha=0.8,linestyle=':')    
        
        query1 = """
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
    
    select nh302.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        nh302Data = self.db.output(query1, self.db.schema)
        nh302Fix = ''.join(str(s) for s in str(nh302Data) if s not in "()L[],")
        self.ax1.text(0.8, 0.7e-7, nh302Fix, size = 11, color='red')
        #plt.figtext(0.2, 0.2, nh302Fix)
        
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
    
    select nox02.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        nox02Data = self.db.output(query2, self.db.schema)
        nox02Fix = ''.join(str(s) for s in str(nox02Data) if s not in "()L[],")
        self.ax1.text(1.8, 0.7e-7, nox02Fix, size = 11, color='red')
        #plt.figtext(0.2, 0.1, nox02Fix)
        
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
    
    select voc02.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        voc02Data = self.db.output(query3, self.db.schema)
        voc02Fix = ''.join(str(s) for s in str(voc02Data) if s not in "()L[],")
        self.ax1.text(2.8, 0.7e-7, voc02Fix, size = 11, color='red')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select pm2502.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        pm2502Data = self.db.output(query4, self.db.schema)
        pm2502Fix = ''.join(str(s) for s in str(pm2502Data) if s not in "()L[],")
        self.ax1.text(3.8, 0.7e-7, pm2502Fix, size = 11, color='red')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select pm1002.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        pm1002Data = self.db.output(query5, self.db.schema)
        pm1002Fix = ''.join(str(s) for s in str(pm1002Data) if s not in "()L[],")
        self.ax1.text(4.8, 0.7e-7, pm1002Fix, size = 11, color='red')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select co02.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        co02Data = self.db.output(query6, self.db.schema)
        co02Fix = ''.join(str(s) for s in str(co02Data) if s not in "()L[],")
        self.ax1.text(5.8, 0.7e-7, co02Fix, size = 11, color='red')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select sox02.x from co02, nox02, sox02, voc02, nh302, pm1002, pm2502 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        sox02Data = self.db.output(query7, self.db.schema)
        sox02Fix = ''.join(str(s) for s in str(sox02Data) if s not in "()L[],")
        self.ax1.text(6.8, 0.7e-7, sox02Fix, size = 11, color='red')
        #plt.figtext(0.2, 0.1, nox02Fix)
        
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
    
    select nh301.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        nh301Data = self.db.output(query11, self.db.schema)
        nh301Fix = ''.join(str(s) for s in str(nh301Data) if s not in "()L[],")
        self.ax1.text(0.8, 0.4e-7, nh301Fix, size = 11, color='green')
        #plt.figtext(0.2, 0.2, nh302Fix)
        
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
    
    select nox01.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        nox01Data = self.db.output(query21, self.db.schema)
        nox01Fix = ''.join(str(s) for s in str(nox01Data) if s not in "()L[],")
        self.ax1.text(1.8, 0.4e-7, nox01Fix, size = 11, color='green')
        #plt.figtext(0.2, 0.1, nox02Fix)
        
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
    
    select voc01.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        voc01Data = self.db.output(query31, self.db.schema)
        voc01Fix = ''.join(str(s) for s in str(voc01Data) if s not in "()L[],")
        self.ax1.text(2.8, 0.4e-7, voc01Fix, size = 11, color='green')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select pm2501.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        pm2501Data = self.db.output(query41, self.db.schema)
        pm2501Fix = ''.join(str(s) for s in str(pm2501Data) if s not in "()L[],")
        self.ax1.text(3.8, 0.4e-7, pm2501Fix, size = 11, color='green')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select pm1001.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        pm1001Data = self.db.output(query51, self.db.schema)
        pm1001Fix = ''.join(str(s) for s in str(pm1001Data) if s not in "()L[],")
        self.ax1.text(4.8, 0.4e-7, pm1001Fix, size = 11, color='green')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select co01.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        co01Data = self.db.output(query61, self.db.schema)
        co01Fix = ''.join(str(s) for s in str(co01Data) if s not in "()L[],")
        self.ax1.text(5.8, 0.4e-7, co01Fix, size = 11, color='green')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select sox01.x from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        sox01Data = self.db.output(query71, self.db.schema)
        sox01Fix = ''.join(str(s) for s in str(sox01Data) if s not in "()L[],")
        self.ax1.text(6.8, 0.4e-7, sox01Fix, size = 11, color='green')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select nh3005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        nh3005Data = self.db.output(query12, self.db.schema)
        nh3005Fix = ''.join(str(s) for s in str(nh3005Data) if s not in "()L[],")
        self.ax1.text(0.8, 0.22e-7, nh3005Fix, size = 11, color='blue')
        #plt.figtext(0.2, 0.2, nh302Fix)
        
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
    
    select nox005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        nox005Data = self.db.output(query22, self.db.schema)
        nox005Fix = ''.join(str(s) for s in str(nox005Data) if s not in "()L[],")
        self.ax1.text(1.8, 0.22e-7, nox005Fix, size = 11, color='blue')
        #plt.figtext(0.2, 0.1, nox02Fix)
        
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
    
    select voc005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        voc005Data = self.db.output(query32, self.db.schema)
        voc005Fix = ''.join(str(s) for s in str(voc005Data) if s not in "()L[],")
        self.ax1.text(2.8, 0.22e-7, voc005Fix, size = 11, color='blue')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select pm25005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        pm25005Data = self.db.output(query42, self.db.schema)
        pm25005Fix = ''.join(str(s) for s in str(pm25005Data) if s not in "()L[],")
        self.ax1.text(3.8, 0.22e-7, pm25005Fix, size = 11, color='blue')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select pm10005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        pm10005Data = self.db.output(query52, self.db.schema)
        pm10005Fix = ''.join(str(s) for s in str(pm10005Data) if s not in "()L[],")
        self.ax1.text(4.8, 0.22e-7, pm10005Fix, size = 11, color='blue')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select co005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        co005Data = self.db.output(query62, self.db.schema)
        co005Fix = ''.join(str(s) for s in str(co005Data) if s not in "()L[],")
        self.ax1.text(5.8, 0.22e-7, co005Fix, size = 11, color='blue')
        #plt.figtext(0.2, 0.1, nox02Fix)

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
    
    select sox005.x from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        sox005Data = self.db.output(query72, self.db.schema)
        sox005Fix = ''.join(str(s) for s in str(sox005Data) if s not in "()L[],")
        self.ax1.text(6.8, 0.22e-7, sox005Fix, size = 11, color='blue')
        #plt.figtext(0.2, 0.1, nox02Fix)
        
#------------old piece of Jeremy's code-----------------------------------------------
#Matt took it out because of objects not moveable.
        
        '''query1 = """
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
    
    select nh302.x, nox02.x, voc02.x, pm2502.x, pm1002.x, co02.x, sox02.x
    from co02, nox02, sox02, voc02, nh302, pm1002, pm2502
        
    union all
    
    select nh301.x, nox01.x, voc01.x, pm2501.x, pm1001.x, co01.x, sox01.x
    from co01, nox01, sox01, voc01, nh301, pm1001, pm2501 
    
    union all
    
    select nh3005.x, nox005.x, voc005.x, pm25005.x, pm10005.x, co005.x, sox005.x
    from co005, nox005, sox005, voc005, nh3005, pm10005, pm25005 """ % (
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable,
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable, queryTable, 
        queryTable, queryTable,queryTable)
    
    
        cellTextList = self.db.output(query1, self.db.schema)
        print cellTextList'''
    
        """rowLabels = [' # counties with R > 0.2', 
                     '                              > 0.1', 
                     '                                > 0.05']
        threshTable = table(cellText=cellTextList,rowLabels=rowLabels,
                            colLabels=['']*7,
                            rowColours=['red','green','blue'],
                             colLoc='center', rowLoc='center', loc= 'bottom')
        threshTable.set_fontsize(10)
        
    #    threshTable.set_alpha(.5)
        
        table_props = threshTable.properties()
        table_cells = table_props['child_artists']
    
        for cell in table_cells:
            cell.set_height(0.05)        
            if not cell.get_text().get_text().startswith(' '):
                
                cell.set_alpha(0.0)
                cell.PAD = 0.5
                
            else:
                cell.PAD= 0.05
                cell.set_alpha(0.7)
                
                
        return threshTable"""
    
if __name__ == "__main__": 
    from Database import Database
    import Container
    
    title = 'sgNew'
    cont = Container.Container()
    cont.set('path', 'C:/Nonroad/%s/' % (title))
    cont.set('db', Database(title))
    
    # Emissions per a production lb figure.
    print 'Creating NEI comparision figure.'
    RatioToNEIFig(cont)
        
