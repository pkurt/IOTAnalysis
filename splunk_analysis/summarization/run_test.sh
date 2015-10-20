export PYTHONPATH=/Users/pelinkurtgarberson/Desktop/sdk_python/splunk-sdk-python-master/:/Users/pelinkurtgarberson/IOTAnalysis

#ipython makeSummaries.py 30 '2014-07-01T00:00:00' '2014-09-08T00:00:00' daily
#python makeSummaries.py 30 '2014-01-01T00:00:00' '2015-01-01T00:00:00' daily
#python makeSummaries.py 30 '2014-01-01T00:00:00' '2015-01-01T00:00:00' weekly
#python makeSummaries.py 30 '2014-01-01T00:00:00' '2015-01-01T00:00:00' monthly

#python makeSummaries.py 56 '2014-07-29T00:00:00' '2014-08-06T00:00:00' daily
python makeSummaries.py '[68,69]' '2014-01-01T00:00:00' '2015-01-01T00:00:00' dailyAgg
#python makeSummaries.py '[68,69,70,71]' '2014-01-01T00:00:00' '2015-01-01T00:00:00' dailyAgg
