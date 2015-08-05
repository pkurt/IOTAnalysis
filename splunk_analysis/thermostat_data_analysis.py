import numpy as np
import sys
import os
import math
import ast
import pandas as pd
import splunklib.client as client
import splunklib.results as results
import matplotlib.pyplot as plt
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


# Add functions below!
def main (argv):
    start_time = time.time()
    print 'Start of code'
    assert len(argv) == 4
    thermostatId = int(argv[1])
    StartTime = argv[2]
    EndTime = argv[3]
    print 'thermostatId = ', thermostatId, ', startTime = ', StartTime, ', endTime = ', EndTime

    searchReader = doSplunkSearch(thermostatId, StartTime, EndTime)
    #print 'now getPandasDF'
    sys.stdout.flush()
    myDataDF = getPandasDF(searchReader)
    #print 'now getRunPeriodDF'
    sys.stdout.flush()
    runPeriodDF = getRunPeriodDF(myDataDF)
    dashboard_performance_plots(myDataDF, runPeriodDF)
    checkForAlert(myDataDF, runPeriodDF)
    #print 'runPeriodDF: ', runPeriodDF
    runtime = time.time() - start_time
    sys.stdout.flush()
    print 'It took ', str(runtime), ' to run'
    sys.stdout.flush()

def getRunPeriodDF(myDataDF):
    listOfRunPeriods = []
    #print 'getRunPeriodDF'
    previousMode = 0
#    beginRunTime = None
#    endRunTime = None
    eventsInThisRun = []
    for thisIdx, thisEvent in myDataDF.iterrows():
        isRunning = thisEvent['RunningMode']
        #startedRun = False
        #endedRun = False
     #   print 'thisEvent: ', thisEvent
      #  print 'isRunning: ', isRunning, ', type: ', type(isRunning)
#        if previousMode == 0 and isRunning:
#            startedRun = True
#            beginRunTime = thisEvent['timeStamp']
        if previousMode == 1 and isRunning == False:
            runParameters = getRunParameters(eventsInThisRun)

            #endedRun = True
            endRunTime = thisEvent['timeStamp']
#            duration = runParameters['duration']
#            duration = (endRunTime-beginRunTime).total_seconds() / 60.
           # print 'append beginRunTime: ', runParameters['beginRunTime'], ', end: ', runParameters['endRunTime'], ', duration: ', runParameters['duration']
            thisRunPeriod = {'beginRunTime': runParameters['beginRunTime'], 'endRunTime': runParameters['endRunTime'],
                    'duration': runParameters['duration'], 'performance': runParameters['performance']}
            listOfRunPeriods.append(thisRunPeriod)

            ### Clear events from this run to look for new one:
            eventsInThisRun = []
        if isRunning:
            eventsInThisRun.append(thisEvent)
        previousMode = thisEvent['RunningMode']
       #def getPerformance(InsideTemp,OutsideTemp,Duration):

    #### Got all run periods, now build pandas dataframe
    #print 'Define runPeriodDF from ', listOfRunPeriods
    runPeriodDF = pd.DataFrame(listOfRunPeriods)
    return runPeriodDF


            

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
        #prevLine = cp.deepcopy(line)
        #thisDict = ast.literal_eval(line['_raw'])
        thisDict = json.loads(line['_raw'])
        myData.append(thisDict)
        lineNum += 1
        #print 'this row is: ', thisDict
        #print 'thisInsideTemp is: ', thisDict['InsideTemp']
    myDataDF = pd.DataFrame(myData)
    print 'got pandas dataframe: ', myDataDF
    myDataDF['timeStamp'] = pd.to_datetime(myDataDF['timeStamp'])
   # print 'sort data in getPandasDF'
    sys.stdout.flush()
    myDataDF = myDataDF.sort('timeStamp')
    #print 'Full pandas data = ', myDataDF
    #print 'Data where it is running = ', myDataDF[myDataDF['RunningMode'] == 1]
    #print 'Data where outsidetemp > 78 degrees = ', myDataDF[myDataDF['OutsideTemp'] > 78.]
  #  print 'Return myDataDF'
    sys.stdout.flush()
    return myDataDF

#### Follow the example here: http://dev.splunk.com/view/python-sdk/SP-CAAAER5#reader
def doSplunkSearch(thermostatId, StartTime, EndTime):
        
    #### do splunk search
    #### output = splunkSearch(thermostatId, StartTime, EndTime)
    #### Organize into pandas dataFrame, myDataDF
    service = client.connect(host='localhost', port=8089, username='admin', password='Pg18december')
    #print 'got service, now make job'
    kwargs_oneshot={"earliest_time": StartTime,
                    "latest_time": EndTime,
                    "count": 0}
    jobSearchString= "search id="+str(thermostatId)+" | sort _time "
   # print 'jobSearchName: ', jobSearchString
    job_results = service.jobs.oneshot(jobSearchString, **kwargs_oneshot)
    reader = results.ResultsReader(io.BufferedReader(responseReaderWrapper.ResponseReaderWrapper(job_results)))
    #reader = results.ResultsReader(job_results)
    return reader

def dashboard_performance_plots(myDataDF, runPeriodDF):
    print 'Now make plots for ', myDataDF
    xKey='timeStamp'
    myPdf = PdfPages('testPdf.pdf')
    chartOptionsDict = {'InsideTemp': {'color': 'mediumturquoise', 'style': '-', 'desc': 'Inside Temp', 'linewidth':2},
                        'OutsideTemp': {'color': 'mediumvioletred', 'style': '-', 'desc': 'Outside Temp', 'linewidth':2},
                        'SetPoint': {'color': 'blue', 'style': '-', 'desc': 'Setpoint', 'linewidth':2}
                        }
    plotOptionsDict = {'xlabel': 'Time', 'ylabel': 'Temperature', 'grid': True, 'doDates': True, 'figsize': (15,10),
                      'xAxisFontSize': 25, 'yAxisFontSize': 25, 'xLabelSize': 28, 'yLabelSize': 28, 'xMarginXtra': 10.0,
                      'y_limit': [45,135]}
    print 'datetime values are: ', myDataDF[xKey]
    drawLegOutputs, drawLegLabels = drawing.overlayChartsFromPandasDF(plt, myDataDF, xKey, chartOptionsDict, plotOptionsDict)
    plt.legend(drawLegOutputs, drawLegLabels, prop={'size':28})
    #plt.show()
    myPdf.savefig()
    plt.close()

#    ### now do runPeriodDF
    #print 'Will draw duration from runPeriodDF: ', runPeriodDF
    chartOptionsDict = {'duration': {'type': 'bar', 'maxBarWidth': 30. / (60.*24.), 'color': 'gold', 'style': '-'}}
    plotOptionsDict = {'xlabel': 'Time', 'ylabel': 'Run Duration [minutes]', 'grid': True, 'doDates': True, 'figsize': (15,10),
                       'xAxisFontSize': 25, 'yAxisFontSize': 25, 'xLabelSize': 28, 'yLabelSize': 28, 'xMarginXtra': 2.0}
    drawOutput = drawing.overlayChartsFromPandasDF(plt, runPeriodDF, 'beginRunTime', chartOptionsDict, plotOptionsDict)
    myPdf.savefig()
    plt.close()

    #print 'Now draw performance plot'
    chartOptionsDict = {'performance': {'type': 'bar', 'maxBarWidth': 30. / (60.*24.), 'color': 'lightseagreen', 'style': '-'}}
    plotOptionsDict = {'xlabel': 'Time', 'ylabel': 'Performance', 'grid': True, 'doDates': True,'figsize': (15,10),
                       'xAxisFontSize': 25, 'yAxisFontSize': 25, 'xLabelSize': 28, 'yLabelSize': 28, 'xMarginXtra': 2.0}
    drawing.overlayChartsFromPandasDF(plt, runPeriodDF, 'beginRunTime', chartOptionsDict, plotOptionsDict)
    myPdf.savefig()
    plt.close()

    myPdf.close()


def getRunParameters(eventsInThisRun):
    def getPerformance(insideTemps, outsideTemps, duration):
        avgTempDiff = np.mean([outTemp - inTemp for inTemp, outTemp in zip(insideTemps, outsideTemps)])
        if(duration > 0.0001):
            performance = math.sqrt(max(0.01, avgTempDiff)) * (max(insideTemps) - min(insideTemps)) / duration
        else:
            performance = 0
        return performance

    print 'getRunParameters for events: ', eventsInThisRun
    runParameters = {}
    runParameters['beginRunTime'] = eventsInThisRun[0]['timeStamp']
    runParameters['endRunTime'] = eventsInThisRun[-1]['timeStamp']
    runParameters['duration'] = (eventsInThisRun[-1]['timeStamp'] -
                eventsInThisRun[0]['timeStamp']).total_seconds() / 60.
    print 'duration: ', runParameters['duration']
    insideTemps = [event['InsideTemp'] for event in eventsInThisRun]
    outsideTemps = [event['OutsideTemp'] for event in eventsInThisRun]
    runParameters['performance'] = getPerformance(insideTemps, outsideTemps, runParameters['duration'])
    return runParameters

#def checkForAlert(myDataDF, runPeriodDF):
def checkForAlert(myDataDF, runParameters):
    print 'checkforAlert'
    myEmail = 'pelin.kurt.4d@gmail.com'
    myPassword='Pg18december'
    #eMailAddresses=['pelin.kurt.4d@gmail.com', 'mwchaney@gmail.com', 'scott@salusinc.com']
    eMailAddresses=['pelin.kurt.4d@gmail.com']

    #avgPerformance = np.mean(runPeriodDF['performance'])
    avgPerformance = np.mean(runParameters['performance'])
    print 'avgPerformance :', avgPerformance
    if avgPerformance < 30.:
        msgText = 'Performance alert. Average performance is '+str(avgPerformance)
        msgSubject = 'Alarm testing!!!'
        #makeAlert(msgText, msgSubject, myEmail, myPassword, eMailAddresses)

#def makeAlert(msgText, myEmail, myPassword, eMailAddresses):
#    print 'makeAlert'
#    recipientEmails=", ".join(eMailAddresses)
#    print 'prepare message to send'
#    server = smtplib.SMTP('smtp.gmail.com:587')
#    server.ehlo()
#    server.starttls()
#    server.login(myEmail, myPassword)
#    server.sendmail(myEmail, recipientEmails, msgText)
#    server.quit()

def makeAlert(msgText, msgSubject, myEmail, myPassword, eMailAddresses):
    print 'makeAlert'
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(myEmail, myPassword)
    msg = MIMEText(msgText)
    msg['Subject'] = msgSubject
    msg['From'] = myEmail
    msg['To'] = ", ".join(eMailAddresses)
    server.sendmail(myEmail, eMailAddresses, msg.as_string())


if __name__ == "__main__":
    main(sys.argv)
