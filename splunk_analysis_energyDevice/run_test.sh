
export PYTHONPATH=/Users/PelinKurtGarberson/salusWork/IOTAnalysis/sdk_python/splunk-sdk-python-master/:/Users/PelinKurtGarberson/salusWork/IOTAnalysis/

#laundary-dryer with 12sec time resolution + 1sec test resolution with 5min test-duration
python electric_device_analysis.py '[1,2,3]' '2014-01-01T00:00:00' '2014-01-10T00:00:00'

#hairdryer:

#microwave:

#blender:

#lightbulb:

#### OLD:
#python electric_device_analysis.py 100 '2014-01-01T00:00:00' '2015-01-01T00:00:00'
#python electric_device_analysis.py 100 '2014-01-01T00:00:00' '2014-01-05T00:00:00'

#python electric_device_analysis.py 102 '2014-01-01T00:00:00' '2015-01-01T00:00:00'

#laundary-dryer
#python electric_device_analysis.py 102 '2014-01-01T00:00:00' '2014-01-20T00:00:00'

#hairdryer:
#python electric_device_analysis.py 103 '2014-01-01T00:00:00' '2014-01-20T00:00:00'

#microwave:
#python electric_device_analysis.py 106 '2014-01-01T00:00:00' '2014-01-20T00:00:00'

#blender:
#python electric_device_analysis.py 104 '2014-01-01T00:00:00' '2014-01-20T00:00:00'

#lightbulb:
#python electric_device_analysis.py 105 '2014-01-01T00:00:00' '2014-01-20T00:00:00'
#python electric_device_analysis.py 105 '2014-01-01T00:00:00' '2014-05-01T00:00:00'
#python electric_device_analysis.py '[105]' '2014-01-01T00:00:00' '2015-01-01T00:00:00'
