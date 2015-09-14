#!/bin/bash

export RUN_BROWSER=/Applications/Firefox.app/Contents/MacOS/firefox
export RUN_BROWSER_SKIPS=
run_firefox_tests.bash
rc=$?
exit $rc

