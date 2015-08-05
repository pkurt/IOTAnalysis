import datetime
import time
import random
import sys
import argparse


#{"EventNo":1, "device_id":1, "timeStamp":"2015-06-03 12:00:00", "Power": 2000, "Voltage":220.00, "Current":15.00, "RunMode" : 0}.

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


def main(argv):
    assert len(argv) == 4
    startTime=datetime.datetime.strptime(argv[0], '%Y-%m-%d')
    endTime=datetime.datetime.strptime(argv[1], '%Y-%m-%d')
    timeStepSeconds = int(argv[2])
    testTimeStepSeconds = int(argv[3])
    outFileName = argv[4]

    house_id=13
    out_file_init = open(outFileName, 'w')
    out_file_init.write('')
    out_file_init.close()
    simulated_current_time = startTime
    prev_simulated_time = simulated_current_time
    while simulated_current_time < endTime:
        simulated_current_time += datetime.timedelta(seconds=timeStepSeconds)
        delta_simulated_time = simulated_current_time - prev_simulated_time
        simulated_current_day = simulated_current_time.day
        simulated_current_hour = simulated_current_time.hour
        simulated_current_minute = simulated_current_time.minute
        basePower = get_power_for_time(simulated_current_hour, simulated_current_minute)
        print 'time: ', simulated_current_time, ', power: ', basePower

        #write_output(house_id, simulated_current_time, temp_out, temp_in, setpoint, running_mode, outFileName)
        prev_simulated_time=simulated_current_time


#def write_output(house_id, simulated_current_time, temp_out, temp_in, setpoint, running_mode, file_name):
#    out_file = open(file_name, 'a')
#    data_line = '{"id":'+str(house_id)+', "timeStamp":"'+str(simulated_current_time)
#    data_line += '", "OutsideTemp": '+str(temp_out)
#    data_line += ', "InsideTemp": '+str(temp_in)
#    data_line += ', "SetPoint": '+str(setpoint)
#    data_line += ', "RunningMode": '+str(running_mode)
#    data_line += '},\n'
#    out_file.write(data_line)
#    out_file.close()


if __name__ == "__main__":
    main(sys.argv[1:])


