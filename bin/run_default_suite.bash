#!/bin/bash

export NODE=/Users/clb/emsdk/node/0.10.18_64bit/bin
export PATH=/Users/clb/emsdk/node/0.10.18_64bit/bin:$PATH
#export SPIDERMONKEY=/home/clb/mozilla-central/obj-x86_64-unknown-linux-gnu/js/src/js

echo "System version information: (uname -a):"
uname -a
#echo "CPU information:"
#lscpu
#echo "Linux distribution:"
#lsb_release -a
echo "Node version:"
which node
node --version
echo "Clang version:"
which clang
clang --version
echo "PATH:"
echo $PATH
echo "SPIDERMONKEY: "
echo $SPIDERMONKEY
echo "Currently checked out emscripten branch:"
git rev-list --max-count=1 HEAD

python tests/parallel_test_core.py

