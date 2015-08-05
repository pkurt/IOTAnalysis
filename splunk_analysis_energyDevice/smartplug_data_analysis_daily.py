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
    #print 'now getRunPeriodDF'
    sys.stdout.flush()
    runPeriodDF = getRunPeriodDF(myDataDF)
    #dashboard_performance_plots(myDataDF, runPeriodDF)
    #checkForAlert(myDataDF, runPeriodDF)
    #print 'runPeriodDF: ', runPeriodDF
    runtime = time.time() - start_time
    sys.stdout.flush()
    print 'It took ', str(runtime), ' to run'
    sys.stdout.flush()


def getRunPeriodDF(myDataDF):
    listOfRunPeriods = []
    previousMode = 0
    eventsInThisRun = []
    for thisIdx, thisEvent in myDataDF.iterrows():
        isRunning = thisEvent['avgRunningMode']
        if previousMode == 1 and isRunning == False:
            runParameters = getRunParameters(eventsInThisRun)
            endRunTime = thisEvent['timeStamp']
            thisRunPeriod = {'beginRunTime': runParameters['beginRunTime'], 'endRunTime': runParameters['endRunTime']}
            listOfRunPeriods.append(thisRunPeriod)
            eventsInThisRun = []
        if isRunning:
            eventsInThisRun.append(thisEvent)
        previousMode = thisEvent['avgRunningMode']
    
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

if __name__ == "__main__":
    main(sys.argv)
