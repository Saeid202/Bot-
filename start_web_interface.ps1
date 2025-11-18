# PowerShell script to start the web interface
Write-Host "Starting Product Scraper Bot Web Interface..." -ForegroundColor Green
Write-Host ""

# Navigate to script directory
Set-Location $PSScriptRoot

# Start Streamlit
streamlit run web_interface.py

