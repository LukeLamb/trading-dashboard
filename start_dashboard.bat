@echo off
echo Starting Trading Dashboard...
echo ================================

REM Activate virtual environment and run dashboard
call venv\Scripts\activate.bat && python run_dashboard.py

pause