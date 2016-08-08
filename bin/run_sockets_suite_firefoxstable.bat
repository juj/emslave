@echo off

IF [%FIREFOX_STABLE_BROWSER%]==[] (GOTO error_no_firefox_stable_browser)

set FIREFOX_BROWSER=%FIREFOX_STABLE_BROWSER%

set TEST_RUNNER_PARAMS=sockets
call run_firefox_tests.bat
EXIT /B %ERRORLEVEL%

:error_no_firefox_stable_browser
echo Need to set FIREFOX_STABLE_BROWSER env. var before running run_browser_suite_firefoxstable.bat!
goto :eof
