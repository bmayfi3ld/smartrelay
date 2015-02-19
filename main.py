# main.py
# main loop to be run on a beaglebone for use with other smart relay components
# Author: Brandon Mayfield 

print('Starting Up')

import gspread                          # allows access to Google spreadsheets
import Adafruit_BBIO.ADC as ADC         # ADC control
import Adafruit_BBIO.GPIO as GPIO       # GPIO control
from time import sleep                  # pausing
from datetime import datetime           # timestamp
import thread                           # multithreading
import threading
import ConfigParser                     # read config file
import logging                          # for basic local logging
from os.path import isfile                   # checking for existing files



# global variables
commandList = [0,0,0,1]                                     # 4 checked sources: button, logs, remote button, current fault
latestValues = {'voltage' : 120, 'amps' : 6, 'temp' : 60};  # most recent values of sensor reading
onoff = 'Off'                                               # relay on or off
button_status = 0                                           # 0 = nothing, 1 = command toggle, 2 = reset all command

# global setup
Config = ConfigParser.ConfigParser()    # read in config file
Config.read("config.ini")

# define functions (which usually are individual threads)

# # the logger just takes the values and updates the global variables
def value_update():
    global latestValues
    
    #I/O init
    ADC.setup()
    GPIO.setup("P9_41", GPIO.OUT)
    GPIO.setup("P9_42", GPIO.OUT)   
    
    # running average of the last 10 periods to get accurate frequency
    while(1) :
        # start a loop that will run once per period
        # checked by finding max/min of voltage
        latestValues['voltage'] = ADC.read("AIN1") * 1.8
        
    
# # always checking to see if the device needs to shutoff
def commander():
    print('Commander Thread')
    
    global commandList
    global onoff
    global button_status
    global latestValues
    output_pin = "P9_42"
    
    # init
    GPIO.setup(output_pin, GPIO.OUT)
    
    print('Commander Thread Initialized')
    
    while(1):
        if (commandList.count(0) > 0): 
            GPIO.output(output_pin, GPIO.LOW)
            onoff = 'Off'
        else: 
            GPIO.output(output_pin, GPIO.HIGH)
            onoff = 'On'
        
        # check if values are out of range
        # if out of thresh(from config) turn off until return
        # if out of thresh for current kill until further notice
        thresh_list = Config.options('Threshold')
        for item in thresh_list:
            thresh_in = Config.get('Threshold',item).split(',')
            if latestValues[item] > int(thresh_in[1]) or latestValues[item] < int(thresh_in[0]):
                commandList[1] = 0
            else:
                commandList[1] = 1
        # commandList[1] = 1
        
        # check if button has something to say
        # basic on/off 1
        # hard reset 2 (cloud also needs to be able to)
        if (button_status == 1):
            commandList[0] = not commandList[0]
            button_status = 0
            sleep(1)
        
# # button thread to handle button commands
def button_interrupt():
    
    global button_status
    button_pin = 'P9_11' #GPIO 30
    count = 0
    
    # init
    GPIO.setup(button_pin, GPIO.IN)
    
    # main loop
    while(1):
        
        GPIO.wait_for_edge(button_pin, GPIO.RISING)    # wait for initial hit
        
        while(GPIO.input(button_pin)):
            count += 1
            
        if count > 50000:
            button_status = 2
        elif count > 1500:
            button_status = 1
            
        count = 0
        sleep(1)

# # this thread handles dumb basic logging
def logger():
    print('Logging Thread')
    global latestValues
    
    #logging init
    if not isfile('data.log'):
        logging.basicConfig(filename='data.log',level=logging.INFO, format='%(message)s')
        newHeader = 'Time'
        for variable in latestValues:
            newHeader += ', ' + variable
        logging.info(newHeader)
    else:
        logging.basicConfig(filename='data.log',level=logging.INFO, format='%(message)s')
        
    print('Logging Thread Initialized')
    
    # main loop
    while(1):
        
        #create logs
        newLog = str(datetime.today())
        for variable, value in latestValues.iteritems():
            newLog += ', ' + str(value)
        logging.info(newLog);
        
        sleep(15)
        
# # this thread handles cloud logging and pulling commands
def cloud_logger():
    print('Cloud Thread')
    
    global latestValues
    global commandList
    global onoff
    
    #cloud init
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
    
    #main loop
    while(1):
        
        #create logs
        newLog = str(datetime.today())
        for variable, value in latestValues.iteritems():
            newLog += ', ' + str(value)
        
        logs.append_row(newLog.split(', '))
        
        #update cloud config page
        cofig.update_acell('B1', onoff)
        cofig.update_acell('B3', datetime.today())
        
        #check for command
        if(cofig.acell('B2').value == 'Off'): commandList[2] = 0
        else: commandList[2] = 1
        
        sleep(15)
        
def debug():
    print('Debugging')
    global commandList
    global onoff
    global button_status
    
    num = 0
    
    sleep(15)
    
    while(1):
        print(onoff)
        print(num)
        num += 1
        print(commandList)
        sleep(5)

print('Initialized')


# start threads
thread.start_new_thread(logger, ( ))
thread.start_new_thread(cloud_logger, ( ))
thread.start_new_thread(button_interrupt, ( ))
thread.start_new_thread(commander, ( ))
thread.start_new_thread(debug, ( ))

# thread.start_new_thread(checkRemote, ( ))
print('Threads Started')


raw_input("Press Enter to kill program\n")
print('Done')

