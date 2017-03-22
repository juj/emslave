#!/bin/bash

if [ -z "$SLAVE_NAME" ]; then
    echo "Need to set SLAVE_NAME env. var before running run_firefox_tests.bash!"
    exit 1
fi

if [ -z "$SLAVE_ROOT" ]; then
    echo "Need to set SLAVE_ROOT env. var before running run_firefox_tests.bash!"
    exit 1
fi

if [ -z "$FIREFOX_BROWSER" ]; then
    echo "Need to set FIREFOX_BROWSER env. var before running run_firefox_tests.bash!"
    exit 1
fi

if [ -z "$TEST_RUNNER_PARAMS" ]; then
    echo "Need to set TEST_RUNNER_PARAMS env. var before running run_firefox_tests.bash!"
    exit 1
fi

source build_env.bash

echo "Killing any old leftover firefox processes:"
pkill -9 -x firefox
pkill -9 -x Firefox

echo "Removing old Firefox user profile and creating a new one.."

rm -rf $SLAVE_ROOT/emscripten_firefox_profile/
mkdir $SLAVE_ROOT/emscripten_firefox_profile/
cp $SLAVE_ROOT/firefox_profile_template/* $SLAVE_ROOT/emscripten_firefox_profile/

export EMSCRIPTEN_BROWSER="$FIREFOX_BROWSER -profile $SLAVE_ROOT/emscripten_firefox_profile/"

echo "ENVIRONMENT VARIABLES: "
echo "- EMSCRIPTEN_BROWSER: "
echo $EMSCRIPTEN_BROWSER

export TESTS_TO_SKIP=
if [ "$(uname)" == "Darwin" ]; then # Mac OS X
	export TESTS_TO_SKIP="skip:browser.test_html5_webgl_create_context skip:browser.test_glgears skip:browser.test_glgears_deriv skip:browser.test_subdata"
	echo "Skipping browser.test_html5_webgl_create_context because of https://bugzilla.mozilla.org/show_bug.cgi?id=1285937"
    echo "Skipping browser.test_glgears, browser.test_glgears_deriv and browser.test_subdata because of intermittent requestAnimationFrame-related failures (TODO)"
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then # Linux
	echo "."
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ]; then # Windows Cygwin
	echo "."
fi

# https://bugzilla.mozilla.org/show_bug.cgi?id=745154
export MOZ_DISABLE_AUTO_SAFE_MODE=1
echo "Set MOZ_DISABLE_AUTO_SAFE_MODE=1, see https://bugzilla.mozilla.org/show_bug.cgi?id=745154"

# https://bugzilla.mozilla.org/show_bug.cgi?id=653410#c9
export MOZ_DISABLE_SAFE_MODE_KEY=1
echo "Set MOZ_DISABLE_SAFE_MODE_KEY=1, see https://bugzilla.mozilla.org/show_bug.cgi?id=653410#c9"

# https://bugzilla.mozilla.org/show_bug.cgi?id=1299359#c0
export JIT_OPTION_asmJSAtomicsEnable=true
echo "Set JIT_OPTION_asmJSAtomicsEnable=true, see # https://bugzilla.mozilla.org/show_bug.cgi?id=1299359#c0"

echo "Running browser tests.."
echo "Skipping tests $TESTS_TO_SKIP"
python -u tests/runner.py $TEST_RUNNER_PARAMS $TESTS_TO_SKIP
rc=$?
echo "Test run finished. Killing any running firefox processes:"
pkill -9 -x firefox
pkill -9 -x Firefox

exit $rc

