"""Quick test to verify imports work"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python-product-AIBot"))

try:
    from scraper.scraper_factory import create_scraper
    from scraper.site_detector import detect_site_from_url, get_all_supported_sites
    from scraper.normalize import normalize_product, prepare_for_database
    
    print("✓ All imports successful!")
    
    # Test site detection
    test_urls = [
        "https://www.amazon.com/s?k=laptop",
        "https://www.ebay.com/sch/i.html",
        "https://www.alibaba.com/trade/search",
        "https://www.unknown-site.com"
    ]
    
    print("\n✓ Site Detection Tests:")
    for url in test_urls:
        site = detect_site_from_url(url)
        print(f"  {url[:40]}... -> {site}")
    
    # Test factory
    print("\n✓ Factory Tests:")
    scraper = create_scraper(url="https://www.amazon.com/s?k=laptop")
    print(f"  Created scraper: {scraper.site_name}")
    
    scraper2 = create_scraper(site_name="eBay")
    print(f"  Created scraper: {scraper2.site_name}")
    
    # Test supported sites
    print(f"\n✓ Supported sites: {len(get_all_supported_sites())} sites")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

