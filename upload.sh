#!/bin/bash

if [ "$1" != "" ] && [ "$2" != "" ]; then
  for i in $(cat "$1_files.txt")
  do
    eval "echo \"Uploading $i to /dev/tty$2...\""
    eval "ampy -p /dev/tty$2 put $i"
  done
else
  printf "Usage: upload.sh [sta/ap] [port]\nExample: upload.sh sta ACM0\n"
fi
