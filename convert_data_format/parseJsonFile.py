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
            variableNamesToSave, bufferSizeLimit):
        ### Put member variables here:
        self.jsonBuffer = []
        self.outputFileName = outputFileName
        self.inputFileName = inputFileName
        self.variableNamesToSave = variableNamesToSave
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
                        line += next(f)
    
                # do something with jfile
                # append jsons to self.jsonBuffer
                self.jsonBuffer.append(myjson)
        print 'done with json file, final buffer is : ', self.jsonBuffer


    
    def saveOutput(self):
        ''' From json buffer create output dataframe
        Save outputDF to self.outputFileName
        Create output file if it does not already exist
        Otherwise append to output file
        Finally, clear self.jsonBuffer '''

        pass

