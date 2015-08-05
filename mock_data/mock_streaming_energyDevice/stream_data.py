import datetime
import time
import random
import sys
import argparse



def get_power_for_time(hour, minute):
    def getSmoothTransition(initVal, finalVal, initTime, finalTime, currentTime):
        return initVal + ((finalVal - initVal) * (currentTime-initTime) / (finalTime - initTime))
    min_power_used = None
    max_power_used = None
    min_power_used = 1200.
    max_power_used = 2000.
    
    power_range = max_power_used - min_power_used
    eff_hour = hour+(minute / 60.)
    if eff_hour >= 0 and eff_hour < 5: power_used = min_power_used
    elif eff_hour >= 5. and eff_hour < 9.: power_used = getSmoothTransition(min_power_used, max_power_used, 5., 9., eff_hour)
    elif eff_hour >= 9. and eff_hour < 10: power_used = getSmoothTransition(max_power_used, min_power_used, 9., 10., eff_hour)
    elif eff_hour >= 10. and eff_hour < 17.: power_used = min_power_used
    elif eff_hour >= 17 and eff_hour < 19.: power_used = getSmoothTransition(min_power_used, max_power_used, 17., 19., eff_hour)
    elif eff_hour >= 19 and eff_hour < 23.: power_used = getSmoothTransition(max_power_used, min_power_used, 19., 23., eff_hour)
    elif eff_hour >= 23.: power_used = min_power_used
    short_power_out_offset = random.gauss(0, 50.)
    power_used += short_power_out_offset
    return power_used


def main(parser):
#    assert len(argv) == 4
#    startTime=datetime.datetime.strptime(argv[0], '%Y-%m-%d')
#    endTime=datetime.datetime.strptime(argv[1], '%Y-%m-%d')
#    timeStepSeconds = int(argv[2])
#    testTimeStepSeconds = int(argv[3])
#    outFileName = argv[4]

    deviceTypes = {'LDryer': {'power': 3000.},
                   'HDryer': {'power': 1875.},
                   'Blender': {'power': 300.},
                   'LightBulb': {'power': 60.},
                   'Microwave': {'power': 800.},
                  }

    inArgs = parser.parse_args()
    print 'inArgs: ', inArgs
    assert inArgs.deviceType in deviceTypes

    secondsPerDay = 24.*3600.
    probPerTimeStep = inArgs.probTestPerDay * inArgs.timeStepSeconds / secondsPerDay

    out_file_init = open(inArgs.outFileName, 'w')
    out_file_init.write('')
    out_file_init.close()
    simulated_current_time = inArgs.startTime
    prev_simulated_time = simulated_current_time
    currentlyTesting = False
    howLongHaveIBeenTesting = 0
    while simulated_current_time < inArgs.endTime:
        timeStepSize = inArgs.timeStepSeconds
        if currentlyTesting == False:
            currentlyTesting = random.random() < probPerTimeStep
        if currentlyTesting:   ### means we need to take small steps ...
            timeStepSize = inArgs.testTimeStepSeconds
        simulated_current_time += datetime.timedelta(seconds=timeStepSize)
        delta_simulated_time = simulated_current_time - prev_simulated_time
        simulated_current_day = simulated_current_time.day
        simulated_current_hour = simulated_current_time.hour
        simulated_current_minute = simulated_current_time.minute
        basePower = get_power_for_time(simulated_current_hour, simulated_current_minute)
        actualPower = basePower
        if currentlyTesting and (howLongHaveIBeenTesting > inArgs.deviceTestTime):
            #### have exceeding testing time limit. Do not apply and reset.
            print 'reset testing to false'
            currentlyTesting = False
            howLongHaveIBeenTesting = 0
        if currentlyTesting:   ### an actual test, do i
            if inArgs.preTestTime < howLongHaveIBeenTesting < inArgs.deviceTestTime-inArgs.postTestTime:
                actualPower += deviceTypes[inArgs.deviceType]['power']
            howLongHaveIBeenTesting += timeStepSize
            print 'currentlyTesting is true. how long so far? ', howLongHaveIBeenTesting, ', deviceTime: ', inArgs.deviceTestTime
        
        print 'time: ', simulated_current_time, ', power: ', basePower, ', actualPower: ', actualPower

        write_output(inArgs.houseId, simulated_current_time, actualPower, currentlyTesting, inArgs.outFileName)
        prev_simulated_time=simulated_current_time


def write_output(house_id, simulated_current_time, actualPower, currentlyTesting, file_name):
    out_file = open(file_name, 'a')
    data_line = '{"id":'+str(house_id)+', "timeStamp":"'+str(simulated_current_time)
    data_line += '", "powerUsage": '+str(actualPower)
    data_line += ', "isTesting": '+str(int(currentlyTesting))
    data_line += '},\n'
    out_file.write(data_line)
    out_file.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Energy simulation')
    parser.add_argument('--startTime', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'))
    parser.add_argument('--endTime', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'))
    parser.add_argument('--timeStepSeconds', type=int)
    parser.add_argument('--testTimeStepSeconds', type=int)
    parser.add_argument('--outFileName', type=str)
    parser.add_argument('--deviceType', type=str)
    parser.add_argument('--deviceTestTime', type=int)
    parser.add_argument('--preTestTime', type=int)
    parser.add_argument('--postTestTime', type=int)
    parser.add_argument('--probTestPerDay', type=float)
    parser.add_argument('--houseId', type=int)
    main(parser)



