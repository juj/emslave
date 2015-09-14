#!/bin/bash

echo "Deleting .emscripten to recreate it from scratch."
rm -f ~/.emscripten
./emcc --help

echo "Contents of ~/.emscripten:"
cat ~/.emscripten

export NODE=/Users/clb/emsdk/node/0.10.18_64bit/bin
export PATH=/Users/clb/emsdk/node/0.10.18_64bit/bin:$PATH
#export SPIDERMONKEY=/home/clb/mozilla-central/obj-x86_64-unknown-linux-gnu/js/src/js

echo "Node version:"
node --version
echo "Clang version:"
clang --version
echo "PATH:"
echo $PATH
echo "Currently checked out emscripten branch:"
git rev-list --max-count=1 HEAD

python tests/runner.py other






