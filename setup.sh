sudo apt-get update
sudo apt-get install build-essential python-dev python-setuptools python-pip python-smbus ntpdate -y
wget -c https://raw.github.com/RobertCNelson/tools/master/pkgs/dtc.sh
chmod +x dtc.sh
./dtc.sh
sudo pip install Adafruit_BBIO
sudo pip install gspread
git clone https://github.com/adafruit/Adafruit_Python_CharLCD.git
cd Adafruit_Python_CharLCD
sudo python setup.py install
cd ..
git clone https://github.com/adafruit/Adafruit_Python_DHT.git
cd Adafruit_Python_DHT
sudo python setup.py install
cd ..
git clone https://github.com/supernova2468/smartrelay.git
cd smartrelay
sed -i -e '$i \ntpdate 0.us.pool.ntp.org\n' rc.local
