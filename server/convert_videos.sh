#!/bin/sh
FILES="/home/pi/SERVER/server/static/recordings/*.h264"
for f in $FILES
do
  ls $f 
  # take action on each file. $f store current file name
  #cat $f
  string_to_replace=".mp4"
  result_string="${f/.h264/$string_to_replace}"
  echo $result_string
  MP4Box -fps 26 -add $f $result_string
  rm -f $f
done 

