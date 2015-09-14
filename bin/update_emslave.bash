#!/bin/bash

cd ~/emslave
git pull
 
cd ~/emslave/buildslave/$SLAVE_NAME/emsdk
git pull
./emsdk install sdk-incoming-64bit
./emsdk activate --embedded sdk-incoming-64bit
