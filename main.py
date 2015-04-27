# main.py
# main loop to be run on a beaglebone for use with other smart relay components
# Author: Brandon Mayfield

import gspread                          # allows access to Google spreadsheets
import Adafruit_BBIO.ADC as ADC         # ADC control
import Adafruit_BBIO.GPIO as GPIO       # GPIO control
from time import sleep                  # pausing
import time
import datetime                         # timestamp
import thread                           # multithreading
import threading
import ConfigParser                     # read config file
import logging                          # for basic local logging
import logging.handlers                 # to remove file once size is exceeded
from os.path import isfile              # checking for existing files
import Adafruit_CharLCD as LCD          # lcd driver
import Adafruit_DHT                     # temp and humidity sensor driver
import Adafruit_BBIO.PWM as PWM         # PWM
import smtplib                          # for sending mail
import urllib2                          # to post data to gae
from itertools import cycle             # for button toggle

print('Starting Up')
# # responsible for heartbeat
def runner():
    print('Running')
    
    global command_list
    global onoff
    global button_status
    global latest_values
    
    num = 0
    GPIO.setup(pin_registry['led1'], GPIO.OUT)
    
    sleep(5)
    
    while True:
        #flash heartbeat light
        blink = .1
        GPIO.output(pin_registry['led1'], GPIO.HIGH)
        sleep(blink)
        GPIO.output(pin_registry['led1'], GPIO.LOW)
        sleep(blink)
        GPIO.output(pin_registry['led1'], GPIO.HIGH)
        sleep(blink)
        GPIO.output(pin_registry['led1'], GPIO.LOW)
        
        sleep(1)

thread.start_new_thread(runner, ())

# wait for correct time
while datetime.date.today() < datetime.date(2015,04,9):
    print('Waiting for Time')
    sleep(5)

# global variables
directory = '/var/lib/cloud9/workspace/smartrelay/'
command_list = [1, 0, 1, 1]     # 4 sources: button, logs, remote, current
latest_values = {
    'voltage'           : -1,
    'current'           : -1,
    'temperature'       : -1,
    'battery_voltage'   : -1,
    'humidity'          : -1,
    'frequency'         : -1
}                               # most recent values of sensor reading
cutoff_dict = {
    'battery_voltage'   : [0,500],
	'current'           : [0,500],
	'frequency'         : [0,500],
	'humidity'          : [0,500],
	'temperature'       : [0,500],
	'voltage'           : [0,500],
}
onoff = 'Off'                   # relay on or off
button_status = 0               # 1 = command toggle, 2 = reset all
pin_registry = {
    'relay_output'      : 'P9_14',
    'relay_secondary'   : 'P9_12',
    'led1'              : 'P9_16',
    'led2'              : 'P8_19',
    'frequency_input'   : 'P9_42',
    'button_input'      : 'P9_24',
    'button_secondary'  : 'P9_26',
    'lcd_rs'            : 'P8_17',
    'lcd_en'            : 'P8_15',
    'lcd_d4'            : 'P8_13',
    'lcd_d5'            : 'P8_11',
    'lcd_d6'            : 'P8_9',
    'lcd_d7'            : 'P8_7',
    'lcd_backlight'     : 'P8_7',
    'temp_input'        : 'P9_22',
    'voltage_ain'       : 'P9_36',
    'battery_ain'       : 'P9_40',
    'current_ain'       : 'P9_38'
}

frequency_watchdog = 0
# global setup
button_toggle = cycle(range(2))
ADC.setup()

class frequency_update(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global latest_values
        global pin_registry
        global frequency_watchdog
        
        self.frequency_time_to_measure = .25
    
    def run(self):
        global frequency_watchdog
        # frequency measure
        count = 0
        end = time.time() + self.frequency_time_to_measure
        try:
            while end > time.time():
                GPIO.wait_for_edge(pin_registry['frequency_input'], GPIO.RISING)
                count += 1
        except RuntimeError: # if the previous event failed
            return
        value = count/float(self.frequency_time_to_measure) - 4
        if abs(value - 60) < 4:
            latest_values['frequency'] = round(value,1)
        frequency_watchdog += 1
        

# # the logger just takes the values and updates the global variables
def value_update():
    print('Value Update Thread')

    global latest_values
    global pin_registry
    
    # I/O init
    GPIO.setup(pin_registry['frequency_input'], GPIO.IN)

    # timer
    time_to_measure = 4 # in seconds
    counter = 0
    
    print('Value Update Initialized')
    
    while True:
        
        # frequency
        current_num = frequency_watchdog
        thread = frequency_update()
        thread.start()
        thread.join(1)
        if current_num == frequency_watchdog:
            latest_values['frequency'] = 0
        
        # voltage measure
        voltage_stack = []
        end = time.time() + time_to_measure
        while end > time.time():
            voltage_stack.append(ADC.read(pin_registry['voltage_ain']))
        # print voltage_stack
        value = max(voltage_stack)
        value = value * 349.514902442
        if value < 1:
            value = 0
        latest_values['voltage'] = round(value,1)
        
        # amps measure
        current_stack = []
        end = time.time() + time_to_measure
        while end > time.time():
            current_stack.append(ADC.read(pin_registry['current_ain']))
        value = max(current_stack)
        value *=  1.8
        if value < .03:
            value = 0
        value *= 10
        latest_values['current'] = round(value,1)
        counter += 1
        print '{},{}'.format(latest_values['voltage'], counter)
        
        
        sleep(5)
        
# # always checking to see if the device needs to shutoff
def commander():
    print('Commander Thread')
    
    global command_list
    global onoff
    global button_status
    global latest_values
    global pin_registry
    global cutoff_dict
    
    # init
    GPIO.setup(pin_registry['relay_output'], GPIO.OUT)
    
    
    sleep(9)   # delay to allow other commands to init
    
    print('Commander Thread Initialized')
    
    
    while True:

        # basic shutoff check
        if (command_list.count(0) > 0):
            GPIO.output(pin_registry['relay_output'], GPIO.LOW)
            GPIO.output(pin_registry['relay_secondary'], GPIO.LOW)
            GPIO.output(pin_registry['led2'], GPIO.LOW)
            onoff = 'Off'
        else: 
            GPIO.output(pin_registry['relay_output'], GPIO.HIGH)
            GPIO.output(pin_registry['relay_secondary'], GPIO.HIGH)
            GPIO.output(pin_registry['led2'], GPIO.HIGH)
            onoff = 'On'
        
        # check if values are out of range
        # if out of thresh(from config) turn off until return
        # if out of thresh for current kill until further notice
        trip_count = 0
        current_trip = False
        for item in cutoff_dict:
            thresh_in = cutoff_dict[item]
            
            item_v = latest_values[item]
            if item_v > int(thresh_in[1]) or item_v < int(thresh_in[0]):
                trip_count += 1
                if item == 'current':
                    current_trip = True
        
        if trip_count > 0:
            command_list[1] = 0
        else:
            command_list[1] = 1
            
        if current_trip:
            command_list[3] = 0
        
        # check if button has something to say
        # basic on/off 1
        # hard reset 2 (cloud also needs to be able to)
        if button_status == 1:
            command_list[0] = button_toggle.next()
            button_status = 0
        elif button_status == 2:
            command_list[2] = 1 # reset remote
            command_list[3] = 1 # reset current
            button_status = 0
        sleep(1)
        
# # button thread to handle button commands
def button_interrupt():
    print('Button Thread')
    
    global button_status
    global pin_registry
    count = 0
    
    # init
    GPIO.setup(pin_registry['button_input'], GPIO.IN)
    
    while True:
        
        GPIO.wait_for_edge(pin_registry['button_input'], GPIO.RISING)
        
        # waiting for hit
        while(GPIO.input(pin_registry['button_input'])):
            count += 1
        
        # debounce, determine hit or hold
        if count > 50000:
            button_status = 2
        elif count > 1000:
            button_status = 1
            
        count = 0
        
        sleep(1)

# # this thread handles dumb basic logging, also updates things that won't be changing very quickly
def logger():
    print('Logging Thread')
    
    global pin_registry
    global latest_values
    global onoff
    global command_list
    
    # log init    
    LOG_FILENAME = directory + 'data.log'
    # Set up a specific logger with our desired output level
    my_logger = logging.getLogger('MyLogger')
    my_logger.setLevel(logging.DEBUG)
    
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(
                  LOG_FILENAME, maxBytes=250000000, backupCount=3)
    
    my_logger.addHandler(handler)
    
    # lcd init
    lcd_columns = 16
    lcd_rows = 2 
    slide = 2
    global lcd
    lcd = LCD.Adafruit_CharLCD(
        pin_registry['lcd_rs'],
        pin_registry['lcd_en'], 
        pin_registry['lcd_d4'], 
        pin_registry['lcd_d5'], 
        pin_registry['lcd_d6'], 
        pin_registry['lcd_d7'], 
        lcd_columns,
        lcd_rows, 
        pin_registry['lcd_backlight']
    )
    lcd.message('Booting Up...')
    
    # I/O init
    
    GPIO.setup(pin_registry['led2'], GPIO.OUT)
    GPIO.setup(pin_registry['button_secondary'], GPIO.IN)
    
    GPIO.setup(pin_registry['relay_output'], GPIO.OUT)
    GPIO.setup(pin_registry['relay_secondary'], GPIO.OUT)
    
    sleep(10)
    
    print('Logging Thread Initialized')
    
    r1 = 0
    
    while True:
        # get battery voltage
        value = ADC.read(pin_registry['battery_ain'])
        value = value * 1.8 * 10
        value = round(value,2)
        latest_values['battery_voltage'] = round(value,1)
        # rint value
        
        # get temp
        humidity, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin_registry['temp_input'])
        
        if humidity == None:
            humidity = -1;
        if temp == None:
            temp = -1;
        else:
            temp = 9.0/5.0 * temp + 32

        latest_values['temperature'] = round(temp,1)
        latest_values['humidity'] = round(humidity,1)
        
        # create logs
        newLog = str(datetime.datetime.today())
        for variable, value in latest_values.iteritems():
            newLog += ', ' + str(value)
        my_logger.info(newLog)
        
        sleep(2)
        # update lcd
        lcd.clear()
        # lcd.message('{},{}'.format(latest_values['current'],r1))
        if onoff == 'Off':
            lcd.message('Btn:{} Amp:{}\nInt:{} Thresh:{}'.format(command_list[0],command_list[3],command_list[2],command_list[1]))
        elif slide == 1:
            lcd.message('Temp:' + '{0:0.1f}*F'.format(temp) + '\nBat Volt: ' + str(latest_values['battery_voltage']))
            slide += 1
        elif slide == 2:
            lcd.message('Voltage:' + str(latest_values['voltage']) + '\nCurrent: ' + str(latest_values['current']))
            slide = 1
        
        sleep(13)
        
# # this thread handles cloud logging and pulling commands       
def cloud_logger():
    print 'Cloud Thread'
    # Dev Cloud Thread
    global latest_values
    global command_list
    global onoff
    global cutoff_dict
    
    request_stack = []
    
    sleep(30)
    print 'Cloud Thread Initialized'
    
    while True:
        #build log
        if onoff == 'On':
            state = True
        else:
            state = False
        
        urlstring = 'https://smart-relay.appspot.com/post?timestamp={}&temperature={}&humidity={}&voltage={}&current={}&battery_voltage={}&frequency={}&state={}&password={}'
        request = urlstring.format(
            str(time.time()),
            latest_values['temperature'],
            latest_values['humidity'],
            latest_values['voltage'],
            latest_values['current'],
            latest_values['battery_voltage'],
            latest_values['frequency'],
            state,
            'my_password'
            )
            
        if len(request_stack) < 100:
		    request_stack.append(request)
        
        response = ''
        for r in list(request_stack):
    	    try:
                response = urllib2.urlopen(r).read()
                request_stack.remove(r)
                time.sleep(5)
                
            except urllib2.URLError:
                print 'Cloud Thread Failed'
                break
        else:
    		response_list = response.split(',')
    		if 'rue' in response_list[0]:
    			command_list[2] = 1
    		else:
    			command_list[2] = 0
    		int_list = []
    		for r in response_list:
    			if 'rue' not in r and 'alse' not in r:
    				int_list.append(int(r))
    		
    		cutoff_dict['battery_voltage'] = [int_list[0],int_list[1]]
    		cutoff_dict['current'] = [int_list[2],int_list[3]]
    		cutoff_dict['frequency'] = [int_list[4],int_list[5]]
    		cutoff_dict['humidity'] = [int_list[6],int_list[7]]
    		cutoff_dict['temperature'] = [int_list[8],int_list[9]]
    		cutoff_dict['voltage'] = [int_list[10],int_list[11]]
    	
        sleep(60)
    

print('Initialized')


# start threads
thread.start_new_thread(logger, ())
thread.start_new_thread(cloud_logger, ())
thread.start_new_thread(button_interrupt, ())
thread.start_new_thread(commander, ())
thread.start_new_thread(value_update, ())
thread.start_new_thread(frequency_update, ())

print('Threads Started')


# for when being run by cron job

while True:
    sleep(60)
    

raw_input("Press Enter to kill program\n")
PWM.cleanup()
lcd.clear()
print('Done')
