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

def convertStringToList(myStr, dtype):
    ''' Assume we have been given a string of a list.
        Extract and return the list
        dtype: this will be the type of the list elements
        '''
    assert myStr[0] == '['
    assert myStr[-1] == ']'
    ### Convert string of '[1,2,3]' to '1,2,3'
    contents = myStr[1:-1]
    ### Now split string into list ('1,2,3' => ['1', '2', '3'])
    myStringList = contents.split(',')
    ### Now convert to proper data type
    outputList = [dtype(ele) for ele in myStringList]
    return outputList


# Add your function below!
#def main (electricDeviceIdList, StartTime, EndTime):
def main (argv):
    start_time = time.time()
    print 'Start of code'
    assert len(argv) == 5
    #electricDeviceId = int(argv[1])
    electricDeviceIdList = convertStringToList(argv[1], dtype=int)
    startTime = argv[2]
    endTime = argv[3]
    ### Start time and end time have format "YYYY-mm-DDTHH:MM:ss"
    startTimeString = convertDateTimeStringToDate(startTime)
    endTimeString = convertDateTimeStringToDate(endTime)
    summaryType = argv[4]

    summaryDefinitions = {'dailyAggregated': {'span': '1d'}, 'hourlyAggregated': {'span': '1h'}, 'weeklyAggregated': {'span': '1w'}, 'monthlyAggregated': {'span': '1mon'} }
    assert summaryType in summaryDefinitions
    span = summaryDefinitions[summaryType]['span']

    summariesToDo = \
       [
         {'inVariable': 'powerUsage', 'outVariable': 'maxPowerUsage', 'function': 'max', 'doTimeWeight': False},
         {'inVariable': 'powerUsage', 'outVariable': 'avgPowerUsage', 'function': 'avg', 'doTimeWeight': True},
         {'inVariable': 'powerUsage', 'outVariable': 'minPowerUsage', 'function': 'min', 'doTimeWeight': False}, 
         {'inVariable': 'isTesting', 'outVariable': 'avgIsTesting', 'function': 'avg', 'doTimeWeight': True}
        ]
    
    searchReader = doSplunkSummarizationSearch(electricDeviceIdList, startTime, endTime, span, summariesToDo)
    print 'searchReader is '
    print searchReader
    outFileName = 'output/ElectricDeviceSummary_'+summaryType+startTimeString+'_To_'+endTimeString+'.json'
    outFileNameCSV = 'output/summary_'+summaryType+startTimeString+'_To_'+endTimeString+'.csv'
    
    dumpSearchResults(searchReader, electricDeviceIdList, summariesToDo, outFileName)
   
    irregTimeSeriesToSelect = ['avgPowerUsage', 'maxPowerUsage', 'minPowerUsage']
    bothColsToSelect = ['id', 'dataType', 'timeStamp']


    #myDataDF = getPandasDF(searchReader, fillColsNAFor=irregTimeSeriesToSelect)
    myDataDF = getPandasDF(searchReader)
    myDataDF['dataType'] = "dailyAggSummary"
    pd.set_option('precision',3)

    allColsToSelect = bothColsToSelect + irregTimeSeriesToSelect
    myDataDF.to_csv(outFileNameCSV, index=False, float_format='%.3f', columns=allColsToSelect)

#def getPandasDF(searchReader, fillColsNAFor):
def getPandasDF(searchReader):

    myData = []
    for line in searchReader:
        myData.append(line)
    myDataDF = pd.DataFrame(myData)
    #myDataDF[fillColsNAFor] = myDataDF[fillColsNAFor].fillna(method='pad')
    #myDataDF['timeStamp'] = pd.to_datetime([fixBrokenTimeFormat(ele) for ele in myDataDF['timeStamp']])
    sys.stdout.flush()
    #myDataDF = myDataDF.sort(['id', 'timeStamp'])
    sys.stdout.flush()
    return myDataDF


def dumpSearchResults(searchReader, electricDeviceIdList, summariesToDo, outFileName):
    outFile = open(outFileName, 'w')
    print 'searchReader has type: ', type(searchReader)
    for line in searchReader:
        for myID in electricDeviceIdList:
            jsonString = '{"id": '+str(myID)
            jsonString += ', "dataType ":"dailySummary"'

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
def doSplunkSummarizationSearch(electricDeviceIdList, StartTime, EndTime, span, summariesToDo):
        
    #### do splunk search
    #### Organize into pandas dataFrame, myDataDF
    service = client.connect(host='localhost', port=8089, username='admin', password='Pg18december')
    #print 'got service, now make job'
    kwargs_oneshot={"earliest_time": StartTime,
                    "latest_time": EndTime,
                    "count": 0}

    statsStr = ''

    for summary in summariesToDo:
        statsStr += summary['function']+'('+summary['inVariable']+') as '+summary['outVariable']+' '

    idSelectionRequirements = []
    for myID in electricDeviceIdList:
        thisIDStr = 'id='+str(myID)
        idSelectionRequirements.append(thisIDStr)
    idSelectionStr = '('+(' OR '.join(idSelectionRequirements))+')'
    jobSearchString= "search "+idSelectionStr+" | bucket _time span="+span+" | stats " + statsStr + " by _time  | sort _time "

    print 'jobSearchString: ', jobSearchString
    job_results = service.jobs.oneshot(jobSearchString, **kwargs_oneshot)
    reader = results.ResultsReader(io.BufferedReader(responseReaderWrapper.ResponseReaderWrapper(job_results)))
    return reader



if __name__ == "__main__":
    main(sys.argv)
