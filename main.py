print('Starting Up')
import gspread
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.GPIO as GPIO
from time import sleep
from datetime import datetime
from sys import exit
import thread
import ConfigParser


# global variables
lastVoltage = -1;

# define functions
def logger():
    global lastVoltage
    while(1) :
        valueV = ADC.read("AIN1") * 1.8
        print(valueV)
        print(datetime.today())
        values = [valueV,7,datetime.today()]
        logs.append_row(values)
        sleep(60)
    
# several functions all checking for shutdown seperated for safety

def commanderTest():
    while(1):
        GPIO.output("P9_41", GPIO.HIGH)
        sleep(5)
        GPIO.output("P9_41", GPIO.LOW)
        sleep(5)

# # Checking remote spreadsheet        
def checkRemote():
    while(1):
        # Check if need to shutdown
        if(comm.acell('B2').value == "Off"): 
            GPIO.output("P9_42", GPIO.LOW)
        else:
            GPIO.output("P9_42", GPIO.HIGH) #TODO: will need to account for other sources, perhaps a manager
        if(GPIO.input("P9_42")):
            comm.update_acell('B1',"On")
        else:
            comm.update_acell('B1',"Off")



# setup
ADC.setup()
GPIO.setup("P9_41", GPIO.OUT)
GPIO.setup("P9_42", GPIO.OUT)

Config = ConfigParser.ConfigParser()
Config.read("config.ini")


#TODO: Handle no internet
gc = gspread.login(Config.get('SmartRelay','email'), Config.get('SmartRelay','psww'))
wkb = gc.open("Cloud")
logs = wkb.worksheet("logs")
comm = wkb.worksheet("config")

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

