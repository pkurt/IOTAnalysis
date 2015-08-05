import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import datetime
import numpy as np

def overlayChartsFromPandasDF(plt, pandasDF, xKey, chartOptionsDict, plotOptionsDict):
    ''' Inputs:
      plt: the pyplot that is already in use. Assumption: plotting frame is
      already open
      pandasDF: a pandas data frame where array from each key is an option for drawing
      xKey: the key representing the x-values from the data frame
      chartOptionsDict: specifies draw options for each overlaid chart
      The keys must match keys from the pandasDF. These are the y-values
      that will be drawn.
      .... Allowed options for each key:
      .........  Fill options
      .........  Line style
      .........  Color
      .........  Legend string

      Example:
          chartOptionsDict = {'InsideTemp': {'color':'blue', 'style': 'k--', 'legendDesc': 'blah blah'}, 
                             'OutsideTemp': {'color':'red', ...}}
      options to add later: xMin, xMax

      plotOptionsDict: dictionary with plot properties (axis ranges, axis titles, grid markers, etc)
      Example:
          plotOptionsDict = {'xlabel': 'Time', 'ylabel': 'Temperature', ...}

      End of function: return without closing plotting frame
    '''
    def convertDatetime64ToDatetime(myDT64):
        ts = (myDT64 - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')
        return datetime.datetime.utcfromtimestamp(ts)

    if xKey not in pandasDF.keys():
        print 'Error, xKey ', xKey, ' does not exist. Exiting.'
        return 1
    hfmt = matplotlib.dates.DateFormatter('%m/%d %H:%M')
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.xaxis.set_major_formatter(hfmt)
    plt.xticks(rotation=20)
    ### assume type is datetime for xKey. If not then this will crash.
    myDateValues = pandasDF[xKey].values


   # print 'before conversion values are : ', myDateValues, ', values are ', type(myDateValues[0])
    myDateValues = [convertDatetime64ToDatetime(ele) for ele in myDateValues]
    #myDateValues = [ele.astype(datetime.datetime) for ele in myDateValues]
  #  print 'values are : ', myDateValues, ', values are ', type(myDateValues[0])
    for yKey, chartOptions in chartOptionsDict.iteritems():
        # We will draw each chart in these options
        if yKey not in pandasDF.keys():
            print 'Warning, yKey ', yKey, ' does not exist. Skip it.'
            continue
        ### specify draw options:
        linestyle=chartOptions['style'] if chartOptions['style'] else 'o'
        color=chartOptions['color'] if chartOptions['color'] else 'black'
        #plt.plot(pandasDF[xKey], pandasDF[yKey], linestyle=linestyle, color=color)
        if 'xlabel' in plotOptionsDict.keys(): plt.xlabel(plotOptionsDict['xlabel'])
        if 'ylabel' in plotOptionsDict.keys(): plt.ylabel(plotOptionsDict['ylabel'])
        if 'grid' in plotOptionsDict.keys(): plt.grid(plotOptionsDict['grid'])

        myDates = matplotlib.dates.date2num(myDateValues)
        #plt.plot_date(myDates, pandasDF[yKey], linestyle=linestyle, color=color)
        ax = plt.subplot(111)
        if 'type' in chartOptions.keys() and chartOptions['type'] == 'bar':
            xBinWidths = [myDates[j+1]-myDates[j] for j in range(len(myDates)-1)] + [myDates[-1]-myDates[-2]]
            ax.bar(myDates, pandasDF[yKey], color=color, width=xBinWidths)
        else:
            ax.plot(myDates, pandasDF[yKey], linestyle=linestyle, color=color)
        ax.xaxis_date()


