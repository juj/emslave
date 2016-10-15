@echo off

IF [%SLAVE_NAME%]==[] (GOTO error_no_slave_name)
IF [%SLAVE_ROOT%]==[] (GOTO error_no_slave_root)

pushd %SLAVE_ROOT%\buildslave\%SLAVE_NAME%\emsdk
call emsdk_env.bat --vs2015 --embedded
popd

echo System version information: (ver):
call ver

echo Node version:
where node
node --version
echo Clang version:
where clang
clang --version

echo Currently checked out emscripten branch:
git log -n1

echo Currently checked out emscripten-fastcomp branch:
pushd %SLAVE_ROOT%\buildslave\%SLAVE_NAME%\emsdk\clang\fastcomp\src
git log -n1
popd

echo Currently checked out emscripten-fastcomp-clang branch:
pushd %SLAVE_ROOT%\buildslave\%SLAVE_NAME%\emsdk\clang\fastcomp\src\tools\clang
git log -n1
popd

echo ENVIRONMENT VARIABLES:
echo - PATH: "%PATH%"
echo - EM_CONFIG: "%EM_CONFIG%"
echo - EM_CACHE: "%EM_CACHE%"
echo - EMSCRIPTEN: "%EMSCRIPTEN%"
echo - EMSCRIPTEN_TEMP: "%EMSCRIPTEN_TEMP%"
echo - EMSCRIPTEN_BROWSER: "%EMSCRIPTEN_BROWSER%"
echo - BINARYEN_ROOT: "%BINARYEN_ROOT%"
echo - SPIDERMONKEY: "%SPIDERMONKEY%"
echo - FIREFOX_STABLE_BROWSER: "%FIREFOX_STABLE_BROWSER%"
echo - FIREFOX_BETA_BROWSER: "%FIREFOX_BETA_BROWSER%"
echo - FIREFOX_AURORA_BROWSER: "%FIREFOX_AURORA_BROWSER%"
echo - FIREFOX_NIGHTLY_BROWSER: "%FIREFOX_NIGHTLY_BROWSER%"

echo "Setting unbuffered python mode.."
set PYTHONUNBUFFERED=1

EXIT /B %ERRORLEVEL%

:error_no_slave_root
echo Need to set SLAVE_ROOT env. var before running build_env.bat!
goto :eof

:error_no_slave_name
echo Need to set SLAVE_NAME env. var before running build_env.bat!
goto :eof
