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

#if [ -z "$TARGET_EMSCRIPTEN_BRANCH" ]; then
#    echo "Need to set TARGET_EMSCRIPTEN_BRANCH env. var to either 'master' or 'incoming' before running update_emslave.bash!"
#    exit 1
#fi

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
git checkout -- emscripten-tags.txt binaryen-tags.txt
git pull

rm -f ~/.emscripten || true
echo "This file should not be read, nothing but errors here!" > ~/.emscripten
