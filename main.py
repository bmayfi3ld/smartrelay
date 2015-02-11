import gspread
import Adafruit_BBIO.ADC as ADC

from time import sleep

ADC.setup()

gc = gspread.login('', '')

wks = gc.open("Cloud").worksheet("logs")
print('Starting Up')

while(1) :
    valueV = ADC.read("AIN1") * 1.8
    print(valueV)
    values = [valueV,7]
    wks.append_row(values)
    sleep(60)
print('Done')
