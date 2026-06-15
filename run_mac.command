#!/bin/bash
cd "$(dirname "$0")"
echo "Installing dependencies..."
pip3 install -r requirements.txt
echo "Starting application..."
python3 -m streamlit run app.py
