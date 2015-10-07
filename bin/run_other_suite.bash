#!/bin/bash

if [ -z "$SLAVE_NAME" ]; then
    echo "Need to set SLAVE_NAME env. var before running run_other_suite.bash!"
    exit 1
fi

source build_env.bash

python tests/runner.py other
