"""Debug script to inspect website structure and find product selectors"""
import sys
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python-product-AIBot"))

# Set event loop policy for Windows
if sys.platform == 'win32':
    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.async_api import async_playwright


async def debug_website(url):
    """Debug a website to find product selectors"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible browser
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        
        # Take screenshot
        await page.screenshot(path="debug_page.png")
        print("✓ Screenshot saved to: debug_page.png")
        
        # Get page title
        title = await page.title()
        print(f"\nPage Title: {title}")
        
        # Try common product selectors
        print("\n" + "="*50)
        print("Testing Common Product Selectors:")
        print("="*50)
        
        selectors_to_test = [
            "[data-product-id]",
            "[data-product]",
            ".product",
            ".product-item",
            ".product-card",
            ".item",
            "[class*='product']",
            "[class*='item']",
            "[class*='card']",
            "article",
            ".goods",
            ".commodity",
            ".listing",
            "[id*='product']",
            "[id*='item']"
        ]
        
        found_selectors = []
        for selector in selectors_to_test:
            try:
                items = await page.locator(selector).all()
                count = len(items)
                if count > 0:
                    print(f"✓ {selector}: Found {count} items")
                    found_selectors.append((selector, count))
                else:
                    print(f"✗ {selector}: 0 items")
            except Exception as e:
                print(f"✗ {selector}: Error - {e}")
        
        # Get all links that might be products
        print("\n" + "="*50)
        print("Analyzing Links:")
        print("="*50)
        
        links = await page.locator("a[href]").all()
        print(f"Total links found: {len(links)}")
        
        # Look for product-like links
        product_links = []
        for link in links[:20]:  # Check first 20 links
            try:
                href = await link.get_attribute("href")
                text = await link.inner_text()
                if href and text and len(text.strip()) > 5:
                    if any(keyword in href.lower() or keyword in text.lower() 
                           for keyword in ['product', 'item', 'goods', 'detail', 'buy', 'shop']):
                        product_links.append((text[:50], href))
            except:
                pass
        
        if product_links:
            print(f"\nPotential product links found: {len(product_links)}")
            for text, href in product_links[:5]:
                print(f"  - {text}: {href}")
        
        # Get page HTML structure (sample)
        print("\n" + "="*50)
        print("Page Structure Analysis:")
        print("="*50)
        
        # Check for common e-commerce patterns
        body_text = await page.locator("body").inner_text()
        if "product" in body_text.lower() or "item" in body_text.lower():
            print("✓ Page contains product-related text")
        
        # Look for price patterns
        price_patterns = await page.locator("[class*='price'], [class*='cost'], [class*='amount'], [id*='price']").all()
        print(f"✓ Found {len(price_patterns)} elements with price-related classes/ids")
        
        # Wait for user to inspect
        print("\n" + "="*50)
        print("Browser will stay open for 30 seconds for inspection...")
        print("="*50)
        await asyncio.sleep(30)
        
        await browser.close()
        
        # Recommendations
        print("\n" + "="*50)
        print("Recommendations:")
        print("="*50)
        if found_selectors:
            best_selector = max(found_selectors, key=lambda x: x[1])
            print(f"Best selector: {best_selector[0]} (found {best_selector[1]} items)")
        else:
            print("No common selectors found. This site may need custom scraping logic.")


if __name__ == "__main__":
    url = "https://www.wanhui-sh.com.cn"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    asyncio.run(debug_website(url))

