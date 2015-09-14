#!/bin/bash

if [ -z "$SLAVE_NAME" ]; then
    echo "Need to set SLAVE_NAME env. var before running update_emslave.bash!"
    exit 1
fi

if [ -z "$TARGET_EMSCRIPTEN_BRANCH" ]; then
    echo "Need to set TARGET_EMSCRIPTEN_BRANCH env. var to either 'master' or 'incoming' before running update_emslave.bash!"
    exit 1
fi

cd ~/emslave
git pull

if [ ! -d "$HOME/emslave/buildslave/$SLAVE_NAME" ]; then
	echo "ERROR: $HOME/emslave/buildslave/$SLAVE_NAME should exist at this point?!"
	exit 1
fi

if [ ! -d "$HOME/emslave/buildslave/$SLAVE_NAME/emsdk" ]; then
	cd $HOME/emslave/buildslave/$SLAVE_NAME
	git clone https://github.com/juj/emsdk/
	cd emsdk
fi

cd $HOME/emslave/buildslave/$SLAVE_NAME/emsdk
git pull
./emsdk install sdk-$TARGET_EMSCRIPTEN_BRANCH-64bit
./emsdk activate --embedded sdk-$TARGET_EMSCRIPTEN_BRANCH-64bit
