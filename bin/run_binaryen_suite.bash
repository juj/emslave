#!/bin/bash

if [ -z "$SLAVE_NAME" ]; then
    echo "Need to set SLAVE_NAME env. var before running run_binaryen_suite.bash!"
    exit 1
fi

source build_env.bash

echo "- CWD: "
echo $CWD

if [ "$(uname)" == "Darwin" ]; then # Mac OS X
	echo "Skipping GCC tests, they don't quite work on OS X at the moment."
	python -u $SLAVE_ROOT/buildslave/$SLAVE_NAME/emsdk/binaryen/master/check.py --no-test-waterfall --no-abort-on-first-failure --no-run-gcc-tests --valgrind=valgrind
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then # Linux
	python -u $SLAVE_ROOT/buildslave/$SLAVE_NAME/emsdk/binaryen/master/check.py --no-test-waterfall --no-abort-on-first-failure
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ]; then # Windows Cygwin
	python -u $SLAVE_ROOT/buildslave/$SLAVE_NAME/emsdk/binaryen/master/check.py --no-test-waterfall --no-abort-on-first-failure --no-run-gcc-tests
fi
