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
if [ "$(uname)" == "Darwin" ]; then # Mac OS X
	export EMSDK_TARGETS="sdk-$TARGET_EMSCRIPTEN_BRANCH-64bit crunch-1.04 node-0.12.2-64bit spidermonkey-nightly-2015-04-12-64bit"
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then # Linux
	export EMSDK_TARGETS="sdk-$TARGET_EMSCRIPTEN_BRANCH-64bit"
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ]; then # Windows Cygwin
	export EMSDK_TARGETS="sdk-$TARGET_EMSCRIPTEN_BRANCH-64bit crunch-1.03 node-0.12.2-64bit java-7.45-64bit spidermonkey-nightly-2015-04-12-64bit"
fi
./emsdk install $EMSDK_TARGETS
./emsdk activate --embedded $EMSDK_TARGETS
