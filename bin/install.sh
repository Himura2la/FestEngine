#!/bin/bash

if [[ ! $1 == "" ]]; then
    LIB_NAME=`basename $1`
    echo "$LIB_NAME: "

    if [[ $LIB_NAME == *"wx"* || $LIB_NAME == *"vlc"* ]]; then
        echo Protected lib, skipping
        echo
        exit 0
    fi
    
    LOCATE_OUT=`locate $LIB_NAME`
    
    if [[ $LOCATE_OUT == *"/lib/"* ]]; then
        echo $LOCATE_OUT
        echo Removing
        rm $LIB_NAME
    else
        echo Not found
    fi

    echo
    exit 0
fi

echo This script removes the libraries that you already have in your system. 
echo Trying to run \'updatedb\'. This can take a while in case of success.
updatedb
if [[ $? -ne 0 ]]; then
    echo "Failed to run 'updatedb'. The installation may be better if you run me as a superuser :3 (sudo $0)"
fi

find . -maxdepth 1 -type f -name 'lib*' -exec $0 '{}' \;
exit 0
