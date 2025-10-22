@echo off
setlocal EnableDelayedExpansion

cd /d C:\Users\Public\Documents\KSMTA_Optimization

set "LOGDIR=%~dp0logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

for /f %%I in ('powershell -NoLogo -NoProfile -Command "Get-Date -Format yyyyMMddHHmmss"') do (
  set "TIMESTAMP=%%I"
)
set "LOGFILE=!LOGDIR!\run_from_queue_!TIMESTAMP!.log"

echo [%DATE% %TIME%] Starting run_from_queue>>"!LOGFILE!"

echo Checking virtual environment>>"!LOGFILE!"
if not exist ".venv\Scripts\activate.bat" (
  echo [%DATE% %TIME%] .venv not found at "%CD%\.venv">>"!LOGFILE!"
  echo .venv not found at "%CD%\.venv"
  echo [%DATE% %TIME%] Finished run_from_queue with exit code 1>>"!LOGFILE!"
  exit /b 1
)

call ".venv\Scripts\activate.bat" >>"!LOGFILE!" 2>&1

REM Prove we're in the venv
python -c "import sys,site; print('Using Python:', sys.executable); print('site-packages:', *site.getsitepackages(), sep='\n  ')" >>"!LOGFILE!" 2>&1

python scripts\run_from_queue.py %* >>"!LOGFILE!" 2>&1

set "EXITCODE=%ERRORLEVEL%"
echo [%DATE% %TIME%] Finished run_from_queue with exit code %EXITCODE%>>"!LOGFILE!"
exit /b %EXITCODE%
