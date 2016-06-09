@echo off

IF "%FIREFOX_BETA_BROWSER%"=="" (GOTO error_no_firefox_beta_browser)

set FIREFOX_BROWSER=%FIREFOX_BETA_BROWSER%

set TEST_RUNNER_PARAMS=browser
call run_firefox_tests.bat
EXIT /B %ERRORLEVEL%

:error_no_firefox_beta_browser
echo Need to set FIREFOX_BETA_BROWSER env. var before running run_browser_suite_firefoxbeta.bat!
goto :eof
