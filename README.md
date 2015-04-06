# SmartRelay
Oklahoma State University - Capstone Design

Control an outlet with detailed logs and offline support.

Highlights
* Uses common DIY components and public libraries
* Quick setup
* Enthusiast level of detail
* Control an outlet with internet connection
* Offline capabilities

## Why

In the Electrical Engineering program at Oklahoma State University you are required to take a capstone design class. Where you are required to use everything you have learned (or haven't learned) in a top level class to create an interesting and useful project. 

This project similar to common consumer level smart wall outlets will let you control an outlet and receive information about its power usage. Where this project exceeds is when you see the extra enthusiast features it has. 

After configuring the device can operate completely offline, logging and protecting your appliance without any support. If you have internet access however it will push its information to the cloud and allow remote disabling of the relay. 

##Setup

Run setup file from GitHub on a fresh BBB
```sh
wget https://github.com/supernova2468/smartrelay/raw/master/setup.sh --no-check-certificate
chmod u+rwx setup.sh
./setup.sh
```

Setup Config file

```sh
cd smartrelay
nano config.ini
```

Enter in required information

##Credits

This project makes use of several other GitHub projects under the MIT License, they are listed below.

* gspread - https://github.com/burnash/gspread - by: Anton Burnashev
* Adafruit's BeagleBone IO Python Library - https://github.com/adafruit/adafruit-beaglebone-io-python - by: Justin Cooper
* ARM Tools - https://github.com/RobertCNelson/tools - by: Robert Nelson
