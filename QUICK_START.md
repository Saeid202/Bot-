# 🚀 Quick Start Guide

## How to Run the Web Interface

### Method 1: Double-Click (Easiest)
1. **Double-click** `start_web_interface.bat` in Windows Explorer
2. A terminal window will open and Streamlit will start
3. Your browser should open automatically to `http://localhost:8501`
4. **Keep the terminal window open** - closing it will stop the server

### Method 2: PowerShell/Command Prompt
1. Open PowerShell or Command Prompt
2. Navigate to the project:
   ```powershell
   cd C:\Users\shaba\OneDrive\Desktop\BOT\Test-Project
   ```
3. Run:
   ```powershell
   streamlit run web_interface.py
   ```
4. Wait for the message: `You can now view your Streamlit app in your browser`
5. Open your browser to `http://localhost:8501`

### Method 3: PowerShell Script
1. Right-click `start_web_interface.ps1`
2. Select "Run with PowerShell"
3. Browser should open automatically

## ⚠️ Important Notes

- **Keep the terminal window open** - Streamlit runs in that window
- If you see "ERR_CONNECTION_REFUSED", Streamlit is not running
- To stop Streamlit, press `Ctrl+C` in the terminal window
- If port 8501 is busy, use: `streamlit run web_interface.py --server.port 8502`

## 🔍 Troubleshooting

### "streamlit: command not found"
```powershell
pip install streamlit
```

### Port already in use
```powershell
streamlit run web_interface.py --server.port 8502
```
Then open `http://localhost:8502` in your browser

### Browser doesn't open automatically
Manually navigate to: `http://localhost:8501`

## 📋 What You'll See

Once running, you'll see:
- **Navigation sidebar** with two options:
  - "Scrape from URL" - Scrape products from e-commerce sites
  - "Upload PDF" - Extract products from PDF files
- Main interface for entering URLs or uploading PDFs

Enjoy! 🎉

