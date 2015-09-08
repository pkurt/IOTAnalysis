import numpy as np
import sys
import os
import math
import ast
import pandas as pd
import matplotlib.pyplot as plt
import copy as cp
import time
import json
import io
import datetime


class parseJsonFile():
    def __init__(self, outputFileName, inputFileName,
            alwaysSaveVars, sometimesSaveVars, bufferSizeLimit):
        ### Put member variables here:
        #self.jsonBuffer = []
        self.dataBuffer = []
        self.outputFileName = outputFileName
        self.inputFileName = inputFileName
        self.alwaysSaveVars = alwaysSaveVars
        self.sometimesSaveVars = sometimesSaveVars
        self.bufferSizeLimit = bufferSizeLimit

    def streamFromFile(self):
        ''' Loop over lines in the json file
        Create jsons and append to self.jsonBuffer
        Eventually, if self.jsonBuffer gets larger than
        self.bufferSizeLimit, save output results
        to file and clear buffer.
        '''
        
        with open(self.inputFileName) as f:
            for line in f:
                SanityCounter =0
                while True:
                    SanityCounter += 1
                    if SanityCounter > 1000:
                        print 'warning : could not form JSON'
                        break
                    try:
                        myjson = json.loads(line)
                        print 'about to append myjson: ', myjson
                        break
                    except ValueError:
                        # Not yet a complete JSON value
                        try:
                            line += next(f)
                        except Exception as ex:
                            pass
    
                dataToSave = self.convertData(myjson)
                print 'found some data to save: ', dataToSave
                # append jsons to self.jsonBuffer
                self.dataBuffer.append(dataToSave)
        print 'done with json file, final data to save buffer is : ', self.dataBuffer

    def convertData(self, myjson):
        ''' From full input json, extract data we care about,
        defined by alwaysSaveVars and sometimesSaveVars '''
        
        dataToSave = {}
        ### First extract alwaysSaveVars
        for varDef in self.alwaysSaveVars:
            ### varDef is a path to the variable inside the json
            searchLocation = myjson
            for step in varDef['input']:
                try:
                    searchLocation = searchLocation[step]
                except:
                    print 'Error, could not take step ', step,\
                        ' inside of json for variable ', varDef,\
                        ', and json ', myjson
                    searchLocation = None
                    break
            print 'Tried to find data for varDef: ', varDef
            print 'Result is ', searchLocation
            ### Now save variable result
            dataToSave[varDef['output']] = searchLocation

        ### Now extract sometimesSaveVars
        for varDef in self.sometimesSaveVars:
            valToSave = None
            try:
                if myjson['metadata']['display_name'] == varDef['input']:
                    valToSave = myjson['datapoint']['value']
            except:
                print 'Error trying to find variable defined by ', varDef, ', in myjson'
                valToSave = None
            dataToSave[varDef['output']] = valToSave

        ### Have extracted all data we care about. Now return.
        return dataToSave

    
    def saveOutput(self):
        ''' From data buffer create output dataframe
        Save outputDF to self.outputFileName
        Create output file if it does not already exist
        Otherwise append to output file
        Finally, clear self.dataBuffer '''

        print 'Now build pandas data frame'
        outDF = pd.DataFrame(self.dataBuffer)
        print 'outDF is ', outDF
        outDF.to_csv(self.outputFileName, index=False)


