@echo off
cd /d "%~dp0"
set PYTHONPATH=%PYTHONPATH%;%~dp0
set VENV_DIR=.venv
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call "%VENV_DIR%\Scripts\activate.bat"
) else (
    echo .venv folder not found. Please ensure the virtual environment is set up correctly.
)
python utilities\extractor_cmd.py %*