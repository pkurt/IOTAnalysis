import datetime
import time
import random

def get_temp_for_time(hour, minute):
    outside_temp = None
    coldest_outside_temp = 73.
    hottest_outside_temp = 91.
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
        ac_temp_change = -ac_power * time_delta / 8.
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

def main():
    hvac_id=12
    temp_in=78.00
    setpoint=78.00
    running_mode=1
    file_name='sim_hvac_conditions_older_data.json'
    out_file_init = open(file_name, 'w')
    out_file_init.write('')
    out_file_init.close()
    real_start_time = datetime.datetime.now() - datetime.timedelta(days=100)
    simulated_start_time = real_start_time
    simulated_current_time = simulated_start_time
    simulated_start_day = simulated_start_time.day
    insulation = 200.
    ac_power = 1.
    ac_span = 0.5
    print 'start at real time: ', real_start_time, ', simulated time: ', simulated_start_time
    for tidx in range(10000):
        real_current_time = datetime.datetime.now() - datetime.timedelta(days=100)
        delta_real_time = real_current_time - real_start_time
        delta_current_time = 100*delta_real_time
        prev_simulated_time = simulated_current_time
        simulated_current_time = simulated_start_time + delta_current_time
        delta_simulated_time = simulated_current_time - prev_simulated_time
        simulated_current_day = simulated_current_time.day
        simulated_current_hour = simulated_current_time.hour
        simulated_current_minute = simulated_current_time.minute
        temp_out = get_temp_for_time(simulated_current_hour, simulated_current_minute)
        prev_temp_in = temp_in
        temp_in = get_temp_in(prev_temp_in, temp_out, running_mode, delta_simulated_time.seconds / 60., insulation, ac_power)
        prev_running_mode = running_mode
        running_mode = get_running_mode(prev_running_mode, setpoint, temp_in, ac_span)
        print 'real time: ', real_current_time, ', simulated_time: ',\
                simulated_current_time, ', simulated_day: ',\
                simulated_current_day, ', hour: ', simulated_current_hour,\
                ', minute: ', simulated_current_minute, ', temp_out: ', temp_out

        write_output(hvac_id, simulated_current_time, temp_out, temp_in, setpoint, running_mode, file_name)
        time.sleep(5)


        

#{"id":10, "timeStamp":"2015-05-28 12:00:00", "OutsideTemp": 80.00, "InsideTemp":78.00, "SetPoint":75.00, "RunningMode":1, "RunId": 1}

if __name__ == "__main__":
    main()


