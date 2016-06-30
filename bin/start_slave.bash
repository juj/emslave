#!/bin/bash

if [ -z "$SLAVE_ROOT" ]; then
    echo "Need to set SLAVE_ROOT env. var before running start_slave.bash!"
    exit 1
fi

cd $SLAVE_ROOT/buildslave
buildslave start
