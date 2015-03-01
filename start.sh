# start.sh
# author: Brandon Mayfield
# script that handles starting all important systems

echo 'Started'

sleep 30

echo 'Adding Network'
/sbin/route add default gw 192.168.7.1

/usr/sbin/service ntp stop
/usr/sbin/ntpdate now.okstate.edu
sleep 15
/usr/sbin/service ntp start

echo 'Starting Main Thread'
python /var/lib/cloud9/workspace/smartrelay/main.py > /var/lib/cloud9/workspace/smartrelay/python.log &

echo 'Exiting'

