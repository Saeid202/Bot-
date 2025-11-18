"""Debug script to test scraper with more visibility"""
import sys
from pathlib import Path

# Add the project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python-product-AIBot"))
from scraper.alibaba_scraper import AlibabaScraper
from playwright.sync_api import sync_playwright

def debug_scraper():
    print("=" * 50)
    print("Debugging Alibaba Scraper")
    print("=" * 50)
    
    query = "power bank"
    
    print(f"\nQuery: {query}\n")
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode to see what's happening
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        url = f"https://www.alibaba.com/trade/search?SearchText={query}"
        print(f"Navigating to: {url}")
        page.goto(url, wait_until="networkidle", timeout=30000)
        
        print("Waiting for page to load...")
        page.wait_for_timeout(5000)  # Wait 5 seconds
        
        # Take a screenshot to see what we're getting
        screenshot_path = "alibaba_page.png"
        page.screenshot(path=screenshot_path)
        print(f"✓ Screenshot saved to: {screenshot_path}")
        
        # Check page title
        title = page.title()
        print(f"Page title: {title}")
        
        # Try to find the selector
        print("\nLooking for products with selector: .organic-gallery-offer-card")
        items = page.locator(".organic-gallery-offer-card").all()
        print(f"Found {len(items)} items with that selector")
        
        # Try alternative selectors
        print("\nTrying alternative selectors...")
        alt_selectors = [
            ".gallery-offer-card",
            "[data-content='product']",
            ".offer-card",
            ".product-card",
            ".gallery-item"
        ]
        
        for selector in alt_selectors:
            count = len(page.locator(selector).all())
            if count > 0:
                print(f"  ✓ Found {count} items with: {selector}")
            else:
                print(f"  ✗ No items with: {selector}")
        
        # Check page content
        print("\nChecking page content...")
        body_text = page.locator("body").inner_text()
        if "power bank" in body_text.lower() or "product" in body_text.lower():
            print("✓ Page seems to have loaded content")
        else:
            print("⚠ Page content might not have loaded correctly")
        
        # Try to get any product-like elements
        print("\nLooking for any elements that might be products...")
        all_cards = page.locator("[class*='card'], [class*='product'], [class*='offer']").all()
        print(f"Found {len(all_cards)} potential product elements")
        
        if len(all_cards) > 0:
            print("\nFirst few element classes:")
            for i, card in enumerate(all_cards[:5], 1):
                try:
                    class_attr = card.get_attribute("class")
                    print(f"  {i}. {class_attr}")
                except:
                    pass
        
        browser.close()
        print("\n" + "=" * 50)
        print("Debug complete!")
        print("=" * 50)

if __name__ == "__main__":
    debug_scraper()

