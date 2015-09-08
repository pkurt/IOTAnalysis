import parseJsonFile
myparser = parseJsonFile.parseJsonFile\
        (outputFileName="OutFile.csv", inputFileName="input.json",
         alwaysSaveVars=[{'input': ['datapoint', 'created_at'], 'output':"timeStamp"},
                            {'input': ['metadata', 'dsn'], 'output': 'thermostatId'},
                            {'input': ['metadata', 'property_name'], 'output': 'propertyName'}],
         
         sometimesSaveVars=[{'input': 'OutsideTemp', 'output': 'OutsideTemp'},
                            {'input': 'InsideTemp', 'output': 'InsideTemp'},
                            {'input': 'SetPoint', 'output': 'SetPoint'},
                            {'input': 'RunningMode', 'output': 'RunningMode'}],
         bufferSizeLimit=1000
         )
myparser.streamFromFile()
myparser.saveOutput()
