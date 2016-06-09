@echo off

IF "%SLAVE_ROOT%"=="" (GOTO error_no_slave_root)

cd %SLAVE_ROOT%\buildslave
buildslave start

EXIT /B %ERRORLEVEL%

:error_no_slave_root
echo Need to set SLAVE_ROOT env. var before running start_slave.bat!
goto :eof
