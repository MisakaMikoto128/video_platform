#!/bin/bash
echo "ECycle OTA Client Development Environment"
echo "======================================"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install pylint pytest black
else
    source venv/bin/activate
fi

echo "Starting development environment..."
bash 