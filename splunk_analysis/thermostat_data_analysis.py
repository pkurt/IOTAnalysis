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
import multiprocessing as mp
import logging
logger = mp.log_to_stderr(logging.INFO)

def convertSafely(ele, desiredType):
    if desiredType is None:
        return ele
    try:
        return desiredType(ele)
    except:
        return np.nan


# Add functions below!
def main (argv):
    print 'default buffer size: ', io.DEFAULT_BUFFER_SIZE
    #io.DEFAULT_BUFFER_SIZE = 16
    start_time = time.time()
    print 'Start of code'
    assert len(argv) == 5
    thermostatId = int(argv[1])
    StartTime = argv[2]
    EndTime = argv[3]
    DataType = argv[4]
    
    OutDataType="runPeriod"

    print 'thermostatId = ', thermostatId, ', startTime = ', StartTime, ', endTime = ', EndTime
    #searchReader = doSplunkSearch(thermostatId, StartTime, EndTime, DataType)
    myDataDF = doSplunkSearch(thermostatId, StartTime, EndTime, DataType)
    
    print 'pandas data DF:'
    print myDataDF
    sys.stdout.flush()
    print 'now getRunPeriodDF'
    sys.stdout.flush()
    runPeriodDF = getRunPeriodDF(myDataDF)
    if len(runPeriodDF.index)> 0:
        dashboard_performance_plots(myDataDF, runPeriodDF)
        checkForAlert(myDataDF, runPeriodDF)
        #print 'runPeriodDF: ', runPeriodDF
        sys.stdout.flush()
    runtime = time.time() - start_time
    print 'It took ', str(runtime), ' to run'
    sys.stdout.flush()

### added to get json output
    outFileName = 'output/summary_performance_'+StartTime[0:10]+'_To_'+EndTime[0:10]+'_id'+str(thermostatId)+'.json'
    columnsToSave = [{'var':'beginRunTime', 'type':str}, {'var':'endRunTime', 'type':str},
            {'var':'duration', 'type':float}, {'var':'performance', 'type':float}]
    dumpRunPeriodResults(runPeriodDF, thermostatId, columnsToSave, outFileName)


### initialize header for output .csv file:
    outFileNameCSV = 'output/summary_performance_'+StartTime[0:10]+'_To_'+EndTime[0:10]+'_id'+str(thermostatId)+'.csv'
    csvColumns = ['id', 'beginRunTime', 'endRunTime','dataType', 'performance', 'duration']
    sizeOfDF = len(runPeriodDF.index)
    runPeriodDF['id'] = [thermostatId]*sizeOfDF
    runPeriodDF['dataType'] = [OutDataType]*sizeOfDF
    runPeriodDF.to_csv(outFileNameCSV, sep=',', columns=csvColumns, header=True, index=False)




def getRunPeriodDF(myDataDF):
    listOfRunPeriods = []
    print 'getRunPeriodDF'
    previousMode = 0
    eventsInThisRun = []
    for thisIdx, thisEvent in myDataDF.iterrows():
        try:
            isRunning = int(thisEvent['RunningMode'])
        except:
            isRunning = 0

        if previousMode == 1 and isRunning == 0:
            print 'Append run period'
            runParameters = getRunParameters(eventsInThisRun)
            endRunTime = thisEvent['timeStamp']
            thisRunPeriod = {'beginRunTime': runParameters['beginRunTime'], 'endRunTime': runParameters['endRunTime'],
                    'duration': runParameters['duration'], 'performance': runParameters['performance']}
            listOfRunPeriods.append(thisRunPeriod)
            print 'listOfRunPeriods is now: ', listOfRunPeriods

            ### Clear events from this run to look for new one:
            eventsInThisRun = []
        if isRunning==1:
            eventsInThisRun.append(thisEvent)
        try:
            previousMode = int(thisEvent['RunningMode'])
        except:
            previousMode = 0
       #def getPerformance(InsideTemp,OutsideTemp,Duration):
    
    #### Got all run periods, now build pandas dataframe
    print 'Define runPeriodDF from ', listOfRunPeriods
    runPeriodDF = pd.DataFrame(listOfRunPeriods)
    return runPeriodDF
    logger.info('Returning None')


            

def getPandasDF(searchReader):
    #print 'getPandasDF'
    myData = []
    #print 'read data in getPandasDF'
    sys.stdout.flush()


    lineNum = 0
    print 'searchReader has type: ', type(searchReader)
    for line in searchReader:
        #print 'line: ', line
        #thisDict = json.loads(line['_raw'])
        #myData.append(thisDict)
        #thisDict = json.loads(line)
        myData.append(line)
        lineNum += 1
        #print 'this row is: ', thisDict
        #print 'thisInsideTemp is: ', thisDict['InsideTemp']
    #print 'get pandas Dataframe'
    myDataDF = pd.DataFrame(myData)
    #print 'myDataDF: ', myDataDF

    #myDataDF[['RunningMode', 'id']].astype(int)
    #myDataDF[['InsideTemp', 'OutsideTemp', 'Setpoint']].astype(float)
    # to fill missing NAN values
    myDataDF = myDataDF.fillna(method='pad')
    expectedTypes = {'RunningMode': int,
                     'id': int,
                     'InsideTemp': float,
                     'OutsideTemp': float,
                     'SetPoint': float}
    ### convert types:
    for col in myDataDF.columns.values:
        desiredType = expectedTypes.get(col, None)
        myDataDF[col] = [convertSafely(ele, desiredType) for ele in myDataDF[col].values]

    #print 'got pandas dataframe: ', myDataDF
    #print 'got pandas dataframe: ', myDataDF.fillna(method='pad')
    myDataDF['timeStamp'] = pd.to_datetime(myDataDF['timeStamp'])
   # print 'sort data in getPandasDF'
    sys.stdout.flush()
    myDataDF = myDataDF.sort('timeStamp')
    #print 'Full pandas data = ', myDataDF
    #print 'Data where it is running = ', myDataDF[myDataDF['RunningMode'] == 1]
    #print 'Data where outsidetemp > 78 degrees = ', myDataDF[myDataDF['OutsideTemp'] > 78.]
  #  print 'Return myDataDF'
    print 'TotalLineNumber :', lineNum
    sys.stdout.flush()
    return myDataDF

#### Follow the example here: http://dev.splunk.com/view/python-sdk/SP-CAAAER5#reader
def doSplunkSearch(thermostatId, StartTime, EndTime, DataType):
        
    #### do splunk search
    #### output = splunkSearch(thermostatId, StartTime, EndTime)
    #### Organize into pandas dataFrame, myDataDF
    print 'start of doSplunkSearch'
    sys.stdout.flush()
    service = client.connect(host='localhost', port=8089, username='admin', password='Pg18december')
    #jobSearchString= "search id="+str(thermostatId)+" dataType="+str(DataType)+" | sort 0 _time | table _raw"
    jobSearchString= "search id="+str(thermostatId)+" dataType="+str(DataType)+" | sort 0 _time | table id timeStamp InsideTemp OutsideTemp SetPoint RunningMode"
    #jobSearchString= "search id="+str(thermostatId)+" dataType="+str(DataType)+" | sort 0 _time"
                     #table _time InsideTemp OutsideTemp SetPoint RunningMode
    job = service.jobs.create(jobSearchString, **{"exec_mode": "blocking",
                                                  "earliest_time": StartTime,
                                                  "latest_time": EndTime,
                                                  "maxEvents": 5000000})
    print 'created job'
    sys.stdout.flush()
    resultCount = int(job["resultCount"])
    offset = 0   ## start at result 0
    count = 50000    # Get sets of this many results at one time
    thru_counter = 0

    resultingDF = None
    print 'print loop with resultCount = ', resultCount
    sys.stdout.flush()
    while(offset < resultCount):
        print 'Do group starting at offset ', offset
        sys.stdout.flush()
        kwargs_paginate = {"count": count, "offset": offset}

        rs = job.results(**kwargs_paginate)
        reader = results.ResultsReader(io.BufferedReader(rs))

        if offset == 0:   ### first time
            print 'Before getting original DF'
            sys.stdout.flush()
            resultingDF = getPandasDF(reader)
            print 'got original DF'
            sys.stdout.flush()
        else:
            print 'Before adding DF, resultingDF: ', resultingDF
            sys.stdout.flush()
            resultingDF = resultingDF.append(getPandasDF(reader), ignore_index=True)
        offset += count
        print 'After adding DF, resultingDF: ', resultingDF
        sys.stdout.flush()
    print 'Done with splunk search'
    sys.stdout.flush()
    return resultingDF


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
    print 'Will draw duration from runPeriodDF: ', runPeriodDF
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

    #print 'getRunParameters for events: ', eventsInThisRun
    runParameters = {}
    runParameters['beginRunTime'] = eventsInThisRun[0]['timeStamp']
    runParameters['endRunTime'] = eventsInThisRun[-1]['timeStamp']
    runParameters['duration'] = (eventsInThisRun[-1]['timeStamp'] -
                eventsInThisRun[0]['timeStamp']).total_seconds() / 60.
    #print 'duration: ', runParameters['duration']
    insideTemps = [event['InsideTemp'] for event in eventsInThisRun]
    outsideTemps = [event['OutsideTemp'] for event in eventsInThisRun]
    runParameters['performance'] = getPerformance(insideTemps, outsideTemps, runParameters['duration'])
    return runParameters
    
    


### write the output in JSON format
def dumpRunPeriodResults(runPeriodDF, thermostatId, columnsToSave, outFileName):
    outFile = open(outFileName, 'w')
    for idx, row in runPeriodDF.iterrows():
        jsonString = '{"id": '+str(thermostatId)
        jsonString += ', "dataType": "runPeriod"'
        for column in columnsToSave:
            if column['type'] != str:
                jsonString += ', "'+column['var']+'": '+str(row[column['var']])
            else:
                jsonString += ', "'+column['var']+'": "'+str(row[column['var']])+'"'
        jsonString += '},\n'
        outFile.write(jsonString)
    outFile.close()




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


### HVAC FAULT DETECTION ###

#Baseline data to be presented to the consumer with HFD:
#   Date of first detected fault
#   Frequency within a single dat of fault
#   Number of consecutive days with a fault
#   What system is having the issue

#How to consider if a system is having an issue:
#   Aggregated for date time and night time for the past month AND the past week 
#   Average Outdoor temperature
#   Average indoor temperature
#   Customer interactions with the thermostat
#   Of the total run time, what % did not reach the desired set point prior to a scheduled set point change
#   At the average outdoor and indoor temperature delta, what is the average run time required to change the interior temp by 3 degrees F
#   What is the average number of times the system cycled in a given hour

# Things to work on next:
#1. an analysis to determine if a user has a bad schedule. (what % did not reach the desired set point prior to a scheduled set point change)
#2. an analysis to determine the average run time required to change the interior temperature 3F.
#3. Running aggregations for 1 termostat for all time. It will run alll those termostat aggregations daily and load into splunk...
#4. Update to use Mike's data format...


    
 

