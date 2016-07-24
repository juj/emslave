@echo off

IF "%SLAVE_NAME%"=="" (GOTO error_no_slave_name)

call build_env.bat

set EM_TESTRUNNER_DETECT_TEMPFILE_LEAKS=1
python -u tests/runner.py other
set EM_TESTRUNNER_DETECT_TEMPFILE_LEAKS=

EXIT /B %ERRORLEVEL%

:error_no_slave_name
echo Need to set SLAVE_NAME env. var before running run_other_suite.bat!
goto :eof
