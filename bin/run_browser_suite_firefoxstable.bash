#!/bin/bash

if [ -z "$FIREFOX_STABLE_BROWSER" ]; then
    echo "Need to set FIREFOX_STABLE_BROWSER env. var before running run_browser_suite_firefoxstable.bash!"
    exit 1
fi

export FIREFOX_BROWSER="$FIREFOX_STABLE_BROWSER"

export TEST_RUNNER_PARAMS=browser.test_aaa_pthread_gcc_atomic_fetch_and_op
run_firefox_tests.bash
rc=$?
exit $rc
