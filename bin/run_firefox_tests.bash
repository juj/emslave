#!/bin/bash

if [ -z "$SLAVE_NAME" ]; then
    echo "Need to set SLAVE_NAME env. var before running run_firefox_tests.bash!"
    exit 1
fi

if [ -z "$FIREFOX_BROWSER" ]; then
    echo "Need to set FIREFOX_BROWSER env. var before running run_firefox_tests.bash!"
    exit 1
fi

source build_env.bash

echo "Killing any old leftover firefox processes:"
pkill -9 -x firefox

echo "Removing old Firefox user profile and creating a new one.."

rm -rf ~/emslave/emscripten_firefox_profile/
mkdir ~/emslave/emscripten_firefox_profile/
cp ~/emslave/firefox_profile_template/* ~/emslave/emscripten_firefox_profile/

export EMSCRIPTEN_BROWSER="$FIREFOX_BROWSER -profile $HOME/emslave/emscripten_firefox_profile/"

echo "Running browser tests.."
python tests/runner.py browser.test_sdl1 $BROWSER_RUN_SKIPS
rc=$?
echo "Test run finished. Killing any running firefox processes:"
pkill -9 -x firefox

exit $rc

