"""
Creates a figure that represents the percentage of emmission contributions
for each pollutnant.
Makes figure. Saved to Figures/Contribution_Figure.png.
X-axis: Feedsotcks.
Y-axis: Amount of air pollutant emmisions. 0-1, for percentage.
Columns: All the different air emmission pollutants .
Rows: Type of operation. (harvest, non-harvest, transport, fertilizers, pesticides.)
"""

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from pylab import median, mean
import matplotlib
from ContributionTests import ChooseSQL
# import time
import os


class ContributionAnalysis():
    def __init__(self, cont):
        """
        Create graphics and store data in a spreadsheet.
        @param db: Database.
        @param path: Directory path.
        """
        self.db = cont.get('db')
        self.path = cont.get('path')
        self.document_file = "ContributionAnalysis"
    #    startTime = time.time()
    # -----------inputs begin
        # create container and canvas for all plots.
        fig = Figure(figsize=(7,5), dpi=200)
        canvas = FigureCanvas(fig)
            
        f_color = ['r', 'b', 'g', 'k', 'c']
        f_marker = ['o', 'o', 'o', 'o', 'o']
    
        feedstock_list = ['CG', 'SG', 'CS', 'WS'] # , 'FR']
        pollutant_list = [ 'NOx', 'VOC', 'PM25', 'PM10', 'CO', 'SOx'] # 'NH3',
        pollutant_labels = ['$NO_x$', '$VOC$', '$PM_{2.5}$', '$PM_{10}$', '$CO$', '$SO_x$'] #'$NH_3$', 
        activity_list = ['Non-Harvest', 'Fertilizer', 'Chemical', 'Harvest', 'Transport']
        activity_labels = ['Non-Harvest', 'N-Fertilizer', 'Pesticide', 'Harvest', 'Transport']
        
        self.f = open(os.path.join(self.path, 'Figures', 'Contribution_numerical.csv'), 'w')
    # -----------inputs end
        
        index = 0
        for y_label, activity in enumerate(activity_list):
            print activity
            # create subplots.
            for titleLabel, pollutant in enumerate(pollutant_list):
                # add a sublot to the figure.
                ax = fig.add_subplot(5, len(pollutant_list), index + 1)
                # set the min and max of the axis.
                ax.set_xlim([-1, 5])
                ax.set_ylim([-0.1, 1.1])
          
                # show y labels on first column only
                if index % len(pollutant_list) == 0:
                    matplotlib.rcParams.update({'font.size': 8})
                    ax.set_ylabel(activity_labels[y_label])
                else: 
                    ax.set_yticklabels([])
                
                # show pollutant labels above first row of plots
                if index < len(pollutant_list):
                    ax.set_title(pollutant_labels[titleLabel])
                
                # show x labels below last row only
                if index < len(pollutant_list)*(len(activity_list)-1):
                    ax.set_xticklabels([])
                else:
                    ax.set_xticklabels(([''] + feedstock_list), rotation='vertical')
        
                index += 1
                self.f.write(pollutant + ',' + activity + '\n')
                for f_num, feedstock in enumerate(feedstock_list):
                    # used to decide what to query.
                    choose_query = ChooseSQL(activity=activity, pollutant=pollutant, feedstock=feedstock, schema=self.db.schema)
                    # make plots.
                    self.make_plots(ax=ax, query=choose_query, f_num=f_num, f_color=f_color[f_num], f_marker=f_marker[f_num], feedstock=feedstock)  
         
                self.f.write('\n')
        
    #    print figure to a .png file (small file size)
    #    canvas.print_figure('Contribution Analysis.tiff')      
        fig.savefig(os.path.join(self.path, 'Figures', 'Contribution_Figure.png'), format='png')
           
        self.f.close()
    #    print time.time() - startTime, ' seconds'

    def make_plots(self, ax, query, f_num, f_color, f_marker, feedstock):
        """
        Formats the plots
        @param ax: Subplot. 
        @param query: Query to grab data for plot.  
        @param f_num: Feedstock index.
        @param f_color: Color to make points.
        @param f_marker: Marker type to put on graph. (circles, boxes, ect...)
        @param feedstock: Type of feedstock ('CG','SG','CS','WS','FR')   
        """

        query.get_query()

        if query.query_string.startswith('No'):
            pass    

        elif query.query_string.startswith('FR'):
            data = [1, 1]
            ax.plot([f_num] * 2, [1, 1], f_color, marker=f_marker, markersize=2)

        else:
            data = self.db.output(query.query_string)
            mean_val = mean(data[0])
            med_val = median(data[0])
            max_val = max(data[0])
            min_val = min(data[0])

            ax.plot([f_num], mean_val, f_color, marker='_', markersize=20)
            ax.plot([f_num], med_val, f_color, marker='_', markersize=7)
    
            # Plot the max/min values
            ax.plot([f_num] * 2, [max_val, min_val], f_color, marker=f_marker, markersize=2)    
            
            self.write_results(feedstock=feedstock, max_val=str(max_val[0]), med_val=str(med_val), min_val=str(min_val[0]))

    def write_results(self, feedstock, max_val, med_val, min_val):
        """
        Writes the results to a file in a readable format. 
        """
        self.f.write(feedstock + ',' + max_val + ',' + med_val + ',' + min_val + '\n')
    

if __name__ == "__main__":  
    # used for testing.
    from model.Database import Database
    import Container
    
    title = 'sgNew'
    cont = Container.Container()
    cont.set('model_run_title', title)
    cont.set('path', 'C:/Nonroad/%s/' % (title,))
    cont.set('db', Database(title))
    
    # Emissions per a production lb figure.
    print 'Creating contribution figure.'
    ContributionAnalysis(cont)   
