#!/bin/bash

build_env.bash

echo "Currently checked out emscripten branch:"
git log -n1

echo "Currently checked out emscripten-fastcomp branch:"
pushd ~/emslave/buildslave/$SLAVE_NAME/emsdk/clang/fastcomp/src
git log -n1
popd

echo "Currently checked out emscripten-fastcomp-clang branch:"
pushd ~/emslave/buildslave/$SLAVE_NAME/emsdk/clang/fastcomp/src/tools/clang
git log -n1
popd

python tests/parallel_test_core.py ALL.test_hello_world
