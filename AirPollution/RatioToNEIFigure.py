from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from pylab import *
import matplotlib.pyplot as plt
from scipy.stats import scoreatpercentile

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
    
        self.f = open(self.path+'Figures/RatioToNEI_Numerical.csv','w')
        
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
                
            axisTitle = 'Ratio (R) of %s emissions to 2008 NEI' % (feedstockList[feedstock])
    #-----------------PART 1, EXTRACT DATA FROM THE DATABASE-----------------    
            data_array = self.__collectData__(queryTable)
            self.__generalStats__(data_array, pollutantList, feedstockList, feedstock)
        
    #-----------------PART 2, PLOT DATA----------------------------------
      
            #pretty plotting things
            fig = plt.figure(figsize=(8,8))
            canvas = FigureCanvas(fig)        
            self.ax1 = fig.add_subplot(111)
        
    #adjust this value to change the plot size for the paper    
    #----------------------------------------------------------------
            plt.subplots_adjust(left=0.3, right=0.99, top=0.95, bottom=0.25)
    #---------------------------------------------------------------- 
            
    #-------create boxplot
            bp = plt.boxplot(data_array, notch=0, sym='', vert=1, whis=1000)
                
            plt.setp(bp['boxes'], color='black')
            plt.setp(bp['whiskers'], color='black', linestyle='-') 
            plt.yscale('log')
        
            perc95 = self.__plotInterval__(data_array)
            
            tT = self.__countAtThreshold__(queryTable)
            
            self.__setAxis__(plotTitle, axisTitle, data_array, data_labels)    
            
    
                         
        #    show()
            fig.savefig(self.path+'Figures/RatioToNEI_'+queryTable+'.png', format = 'png')
    
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
                 scoreatpercentile(data_array[pNum],50),
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
        
        # calculate mean and plot it. Make sure there are no None elements when calculating mean.
        means = [mean([data for data in data_array[0] if data[0] is not None]), mean([data for data in data_array[1] if data[0] is not None]),
                  mean([data for data in data_array[2] if data[0] is not None]), mean([data for data in data_array[3] if data[0] is not None]),
                  mean([data for data in data_array[4] if data[0] is not None]), mean([data for data in data_array[5] if data[0] is not None]),
                  mean([data for data in data_array[6] if data[0] is not None])]
        plt.plot((self.numArray), means, '_', markersize=75, color='b')
        
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
    
        self.ax1.set_ylabel(axisTitle, size=15, style='normal')    
    #manually enter axis tick labels because they need to be the same for all plots.     
        self.ax1.set_yticklabels(['$10^{-6}$','$10^{-5}$','$10^{-4}$','$10^{-3}$','$10^{-2}$','$10^{-1}$','$1$'],
                             size=15,weight='bold', style='normal')
    
        self.ax1.set_xticklabels(data_labels, size=15, style='normal')                         
    
        # Set the axes ranges and axes labels    
        self.ax1.set_xlim(0.5, self.numPollut*1.15+1) 
        top = 3
        bottom = 10e-7
        self.ax1.set_ylim(bottom, top)
    #    ax1.xaxis.set_visible(False)
        
        # Removed the number of counties that are used. Because alot of the NEI data does not use NH3 data which messes up this function.
        #self.ax1.annotate('N = '+str(shape(data_array)[1])+' counties', xy=(6.5, 1), xytext=(5.5, 1))
    
       
        
        for x in range(7):
            minVal = round(min(data_array[x])[0],15)
    
            if minVal < 1e-6:
    #min
                self.ax1.annotate('min=', xy=(x + 1.3, 1.7e-6),size=9)  
    #value            
                self.ax1.annotate(str(minVal)[0]+str(minVal)[-4:], xy=(x+1.3, 1.2e-6),size=9) 
    #arrow pointing down
                self.ax1.annotate('', xy=(x+1.2, 1.0e-6),
                             xytext=(x+1.2,1.7e-6), 
                             arrowprops=dict(arrowstyle="->"))   
        

     
    """
    get count of values at a certain threshold
    """
    def __countAtThreshold__(self, queryTable):
        
        #plot threshold values 
        plt.plot(range(9),[0.2]*9,color='red',alpha=0.8,linestyle='-.')
        plt.plot(range(9),[0.1]*9,color='green',alpha=0.8,linestyle='--')
        plt.plot(range(9),[0.05]*9,color='blue',alpha=0.8,linestyle=':')    
        
        query = """
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
    
        cellTextList = self.db.output(query, self.db.schema)
        rowLabels = [' # counties with R > 0.2', 
                     '                   > 0.1', 
                     '                  > 0.05']
        threshTable = table(cellText=cellTextList,rowLabels=rowLabels,
                            colLabels=['']*7,
                            rowColours=['red','green','blue'],
                             colLoc='center', rowLoc='center',loc='bottom')
        threshTable.set_fontsize(12)
        
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
                
                
        return threshTable
    
if __name__ == "__main__": 
    from model.Database import Database
    import Container
    
    title = 'sgNew'
    cont = Container.Container()
    cont.set('path', 'C:/Nonroad/%s/' % (title))
    cont.set('db', Database(title))
    
    # Emissions per a production lb figure.
    print 'Creating NEI comparision figure.'
    RatioToNEIFig(cont)
        
