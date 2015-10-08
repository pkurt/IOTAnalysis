#export PYTHONPATH=/Users/pelinkurtgarberson/Desktop/sdk_python/splunk-sdk-python-master/:/Users/pelinkurtgarberson/IOTAnalysis
export PYTHONPATH=/Users/pelinkurtgarberson/IOTAnalysis/sdk_python/splunk-sdk-python-master/:/Users/pelinkurtgarberson/IOTAnalysis

#python thermostat_data_analysis_os.py 30 '2014-07-01T00:00:00' '2014-08-01T00:00:00' 'all'
#python thermostat_data_analysis.py 30 '2014-07-01T00:00:00' '2014-08-01T00:00:00' 'all'
#python thermostat_data_analysis.py 30 '2014-01-01T00:00:00' '2015-01-01T00:00:00' 'all'

python thermostat_data_analysis.py 56 '2014-01-01T00:00:00' '2015-01-01T00:00:00' 'fullSim'
#python thermostat_data_analysis.py 56 '2014-08-01T00:00:00' '2015-09-01T00:00:00' 'fullSim'
