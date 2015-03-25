sudo apt-get update
sudo apt-get install build-essential python-dev python-setuptools python-pip python-smbus ntp -y
sudo rm /etc/localtime
sudo ln -s /usr/share/zoneinfo/US/Central /etc/localtime
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
chmod 777 start.sh
echo "@reboot /var/lib/cloud9/smartrelay/smartrelay/start.sh > /var/lib/cloud9/smartrelay/smartrelay/start.log &" > temp
sudo crontab temp
rm temp
/sbin/iptables -A INPUT -p tcp --destination-port 22 -j DROP