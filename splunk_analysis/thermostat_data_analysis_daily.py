import numpy as np
import sys
#sys.path.append('/Users/pelinkurtgarberson/Desktop/splunk_analysis/')
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
import collections


# Add your function below!
#def main (thermostatId, StartTime, EndTime, DataType):
def main (argv):
    start_time = time.time()
    print 'Start of code'
    assert len(argv) == 5
    thermostatId = int(argv[1])
    StartTime = argv[2]
    EndTime = argv[3]
    DataType = argv[4]

    print 'thermostatId = ', thermostatId, ', startTime = ', StartTime, ', endTime = ', EndTime, ', dataType = ', DataType

    searchReader = doSplunkSearch(thermostatId, StartTime, EndTime, DataType)
    #print 'now getPandasDF'
    sys.stdout.flush()
    myDataDF = getPandasDF(searchReader)
    sys.stdout.flush()
#    print 'now getRunPeriodDF'
#    runPeriodDF = getRunPeriodDF(myDataDF)
    #print 'runPeriodDF is ', runPeriodDF
    dashboard_performance_plots(myDataDF)
    #checkForAlert(myDataDF, runPeriodDF)
    #print 'runPeriodDF: ', runPeriodDF
    runtime = time.time() - start_time
    sys.stdout.flush()
    print 'It took ', str(runtime), ' to run'
    sys.stdout.flush()


#def getRunPeriodDF(myDataDF):
#    listOfRunPeriods = []
#    previousMode = 0
#    eventsInThisRun = []
#    print 'getRunPeriodDF from myDataDF: ', myDataDF
#    for thisIdx, thisEvent in myDataDF.iterrows():
#        isRunning = thisEvent['avgRunningMode']
#        if previousMode == 1 and isRunning == False:
#            runParameters = getRunParameters(eventsInThisRun)
#            endRunTime = thisEvent['timeStamp']
#            thisRunPeriod = {'beginRunTime': runParameters['beginRunTime'], 'endRunTime': runParameters['endRunTime'],'duration': runParameters['duration'], 'performance': runParameters['performance']}
#            listOfRunPeriods.append(thisRunPeriod)
#            eventsInThisRun = []
#        if isRunning:
#            eventsInThisRun.append(thisEvent)
#        previousMode = thisEvent['avgRunningMode']
#    print 'now make runPeriodDF from listOfRunPeriods: ', listOfRunPeriods
#    
#    runPeriodDF = pd.DataFrame(listOfRunPeriods)
#    return runPeriodDF

def getPandasDF(searchReader):
    print 'getPandasDF'
    myData = []
    print 'read data in getPandasDF'
    sys.stdout.flush()


    lineNum = 0
    #print 'searchReader has type: ', type(searchReader)
    for line in searchReader:
#        print 'line: ', line
#        if lineNum % 50 == 0: print 'lineNum: ', lineNum
        #prevLine = cp.deepcopy(line)
        #thisDict = ast.literal_eval(line['_raw'])
        thisDict = json.loads(line['_raw'])
        myData.append(thisDict)
        lineNum += 1
        #print 'this row is: ', thisDict
        #print 'thisInsideTemp is: ', thisDict['InsideTemp']
    myDataDF = pd.DataFrame(myData)
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
def doSplunkSearch(thermostatId, StartTime, EndTime, DataType):
        
    #### do splunk search
    #### output = splunkSearch(thermostatId, StartTime, EndTime)
    #### Organize into pandas dataFrame, myDataDF
    service = client.connect(host='localhost', port=8089, username='admin', password='xxxxx')
    #print 'got service, now make job'
    kwargs_oneshot={"earliest_time": StartTime,
                    "latest_time": EndTime,
                    "count": 0}
    jobSearchString= "search id="+str(thermostatId)+" dataType="+str(DataType)+" | sort _time "
    job_results = service.jobs.oneshot(jobSearchString, **kwargs_oneshot)
   # print 'jobSearchName: ', jobSearchString
    reader = results.ResultsReader(io.BufferedReader(responseReaderWrapper.ResponseReaderWrapper(job_results)))
    #reader = results.ResultsReader(job_results)
    return reader


def dashboard_performance_plots(myDataDF):
    print 'Now make plots for ', myDataDF
    xKey='timeStamp'
    myPdf = PdfPages('AggregatedResultsFromId20.pdf')
    chartOptionsDict = collections.OrderedDict([
                        ('maxInsideTemp', {'color': 'mediumturquoise', 'style': '--', 'desc': 'DayMaxInsideTemp', 'linewidth':6}),
                        ('avgInsideTemp', {'color': 'mediumturquoise', 'style': '-', 'desc': 'DayAvgInsideTemp', 'linewidth':6}),
                        ('minInsideTemp', {'color': 'mediumturquoise', 'style': '--', 'desc': 'DayMinInsideTemp', 'linewidth':6}),
                        ('maxOutsideTemp', {'color': 'mediumvioletred', 'style': '--', 'desc': 'DayMaxOutsideTemp', 'linewidth':6}),
                        ('avgOutsideTemp', {'color': 'mediumvioletred', 'style': '-', 'desc': 'DayAvgOutsideTemp', 'linewidth':6}),
                        ('minOutsideTemp', {'color': 'mediumvioletred', 'style': '--', 'desc': 'DayMinOutsideTemp', 'linewidth':6}),
                        ('avgSetPoint', {'color': 'blue', 'style': '-', 'desc': 'Setpoint', 'linewidth':6})
                       ])
    plotOptionsDict = {'xlabel': 'Time', 'ylabel': 'Temperature', 'grid': True, 'doDates': True, 'figsize': (20,10),
        'xAxisFontSize': 25, 'yAxisFontSize': 25, 'xLabelSize': 35, 'yLabelSize': 35, 'xMarginXtra': 10.0,
        'y_limit': [20,150]}
    print 'datetime values are: ', myDataDF[xKey]
    drawLegOutputs, drawLegLabels = drawing.overlayChartsFromPandasDF(plt, myDataDF, xKey, chartOptionsDict,plotOptionsDict)
    plt.legend(drawLegOutputs, drawLegLabels, prop={'size':28})
    #plt.show()
    myPdf.savefig()
    plt.close()
    
    #    ### now do runPeriodDF
    print 'Will draw average running time'
    chartOptionsDict = {'avgRunningMode': {'type': 'bar', 'color': 'gold', 'style': '-'}}
    plotOptionsDict = {'xlabel': 'Time', 'ylabel': 'Fraction Run Time', 'grid': True, 'doDates': True, 'figsize': (20,10),
        'xAxisFontSize': 25, 'yAxisFontSize': 25, 'xLabelSize': 35, 'yLabelSize': 35, 'xMarginXtra': 2.0}
    drawOutput = drawing.overlayChartsFromPandasDF(plt, myDataDF, xKey, chartOptionsDict, plotOptionsDict)
    myPdf.savefig()
    plt.close()
    
#    print 'Now draw performance plot'
#    chartOptionsDict = {'performance': {'type': 'bar', 'color': 'lightseagreen', 'style': '-'}}
#    plotOptionsDict = {'xlabel': 'Time', 'ylabel': 'Performance', 'grid': True, 'doDates': True,'figsize': (20,10),
#        'xAxisFontSize': 25, 'yAxisFontSize': 25, 'xLabelSize': 28, 'yLabelSize': 28, 'xMarginXtra': 2.0}
#    drawing.overlayChartsFromPandasDF(plt, runPeriodDF, 'beginRunTime', chartOptionsDict, plotOptionsDict)
#    myPdf.savefig()
#    plt.close()
    
    myPdf.close()



def getRunParameters(eventsInThisRun):
    def getPerformance(insideTemps, outsideTemps, duration):
        avgTempDiff = np.mean([outTemp - inTemp for inTemp, outTemp in zip(insideTemps, outsideTemps)])
        if(duration > 0.0001):
            performance = math.sqrt(max(0.01, avgTempDiff)) * (max(insideTemps) - min(insideTemps)) / duration
        else:
            performance = 0
        return performance
    
    runParameters = {}
    runParameters['beginRunTime'] = eventsInThisRun[0]['timeStamp']
    runParameters['endRunTime'] = eventsInThisRun[-1]['timeStamp']
    runParameters['duration'] = (eventsInThisRun[-1]['timeStamp'] -
                                 eventsInThisRun[0]['timeStamp']).total_seconds() / 60.
    insideTemps = [event['avgInsideTemp'] for event in eventsInThisRun]
    outsideTemps = [event['avgOutsideTemp'] for event in eventsInThisRun]
    runParameters['performance'] = getPerformance(insideTemps, outsideTemps, runParameters['duration'])
    return runParameters






#def checkForAlert(myDataDF, runPeriodDF):
def checkForAlert(myDataDF, runParameters):
    print 'checkforAlert'
    myEmail = 'pelin.kurt.4d@gmail.com'
    myPassword='xxxxxx'
    #eMailAddresses=['pelin.kurt.4d@gmail.com', 'mwchaney@gmail.com', 'scott@salusinc.com']
    eMailAddresses=['pelin.kurt.4d@gmail.com']
    
    #avgPerformance = np.mean(runPeriodDF['performance'])
    avgPerformance = np.mean(runParameters['performance'])
    print 'avgPerformance :', avgPerformance
    if avgPerformance < 30.:
        msgText = 'Performance alert. Average performance is '+str(avgPerformance)
        msgSubject = 'Alarm testing!!!'
        #makeAlert(msgText, msgSubject, myEmail, myPassword, eMailAddresses)


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
