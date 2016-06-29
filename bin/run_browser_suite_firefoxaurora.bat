@echo off

IF [%FIREFOX_AURORA_BROWSER%]==[] (GOTO error_no_firefox_aurora_browser)

set FIREFOX_BROWSER=%FIREFOX_AURORA_BROWSER%

set TEST_RUNNER_PARAMS=browser
call run_firefox_tests.bat
EXIT /B %ERRORLEVEL%

:error_no_firefox_aurora_browser
echo Need to set FIREFOX_AURORA_BROWSER env. var before running run_browser_suite_firefoxaurora.bat!
goto :eof
