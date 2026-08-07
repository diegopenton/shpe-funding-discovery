@echo off
title SHPE Funding Discovery
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --default-timeout=180 --retries 10 -r requirements.txt
python -m streamlit run app.py
pause
