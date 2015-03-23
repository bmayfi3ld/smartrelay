# main.py
# main loop to be run on a beaglebone for use with other smart relay components
# Author: Brandon Mayfield

import gspread                          # allows access to Google spreadsheets
import Adafruit_BBIO.ADC as ADC         # ADC control
import Adafruit_BBIO.GPIO as GPIO       # GPIO control
from time import sleep                  # pausing
from time import time                   # timing
from datetime import datetime           # timestamp
import thread                           # multithreading
import ConfigParser                     # read config file
import logging                          # for basic local logging
import logging.handlers                 # to remove file once size is exceeded
from os.path import isfile              # checking for existing files
import Adafruit_CharLCD as LCD          # lcd driver
import Adafruit_DHT                     # temp and humidity sensor driver
import Adafruit_BBIO.PWM as PWM         # PWM

print('Starting Up')

# global variables
command_list = [0, 0, 1, 1]     # 4 sources: button, logs, remote, amps
latest_values = {
    'voltage'   : -1,
    'amps'      : -1,
    'temp'      : -1,
    'battery'   : -1,
    'humidity'  : -1,
    'frequency' : -1
}                               # most recent values of sensor reading
onoff = 'Off'                   # relay on or off
button_status = 0               # 1 = command toggle, 2 = reset all
pin_registry = {
    'relay_output'      : 'P9_14',
    'frequency_input'   : 'P9_42',
    'button_input'      : 'P9_11',
    'lcd_rs'            : 'P8_17',
    'lcd_en'            : 'P8_15',
    'lcd_d4'            : 'P8_13',
    'lcd_d5'            : 'P8_11',
    'lcd_d6'            : 'P8_9',
    'lcd_d7'            : 'P8_7',
    'lcd_backlight'     : 'P8_7',
    'temp_input'        : 'P9_12',
    'voltage_ain'       : 'P9_39',
    'battery_ain'       : 'P9_40'
}


# global setup
Config = ConfigParser.ConfigParser()    # read in config file
Config.read("config.ini")

# define functions (which usually are individual threads)

# # the logger just takes the values and updates the global variables
def value_update():
    print('Value Update Thread')

    global latest_values
    global pin_registry

    # I/O init
    ADC.setup()
    GPIO.setup(pin_registry['frequency_input'], GPIO.IN)
    
    # frequency vars
    time_to_measure = 10 # in seconds
    
    # voltage vars
    cycles = 100
    
    print('Value Update Initialized')
    
    while True:
        # get battery voltage
        latest_values['battery'] = ADC.read(pin_registry['battery_ain']) * 1.8 * 10
        
        # frequency measure
        count = 0
        end = time() + time_to_measure
        while end > time():
            GPIO.wait_for_edge(pin_registry['frequency_input'], GPIO.RISING)
            count += 1
        value = count/float(timer)
        latest_values['frequency'] = value
        
        # peak measure
        voltage_stack = []
        end = time() + time_to_measure
        while end > time():
            voltage_stack.append(ADC.read(pin_registry['voltage_ain']))
        voltage = round(max(voltage_stack), 4)
        latest_values['voltage'] = voltage
        
        
        # print('voltage: ' + str(latest_values['voltage']) + ' frequency: ' + str(latest_values['frequency']))
        
        sleep(1)
        
# # always checking to see if the device needs to shutoff
def commander():
    print('Commander Thread')
    
    global command_list
    global onoff
    global button_status
    global latest_values
    global pin_registry
    
    # init
    GPIO.setup(pin_registry['relay_output'], GPIO.OUT)
    sleep(15)   # delay to allow other commands to init
    
    print('Commander Thread Initialized')
    
    while True:
        # basic shutoff check
        if (command_list.count(0) > 0):
            GPIO.output(pin_registry['relay_output'], GPIO.LOW)
            onoff = 'Off'
        else: 
            GPIO.output(pin_registry['relay_output'], GPIO.HIGH)
            onoff = 'On'
        
        # check if values are out of range
        # if out of thresh(from config) turn off until return
        # if out of thresh for current kill until further notice
        thresh_list = Config.options('Threshold')
        trip_count = 0
        for item in thresh_list:
            thresh_in = Config.get('Threshold', item).split(',')
            
            item_v = latest_values[item]
            if item_v > int(thresh_in[1]) or item_v < int(thresh_in[0]):
                trip_count += 1
        
        if trip_count > 0:
            command_list[1] = 0
        else:
            command_list[1] = 1
        
        # check if button has something to say
        # basic on/off 1
        # hard reset 2 (cloud also needs to be able to)
        if (button_status == 1):
            command_list[0] = not command_list[0]
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
        elif count > 1500:
            button_status = 1
            
        count = 0
        
        sleep(1)

# # this thread handles dumb basic logging, also updates things that won't be changing very quickly
def logger():
    print('Logging Thread')
    
    global pin_registry
    global latest_values
    global onoff
    
    # logging init
    # file_name = 'data.log'
    # if not isfile(file_name):
    #     logging.basicConfig(filename=file_name, level=logging.INFO, format='%(message)s')
    #     newHeader = 'Time'
    #     for variable in latest_values:
    #         newHeader += ', ' + variable
    #     logging.info(newHeader)
    # else:
    #     logging.basicConfig(filename=file_name, level=logging.INFO, format='%(message)s')
        
    LOG_FILENAME = 'data.log'
    # Set up a specific logger with our desired output level
    my_logger = logging.getLogger('MyLogger')
    my_logger.setLevel(logging.DEBUG)
    
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(
                  LOG_FILENAME, maxBytes=20, backupCount=5)
    
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
                                
    print('Logging Thread Initialized')
    
    while True:
        # get temp
        humidity, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin_registry['temp_input'])
        
        if humidity == None:
            humidity = -1;
        if temp == None:
            temp = -1;
        else:
            temp = 9.0/5.0 * temp + 32

        
        latest_values['temp'] = temp
        latest_values['humidity'] = humidity
        
        # 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)
        
        # create logs
        newLog = str(datetime.today())
        for variable, value in latest_values.iteritems():
            newLog += ', ' + str(value)
        my_logger.info(newLog)
        
        # update lcd
        lcd.clear()
        if slide == 1:
            lcd.message('Temp:' + '{0:0.1f}*F'.format(temp) + '\nStatus: ' + onoff)
            slide += 1
        elif slide == 2:
            lcd.message('Bat Volt:' + str(latest_values['battery']) + '\nStatus: ' + onoff)
            slide = 1
        
        sleep(15)
        
# # this thread handles cloud logging and pulling commands
def cloud_logger():
    print('Cloud Thread')
    
    global latest_values
    global command_list
    global onoff
    
    # cloud init
    try:
        gc = gspread.login(Config.get('SmartRelay','email'), Config.get('SmartRelay','psww'))
        wkb = gc.open_by_url(Config.get('SmartRelay','sheet URL'))
        logs = wkb.worksheet("logs")
        cofig = wkb.worksheet("config")
    except:
        print('Cloud Connection Failed')
        sleep(30)
        cloud_logger()
        return
    
    print('Cloud Thread Initialized')
    
    while True:
        # create logs
        newLog = str(datetime.today())
        for variable, value in latest_values.iteritems():
            newLog += ', ' + str(value)
        
        logs.append_row(newLog.split(', '))
        
        # update cloud config page
        cofig.update_acell('B1', onoff)
        cofig.update_acell('B3', datetime.today())
        
        # check for command
        if(cofig.acell('B2').value == 'Off'): 
            command_list[2] = 0
        else: 
            command_list[2] = 1
        
        sleep(15)
        
def debug():
    print('Debugging')
    
    global command_list
    global onoff
    global button_status
    global latest_values
    
    num = 0
    
    sleep(15)
    
    while True:
        print(onoff)
        print(num)
        num += 1
        print(command_list)
        print(latest_values)
        # print('Humidity is at ' + str(latest_values['humidity']))
        sleep(10)


print('Initialized')


# start threads
thread.start_new_thread(logger, ())
thread.start_new_thread(cloud_logger, ())
thread.start_new_thread(button_interrupt, ())
thread.start_new_thread(commander, ())
thread.start_new_thread(debug, ())
thread.start_new_thread(value_update, ())

print('Threads Started')

raw_input("Press Enter to kill program\n")
PWM.cleanup()
lcd.clear()
print('Done')
