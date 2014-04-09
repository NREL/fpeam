from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from pylab import *
import matplotlib.pyplot as plt
from scipy.stats import scoreatpercentile

"""
@comments: much of this plotting utility was taken from the following URL:
http://matplotlib.org/examples/pylab_examples/boxplot_demo2.html
"""

"""
Creates a graph for each air pollutant emmision. Calculates emissions per acre.
Saved as Figures/EmissionsPerAcre_'+pollutant+'.png
Each graph has the total amount of air pollutants for each feedstock.
X-axis: feedstock
Y-axis: pollutant emmisions per acre.
"""
class EmissionsPerAcreFigure():
    '''
    Create emmision graphs per a acre..
    @param db: Database.
    @param path: Directory path.
    '''
    def __init__(self, cont):
        self.path = cont.get('path')
        self.db = cont.get('db')
        self.documentFile = "EmissionsPerAcreFigure"
                    
    #define inputs/constants:  
        pollutantLabels = ['$NO_x$', '$NH_3$', '$CO$', '$SO_x$','$VOC$','$PM_{10}$','$PM_{2.5}$']
        
        feedstockList = ['Corn Grain','Switchgrass','Corn Stover','Wheat Straw']
        fList = ['CG','SG','CS','WS']
        pollutantList = ['NOx','NH3','CO','SOx','VOC','PM10','PM25']
    
        queryTable = 'summedemissions'
    
        for pNum, pollutant in enumerate(pollutantList):
    #-----------------EXTRACT DATA FROM THE DATABASE-----------------    
            dataArray = self.__collectData__(queryTable, feedstockList, pollutant)
    #-----------------PART 2, PLOT DATA----------------------------------
            #pretty plotting things
            fig = plt.figure(figsize=(8,6))
            canvas = FigureCanvas(fig)        
            self.ax1 = fig.add_subplot(111)
    #adjust this value to change the plot size
    #----------------------------------------------------------------
            plt.subplots_adjust(left=0.15, right=0.99, top=0.95, bottom=0.1)
    #---------------------------------------------------------------- 

    #-------create boxplot
            bp = plt.boxplot(dataArray, notch=0, sym='', vert=1, whis=1000)
                
            plt.setp(bp['boxes'], color='black')
            plt.setp(bp['whiskers'], color='black', linestyle='-')
            # remove to get rid of log scale.
            plt.yscale('log')
    
            plotTitle=pollutantLabels[pNum]
            axisTitle = '%s emissions  (g/acre)' % (pollutantLabels[pNum])
            
            self.__setAxis__(plotTitle, axisTitle, dataArray, fList)    
            #plot 95% intervals 
            self.__plotInterval__(dataArray)
    
            fig.savefig(self.path + 'Figures/EmissionsPerAcre_'+pollutant+'.png', format = 'png')
    
            print pollutant
                
            
    
    def __collectData__(self, queryTable, feedstockList, pollutant):
        data = []
        for fNum, feedstock in enumerate(feedstockList):
            '''
            emmissions per acre = (pollutant mt) / (total acres)
            emmissions = pollutant / harv_ac
            TODO: Should harv_ac > 0.0 be here? Should this be in the Options class to eliminate the problem in the first place.
            '''
            query = """
                    SELECT (%s) / (harv_ac) FROM %s.%s WHERE harv_ac > 0.0 AND feedstock ilike '%s';
                    """  % (pollutant, self.db.schema, queryTable, feedstock)
            emmisions = self.db.output(query, self.db.schema)
            data.append(emmisions)
             
        return data
    
    
    
    def __plotInterval__(self, dataArray):
    
        numFeed = 4
        numArray = array([x for x in range(numFeed)]) + 1 #index starts at 1, not zero
            
        #plot 95% interval
        perc95 = array([scoreatpercentile(dataArray[0],95), scoreatpercentile(dataArray[1],95),
                        scoreatpercentile(dataArray[2],95), scoreatpercentile(dataArray[3],95)])
                          
        #plot 5% interval
        perc5 = array([scoreatpercentile(dataArray[0],5), scoreatpercentile(dataArray[1],5),
                        scoreatpercentile(dataArray[2],5), scoreatpercentile(dataArray[3],5)])
                        
        plt.plot((numArray), perc95, '_', markersize=15, color='k')                 
        plt.plot((numArray), perc5, '_', markersize=15, color='k')
        
        # calculate mean and plot it. Make sure there are no None elements when calculating mean.
        means = [mean([data for data in dataArray[0] if data[0] is not None]), mean([data for data in dataArray[1] if data[0] is not None]),
                  mean([data for data in dataArray[2] if data[0] is not None]), mean([data for data in dataArray[3] if data[0] is not None])]
        plt.plot((numArray), means, '_', markersize=75, color='b')
        
        
    """
    function to set axis titles and plot titles
    """
    def __setAxis__(self, plotTitle, axisTitle, dataArray, data_labels):
    # Add a horizontal grid to the plot
        self.ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey',
                      alpha=0.7)
                      
        #determine limits of axis
        # to view all, let it be logarithim scale: self.ax1.set_ylim(bottom=1e-07, top=1e-01)
        # to view sg, cs, and ws spread: self.ax1.set_ylim(bottom=1e-07, top=0.0002
        # to view cg spread: self.ax1.set_ylim(bottom=0.0002, top=.003)     
        # to view pm spread: self.ax1.set_ylim(bottom=1e-04, top=0.002)                  
        self.ax1.set_ylim(bottom=1e-07, top=1e-01)
                
        # Hide these grid behind plot objects
        self.ax1.set_axisbelow(True)
    
        self.ax1.set_ylabel(axisTitle, size=25, style='normal')    
        
    
        self.ax1.set_xticklabels(data_labels, size=25, style='normal')   
        
if __name__ == "__main__": 
    from model.Database import Database
    import Container
    
    title = 'sgNew'
    cont = Container.Container()
    cont.set('path', 'C:/Nonroad/%s/' % (title))
    cont.set('db', Database(title))
    
    # Emissions per a production acre figure.
    print 'Creating emissions per acre figure.'
    EmissionsPerAcreFigure(cont)                      
    
