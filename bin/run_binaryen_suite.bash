#!/bin/bash

if [ -z "$SLAVE_NAME" ]; then
    echo "Need to set SLAVE_NAME env. var before running run_binaryen_suite.bash!"
    exit 1
fi

source build_env.bash

python -u check.py --no-test-waterfall --no-abort-on-first-failure
