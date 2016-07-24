@echo off
IF [%SLAVE_NAME%]==[] (GOTO error_no_slave_name)
IF [%SLAVE_ROOT%]==[] (GOTO error_no_slave_root)
IF [%FIREFOX_BROWSER%]==[] (GOTO error_no_firefox_browser)
IF [%TEST_RUNNER_PARAMS%]==[] (GOTO error_no_test_runner_params)
call build_env.bat

echo Killing any old leftover firefox processes:
call taskkill /f /im firefox.exe

echo Removing old Firefox user profile and creating a new one..

rmdir /s /q %SLAVE_ROOT%\emscripten_firefox_profile
mkdir %SLAVE_ROOT%\emscripten_firefox_profile
xcopy %SLAVE_ROOT%\firefox_profile_template\* %SLAVE_ROOT%\emscripten_firefox_profile\

set EMSCRIPTEN_BROWSER=%FIREFOX_BROWSER% -profile %SLAVE_ROOT:\=/%/emscripten_firefox_profile

echo ENVIRONMENT VARIABLES: 
echo - EMSCRIPTEN_BROWSER: "%EMSCRIPTEN_BROWSER%"

echo Running browser tests..
python -u tests/runner.py %TEST_RUNNER_PARAMS% skip:browser.test_html_source_map
set RETURNCODE=%ERRORLEVEL%
echo Test run finished with process exit code %RETURNCODE%. Killing any running firefox processes:
call taskkill /f /im firefox.exe

EXIT /B %RETURNCODE%

:error_no_slave_name
echo Need to set SLAVE_NAME env. var before running run_firefox_tests.bat!
goto :eof

:error_no_slave_root
echo Need to set SLAVE_ROOT env. var before running run_firefox_tests.bat!
goto :eof

:error_no_firefox_browser
echo Need to set FIREFOX_BROWSER env. var before running run_firefox_tests.bat!
goto :eof

:error_no_test_runner_params
echo Need to set TEST_RUNNER_PARAMS env. var before running run_firefox_tests.bat!
goto :eof
