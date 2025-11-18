from playwright.sync_api import sync_playwright
import random
import time

class AlibabaScraper:

    def run(self, query, max_results=5):
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
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Random delay to mimic human behavior
            time.sleep(random.uniform(2, 4))
            
            # Wait for content to load
            try:
                # Wait for product cards to appear
                page.wait_for_selector(".organic-gallery-offer-card", timeout=10000)
            except:
                # If selector not found, wait a bit more and try alternative selectors
                page.wait_for_timeout(3000)
            
            # Try multiple selectors in case the page structure changed
            items = []
            selectors = [
                ".organic-gallery-offer-card",
                ".gallery-offer-card",
                "[data-content='product']",
                ".offer-card"
            ]
            
            for selector in selectors:
                items = page.locator(selector).all()
                if len(items) > 0:
                    break

            products = []
            for item in items[:max_results]:
                try:
                    title = item.locator(".element-title-normal_content").inner_text()
                except:
                    # Try alternative title selectors
                    try:
                        title = item.locator("h2, .title, [class*='title']").first.inner_text()
                    except:
                        title = ""

                try:
                    price = item.locator(".element-offer-price-normal_price").inner_text()
                except:
                    # Try alternative price selectors
                    try:
                        price = item.locator(".price, [class*='price']").first.inner_text()
                    except:
                        price = ""

                if title or price:  # Only add if we got some data
                    products.append({
                        "title": title.strip() if title else "",
                        "price": price.strip() if price else "",
                        "source": "Alibaba"
                    })

            context.close()
            browser.close()
            return products