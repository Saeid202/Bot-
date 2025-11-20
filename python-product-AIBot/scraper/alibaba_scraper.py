try:
    from playwright.sync_api import sync_playwright
except Exception:
    # In test environments playwright may not be installed; allow tests
    # to monkeypatch `sync_playwright` on the module.
    sync_playwright = None
import random
import time

class AlibabaScraper:

    def run(self, query, max_results=5):
        try:
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

                url = f"https://www.alibaba.com/trade/search?SearchText={query}"
                
                # Navigate with realistic wait conditions
                try:
                    page.goto(url, wait_until='networkidle', timeout=30000)
                except Exception as e:
                    # If networkidle fails, try domcontentloaded
                    try:
                        page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    except:
                        raise Exception(f"Failed to navigate to {url}: {e}")
                
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
                    "[class*='product-item']",
                    "[class*='offer-item']"
                ]
                
                # Wait for at least one selector to appear
                for selector in selectors:
                    try:
                        page.wait_for_selector(selector, timeout=5000)
                        items = page.locator(selector).all()
                        if len(items) > 0:
                            break
                    except Exception:
                        continue
                
                # If no items found, wait a bit more and try again
                if len(items) == 0:
                    page.wait_for_timeout(3000)
                    for selector in selectors:
                        try:
                            items = page.locator(selector).all()
                            if len(items) > 0:
                                break
                        except Exception:
                            continue

                products = []
                for item in items[:max_results]:
                    try:
                        # Try to extract title
                        title = ""
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

                        # Try to extract price
                        price = ""
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

                        # Only add if we got some data
                        if title or price:
                            products.append({
                                "title": title.strip() if title else "",
                                "price": price.strip() if price else "",
                                "source": "Alibaba"
                            })
                    except Exception:
                        # Skip items that cause errors
                        continue

                return products
        except Exception as e:
            # Return empty list on error rather than crashing
            print(f"Error in AlibabaScraper: {e}")
            return []