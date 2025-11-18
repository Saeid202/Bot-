@echo off
echo Starting Product Scraper Bot Web Interface...
echo.
cd /d "%~dp0"
streamlit run web_interface.py
pause

