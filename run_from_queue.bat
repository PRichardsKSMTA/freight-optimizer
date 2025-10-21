@REM cd /d C:\Users\Public\Documents\KSMTA_Optimization
@REM call .venv\Scripts\activate.bat
@REM python scripts\run_from_queue.py


@REM @echo off
@REM cd /d C:\Users\Public\Documents\KSMTA_Optimization

@REM if not exist ".venv\Scripts\python.exe" (
@REM   echo .venv not found at "%CD%\.venv"
@REM   exit /b 1
@REM )

@REM ".venv\Scripts\python.exe" -c "import sys; print('Using Python:', sys.executable)"
@REM ".venv\Scripts\python.exe" scripts\run_from_queue.py %*


@echo off
cd /d C:\Users\Public\Documents\KSMTA_Optimization

if not exist ".venv\Scripts\activate.bat" (
  echo .venv not found at "%CD%\.venv"
  exit /b 1
)

call ".venv\Scripts\activate.bat"

REM Prove we're in the venv
python -c "import sys,site; print('Using Python:', sys.executable); print('site-packages:', *site.getsitepackages(), sep='\n  ')"

python scripts\run_from_queue.py %*
