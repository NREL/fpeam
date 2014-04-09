'''
Created on Aug 26, 2013

@author: lcauser
'''
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from pylab import *
import matplotlib.pyplot as plt
from scipy.stats import scoreatpercentile

class EmissionPerProdFigure(object):
    '''
    Create emmision graphs per a acre..
    @param db: Database.
    @param path: Directory path.
    '''
    def __init__(self, cont):
        self.path = cont.get('path')
        self.db = cont.get('db')
        self.documentFile = "EmissionsPerProdFigure"
                    
    #define inputs/constants:  
        pollutantLabels = ['$PM_{10}$','$PM_{2.5}$']
        # the order of the 2 list has to be the same.
        feedstockList = ['Corn Grain','Switchgrass','Corn Stover','Wheat Straw', 'Forest Residue']
        fList = ['CG','SG', 'CS','WS', 'FR']
        pollutantList = ['pm10','pm25']
        
        for pNum, pollutant in enumerate(pollutantList):
    #-----------------EXTRACT DATA FROM THE DATABASE-----------------    
            dataArray = self.__collectData__(feedstockList, pollutant, fList)
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
            #plt.yscale('log')
    
            plotTitle=pollutantLabels[pNum]
            axisTitle = '%s emissions (mt fugitive dust/ (dt for cellulosic, bushel for corn grain) feedstock)' % (pollutantLabels[pNum])
            
            self.__setAxis__(plotTitle, axisTitle, dataArray, fList)    
    #plot 95% intervals 
            self.__plotInterval__(dataArray)
    
            fig.savefig(self.path + 'Figures/EmissionsPerProd_'+pollutant+'.png', format = 'png')
    
            print pollutant
                
       
    def __collectData__(self, feedstockList, pollutant, fList):
        data = []
        for fNum, feedstock in enumerate(feedstockList):
            '''
            emmissions per production = (pollutant dt) / (total feedstock harvested dt)
            emmissions = pollutant / prod
            TODO: Should harv_ac > 0.0 be here? Should this be in the Options class to eliminate the problem in the first place.
            '''
            feedAbr = fList[fNum]
            query = """
                WITH fug as (
                    SELECT 
                      """ + feedAbr + """_raw.fips, 
                      sum(""" + feedAbr + """_raw.fug_""" + pollutant + """) as """ + pollutant + """
                    FROM 
                      """ + self.db.schema + """.""" + feedAbr + """_raw
                    GROUP BY """ + feedAbr + """_raw.fips
                    )
                SELECT (fug.""" + pollutant + """ / s.prod)
                FROM """ + self.db.schema + """.summedemissions as s
                LEFT JOIN fug on fug.fips = s.fips
                WHERE s.feedstock ilike '%""" + feedstock + """%' and s.prod > 0.0
                    """
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
        
        # calculate mean and plot it.
        means = [mean(dataArray[0]), mean(dataArray[1]), mean(dataArray[2]), mean(dataArray[3])]
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
        self.ax1.set_ylim(bottom=0.000005, top=0.0009)
                
        # Hide these grid behind plot objects
        self.ax1.set_axisbelow(True)
    
        self.ax1.set_ylabel(axisTitle, size=10, style='normal')    
        
    
        self.ax1.set_xticklabels(data_labels, size=25, style='normal')
        
        
if __name__ == "__main__": 
    from model.Database import Database
    import Container
    
    title = 'sgNew'
    cont = Container.Container()
    cont.set('path', 'C:/Nonroad/%s/' % (title))
    cont.set('db', Database(title))
    
    # Emissions per a production lb figure.
    print 'Creating emissions per lb figure.'
    EmissionPerProdFigure(cont)
    
    
    
    