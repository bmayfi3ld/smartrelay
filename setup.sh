sudo ntpdate pool.ntp.org
date
sudo apt-get update
sudo apt-get install build-essential python-dev python-setuptools python-pip python-smbus -y
wget -c https://raw.github.com/RobertCNelson/tools/master/pkgs/dtc.sh
chmod +x dtc.sh
./dtc.sh
sudo pip install Adafruit_BBIO

sudo pip install gspread
