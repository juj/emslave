#!/bin/bash

echo "Deleting .emscripten to recreate it from scratch."
rm -f ~/.emscripten
./emcc --help

echo "Contents of ~/.emscripten:"
cat ~/.emscripten

export NODE=/Users/clb/emsdk/node/0.10.18_64bit/bin
export PATH=/Users/clb/emsdk/node/0.10.18_64bit/bin:$PATH
#export SPIDERMONKEY=/home/clb/mozilla-central/obj-x86_64-unknown-linux-gnu/js/src/js

echo "System version information:"
uname -a
echo "Node version:"
node --version
echo "Clang version:"
clang --version
echo "PATH:"
echo $PATH
echo "Currently checked out emscripten branch:"
git rev-list --max-count=1 HEAD

echo "Killing any old leftover firefox processes:"
pkill -9 -x firefox

echo "Removing old Firefox user profile and creating a new one.."

rm -rf ~/firefox_profiles/emcc_temp_profile/
mkdir ~/firefox_profiles/emcc_temp_profile/
cp ~/firefox_profiles/prefs.js ~/firefox_profiles/emcc_temp_profile/

export EMSCRIPTEN_BROWSER="$RUN_BROWSER -profile /home/clb/firefox_profiles/emcc_temp_profile/"
export SPIDERMONKEY=/home/clb/mozilla-central/obj-x86_64-unknown-linux-gnu/js/src/js

echo "Running browser tests.."
python tests/runner.py browser $RUN_BROWSER_SKIPS
rc=$?
echo "Test run finished. Killing any running firefox processes:"
pkill -9 -x firefox

exit $rc

