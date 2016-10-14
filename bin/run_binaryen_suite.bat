@echo off

IF "%SLAVE_NAME%"=="" (GOTO error_no_slave_name)

call build_env.bat

call python -u check.py --no-test-waterfall --no-abort-on-first-failure --no-run-gcc-tests

EXIT /B %ERRORLEVEL%

:error_no_slave_name
echo Need to set SLAVE_NAME env. var before running run_binaryen_suite.bat!
goto :eof
