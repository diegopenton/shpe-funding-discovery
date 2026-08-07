@echo off
title SHPE Funding Discovery

if not exist .venv (
  echo Creating virtual environment...
  py -m venv .venv
)

call .venv\Scripts\activate.bat

python -c "import streamlit, pandas, pydeck" >nul 2>&1
if errorlevel 1 (
  echo Installing dependencies...
  python -m pip install --default-timeout=300 --retries 10 -r requirements.txt
)

python -m streamlit run app.py
pause
