#!/bin/bash

build_env.bash

python tests/parallel_test_core.py ALL.test_hello_world
