#!/bin/bash

if [ -z "$SLAVE_NAME" ]; then
    echo "Need to set SLAVE_NAME env. var before running update_emslave.bash!"
    exit 1
fi

cd ~/emslave
git pull
 
cd ~/emslave/buildslave/$SLAVE_NAME/emsdk
git pull
./emsdk install sdk-incoming-64bit
./emsdk activate --embedded sdk-incoming-64bit
