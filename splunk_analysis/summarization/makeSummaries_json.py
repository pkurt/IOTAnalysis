import numpy as np
import sys
import os
import math
import splunklib.client as client
import splunklib.results as results
import pythonUtils.responseReaderWrapper as responseReaderWrapper
import copy as cp
import time
import io
import json
import datetime

def convertDateTimeStringToDate(dt):
    myDatetime = datetime.datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    myDateString = myDatetime.strftime("%Y-%m-%d")
    return myDateString

def fixBrokenTimeFormat(dtString):
    #### Example :
    #2014-11-18T00:00:00.000-08:00
    return dtString[:19]

# Add your function below!
#def main (thermostatId, StartTime, EndTime):
def main (argv):
    start_time = time.time()
    print 'Start of code'
    assert len(argv) == 5
    thermostatId = int(argv[1])
    startTime = argv[2]
    endTime = argv[3]
    ### Start time and end time have format "YYYY-mm-DDTHH:MM:ss"
    startTimeString = convertDateTimeStringToDate(startTime)
    endTimeString = convertDateTimeStringToDate(endTime)
    summaryType = argv[4]
    print 'thermostatId = ', thermostatId, ', startTime = ', startTime, ', endTime = ', endTime

    summaryDefinitions = {'daily': {'span': '1d'}, 'hourly': {'span': '1h'}, 'weekly': {'span': '1w'}, 'monthly': {'span': '1mon'} }
    assert summaryType in summaryDefinitions
    span = summaryDefinitions[summaryType]['span']

    summariesToDo = \
       [
         {'inVariable': 'InsideTemp', 'outVariable': 'maxInsideTemp', 'function': 'max'},
         {'inVariable': 'InsideTemp', 'outVariable': 'avgInsideTemp', 'function': 'avg'},
         {'inVariable': 'InsideTemp', 'outVariable': 'minInsideTemp', 'function': 'min'},
         {'inVariable': 'OutsideTemp', 'outVariable': 'avgOutsideTemp', 'function': 'avg'},
         {'inVariable': 'SetPoint', 'outVariable': 'avgSetPoint', 'function': 'avg'},
         {'inVariable': 'RunningMode', 'outVariable': 'avgRunningMode', 'function': 'avg'},
         {'inVariable': 'OutsideTemp', 'outVariable': 'maxOutsideTemp', 'function': 'max'},
         {'inVariable': 'OutsideTemp', 'outVariable': 'minOutsideTemp', 'function': 'min'},
         {'inVariable': 'performance', 'outVariable': 'avgPerformance', 'function': 'avg'},
         {'inVariable': 'duration', 'outVariable': 'avgDuration', 'function': 'avg'},
         {'inVariable': 'duration', 'outVariable': 'numCycles', 'function': 'count'}]

    searchReader = doSplunkSummarizationSearch(thermostatId, startTime, endTime, span, summariesToDo)
    print 'searchReader is '
    print searchReader
    outFileName = 'output/summary_'+summaryType+startTimeString+'_To_'+endTimeString+'.json'
    dumpSearchResults(searchReader, thermostatId, summariesToDo, outFileName)


def dumpSearchResults(searchReader, thermostatId, summariesToDo, outFileName):
    outFile = open(outFileName, 'w')
    for line in searchReader:
        jsonString = '{"id": '+str(thermostatId)
        #jsonString += ', "dataType": "dailyAggregatedSummary"'
        #jsonString += ', "dataType": "dailySummary"'
        #jsonString += ', "dataType": "weeklySummary"'
        jsonString += ', "dataType": "monthlySummary"'
        print 'line: ', line
        jsonString += ', "timeStamp": "'+ fixBrokenTimeFormat(line['_time'])+'", '
        for idx, summary in enumerate(summariesToDo):
            varName = summary['outVariable']
            print 'line is ', line, ', type: ', type(line)
            #value = line.get(varName, default=0)
            value = 0 if varName not in line else line[varName]
            jsonString += '"' + varName + '":'+str(value)
            if idx != len(summariesToDo)-1:
                jsonString += ', '
        jsonString += '},'

        outFile.write(jsonString+'\n')
    outFile.close()


#### Follow the example here: http://dev.splunk.com/view/python-sdk/SP-CAAAER5#reader
def doSplunkSummarizationSearch(thermostatId, StartTime, EndTime, span, summariesToDo):
        
    #### do splunk search
    #### output = splunkSearch(thermostatId, StartTime, EndTime)
    #### Organize into pandas dataFrame, myDataDF
    service = client.connect(host='localhost', port=8089, username='admin', password='Pg18december')
    #print 'got service, now make job'
    kwargs_oneshot={"earliest_time": StartTime,
                    "latest_time": EndTime,
                    "count": 0}
    statsStr = ''
    for summary in summariesToDo:
        statsStr += summary['function']+'('+summary['inVariable']+') as '+summary['outVariable']+' '
    jobSearchString= "search id="+str(thermostatId)+" AND (dataType=all OR dataType=runPeriods) | bucket _time span="+\
            span+" | stats " + statsStr + " by _time  | sort _time "
    print 'jobSearchString: ', jobSearchString
    job_results = service.jobs.oneshot(jobSearchString, **kwargs_oneshot)
    reader = results.ResultsReader(io.BufferedReader(responseReaderWrapper.ResponseReaderWrapper(job_results)))
    #reader = results.ResultsReader(job_results)
    return reader


if __name__ == "__main__":
    main(sys.argv)
