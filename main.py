# main.py
# main loop to be run on a beaglebone for use with other smart relay components
# Author: Brandon Mayfield

import gspread                          # allows access to Google spreadsheets
import Adafruit_BBIO.ADC as ADC         # ADC control
import Adafruit_BBIO.GPIO as GPIO       # GPIO control
from time import sleep                  # pausing
import time                             # timing
from datetime import datetime           # timestamp
import thread                           # multithreading
import threading
import ConfigParser                     # read config file
import logging                          # for basic local logging
from os.path import isfile              # checking for existing files
import Adafruit_CharLCD as LCD          # lcd driver
import Adafruit_DHT                     # temp and humidity sensor driver
import Adafruit_BBIO.PWM as PWM         # PWM
from Adafruit_BBIO.SPI import SPI       # SPI

print('Starting Up')

# global variables
command_list = [0, 0, 1, 1]     # 4 sources: button, logs, remote, amps
latest_values = {
    'voltage'   : 120,
    'amps'      : 6,
    'temp'      : -1,
    'battery'   : -1,
    'humidity'  : -1,
    'frequency' : -1
}                               # most recent values of sensor reading
onoff = 'Off'                   # relay on or off
button_status = 0               # 1 = command toggle, 2 = reset all
pin_registry = {
    'relay_output'      : 'P9_42',
    'frequency_input'   : 'P9_15',
    'button_input'      : 'P9_11',
    'lcd_rs'            : 'P8_8',
    'lcd_en'            : 'P8_10',
    'lcd_d4'            : 'P8_18',
    'lcd_d5'            : 'P8_16',
    'lcd_d6'            : 'P8_14',
    'lcd_d7'            : 'P8_12',
    'lcd_backlight'     : 'P8_7',
    'temp_input'        : 'P9_12',
    'voltage_ain'       : 'P9_39'
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
    
    # sd calc init
    correct = 50
    attempts = 1
    deviation_total = 0
    cycles = 50
    
    
    print('Value Update Initialized')
    
    while True:
        # get battery voltage
        latest_values['battery'] = ADC.read("AIN1") * 1.8 * 10
        
        # frequency measure
        start = time.time()
        for i in range(cycles):
            GPIO.wait_for_edge(pin_registry['frequency_input'], GPIO.FALLING)
        duration = time.time() - start
        value = cycles / duration
        print(value)
        latest_values['frequency'] = value
        deviation_total += abs(value - correct)
        deviation = deviation_total / attempts
        print(deviation)
        attempts += 1
        
        # peak measure
        voltage = 0
        for i in range(cycles):
            value = ADC.read(pin_registry['voltage_ain']) * 1.8
            if value > voltage:
                voltage = value
        
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

# # this thread handles dumb basic logging
def logger():
    print('Logging Thread')
    
    global pin_registry
    global latest_values
    global onoff
    
    # logging init
    if not isfile('data.log'):
        logging.basicConfig(filename='data.log', level=logging.INFO, format='%(message)s')
        newHeader = 'Time'
        for variable in latest_values:
            newHeader += ', ' + variable
        logging.info(newHeader)
    else:
        logging.basicConfig(filename='data.log', level=logging.INFO, format='%(message)s')
        
    # lcd init
    lcd_columns = 16
    lcd_rows = 2 
    slide = 2
    
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
        temp = 9.0/5.0 * temp + 32
        latest_values['temp'] = temp
        latest_values['humidity'] = humidity
        
        # 'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)
        
        # create logs
        newLog = str(datetime.today())
        for variable, value in latest_values.iteritems():
            newLog += ', ' + str(value)
        logging.info(newLog)
        
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
        # print('Humidity is at ' + str(latest_values['humidity']))
        sleep(5)


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
print('Done')
