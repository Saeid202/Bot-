@echo off
title Streamlit - Product Scraper Bot
color 0A
echo ========================================
echo   Product Scraper Bot - Web Interface
echo ========================================
echo.
echo Starting Streamlit server...
echo.
echo IMPORTANT: Keep this window open!
echo The server will be available at: http://localhost:8501
echo.
echo To stop the server, press Ctrl+C
echo.
echo ========================================
echo.

cd /d "%~dp0"
python -m streamlit run web_interface.py

pause

