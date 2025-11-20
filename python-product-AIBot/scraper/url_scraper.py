"""Scraper that accepts a URL and extracts products from that page"""
import sys
import os

# CRITICAL: Set event loop policy BEFORE importing Playwright on Windows
if sys.platform == 'win32':
    import asyncio
    # Python 3.13+ on Windows: Use ProactorEventLoop for subprocess support
    # This is required for Playwright to create subprocesses
    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    elif hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        # Fallback to Selector if Proactor not available
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    from playwright.sync_api import sync_playwright
except Exception:
    # Playwright may not be installed in test environments; allow
    # importing this module and let callers mock or handle absence.
    sync_playwright = None
import random
import time

class URLScraper:
    """Scraper that works with direct URLs instead of search queries"""
    
    def scrape_from_url(self, url, max_results=10):
        """
        Scrape products from a given URL
        
        Args:
            url: The Alibaba page URL to scrape
            max_results: Maximum number of products to extract
            
        Returns:
            List of product dictionaries with title, price, and source
        """
        # If Playwright is not available, inform and return empty list
        if sync_playwright is None:
            print("Playwright is not installed or available in this environment. Skipping scrape.")
            return []

        # Ensure event loop policy is set (double-check)
        if sys.platform == 'win32':
            import asyncio
            if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            elif hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        with sync_playwright() as p:
            # Launch browser with stealth settings
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            
            # Create context with realistic settings
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                color_scheme='light',
            )
            
            # Add stealth scripts to hide automation
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                window.chrome = {
                    runtime: {}
                };
                
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' })
                    })
                });
            """)
            
            page = context.new_page()
            
            # Add extra headers
            page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })

            # Navigate to the provided URL
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Random delay to mimic human behavior
            time.sleep(random.uniform(2, 4))
            
            # Wait for content to load - try multiple selectors
            items = []
            selectors = [
                ".organic-gallery-offer-card",
                ".gallery-offer-card",
                "[data-content='product']",
                ".offer-card",
                ".product-card",
                ".gallery-item",
                ".list-item",
                "[class*='product']",
                "[class*='offer']"
            ]
            
            # Try to find products with different selectors
            for selector in selectors:
                try:
                    page.wait_for_selector(selector, timeout=5000)
                    items = page.locator(selector).all()
                    if len(items) > 0:
                        break
                except:
                    continue
            
            # If no items found, wait a bit more and try again
            if len(items) == 0:
                page.wait_for_timeout(3000)
                for selector in selectors:
                    items = page.locator(selector).all()
                    if len(items) > 0:
                        break

            products = []
            for item in items[:max_results]:
                try:
                    # Try primary selectors first
                    title = ""
                    price = ""
                    
                    try:
                        title = item.locator(".element-title-normal_content").inner_text()
                    except:
                        try:
                            title = item.locator(".element-title, .title, h2, h3, [class*='title']").first.inner_text()
                        except:
                            try:
                                title = item.locator("a").first.get_attribute("title") or ""
                            except:
                                title = ""

                    try:
                        price = item.locator(".element-offer-price-normal_price").inner_text()
                    except:
                        try:
                            price = item.locator(".price, [class*='price'], [class*='Price']").first.inner_text()
                        except:
                            try:
                                price = item.locator("[class*='cost'], [class*='amount']").first.inner_text()
                            except:
                                price = ""

                    if title or price:  # Only add if we got some data
                        products.append({
                            "title": title.strip() if title else "N/A",
                            "price": price.strip() if price else "N/A",
                            "source": "Alibaba",
                            "url": url
                        })
                except Exception as e:
                    # Skip items that cause errors
                    continue

            context.close()
            browser.close()
            return products

