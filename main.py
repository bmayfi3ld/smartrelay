# main.py
# main loop to be run on a beaglebone for use with other smart relay components
# Author: Brandon Mayfield 

print('Starting Up')

import gspread                          # allows access to Google spreadsheets
import Adafruit_BBIO.ADC as ADC         # ADC control
import Adafruit_BBIO.GPIO as GPIO       # GPIO control
from time import sleep                  # pausing
from datetime import datetime           # timestamp
from sys import exit                    # program exit
import thread                           # multithreading
import ConfigParser                     # read config file


# global variables
commandList = [0,0,0] # 3 input sources: button, logs, remote button
latestValues = {'voltage' : -1, 'amps' : -1, 'temp' : -1};

# define functions (which usually are individual threads)

# # the logger just takes the values and updates the global variables
def valueUpdate():
    global latestValues
    # Running average of the last 10 periods to get accurate frequency
    while(1) :
        # start a loop that will run once per period
        # checked by finding max/min of voltage
        latestValues['voltage'] = ADC.read("AIN1") * 1.8
    
# # always checking to see if the device needs to shutoff
def commander():
    global commandList
    while(1):
        if (commandList.count(0) > 0) #shutdown
        else #on
        
        #check if values are out of range
        # if so turn off valueUpdate (change from thread module to threading)
        # wait 30 seconds then turn back on, if occuring twice in 10 min period leave off
        
        #check if button has been pressed
        #toggle off
        
        

# # this thread handles all cloud interaction      
def logger():
    while(1):
        # update local/cloud logs\
        # use logging module
        # push/pull relevant data
        
        #TODO: Handle no internet
        gc = gspread.login(Config.get('SmartRelay','email'), Config.get('SmartRelay','psww'))
        wkb = gc.open("Cloud")
        logs = wkb.worksheet("logs")
        comm = wkb.worksheet("config")
        
        # Check if need to shutdown
        # if(comm.acell('B2').value == "Off"): 
        #     GPIO.output("P9_42", GPIO.LOW)
        # else:
        #     GPIO.output("P9_42", GPIO.HIGH) #TODO: will need to account for other sources, perhaps a manager
        # if(GPIO.input("P9_42")):
        #     comm.update_acell('B1',"On")
        # else:
        #     comm.update_acell('B1',"Off")



# setup
ADC.setup()
GPIO.setup("P9_41", GPIO.OUT)
GPIO.setup("P9_42", GPIO.OUT)

Config = ConfigParser.ConfigParser()
Config.read("config.ini")




print('Initialized')

# start threads
thread.start_new_thread(logger, ( ))
thread.start_new_thread(commanderTest, ( ))
# thread.start_new_thread(checkRemote, ( ))
print('Threads Started')



input("Press Enter to kill program\n")
GPIO.setup("P9_41", GPIO.IN)
print('Done')
exit()

