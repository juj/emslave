#!/bin/bash

if [ -z "$FIREFOX_BETA_BROWSER" ]; then
    echo "Need to set FIREFOX_BETA_BROWSER env. var before running run_browser_suite_firefoxbeta.bash!"
    exit 1
fi

export FIREFOX_BROWSER="$FIREFOX_BETA_BROWSER"

export TEST_RUNNER_PARAMS=browser.test_sdl1
run_firefox_tests.bash
rc=$?
exit $rc
