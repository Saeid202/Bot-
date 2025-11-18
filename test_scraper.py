"""Test script to verify the scraper works without Supabase"""
import sys
from pathlib import Path

# Add the project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Import with proper path handling
sys.path.insert(0, str(ROOT / "python-product-AIBot"))
from scraper.alibaba_scraper import AlibabaScraper
from scraper.normalize import normalize_product

def test_scraper():
    print("=" * 50)
    print("Testing Alibaba Scraper")
    print("=" * 50)
    
    query = "power bank"
    max_results = 3
    
    print(f"\nQuery: {query}")
    print(f"Max results: {max_results}\n")
    
    try:
        scraper = AlibabaScraper()
        print("Scraping products...")
        raw_products = scraper.run(query, max_results)
        
        print(f"\n✓ Scraped {len(raw_products)} products.\n")
        
        if raw_products:
            print("Raw products:")
            for i, product in enumerate(raw_products, 1):
                print(f"\n{i}. Title: {product.get('title', 'N/A')}")
                print(f"   Price: {product.get('price', 'N/A')}")
                print(f"   Source: {product.get('source', 'N/A')}")
            
            print("\n" + "=" * 50)
            print("Normalized products:")
            print("=" * 50)
            
            normalized = [normalize_product(p) for p in raw_products]
            for i, product in enumerate(normalized, 1):
                print(f"\n{i}. Title: {product.get('title', 'N/A')}")
                print(f"   Price: {product.get('price', 'N/A')}")
                print(f"   Source: {product.get('source', 'N/A')}")
            
            print("\n✓ Scraper test completed successfully!")
            return True
        else:
            print("⚠ Warning: No products were scraped. This might be due to:")
            print("  - Website structure changes")
            print("  - Network issues")
            print("  - Selector changes")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_scraper()

