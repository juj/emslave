@echo off

IF "%SLAVE_NAME%"=="" (GOTO error_no_slave_name)

call build_env.bat

call emcc --clear-cache

call python -u tests/parallel_test_core.py

EXIT /B %ERRORLEVEL%

:error_no_slave_name
echo Need to set SLAVE_NAME env. var before running run_default_suite.bat!
goto :eof
