"""
@author: nfisher
"""
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from pylab import median, mean
import matplotlib
from ContributionTests import ChooseSQL
#import time

'''
Creates a figure that represents the percentage of emmission contributions
for each pollutnant.
Makes figure. Saved to Figures/Contribution_Figure.png.
X-axis: Feedsotcks.
Y-axis: Amount of air pollutant emmisions. 0-1, for percentage. 
Columns: All the different air emmission pollutants .
Rows: Type of operation. (harvest, non-harvest, transport, fertilizers, pesticides.)
'''
class ContributionAnalysis():
    
    '''
    Create graphics and store data in a spreadsheet.
    @param db: Database.
    @param path: Directory path.
    '''
    def __init__(self, cont):
        self.db = cont.get('db')
        self.path = cont.get('path')
        self.documentFile = "ContributionAnalysis"
    #    startTime = time.time()
    #-----------inputs begin
    
        # create container and canvas for all plots.
        fig = Figure( figsize=(7,5), dpi=200) 
        canvas = FigureCanvas(fig)
            
        fColor = ['r','b','g','k','c']
        fMarker = ['o','o','o','o','o']
    
        feedstockList = ['CG','SG','CS','WS','FR']
        pollutantList = ['NH3','NOx','VOC','PM25','PM10','CO','SOx']
        pollutantLabels = ['$NH_3$','$NO_x$','$VOC$','$PM_{2.5}$','$PM_{10}$','$CO$','$SO_x$'] 
        activityList = ['Non-Harvest','Fertilizer','Chemical','Harvest','Transport']
        activityLabels = ['Non-Harvest','N-Fertilizer','Pesticide','Harvest','Transport']
        
        self.f = open(self.path + 'Figures/Contribution_numerical.csv','w') 
    #-----------inputs end
        
        index = 0
        for yLabel, activity in enumerate(activityList):
            print activity
            # create subplots.
            for titleLabel, pollutant in enumerate(pollutantList):
                # add a sublot to the figure.
                ax = fig.add_subplot( 5, 7, index+1 )
                # set the min and max of the axis.
                ax.set_xlim([-1,5])
                ax.set_ylim([-0.1, 1.1])
          
                #show y labels on first column only
                if index % 7 == 0   :
                    matplotlib.rcParams.update({'font.size': 8})
                    ax.set_ylabel(activityLabels[yLabel])
                else: 
                    ax.set_yticklabels([])
                
                #show pollutant labels above first row of plots
                if index < 7:
                    ax.set_title(pollutantLabels[titleLabel])
                
                #show x labels below last row only
                if index < 28:
                    ax.set_xticklabels([])
                else:
                    ax.set_xticklabels(([''] + feedstockList), rotation='vertical')
        
                index+=1
                self.f.write(pollutant+','+activity+'\n')
                for fNum, feedstock in enumerate(feedstockList):
                    # used to decide what to query.
                    chooseQuery = ChooseSQL(activity, pollutant, feedstock, self.db.schema)
                    # make plots.
                    self.makePlots(ax, chooseQuery, fNum, 
                              fColor[fNum], fMarker[fNum], feedstock)  
         
                self.f.write('\n')
        
    #    print figure to a .png file (small file size)
    #    canvas.print_figure('Contribution Analysis.tiff')      
        fig.savefig(self.path + 'Figures/Contribution_Figure.png', format = 'png')
           
        self.f.close()
    #    print time.time() - startTime, ' seconds'
    
    
    """
    Formats the plots
    @param ax: Subplot. 
    @param query: Query to grab data for plot.  
    @param fNum: Feedstock index.
    @param fColor: Color to make points.
    @param fMarker: Marker type to put on graph. (circles, boxes, ect...)
    @param feedstock: Type of feedstock ('CG','SG','CS','WS','FR')   
    """
    def makePlots(self, ax, query, fNum, fColor, fMarker, feedstock):
                
        query.getQuery()
        
        if query.queryString.startswith('No'):
            pass    
        
        elif query.queryString.startswith('FR'):
            data = [1,1]
            ax.plot([fNum]*2,[1,1],fColor,marker=fMarker,markersize=2)
            
        else:
            data = self.db.output(query.queryString, self.db.schema)
            meanVal = mean(data)
            medVal = median(data)
            maxVal = max(data)
            minVal = min(data)
            
            ax.plot([fNum],meanVal,fColor,marker='_', markersize=20)
            ax.plot([fNum],medVal,fColor,marker='_', markersize=7)
    
            #Plot the max/min values
            ax.plot([fNum]*2,[maxVal, minVal],fColor,marker=fMarker, markersize=2)    
            
            self.writeResults(feedstock, str(maxVal[0]), str(medVal), str(minVal[0]))
    
    
    """
    Writes the results to a file in a readable format. 
    """
    def writeResults(self, feedstock, maxVal, medVal, minVal):
        self.f.write(feedstock+','+maxVal+','+medVal+','+minVal+'\n')
    



if __name__ == "__main__":  
    # used for testing.
    from model.Database import Database
    import Container
    
    title = 'sgNew'
    cont = Container.Container()
    cont.set('modelRunTitle', title)
    cont.set('path', 'C:/Nonroad/%s/' % (title))
    cont.set('db', Database(title))
    
    # Emissions per a production lb figure.
    print 'Creating contribution figure.'
    ContributionAnalysis(cont)   
    