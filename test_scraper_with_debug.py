"""Test scraper with detailed debugging"""
import sys
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python-product-AIBot"))

if sys.platform == 'win32':
    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from typing import TYPE_CHECKING
import importlib

if TYPE_CHECKING:
    from playwright.async_api import async_playwright  # type: ignore

try:
    _pw_mod = importlib.import_module("playwright.async_api")
    async_playwright = _pw_mod.async_playwright
except Exception:
    async_playwright = None

async def debug_page(url):
    """Debug what's actually on the page"""
    if async_playwright is None:
        print("Playwright is not installed or available in this environment. Install Playwright to run this debug script.")
        return
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(5)
        
        # Check page title
        title = await page.title()
        print(f"Page title: {title}")
        
        # Check for CAPTCHA
        if "captcha" in title.lower() or "robot" in title.lower():
            print("⚠️ CAPTCHA detected!")
        
        # Get page content
        body_text = await page.locator("body").inner_text()
        print(f"Page has {len(body_text)} characters of text")
        
        # Try Amazon selectors
        print("\nTesting Amazon selectors:")
        for selector in ["[data-component-type='s-search-result']", ".s-result-item", "[data-asin]"]:
            count = await page.locator(selector).count()
            print(f"  {selector}: {count} items")
        
        # Try eBay selectors
        print("\nTesting eBay selectors:")
        for selector in [".s-item", "[data-view]"]:
            count = await page.locator(selector).count()
            print(f"  {selector}: {count} items")
        
        # Try generic selectors
        print("\nTesting generic selectors:")
        for selector in ["a[href*='product']", "a[href*='item']", ".product", ".item"]:
            count = await page.locator(selector).count()
            print(f"  {selector}: {count} items")
        
        print("\nBrowser will stay open for 20 seconds...")
        await asyncio.sleep(20)
        await browser.close()

if __name__ == "__main__":
    url = "https://www.amazon.com/s?k=laptop"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    asyncio.run(debug_page(url))

