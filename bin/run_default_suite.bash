#!/bin/bash

if [ -z "$SLAVE_NAME" ]; then
    echo "Need to set SLAVE_NAME env. var before running run_default_suite.bash!"
    exit 1
fi

build_env.bash

python tests/parallel_test_core.py ALL.test_hello_world
