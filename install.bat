@echo off
cd /d "%~dp0"
py -3 install_snowvoice.py %*
if errorlevel 1 echo Installation failed. Read the error above.
pause
