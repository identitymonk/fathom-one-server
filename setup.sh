
# install startup script
# ONLY RUN THIS ONCE
head -n -1 /etc/rc.local > rc.local.tmp
#echo "/usr/bin/gpio -g mode 2 alt0" >> rc.local.tmp
echo "cd /home/pi/SERVER/" >> rc.local.tmp
echo "./app.sh >> /home/pi/launch_log.txt 2>&1 &" >> rc.local.tmp
echo "exit 0" >> rc.local.tmp

cat rc.local.tmp > /etc/rc.local
# end startup script install

# set ip address

# disable interface nameing
# sudo echo "  net.ifnames=0" >> /boot/cmdline.txt

# set wifi network priority in /etc/dhcpd.conf by setting the metric for each interface
