# Web Interface for Product Scraper Bot

## 🚀 How to Run the Web Interface

### Step 1: Navigate to Project Directory
```powershell
cd C:\Users\shaba\OneDrive\Desktop\BOT\Test-Project
```

### Step 2: Start the Web Interface
```powershell
streamlit run web_interface.py
```

### Step 3: Open in Browser
The interface will automatically open in your browser at:
```
http://localhost:8501
```

## 📋 How to Use

1. **Enter URL**: Paste an Alibaba product listing URL in the input field
2. **Set Max Products**: Choose how many products to scrape (1-100)
3. **Enable Database Save**: Toggle to save products to Supabase
4. **Click "Scrape Products"**: The bot will scrape and display results
5. **Review & Download**: View products and download as CSV if needed

## 🔗 Supported URLs

- ✅ Alibaba search results: `https://www.alibaba.com/trade/search?SearchText=power+bank`
- ✅ Category pages: `https://www.alibaba.com/catalog/power-bank_cid100003006`
- ✅ Product listing pages: Any Alibaba product listing URL

## ⚙️ Features

- 🖥️ **Web Interface**: Easy-to-use Streamlit interface
- 🔗 **URL Input**: Paste any Alibaba product page URL
- 📊 **Product Display**: View scraped products in a table
- 💾 **Database Integration**: Auto-save to Supabase
- 📥 **CSV Export**: Download scraped products as CSV
- ⚡ **Real-time Status**: See scraping progress in real-time

## 🛠️ Technical Details

- **Framework**: Streamlit
- **Scraper**: Playwright with stealth mode
- **Database**: Supabase
- **Language**: Python

## ⚠️ Troubleshooting

### If the interface doesn't start:
```powershell
# Make sure you're in the right directory
cd C:\Users\shaba\OneDrive\Desktop\BOT\Test-Project

# Install streamlit if needed
python -m pip install streamlit

# Run the interface
streamlit run web_interface.py
```

### If scraping returns 0 products:
- Check if the URL is valid
- CAPTCHA may be blocking (try different URLs)
- Page structure may have changed

### If database save fails:
- Verify Supabase table exists
- Check Supabase connection
- Run `python test_supabase.py` to test connection

## 📝 Example Usage

1. Open the web interface
2. Paste: `https://www.alibaba.com/trade/search?SearchText=power+bank`
3. Set max products to 10
4. Enable "Save to Supabase Database"
5. Click "Scrape Products"
6. Wait for results
7. Review and download if needed

Enjoy scraping! 🎉

