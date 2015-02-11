print('Starting Up')
import gspread
import Adafruit_BBIO.ADC as ADC
from time import sleep
from datetime import datetime
import thread



# define functions
def logger(threadNum):
    while(1) :
        valueV = ADC.read("AIN1") * 1.8
        print(valueV)
        print(datetime.today())
        values = [valueV,7,datetime.today()]
        wks.append_row(values)
        sleep(60)
        
# def commander()


# setup
ADC.setup()
gc = gspread.login('', '')
wks = gc.open("Cloud").worksheet("logs")
print('Initialized')

# start threads
thread.start_new_thread(logger, ("Thread 1", ))
print('Threads started')

while(1) :
    pass

