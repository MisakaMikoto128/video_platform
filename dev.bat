@echo off
echo ECycle OTA Client Development Environment
echo ======================================

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    pip install pylint pytest black
) else (
    call venv\Scripts\activate
)

echo Starting PowerShell development environment...
powershell -NoExit -Command "& {. .\venv\Scripts\Activate.ps1}"
