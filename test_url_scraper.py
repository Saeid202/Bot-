"""Quick test for URL scraper"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python-product-AIBot"))

from scraper.url_scraper import URLScraper

def test_url_scraper():
    print("=" * 50)
    print("Testing URL Scraper")
    print("=" * 50)
    
    # Test URL (Alibaba search)
    test_url = "https://www.alibaba.com/trade/search?SearchText=power+bank"
    
    print(f"\nTesting URL: {test_url}")
    print("Scraping products...\n")
    
    scraper = URLScraper()
    products = scraper.scrape_from_url(test_url, max_results=5)
    
    print(f"✓ Scraped {len(products)} products.\n")
    
    if products:
        print("Products found:")
        for i, product in enumerate(products, 1):
            print(f"\n{i}. Title: {product.get('title', 'N/A')}")
            print(f"   Price: {product.get('price', 'N/A')}")
            print(f"   Source: {product.get('source', 'N/A')}")
    else:
        print("⚠ No products found. This might be due to CAPTCHA or page structure changes.")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_url_scraper()

