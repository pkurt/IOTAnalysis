#python stream_data.py --startTime 2014-01-01 --endTime 2015-01-01\
#   --timeStepSeconds 300 --testTimeStepSeconds 1 --outFileName energySim_v2.json\
#   --deviceType LDryer --deviceTestTime 60 --preTestTime 10 --postTestTime 10\
#   --probTestPerDay 0.2 --houseId 102
python stream_data.py --startTime 2014-01-01 --endTime 2015-01-01\
   --timeStepSeconds 300 --testTimeStepSeconds 1 --outFileName energySim_HDryer.json\
   --deviceType HDryer --deviceTestTime 60 --preTestTime 10 --postTestTime 10\
   --probTestPerDay 0.2 --houseId 103
python stream_data.py --startTime 2014-01-01 --endTime 2015-01-01\
   --timeStepSeconds 300 --testTimeStepSeconds 1 --outFileName energySim_Blender.json\
   --deviceType Blender --deviceTestTime 60 --preTestTime 10 --postTestTime 10\
   --probTestPerDay 0.2 --houseId 104
python stream_data.py --startTime 2014-01-01 --endTime 2015-01-01\
   --timeStepSeconds 300 --testTimeStepSeconds 1 --outFileName energySim_LightBulb.json\
   --deviceType LightBulb --deviceTestTime 60 --preTestTime 10 --postTestTime 10\
   --probTestPerDay 0.2 --houseId 105
python stream_data.py --startTime 2014-01-01 --endTime 2015-01-01\
   --timeStepSeconds 300 --testTimeStepSeconds 1 --outFileName energySim_Microwave.json\
   --deviceType Microwave --deviceTestTime 60 --preTestTime 10 --postTestTime 10\
   --probTestPerDay 0.2 --houseId 106
