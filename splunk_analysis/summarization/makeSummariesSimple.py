import numpy as np
import sys
#sys.path.append('/Users/pelinkurtgarberson/Desktop/splunk_analysis/')
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
    ###
    startTimeString = convertDateTimeStringToDate(startTime)
    endTimeString = convertDateTimeStringToDate(endTime)
    summaryType = argv[4]
    print 'thermostatId = ', thermostatId, ', startTime = ', startTime, ', endTime = ', endTime

    summaryDefinitions = {'daily': {'span': '1d'}, 'hourly': {'span': '1h'}, 'weekly': {'span': '1w'}}
    assert summaryType in summaryDefinitions
    span = summaryDefinitions[summaryType]['span']
    summariesToDo = \
            [{'inVariable': 'InsideTemp', 'outVariable': 'avgInsideTemp', 'function': 'avg'},
             {'inVariable': 'OutsideTemp', 'outVariable': 'avgOutsideTemp', 'function': 'avg'},
             {'inVariable': 'SetPoint', 'outVariable': 'avgSetPoint', 'function': 'avg'},
             {'inVariable': 'RunningMode', 'outVariable': 'avgRunningMode', 'function': 'avg'},
             {'inVariable': 'OutsideTemp', 'outVariable': 'maxOutsideTemp', 'function': 'max'},
             {'inVariable': 'OutsideTemp', 'outVariable': 'minOutsideTemp', 'function': 'min'}]
    
    
    searchReader = doSplunkSummarizationSearch(thermostatId, startTime, endTime, span, summariesToDo)
    print 'searchReader is '
    print searchReader
    outFileName = 'output/summary_'+summaryType+startTimeString+'_To_'+endTimeString+'.json'
    dumpSearchResults(searchReader, thermostatId, summariesToDo, outFileName)


def dumpSearchResults(searchReader, thermostatId, summariesToDo, outFileName):
    outFile = open(outFileName, 'w')
    for line in searchReader:
        #jsonString = '{"id": '+str(thermostatId)
        jsonString = '{"id":14'
        jsonString += ', "dataType": "dailySummary"'
        print 'line: ', line
        jsonString += ', "timeStamp": "'+ fixBrokenTimeFormat(line['_time'])+'", '
        for idx, summary in enumerate(summariesToDo):
            varName = summary['outVariable']
            jsonString += '"' + varName + '":'+line[varName]
            if idx != len(summariesToDo)-1:
                jsonString += ', '
        jsonString += '},'

        outFile.write(jsonString+'\n')
    outFile.close()

        #OrderedDict([('_time', '2014-12-03T00:00:00.000-08:00'), ('avg(InsideTemp)', '76.669419'), ('avg(OutsideTemp)', '80.871817'), ('avg(SetPoint)', '78.000000'), ('avg(RunningMode)', '0.168056'), ('max(OutsideTemp)', '92.4887750601'), ('min(OutsideTemp)', '71.5152583980')])

#### Follow the example here: http://dev.splunk.com/view/python-sdk/SP-CAAAER5#reader
def doSplunkSummarizationSearch(thermostatId, StartTime, EndTime, span, summariesToDo):
        
    #### do splunk search
    #### output = splunkSearch(thermostatId, StartTime, EndTime)
    #### Organize into pandas dataFrame, myDataDF
    service = client.connect(host='localhost', port=8089, username='admin', password='xxxxxx')
    #print 'got service, now make job'
    kwargs_oneshot={"earliest_time": StartTime,
                    "latest_time": EndTime,
                    "count": 0}
    statsStr = ''
    for summary in summariesToDo:
        statsStr += summary['function']+'('+summary['inVariable']+') as '+summary['outVariable']+' '
    jobSearchString= "search id="+str(thermostatId)+" | bucket _time span="+span+" | stats " + statsStr + " by _time  | sort _time "
    print 'jobSearchString: ', jobSearchString
    job_results = service.jobs.oneshot(jobSearchString, **kwargs_oneshot)
    reader = results.ResultsReader(io.BufferedReader(responseReaderWrapper.ResponseReaderWrapper(job_results)))
    #reader = results.ResultsReader(job_results)
    return reader


if __name__ == "__main__":
    main(sys.argv)
