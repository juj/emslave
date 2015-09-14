#!/bin/bash

if [ -z "$FIREFOX_AURORA_BROWSER" ]; then
    echo "Need to set FIREFOX_AURORA_BROWSER env. var before running run_browser_suite_firefoxaurora.bash!"
    exit 1
fi

export FIREFOX_BROWSER="$FIREFOX_AURORA_BROWSER"

export TEST_RUNNER_PARAMS=browser
run_firefox_tests.bash
rc=$?
exit $rc
