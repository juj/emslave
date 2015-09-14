#!/bin/bash

pushd ~/emslave/buildslave/$SLAVE_NAME/emsdk
./emsdk activate --embedded
source ./emsdk_env.sh
popd

echo "System version information: (uname -a):"
uname -a

if which lscpu >/dev/null; then
	echo "CPU information (lscpu):"
	lscpu
fi
if which lsb_release >/dev/null; then
	echo "Linux distribution (lsb_release -a):"
	lsb_release -a
fi

echo "Node version:"
which node
node --version
echo "Clang version:"
which clang
clang --version
echo "PATH:"
echo $PATH
echo "SPIDERMONKEY: "
echo $SPIDERMONKEY

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
