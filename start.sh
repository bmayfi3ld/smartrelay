# start.sh
# author: Brandon Mayfield
# script that handles starting all important systems

echo 'Started'

sleep 10

echo 'Adding Network'
/sbin/route add default gw 192.168.7.1

