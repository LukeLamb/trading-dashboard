@echo off
echo Setting up Trading Dashboard virtual environment...

REM Remove existing virtual environment if it exists
if exist venv rmdir /s /q venv

REM Create new virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
pip install -r requirements.txt

echo.
echo Virtual environment setup complete!
echo.
echo To activate the virtual environment, run:
echo   venv\Scripts\activate.bat
echo.
echo To test the configuration system, run:
echo   python test_config_standalone.py
echo.
pause