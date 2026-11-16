@echo off
set "SVPURE=%LOCALAPPDATA%\SnowVoicePure\App"
if not exist "%SVPURE%\.venv\Scripts\pythonw.exe" (
 echo Please run install.bat first.
 pause
 exit /b 1
)
start "" "%SVPURE%\.venv\Scripts\pythonw.exe" "%SVPURE%\SnowVoice.pyw" --settings
