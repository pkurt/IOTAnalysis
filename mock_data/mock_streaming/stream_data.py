import datetime
import time
import random
import sys, getopt, math
import argparse


def getSeasonalBaselineTemp(month, day, hour, minute, avgBaselineTemp=60, seasonalWeatherVariation=0.4):
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
    seasonalTemp = avgBaselineTemp * (1. +(seasonalWeatherVariation*weatherTerm))
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

def write_output_CSV(hvac_id, current_time, dataType, value, columnName, out_file, csvColumns):
    outLine = str(hvac_id)+','+str(current_time)+','+ str(dataType)
    optionalColumns = csvColumns[3:]
    assert columnName in optionalColumns
    for col in optionalColumns:
        if columnName == col:
            outLine += ','+str(value)
        else:
            outLine += ','
    outLine += '\n'
    out_file.write(outLine)


def write_output_oldJSON(hvac_id, simulated_current_time, temp_out, temp_in, setpoint, running_mode, file_name):
    out_file = open(file_name, 'a')
    data_line = '{"id":'+str(hvac_id)+', "dataType": "all"'+', "timeStamp":"'+str(simulated_current_time)
    data_line += '", "OutsideTemp": '+str(temp_out)
    data_line += ', "InsideTemp": '+str(temp_in)
    data_line += ', "SetPoint": '+str(setpoint)
    data_line += ', "RunningMode": '+str(running_mode)
    data_line += '},\n'
    out_file.write(data_line)
    out_file.close()

def main(argv):

    deviceTypes = {'Thermostat'}
    inArgs = parser.parse_args()
    print 'inArgs: ', inArgs
    assert inArgs.deviceType in deviceTypes


    dataType="fullSim"
    temp_in=78.00
    setpoint=78.00
    running_mode=1
    
    out_file_init = open(inArgs.outFileName, 'w')
    out_file_init.write('')
    out_file_init.close()
    
    simulated_current_time = inArgs.startTime
    prev_simulated_time = simulated_current_time

    ac_power = 1.
    ac_span = 0.5
    avgBaselineTemp = 65

    previous_temp_in_write = 0   ### initial value
    previous_temp_out_write_time = datetime.datetime(1980, 1, 1, 0, 0, 0)  #### initial value
    previous_setpoint_write_time = datetime.datetime(1980, 1, 1, 0, 0, 0)  #### initial value
    previous_running_mode_write = 0   ### initial value
    #print 'start at real time: ', real_start_time, ', simulated time: ', simulated_start_time

    ### initialize header for output .csv file:
    csvColumns = ['hvac_id', 'current_time', 'dataType', 'temp_out', 'temp_in', 'setpoint', 'running_mode']
    headerLine = ','.join(csvColumns)
    out_file = open(inArgs.outFileName, 'w')
    out_file.write(headerLine+'\n')
    #out_file.close()

    while simulated_current_time < inArgs.endTime:
        simulated_current_time += datetime.timedelta(seconds=inArgs.timeStepSeconds)
        delta_simulated_time = simulated_current_time - prev_simulated_time
        simulated_current_month = simulated_current_time.month
        simulated_current_day = simulated_current_time.day
        simulated_current_hour = simulated_current_time.hour
        simulated_current_minute = simulated_current_time.minute
        seasonal_baseline_temp = getSeasonalBaselineTemp(simulated_current_month, simulated_current_day,
                                     simulated_current_hour, simulated_current_minute, inArgs.avgBaselineTemp,
                                     inArgs.seasonalWeatherVariation)
        baseline_temp = seasonal_baseline_temp  ## maybe add in day-to-day non-seasonal variations later?
        temp_out = get_temp_for_time(simulated_current_hour, simulated_current_minute, baseline_temp)
        prev_temp_in = temp_in
        temp_in = get_temp_in(prev_temp_in, temp_out, running_mode, delta_simulated_time.seconds / 60., inArgs.insulation, ac_power)
        prev_running_mode = running_mode
        running_mode = get_running_mode(prev_running_mode, setpoint, temp_in, ac_span)
        print 'simulated_time: ',\
                simulated_current_time, ', simulated_day: ',\
                simulated_current_day, ', hour: ', simulated_current_hour,\
                ', minute: ', simulated_current_minute, ', temp_out: ', temp_out


        write_temp_out = True if simulated_current_time >= previous_temp_out_write_time + datetime.timedelta(minutes=5) else False
        write_temp_in = True if abs(temp_in - previous_temp_in_write) > 0.1 else False
        write_setpoint = True if simulated_current_time >= previous_setpoint_write_time + datetime.timedelta(days=1) else False
        write_running_mode = True if running_mode != previous_running_mode_write else False
        if write_temp_out:
            previous_temp_out_write_time = simulated_current_time
            write_output_CSV(inArgs.hvac_id, simulated_current_time,dataType=dataType, value=temp_out,
                    columnName='temp_out', out_file=out_file, csvColumns=csvColumns)
        if write_temp_in:
            previous_temp_in_write = temp_in
            write_output_CSV(inArgs.hvac_id, simulated_current_time, dataType=dataType, value=temp_in,
                    columnName='temp_in', out_file=out_file, csvColumns=csvColumns)
        if write_setpoint:
            previous_setpoint_write_time = simulated_current_time
            write_output_CSV(inArgs.hvac_id, simulated_current_time, dataType=dataType, value=setpoint,
                    columnName='setpoint', out_file=out_file, csvColumns=csvColumns)
        if write_running_mode:
            previous_running_mode_write = running_mode
            write_output_CSV(inArgs.hvac_id, simulated_current_time, dataType=dataType, value=running_mode,
                    columnName='running_mode', out_file=out_file, csvColumns=csvColumns)
        prev_simulated_time=simulated_current_time
        #time.sleep(5)
    out_file.close()



if __name__ == "__main__":
#main(sys.argv[1:])

    parser = argparse.ArgumentParser(description='Thermostat simulation')
    parser.add_argument('--startTime', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'))
    parser.add_argument('--endTime', type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'))
    parser.add_argument('--timeStepSeconds', type=int)
    parser.add_argument('--outFileName', type=str)
    parser.add_argument('--deviceType', type=str)
    parser.add_argument('--houseId', type=int)
    parser.add_argument('--hvac_id', type=int)
    parser.add_argument('--insulation', type=float)
    parser.add_argument('--avgBaselineTemp', type=float)
    parser.add_argument('--seasonalWeatherVariation', type=float)

    main(parser)


