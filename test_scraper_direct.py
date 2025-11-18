"""Direct test of the scraper to debug issues"""
import sys
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python-product-AIBot"))

# Set event loop policy
if sys.platform == 'win32':
    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from scraper.scraper_factory import create_scraper
from scraper.url_scraper_async import scrape_from_url_sync

def test_scraper():
    """Test scraper with different URLs"""
    test_urls = [
        "https://www.amazon.com/s?k=laptop",
        "https://www.ebay.com/sch/i.html?_nkw=phone",
        "https://www.wanhui-sh.com.cn"
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        print('='*60)
        
        try:
            products = scrape_from_url_sync(url, max_results=3)
            print(f"✓ Scraped {len(products)} products")
            
            if products:
                for i, p in enumerate(products, 1):
                    print(f"\n  Product {i}:")
                    print(f"    Title: {p.get('title', 'N/A')[:50]}")
                    print(f"    Price: {p.get('price', 'N/A')}")
                    print(f"    Source: {p.get('source', 'N/A')}")
            else:
                print("  ⚠ No products found")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_scraper()

