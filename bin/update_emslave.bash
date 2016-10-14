#!/bin/bash

set -e

if [ -z "$SLAVE_NAME" ]; then
    echo "Need to set SLAVE_NAME env. var before running update_emslave.bash!"
    exit 1
fi

if [ -z "$SLAVE_ROOT" ]; then
    echo "Need to set SLAVE_ROOT env. var before running update_emslave.bash!"
    exit 1
fi

if [ -z "$TARGET_EMSCRIPTEN_BRANCH" ]; then
    echo "Need to set TARGET_EMSCRIPTEN_BRANCH env. var to either 'master' or 'incoming' before running update_emslave.bash!"
    exit 1
fi

cd $SLAVE_ROOT
git pull

if [ ! -d "$SLAVE_ROOT/buildslave/$SLAVE_NAME" ]; then
	echo "ERROR: $SLAVE_ROOT/buildslave/$SLAVE_NAME should exist at this point?!"
	exit 1
fi

if [ ! -d "$SLAVE_ROOT/buildslave/$SLAVE_NAME/emsdk" ]; then
	cd $SLAVE_ROOT/buildslave/$SLAVE_NAME
	git clone https://github.com/juj/emsdk/
	cd emsdk
fi

cd $SLAVE_ROOT/buildslave/$SLAVE_NAME/emsdk
git pull

export CMAKE_CONFIG_TO_BUILD=""
if [ "$(uname)" == "Darwin" ]; then # Mac OS X
	export EMSDK_TARGETS="sdk-$TARGET_EMSCRIPTEN_BRANCH-64bit crunch-1.04 binaryen-master-64bit"
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then # Linux
	export EMSDK_TARGETS="sdk-$TARGET_EMSCRIPTEN_BRANCH-64bit binaryen-master-64bit"
	# Override to build Release config because default RelWithDebInfo produces huge 7GB debugging symbols(!)
	export CMAKE_CONFIG_TO_BUILD="--build=Release"
	echo "We are on linux: building *Release* CMake configuration instead of the default one to avoid huge 7GB worth of debugging symbols being generated on disk, which exceeds total amount of RAM at link time on the Linux build slave."
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ]; then # Windows Cygwin
	export EMSDK_TARGETS="sdk-$TARGET_EMSCRIPTEN_BRANCH-64bit crunch-1.03 java-7.45-64bit spidermonkey-nightly-2015-04-12-64bit binaryen-master-64bit"
fi

./emsdk install --build-tests $CMAKE_CONFIG_TO_BUILD $EMSDK_TARGETS

rm -f ~/.emscripten || true
./emsdk activate --embedded $EMSDK_TARGETS
echo "This file should not be read, nothing but errors here!" > ~/.emscripten
