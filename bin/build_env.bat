@echo off

IF "%SLAVE_NAME%"=="" (GOTO error_no_slave_name)
IF "%SLAVE_ROOT%"=="" (GOTO error_no_slave_root)

pushd %SLAVE_ROOT%\buildslave\%SLAVE_NAME%\emsdk
call emsdk_env.bat
popd

echo "System version information: (ver):"
call ver

echo "Node version:"
where node
node --version
echo "Clang version:"
where clang
clang --version

echo "Currently checked out emscripten branch:"
git log -n1

echo "Currently checked out emscripten-fastcomp branch:"
pushd %SLAVE_ROOT%\buildslave\%SLAVE_NAME%\emsdk\clang\fastcomp\src
git log -n1
popd

echo "Currently checked out emscripten-fastcomp-clang branch:"
pushd %SLAVE_ROOT%\buildslave\%SLAVE_NAME%\emsdk\clang\fastcomp\src\tools\clang
git log -n1
popd

echo "ENVIRONMENT VARIABLES: "
echo "- EM_CONFIG: "
echo %EM_CONFIG%
echo "- EM_CACHE: "
echo %EM_CACHE%
echo "- EMSCRIPTEN: "
echo %EMSCRIPTEN%
echo "- PATH: "
echo %PATH%
echo "- SPIDERMONKEY: "
echo %SPIDERMONKEY%

EXIT /B %ERRORLEVEL%

:error_no_slave_root
echo Need to set SLAVE_ROOT env. var before running build_env.bat!
goto :eof

:error_no_slave_name
echo Need to set SLAVE_NAME env. var before running build_env.bat!
goto :eof
