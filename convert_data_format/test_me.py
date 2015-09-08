import parseJsonFile
myparser = parseJsonFile.parseJsonFile\
        (outputFileName="OutFile", inputFileName="input.json",
         alwaysSaveVars=[{'input': ['datapoint', 'created_at'], 'output':"timeStamp"},
                            {'input': ['metadata', 'dsn'], 'output': 'thermostatId'}],
         sometimesSaveVars=[{'input': 'Temperature', 'output': 'OutsideTemp'},
                            {'input': 'InsideTemperature', 'output': 'InsideTemp'},],
         bufferSizeLimit=1000
         )
myparser.streamFromFile()
