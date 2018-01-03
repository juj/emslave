#!/bin/bash

if [ -z "$SLAVE_ROOT" ]; then
    echo "Need to set SLAVE_ROOT env. var before running start_slave.bash!"
    exit 1
fi

if [ "$(uname)" == "Darwin" ]; then # Mac OS X
	export MACOSX_DEPLOYMENT_TARGET=10.11
	echo MACOSX_DEPLOYMENT_TARGET=$MACOSX_DEPLOYMENT_TARGET

	export LLVM_CMAKE_ARGS=-DCMAKE_OSX_SYSROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk,-DHAVE_FUTIMENS=0,-DCMAKE_MACOSX_DEPLOYMENT_TARGET=10.11
	echo LLVM_CMAKE_ARGS=$LLVM_CMAKE_ARGS
fi

cd $SLAVE_ROOT/buildslave
buildslave start
