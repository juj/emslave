#!/bin/bash

if [ -z "$SLAVE_NAME" ]; then
    echo "Need to set SLAVE_NAME env. var before running update_emslave.bash!"
    exit 1
fi

cd ~/emslave
git pull

if [ ! -d "~/emslave/buildslave/$SLAVE_NAME" ]; then
	echo "ERROR: ~/emslave/buildslave/$SLAVE_NAME should exist at this point?!"
	exit 1
fi

if [ ! -d "~/emslave/buildslave/$SLAVE_NAME/emsdk" ]; then
	cd ~/emslave/buildslave/$SLAVE_NAME
	git clone https://github.com/juj/emsdk/
	cd emsdk
fi

cd ~/emslave/buildslave/$SLAVE_NAME/emsdk
git pull
./emsdk install sdk-incoming-64bit
./emsdk activate --embedded sdk-incoming-64bit
