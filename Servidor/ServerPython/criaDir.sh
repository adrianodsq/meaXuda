#!/bin/sh
dir=$1
if [ -d "/home/ftp/sdFiles/"$dir ]; then
    echo "1"
else
    mkdir "/home/ftp/sdFiles/"$dir
fi;
