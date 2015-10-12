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
import pandas as pd

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
         {'inVariable': 'InsideTemp', 'outVariable': 'maxInsideTemp', 'function': 'max', 'doTimeWeight': False},
         {'inVariable': 'InsideTemp', 'outVariable': 'avgInsideTemp', 'function': 'avg', 'doTimeWeight': True},
         {'inVariable': 'InsideTemp', 'outVariable': 'minInsideTemp', 'function': 'min', 'doTimeWeight': False},
         {'inVariable': 'OutsideTemp', 'outVariable': 'avgOutsideTemp', 'function': 'avg', 'doTimeWeight': True},
         {'inVariable': 'SetPoint', 'outVariable': 'avgSetPoint', 'function': 'avg', 'doTimeWeight': True},
         {'inVariable': 'RunningMode', 'outVariable': 'avgRunningMode', 'function': 'avg', 'doTimeWeight': True},
         {'inVariable': 'OutsideTemp', 'outVariable': 'maxOutsideTemp', 'function': 'max', 'doTimeWeight': False},
         {'inVariable': 'OutsideTemp', 'outVariable': 'minOutsideTemp', 'function': 'min', 'doTimeWeight': False},
         {'inVariable': 'performance', 'outVariable': 'avgPerformance', 'function': 'avg', 'doTimeWeight': False},
         {'inVariable': 'duration', 'outVariable': 'avgDuration', 'function': 'avg', 'doTimeWeight': False},
         {'inVariable': 'duration', 'outVariable': 'numCycles', 'function': 'count', 'doTimeWeight': False}]

    searchReader = doSplunkSummarizationSearch(thermostatId, startTime, endTime, span, summariesToDo)
    print 'searchReader is '
    print searchReader
    #outFileName = 'output/summary_'+summaryType+startTimeString+'_To_'+endTimeString+'.json'
    outFileName = 'output/summary_'+summaryType+startTimeString+'_To_'+endTimeString+'_id'+str(thermostatId)+'.csv'
    
    #dumpSearchResults(searchReader, thermostatId, summariesToDo, outFileName)
    myDataDF = getPandasDF(searchReader)
    myDataDF['id'] = [thermostatId]*len(myDataDF.index)
    #myDataDF['dataType'] = "monthlySummary"
    #myDataDF['dataType'] = "weeklySummary"
    myDataDF['dataType'] = "dailySummary"
    pd.set_option('precision',3)
    myDataDF.to_csv(outFileName, index=False, float_format='%.3f', columns=['id', 'dataType', 'timeStamp', 'avgDuration','avgInsideTemp',
        'avgOutsideTemp','avgPerformance','avgRunningMode','avgSetPoint',
        'maxInsideTemp','maxOutsideTemp','minInsideTemp','minOutsideTemp','numCycles'])

def getPandasDF(searchReader):
    myData = []
    for line in searchReader:
        myData.append(line)
    myDataDF = pd.DataFrame(myData)
    # to fill missing NAN valuesc??????????????????????
    #myDataDF = myDataDF.fillna(method='pad')
    myDataDF['timeStamp'] = pd.to_datetime([fixBrokenTimeFormat(ele) for ele in myDataDF['_time']])
    sys.stdout.flush()
    myDataDF = myDataDF.sort('timeStamp')
    sys.stdout.flush()
    return myDataDF


def dumpSearchResults(searchReader, thermostatId, summariesToDo, outFileName):
    #outFile = open(outFileName, 'w')
    print 'searchReader has type: ', type(searchReader)
    for line in searchReader:
        jsonString = '{"id": '+str(thermostatId)
        jsonString += ', "dataType": "dailySummary"'
        #jsonString += ', "dataType": "weeklySummary"'
        #jsonString += ', "dataType": "monthlySummary"'
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

        #outFile.write(jsonString+'\n')
   # outFile.close()


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
    timeWeightStr = ''
    if span == '1h': nSeconds = 60.*60.
    if span == '1d': nSeconds = 24.*60.*60.
    if span == '1w': nSeconds = 7.*24.*60.*60.
    postStr = ''

    #### Here's the trick to handle both (a) missing data and (b) variable spacing in time series:
    ## Determine nSeconds, fill in here:
    # id=56 AND (dataType=fullSim) | sort timeStamp | delta _time as deltaTime |
    #### Then loop over variables like this:
    # streamstats last(RunningMode) as lastRunningMode |
    # eval timeWtRunningMode = deltaTime*lastRunningMode / (nSeconds) |
    # streamstats last(InsideTemp) as lastInsideTemp |
    # eval timeWtInsideTemp = deltaTime*lastInsideTemp / (nSeconds) | bucket _time span=1d |
    # stats avg(lastRunningMode), avg(deltaTime), sum(timeWtRunningMode), avg(lastInsideTemp) by _time
    ####
#'doTimeWeight'
    for summary in summariesToDo:
        if summary['doTimeWeight']:
            timeWeightStr += 'streamstats last('+summary['inVariable']+') as last'+summary['inVariable']+' | '
            timeWeightStr += 'eval timeWt'+summary['inVariable']+' = deltaTime*last'\
                    +summary['inVariable']+ ' | '
            #### Just add the "timeWt" in front of inVariable this case
            if summary['function'] == 'avg':
                statsStr += 'sum(timeWt'+summary['inVariable']+') as sum'+summary['inVariable']+' '
                postStr += ' | eval '+summary['outVariable']+' =  sum'+summary['inVariable']+' / sumDeltaTime'
            else:
                print 'Error, have not implemented time-weighted averages for function '+summary['function']
                assert 0
        else:
            statsStr += summary['function']+'('+summary['inVariable']+') as '+summary['outVariable']+' '
    jobSearchString= "search id="+str(thermostatId)+" AND (dataType=fullSim OR dataType=runPeriod) | sort _time | "+\
            " delta _time as deltaTime | " + timeWeightStr + " bucket _time span="+\
            span+" | stats sum(deltaTime) as sumDeltaTime " + statsStr + " by _time"+postStr
    
    #jobSearchString= "search id="+str(thermostatId)+" AND (dataType=fullSim OR dataType=runPeriod) | bucket _time span="+\
    #        span+" | stats " + statsStr + " by _time  | sort _time "
    print 'jobSearchString: ', jobSearchString
    job_results = service.jobs.oneshot(jobSearchString, **kwargs_oneshot)
    reader = results.ResultsReader(io.BufferedReader(responseReaderWrapper.ResponseReaderWrapper(job_results)))
    #reader = results.ResultsReader(job_results)
    return reader


if __name__ == "__main__":
    main(sys.argv)
