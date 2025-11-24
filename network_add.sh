#!/bin/sh
# scan available wifi networks
#sudo iwlist wlan0 scan | grep ESSID

# connect to available wifi network
#sudo iwconfig wlan0 essid Wifi2Home key s:ABCDE12345


# obtain ip address
# sudo dhclient wlan0

WPA_PATH="/etc/wpa_supplicant/wpa_supplicant.conf"
#WPA_PATH="blah.out"
# read command line arguments
SSID=$1
PSK=$2

# escape any bad characters

# build network string
NETWORK="### BEGIN FATHOM NETWORK ###\r\n
network={
    ssid=\"${SSID}\"
    psk=\"${PSK}\"
}
\r\n### END FATHOM NETWORK ###"

sudo cat $WPA_PATH | sudo sed '/###END###/q' > wpa.tmp
cat wpa.tmp  | sudo tee  $WPA_PATH > /dev/null

wpa_passphrase $1 $2 | sudo tee -a $WPA_PATH > /dev/null

# cycle wifi interface
sudo ifconfig wlan0 down
sudo ifconfig wlan0 up

