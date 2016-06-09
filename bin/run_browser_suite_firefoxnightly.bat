@echo off

IF "%FIREFOX_NIGHTLY_BROWSER%"=="" (GOTO error_no_firefox_nightly_browser)

set FIREFOX_BROWSER=%FIREFOX_NIGHTLY_BROWSER%

set TEST_RUNNER_PARAMS=browser
call run_firefox_tests.bat
EXIT /B %ERRORLEVEL%

:error_no_firefox_nightly_browser
echo Need to set FIREFOX_NIGHTLY_BROWSER env. var before running run_browser_suite_firefoxnightly.bat!
goto :eof
