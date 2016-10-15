#!/bin/bash

if [ -z "$SLAVE_NAME" ]; then
    echo "Need to set SLAVE_NAME env. var before running run_binaryen_suite.bash!"
    exit 1
fi

source build_env.bash

echo "- CWD: "
echo $CWD

python -u $SLAVE_ROOT/buildslave/$SLAVE_NAME/emsdk/binaryen/master/check.py --no-test-waterfall --no-abort-on-first-failure
