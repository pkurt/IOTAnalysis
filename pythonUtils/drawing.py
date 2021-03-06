import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import datetime
import numpy as np

def getPlotFrame(plotOptionsDict):

    #if 'xMarginXtra' in plotOptionsDict.keys() or 'yMarginXtra' in plotOptionsDict.keys():
        #if 'xMarginXtra' in plotOptionsDict.keys():
            #h_pad = plotOptionsDict['xMarginXtra']
        #    extraPadding = plotOptionsDict['xMarginXtra']
        #if 'yMarginXtra' in plotOptionsDict.keys():
            #w_pad = plotOptionsDict['yMarginXtra']
        #plt.tight_layout(pad=extraPadding, h_pad=None, w_pad=None)
#        x0, x1, y0, y1 = plt.axis()
#        print 'x0, x1, y0, y1: ', x0, ', ', x1, ', ', y0, ', ', y1
#        if 'xMarginXtra' in plotOptionsDict.keys():
#            print 'xMarginXtra: ', plotOptionsDict['xMarginXtra']
#            x0 = x0 - plotOptionsDict['xMarginXtra']
#            x1 = x1 + plotOptionsDict['xMarginXtra']
#        if 'yMarginXtra' in plotOptionsDict.keys():
#            print 'yMarginXtra: ', plotOptionsDict['yMarginXtra']
#            y0 = y0 - plotOptionsDict['yMarginXtra']
#            y1 = y1 + plotOptionsDict['yMarginXtra']
#        print 'now update x0, x1, y0, y1: ', x0, ', ', x1, ', ', y0, ', ', y1
#        plt.axis((x0, x1, y0, y1))
    figsize = None
    if 'figsize' in plotOptionsDict.keys(): figsize = plotOptionsDict['figsize']
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)
    if 'doDates' in plotOptionsDict.keys():
        if plotOptionsDict['doDates']:
            hfmt = matplotlib.dates.DateFormatter('%m/%d %H:%M')
            ax.xaxis.set_major_formatter(hfmt)
            plt.xticks(rotation=20)
    if 'xlabel' in plotOptionsDict.keys(): plt.xlabel(plotOptionsDict['xlabel'])
    if 'ylabel' in plotOptionsDict.keys(): plt.ylabel(plotOptionsDict['ylabel'])
    if 'grid' in plotOptionsDict.keys(): plt.grid(plotOptionsDict['grid'])
    if 'xAxisFontSize' in plotOptionsDict.keys():
        for item in ax.get_xticklabels():
            item.set_fontsize(plotOptionsDict['xAxisFontSize'])
    if 'yAxisFontSize' in plotOptionsDict.keys():
        for item in ax.get_yticklabels():
            item.set_fontsize(plotOptionsDict['yAxisFontSize'])
    if 'xLabelSize' in plotOptionsDict.keys():
        ax.xaxis.label.set_fontsize(plotOptionsDict['xLabelSize'])
    if 'yLabelSize' in plotOptionsDict.keys():
        ax.yaxis.label.set_fontsize(plotOptionsDict['yLabelSize'])
    if 'y_limit' in plotOptionsDict.keys():
        #print 'set the y_limit'
        ax.set_ylim(plotOptionsDict['y_limit'])
    if 'x_limit' in plotOptionsDict.keys():
        ax.set_xlim(plotOptionsDict['x_limit'])
    
    ax = plt.subplot(111)

#    ax = plt.gca()
#    ax.set_xlim([xmin,xmax])
#    ax.set_ylim([ymin,ymax])

    return ax

def drawDatetimeOnePtBarPlot(ax, startTime, endTime, value, color):
    dateValues = [convertDatetime64ToDatetime(ele) for ele in [startTime, endTime]]
    dates = matplotlib.dates.date2num(dateValues)
    dateWidths = dates[1] - dates[0]
    drawOutput = ax.bar([dates[0]], value, color=color, width=dateWidths)
    return drawOutput

def convertDatetime64ToDatetime(myDT64):
    ts = (myDT64 - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')
    return datetime.datetime.utcfromtimestamp(ts)


def overlayChartsFromPandasDF(plt, pandasDF, xKey, chartOptionsDict, plotOptionsDict, createNewFig=True, ax=None):
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

    #print 'start of overlay, definitions to do are: ', chartOptionsDict
    if xKey not in pandasDF.keys():
        print 'Error, xKey ', xKey, ' does not exist. Exiting.'
        return 1
    if createNewFig:
        ax = getPlotFrame(plotOptionsDict)
    ### assume type is datetime for xKey. If not then this will crash.
    myDateValues = pandasDF[xKey].values


   # print 'before conversion values are : ', myDateValues, ', values are ', type(myDateValues[0])
    myDateValues = [convertDatetime64ToDatetime(ele) for ele in myDateValues]
    #myDateValues = [ele.astype(datetime.datetime) for ele in myDateValues]
  #  print 'values are : ', myDateValues, ', values are ', type(myDateValues[0])
    #print 'iterate over chartOptionsDict: ', chartOptionsDict
    drawLegOutputs = []
    drawLegLabels = []
    for yKey, chartOptions in chartOptionsDict.iteritems():
    #for yKey, chartOptions in pandasDF.keys():
       # print 'print-y-values, yKey: ', yKey
        # We will draw each chart in these options
        if yKey not in pandasDF.keys():
            print 'Warning, yKey ', yKey, ' does not exist. Skip it.'
            continue
        ### specify draw options:
        linestyle=chartOptions['style'] if 'style' in chartOptions.keys() else 'o'
        color=chartOptions['color'] if 'color' in chartOptions.keys() else 'black'
        linewidth = chartOptions['linewidth'] if 'linewidth' in chartOptions.keys() else 1
        
        #plt.plot(pandasDF[xKey], pandasDF[yKey], linestyle=linestyle, color=color)

        myDates = matplotlib.dates.date2num(myDateValues)
        drawOutput = None
        #plt.plot_date(myDates, pandasDF[yKey], linestyle=linestyle, color=color)
        if 'type' in chartOptions.keys() and chartOptions['type'] == 'bar':
            xBinWidths = [myDates[j+1]-myDates[j] for j in range(len(myDates)-1)] + [myDates[-1]-myDates[-2]]
            #### enforce max bar width
            #print 'myDates are: ', myDates, ', now getWidths'
            if 'maxBarWidth' in chartOptions.keys():
                xBinWidths = [min(chartOptions['maxBarWidth'], ele) for ele in xBinWidths]
            maxBarWidth = chartOptions['maxBarWidth'] if 'maxBarWidth' in chartOptions.keys() else None


            drawOutput = ax.bar(myDates, pandasDF[yKey], color=color, width=xBinWidths)
        else:
            #print 'myDates: ', myDates
            #print 'yKey: ', yKey
            #print 'pandasDF[yKey]: ', pandasDF[yKey].values
            #print 'linestyle: ', linestyle
            #print 'color: ', color
            #print 'linewidth: ', linewidth
            drawOutput = ax.plot(myDates, pandasDF[yKey].values, linestyle=linestyle, color=color, linewidth=linewidth)
        ax.xaxis_date()
        drawLegOutputs.append(drawOutput[0])
        if 'desc' in chartOptions.keys(): drawLegLabels.append(chartOptions['desc'])
    return drawLegOutputs, drawLegLabels


