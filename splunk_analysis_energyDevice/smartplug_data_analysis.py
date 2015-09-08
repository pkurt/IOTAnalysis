import numpy as np
import sys
import os
import math
import ast
import pandas as pd
sys.path.append("/Users/pelinkurtgarberson/Desktop/sdk_python/splunk-sdk-python-master")
import splunklib.client as client
import splunklib.results as results
import matplotlib.pyplot as plt
import matplotlib
import pythonUtils.drawing as drawing
import pythonUtils.responseReaderWrapper as responseReaderWrapper
import copy as cp
from matplotlib.backends.backend_pdf import PdfPages
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import time
import json
import io
from email.mime.text import MIMEText
import datetime

# To identify the test starting point I look for spike in the power.
# You will look for 5% increase of the whole house power which you get from the side bands.
# We can also develop a more sophisticated algorithm. We can apply fit to the side band to estimate the bkg.
def getPeaks(dataDF):
    def getPeakArea(peakInfoObject, dataDF):
        def getRealPeakBounds(peakInfoObject, dataDF, tolerance=0.05):
            ''' If power changes by more than tolerance, have entered peak '''
            startIdx = peakInfoObject['startTestIndex']
            startPrePeak = max(startIdx-5, 0)
            endPrePeak = max(startIdx, 0)
            prePeakEventPowers = dataDF['powerUsage'][startPrePeak:endPrePeak]
            prePeakAvgPower = np.mean(prePeakEventPowers)

            maxIndex = dataDF['powerUsage'].count()
            endIdx = peakInfoObject['endTestIndex']
            startPostPeak = min(maxIndex, endIdx+1)
            endPostPeak = min(maxIndex, endIdx+6)
            postPeakEventPowers = dataDF['powerUsage'][startPostPeak:endPostPeak]
            postPeakAvgPower = np.mean(postPeakEventPowers)

            testPeriodPowers = dataDF['powerUsage'][startIdx:endIdx]
            peakHasStarted = False
            peakHasEnded = False
            peakStartIndex = None
            peakEndIndex = None
            for pidx, power in testPeriodPowers.iteritems():
                #### Have we found start of peak?
                #### Or if we mistakenly thought we found end of peak, correct that
                if peakHasStarted == False or peakHasEnded:
                    if power > (1. + tolerance)*max(prePeakAvgPower, postPeakAvgPower):
                        ### If first time seeing start of peak, init it:
                        if peakHasStarted == False:
                            peakHasStarted = True
                            peakStartIndex = pidx
                        ### if falsely found end of peak, reset
                        peakHasEnded = False
                        peakEndIndex = None
                #### Have we found end of peak?
                if peakHasStarted and peakHasEnded == False:
                    if power < (1. + tolerance)*postPeakAvgPower:
                        peakHasEnded = True
                        peakEndIndex = pidx-1
            if peakStartIndex is None:
                peakStartIndex = startIdx
            if peakEndIndex is None:
                peakEndIndex = endIdx

            peakInfoObject['startIndex'] = peakStartIndex
            peakInfoObject['startTime'] = dataDF['timeStamp'][peakStartIndex]
            peakInfoObject['endIndex'] = peakEndIndex
            peakInfoObject['endTime'] = dataDF['timeStamp'][peakEndIndex]


        def getAverageBetweenTimes(dataDF, startTime, endTime, defaultIndex):
            ''' If window ends up being empty then use defaultIndex value '''
            powerValues = dataDF['powerUsage'][(dataDF['timeStamp'] >= startTime) &
                    (dataDF['timeStamp'] < endTime)]
            print 'data for determining power in window has length: ', powerValues.count()
            if powerValues.count() >= 1:
                averageValue = powerValues.mean()
            else:
                averageValue = dataDF['powerUsage'][defaultIndex]
            return averageValue

        #### First need to find when real peak starts inside of test window
        getRealPeakBounds(peakInfoObject, dataDF, tolerance=0.2)

        #### Get low window and high window
        #### Rules:
        ####     Windows should have at least one event
        ####     Take all events in five minutes before/after
        startWindowTime = peakInfoObject['startTime'] - datetime.timedelta(minutes=6)
        avgPowerStartWindow = getAverageBetweenTimes(dataDF, startWindowTime,
                peakInfoObject['startTime'], peakInfoObject['startIndex']-1)
        beginEndWindowTime = dataDF['timeStamp'][peakInfoObject['endIndex']+1]
        endWindowTime = peakInfoObject['endTime'] + datetime.timedelta(minutes=6)
        avgPowerEndWindow = getAverageBetweenTimes(dataDF, beginEndWindowTime,
                endWindowTime, peakInfoObject['endIndex']+1)
        avgPowerBkg = 0.5*(avgPowerStartWindow+avgPowerEndWindow)
        peakInfoObject['startWindowPower'] = avgPowerStartWindow
        peakInfoObject['endWindowPower'] = avgPowerEndWindow
        peakInfoObject['bkgPower'] = avgPowerBkg

        avgPeakPower = dataDF['powerUsage'][peakInfoObject['startIndex']:peakInfoObject['endIndex']+1].mean()
        peakInfoObject['peakPower'] = avgPeakPower
        peakInfoObject['signalPower'] = peakInfoObject['peakPower'] - peakInfoObject['bkgPower']
        print 'Found peak with startTime: ', peakInfoObject['startTime'],\
           ', endTime: ', peakInfoObject['endTime']
        print 'startWindowPower: ', peakInfoObject['startWindowPower'], ', end: ', peakInfoObject['endWindowPower']
        print 'peak power:',peakInfoObject['peakPower'], ', bkgPower:', peakInfoObject['bkgPower'],  ', signalPower: ', peakInfoObject['signalPower']

    allPeaks = []
    inTesting = False
    inAPeak = False
    previousTimestamp = None
    currentPeakInfo = {}
    for thisIdx, thisEvent in dataDF.iterrows():
        if inTesting == False and thisEvent['isTesting'] == 1:
            inTesting = True
            currentPeakInfo['startTestIndex'] = thisIdx
            currentPeakInfo['startTestTime'] = thisEvent['timeStamp']
        if thisEvent['isTesting'] == 0 and inTesting == True:
            inTesting = False
            currentPeakInfo['endTestIndex'] = thisIdx-1
            currentPeakInfo['endTestTime'] = previousTimestamp
            getPeakArea(currentPeakInfo, dataDF)
            allPeaks.append(currentPeakInfo)
            currentPeakInfo = {}
        previousTimestamp = thisEvent['timeStamp']
    return allPeaks


    #testWindowDF = dataDF[dataDF['isTesting'] == 1]



# Add your function below!
def main (argv):
    start_time = time.time()
    print 'Start of code'
    assert len(argv) == 4
    smartplugId = int(argv[1])
    StartTime = argv[2]
    EndTime = argv[3]
    print 'smartplugId = ', smartplugId, ', startTime = ', StartTime, ', endTime = ', EndTime

    searchReader = doSplunkSearch(smartplugId, StartTime, EndTime)
    #print 'now getPandasDF'
    sys.stdout.flush()
    myDataDF = getPandasDF(searchReader)

    peaks = getPeaks(myDataDF)
    #print 'now getRunPeriodDF'
    sys.stdout.flush()
    #runPeriodDF = getRunPeriodDF(myDataDF)
    print 'draw plots including peaks: ', peaks
    draw_plots(myDataDF, peaks)
    #checkForAlert(myDataDF, runPeriodDF)
    runtime = time.time() - start_time
    sys.stdout.flush()
    print 'It took ', str(runtime), ' to run'
    sys.stdout.flush()
#
#def getRunPeriodDF(myDataDF):
#    listOfRunPeriods = []
#    #print 'getRunPeriodDF'
#    previousMode = 0
##    beginRunTime = None
##    endRunTime = None
#    eventsInThisRun = []
#    for thisIdx, thisEvent in myDataDF.iterrows():
#        isRunning = thisEvent['RunningMode']
#     #   print 'thisEvent: ', thisEvent
#      #  print 'isRunning: ', isRunning, ', type: ', type(isRunning)
#        if previousMode == 1 and isRunning == False:
#            runParameters = getRunParameters(eventsInThisRun)
#
#            endRunTime = thisEvent['timeStamp']
#            print 'append beginRunTime: ', runParameters['beginRunTime'], ', end: ', runParameters['endRunTime']
#            thisRunPeriod = {'beginRunTime': runParameters['beginRunTime'], 'endRunTime': runParameters['endRunTime'],
#                    'duration': runParameters['duration'], 'performance': runParameters['performance']}
#            listOfRunPeriods.append(thisRunPeriod)
#
#            ### Clear events from this run to look for new one:
#            eventsInThisRun = []
#        if isRunning:
#            eventsInThisRun.append(thisEvent)
#        previousMode = thisEvent['RunningMode']
#
#    #### Got all run periods, now build pandas dataframe
#    #print 'Define runPeriodDF from ', listOfRunPeriods
#    runPeriodDF = pd.DataFrame(listOfRunPeriods)
#    return runPeriodDF
#

def getPandasDF(searchReader):
    print 'getPandasDF'
    myData = []
    print 'read data in getPandasDF'
    sys.stdout.flush()


    lineNum = 0
    #print 'searchReader has type: ', type(searchReader)
    for line in searchReader:
        #print 'line: ', line
#        if lineNum % 50 == 0: print 'lineNum: ', lineNum
        thisDict = json.loads(line['_raw'])
        myData.append(thisDict)
        lineNum += 1
        #print 'this row is: ', thisDict
        #if lineNum % 50 == 0: print 'PowerUsage is: ', thisDict['powerUsage']
    myDataDF = pd.DataFrame(myData)
    myDataDF['timeStamp'] = pd.to_datetime(myDataDF['timeStamp'])
   # print 'sort data in getPandasDF'
    sys.stdout.flush()
    myDataDF = myDataDF.sort('timeStamp')
    sys.stdout.flush()
    return myDataDF

#### Follow the example here: http://dev.splunk.com/view/python-sdk/SP-CAAAER5#reader
def doSplunkSearch(smartplugId, StartTime, EndTime):
        
    #### do splunk search
    #### output = splunkSearch(smartplugId, StartTime, EndTime)
    #### Organize into pandas dataFrame, myDataDF
    service = client.connect(host='localhost', port=8089, username='admin', password='xxxxxx')
    #print 'got service, now make job'
    kwargs_oneshot={"earliest_time": StartTime,
                    "latest_time": EndTime,
                    "count": 0}
    jobSearchString= "search id="+str(smartplugId)+" | sort _time "
   # print 'jobSearchName: ', jobSearchString
    job_results = service.jobs.oneshot(jobSearchString, **kwargs_oneshot)
    reader = results.ResultsReader(io.BufferedReader(responseReaderWrapper.ResponseReaderWrapper(job_results)))
    #reader = results.ResultsReader(job_results)
    return reader

def draw_plots(myDataDF, peakInfoObjects):
    #print 'Now make plots for ', myDataDF

    #### First make inclusive plot:
    xKey='timeStamp'
    #myPdf = PdfPages('PowerSummary_LaundryDryer.pdf')
    #myPdf = PdfPages('PowerSummary_HairDryer.pdf')
    #myPdf = PdfPages('PowerSummary_Microwave.pdf')
    myPdf = PdfPages('PowerSummary_Blender.pdf')
    #myPdf = PdfPages('PowerSummary_LightBulb.pdf')
    chartOptionsDict = {'powerUsage': {'color': 'blue', 'style': '-'}
                       }
    plotOptionsDict = {'xlabel': 'Time', 'ylabel': 'Power usage [Watts]', 
                       'grid': True, 'figsize': (50,10), 'doDates': True,
                       'xAxisFontSize': 24, 'yAxisFontSize': 24,
                       'xLabelSize': 28, 'yLabelSize': 28,
                       'xMarginXtra': 2.0}
#        for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
#                             ax.get_xticklabels() + ax.get_yticklabels()):
#                item.set_fontsize(20)
    #plt.figure(figsize=(50,10))
    # print 'datetime values are: ', myDataDF[xKey]
    drawing.overlayChartsFromPandasDF(plt, myDataDF, xKey, chartOptionsDict, plotOptionsDict)
    #plt.show()
    myPdf.savefig()
    plt.close()

    #### Now make peak plots:
    print 'Now draw peaks: ', peakInfoObjects
    for peak in peakInfoObjects:
#        'peakInfoObject['startWindowPower']
#        'peakInfoObject['endWindowPower']
        peakDataDF = myDataDF[peak['startTestIndex']-2:peak['endTestIndex']+ 3]
        chartOptionsDict = {
                'powerUsage': {'color': 'blue', 'style': '-'}
               }
        plotOptionsDict = {'xlabel': 'Time', 'ylabel': 'Power usage [Watts]', 'grid': True, 'doDates': True}
        xKey = 'timeStamp'
        print 'draw for this peak:'
        #drawBackgroundAndPeak()

        ax = drawing.getPlotFrame(plotOptionsDict)
        startSidebandOut = drawing.drawDatetimeOnePtBarPlot(ax, startTime=peak['startTime']-datetime.timedelta(minutes=6),
                                             endTime=peak['startTime'],
                                             value=peak['startWindowPower'], color='mediumvioletred')
        endSidebandOut = drawing.drawDatetimeOnePtBarPlot(ax, startTime=peak['endTime'],
                                             endTime=peak['endTime']+datetime.timedelta(minutes=6),
                                             value=peak['endWindowPower'], color='mediumvioletred')
        peakOut = drawing.drawDatetimeOnePtBarPlot(ax, startTime=peak['startTime'], endTime=peak['endTime'],
                                             value=peak['peakPower'], color='powderblue')
        bkgOut = drawing.drawDatetimeOnePtBarPlot(ax, startTime=peak['startTime'], endTime=peak['endTime'],
                                             value=peak['bkgPower'], color='pink')


        timeSeriesOut = drawing.overlayChartsFromPandasDF(plt, peakDataDF, xKey, chartOptionsDict, plotOptionsDict, createNewFig=False, ax=ax)
        startTestTime = peak['startTestTime']
        endTestTime = peak['endTestTime']
        startEndTestTimeValues = [drawing.convertDatetime64ToDatetime(ele) for ele in [startTestTime, endTestTime]]
        startEndTestTimeDates = matplotlib.dates.date2num(startEndTestTimeValues)
        canvasStartTestTime = startEndTestTimeDates[0]
        canvasEndTestTime = startEndTestTimeDates[1]
        ymin, ymax = ax.get_ylim()
        startTestOut = ax.plot([canvasStartTestTime,canvasStartTestTime],[ymin, ymax],color='black',linestyle='--', linewidth=2)
        endTestTout = ax.plot([canvasEndTestTime,canvasEndTestTime],[ymin, ymax],color='black',linestyle='--', linewidth=2)
        ax.legend((startSidebandOut[0], bkgOut[0], peakOut[0], timeSeriesOut[0], startTestOut[0]),
                  ('Sideband', 'Background', 'Device power', 'Power usage', 'Test begin/end'))
        myPdf.savefig()
        plt.close()

    myPdf.close()

#
#def getRunParameters(eventsInThisRun):
#    def getPerformance(insideTemps, outsideTemps, duration):
#        avgTempDiff = np.mean([outTemp - inTemp for inTemp, outTemp in zip(insideTemps, outsideTemps)])
#        if(duration > 0.0001):
#            performance = math.sqrt(max(0.01, avgTempDiff)) * (max(insideTemps) - min(insideTemps)) / duration
#        else:
#            performance = 0
#        return performance
#
#    runParameters = {}
#    runParameters['beginRunTime'] = eventsInThisRun[0]['timeStamp']
#    runParameters['endRunTime'] = eventsInThisRun[-1]['timeStamp']
#    runParameters['duration'] = (eventsInThisRun[-1]['timeStamp'] -
#                eventsInThisRun[0]['timeStamp']).total_seconds() / 60.
#    insideTemps = [event['InsideTemp'] for event in eventsInThisRun]
#    outsideTemps = [event['OutsideTemp'] for event in eventsInThisRun]
#    runParameters['performance'] = getPerformance(insideTemps, outsideTemps, runParameters['duration'])
#    return runParameters
#
#def checkForAlert(myDataDF, runParameters):
#    print 'checkforAlert'
#    myEmail = 'pelin.kurt.4d@gmail.com'
#    myPassword='xxxxxx'
#    #eMailAddresses=['pelin.kurt.4d@gmail.com', 'mwchaney@gmail.com', 'scott@salusinc.com']
#    eMailAddresses=['pelin.kurt.4d@gmail.com']
#
#    avgPerformance = np.mean(runParameters['performance'])
#    print 'avgPerformance :', avgPerformance
#    if avgPerformance < 30.:
#        msgText = 'Performance alert. Average performance is '+str(avgPerformance)
#        msgSubject = 'Alarm testing!!!'
#        makeAlert(msgText, msgSubject, myEmail, myPassword, eMailAddresses)
#
#
#def makeAlert(msgText, msgSubject, myEmail, myPassword, eMailAddresses):
#    print 'makeAlert'
#    server = smtplib.SMTP('smtp.gmail.com:587')
#    server.ehlo()
#    server.starttls()
#    server.login(myEmail, myPassword)
#    msg = MIMEText(msgText)
#    msg['Subject'] = msgSubject
#    msg['From'] = myEmail
#    msg['To'] = ", ".join(eMailAddresses)
#    server.sendmail(myEmail, eMailAddresses, msg.as_string())
#

if __name__ == "__main__":
    main(sys.argv)
