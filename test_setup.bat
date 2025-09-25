@echo off
echo Testing Trading Dashboard Configuration System...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run configuration test
python test_config_standalone.py

echo.
pause