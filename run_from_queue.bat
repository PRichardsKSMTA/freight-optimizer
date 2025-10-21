@echo off
setlocal EnableDelayedExpansion

cd /d C:\Users\Public\Documents\KSMTA_Optimization

set "LOGDIR=%~dp0logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

for /f "tokens=2-7 delims=/.: " %%a in ("%DATE% %TIME%") do (
  set "MM=%%a"
  set "DD=%%b"
  set "YYYY=%%c"
  set "hh=%%d"
  set "mm=%%e"
  set "ss=%%f"
)

for %%V in (MM DD hh mm ss) do (
  set "_val=!%%V!"
  set "_val=0!_val!"
  set "%%V=!_val:~-2!"
)

set "TIMESTAMP=!YYYY!!MM!!DD!!hh!!mm!!ss!"
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
