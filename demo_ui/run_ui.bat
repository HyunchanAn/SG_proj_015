@echo off
:: Starting Streamlit Demonstration UI
cd /d "%~dp0"
echo Checking python environment for streamlit...
streamlit run app.py
if %ERRORLEVEL% neq 0 (
    echo Streamlit failed to start. Trying to run using python -m streamlit.
    python -m streamlit run app.py
)
pause
