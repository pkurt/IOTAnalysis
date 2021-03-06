import datetime
import time
import random
import sys, getopt, math

def getSeasonalBaselineTemp(month, day, hour, minute, avgBaselineTemp=60):
    dayOfYear = None
    if month == 1: dayOfYear = day
    elif month == 2: dayOfYear = day+31
    elif month == 3: dayOfYear = day+31+28
    elif month == 4: dayOfYear = day+31+28+31
    elif month == 5: dayOfYear = day+31+28+31+30
    elif month == 6: dayOfYear = day+31+28+31+30+31
    elif month == 7: dayOfYear = day+31+28+31+30+31+30
    elif month == 8: dayOfYear = day+31+28+31+30+31+30+31
    elif month == 9: dayOfYear = day+31+28+31+30+31+30+31+31
    elif month == 10: dayOfYear = day+31+28+31+30+31+30+31+31+30
    elif month == 11: dayOfYear = day+31+28+31+30+31+30+31+31+30+31
    elif month == 12: dayOfYear = day+31+28+31+30+31+30+31+31+30+31+30
    fractionThroughYear = (float(dayOfYear) + (hour / 24.) + (minute / (24.*60.)) ) / 365.
    print 'fractionThroughYear = ', fractionThroughYear
    radiansThroughYear = 2.*math.pi*float(fractionThroughYear)
    print 'radians: ', radiansThroughYear
    weatherTerm = -1.*math.cos(radiansThroughYear-0.1)
    print 'weatherTerm: ', weatherTerm
    seasonalTemp = avgBaselineTemp * (1. +(0.4*weatherTerm))
    return seasonalTemp


def get_temp_for_time(hour, minute, baseline=65.):
    outside_temp = None
    coldest_outside_temp = baseline * 0.7
    hottest_outside_temp = baseline * 1.3
    outside_temp_range = hottest_outside_temp - coldest_outside_temp
    eff_hour = hour+(minute / 60.)
    if eff_hour >= 0 and eff_hour < 5: outside_temp = coldest_outside_temp
    elif eff_hour >= 5. and eff_hour < 15: outside_temp = coldest_outside_temp + (outside_temp_range * (eff_hour-5) / (15.-5.))
    elif eff_hour >= 15. and eff_hour < 17.: outside_temp = hottest_outside_temp
    elif eff_hour >= 17: outside_temp = hottest_outside_temp - (outside_temp_range * (eff_hour-17) / (24.-17.))
    short_temp_out_offset = random.gauss(0, 0.5)
    outside_temp += short_temp_out_offset
    return outside_temp

def get_temp_in(prev_temp_in, temp_out, running_mode, time_delta, insulation, ac_power):
    temp_diff = temp_out - prev_temp_in
    print 'prev_temp_in: ', prev_temp_in, ', temp_diff: ', temp_diff, ', insulation: ', insulation, ', ac_power: ', ac_power
    print 'time_delta: ', time_delta, ', temp_out: ', temp_out
    natural_temp_change = time_delta*temp_diff / insulation
    print 'natural_temp_change: ', natural_temp_change
    ac_temp_change = 0
    if running_mode == 1:
        ac_temp_change = -ac_power * time_delta / 6.
    print 'ac_temp_change: ', ac_temp_change
    resulting_temp_in = prev_temp_in + natural_temp_change + ac_temp_change
    print 'resulting_temp_in: ', resulting_temp_in
    return resulting_temp_in

def get_running_mode(prev_running_mode, setpoint, temp_in, ac_span):
    if temp_in > setpoint + ac_span: return 1
    elif temp_in < setpoint - ac_span: return 0
    else: return prev_running_mode

def write_output(hvac_id, simulated_current_time, temp_out, temp_in, setpoint, running_mode, file_name):
    out_file = open(file_name, 'a')
    data_line = '{"id":'+str(hvac_id)+', "timeStamp":"'+str(simulated_current_time)
    data_line += '", "OutsideTemp": '+str(temp_out)
    data_line += ', "InsideTemp": '+str(temp_in)
    data_line += ', "SetPoint": '+str(setpoint)
    data_line += ', "RunningMode": '+str(running_mode)
    data_line += '},\n'
    out_file.write(data_line)
    out_file.close()

def main(argv):
    assert len(argv) == 4
    startTime=datetime.datetime.strptime(argv[0], '%Y-%m-%d')
    endTime=datetime.datetime.strptime(argv[1], '%Y-%m-%d')
    timeStepSeconds = int(argv[2])
    outFileName = argv[3]

    hvac_id=20
    temp_in=78.00
    setpoint=78.00
    running_mode=1
    out_file_init = open(outFileName, 'w')
    out_file_init.write('')
    out_file_init.close()
    simulated_current_time = startTime
    prev_simulated_time = simulated_current_time
#    real_start_time = datetime.datetime.now() - datetime.timedelta(days=100)
#    simulated_start_time = real_start_time
#    simulated_current_time = simulated_start_time
#    simulated_start_day = simulated_start_time.day
    insulation = 300.
    ac_power = 1.
    ac_span = 0.5
    avgBaselineTemp = 65

    #print 'start at real time: ', real_start_time, ', simulated time: ', simulated_start_time
    while simulated_current_time < endTime:
        simulated_current_time += datetime.timedelta(seconds=timeStepSeconds)
        delta_simulated_time = simulated_current_time - prev_simulated_time
        simulated_current_month = simulated_current_time.month
        simulated_current_day = simulated_current_time.day
        simulated_current_hour = simulated_current_time.hour
        simulated_current_minute = simulated_current_time.minute
        seasonal_baseline_temp = getSeasonalBaselineTemp(simulated_current_month, simulated_current_day,
                                     simulated_current_hour, simulated_current_minute)
        baseline_temp = seasonal_baseline_temp  ## maybe add in day-to-day non-seasonal variations later?
        temp_out = get_temp_for_time(simulated_current_hour, simulated_current_minute, baseline_temp)
        prev_temp_in = temp_in
        temp_in = get_temp_in(prev_temp_in, temp_out, running_mode, delta_simulated_time.seconds / 60., insulation, ac_power)
        prev_running_mode = running_mode
        running_mode = get_running_mode(prev_running_mode, setpoint, temp_in, ac_span)
        print 'simulated_time: ',\
                simulated_current_time, ', simulated_day: ',\
                simulated_current_day, ', hour: ', simulated_current_hour,\
                ', minute: ', simulated_current_minute, ', temp_out: ', temp_out

        write_output(hvac_id, simulated_current_time, temp_out, temp_in, setpoint, running_mode, outFileName)
        prev_simulated_time=simulated_current_time
        #time.sleep(5)



if __name__ == "__main__":
    main(sys.argv[1:])


