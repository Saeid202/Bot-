"""Run the bot with visible browser to see what's happening"""
import sys
from pathlib import Path

# Add the project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python-product-AIBot"))

from scraper.alibaba_scraper import AlibabaScraper
from scraper.normalize import normalize_product
import requests

# Supabase config
SUPABASE_URL = "https://pbkbefdxgskypehrrgvq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBia2JlZmR4Z3NreXBlaHJyZ3ZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM0MjE5NzcsImV4cCI6MjA3ODk5Nzk3N30.r8bq63S5SjYdennWWjN9rWyH_ga15gvwhcZH-yByhW0"

def insert_products_supabase(products):
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    resp = requests.post(url, json=products, headers=headers)
    resp.raise_for_status()
    return resp.json()

def run_bot_visible(query="power bank", max_results=5):
    print("=" * 50)
    print("Running bot with VISIBLE browser")
    print("You will see the browser window open")
    print("=" * 50)
    
    # Temporarily modify the scraper to run in visible mode
    from playwright.sync_api import sync_playwright
    import random
    import time
    
    with sync_playwright() as p:
        # Launch browser in VISIBLE mode (headless=False)
        browser = p.chromium.launch(
            headless=False,  # VISIBLE MODE - you'll see the browser
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
            color_scheme='light',
        )
        
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = context.new_page()
        page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        url = f"https://www.alibaba.com/trade/search?SearchText={query}"
        print(f"\nNavigating to: {url}")
        print("Watch the browser window to see what happens...\n")
        
        page.goto(url, wait_until='networkidle', timeout=30000)
        time.sleep(random.uniform(2, 4))
        
        try:
            page.wait_for_selector(".organic-gallery-offer-card", timeout=10000)
        except:
            page.wait_for_timeout(3000)
        
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
                try:
                    title = item.locator("h2, .title, [class*='title']").first.inner_text()
                except:
                    title = ""

            try:
                price = item.locator(".element-offer-price-normal_price").inner_text()
            except:
                try:
                    price = item.locator(".price, [class*='price']").first.inner_text()
                except:
                    price = ""

            if title or price:
                products.append({
                    "title": title.strip() if title else "",
                    "price": price.strip() if price else "",
                    "source": "Alibaba"
                })

        print(f"\n✓ Scraped {len(products)} products.")
        
        if products:
            print("\nProducts found:")
            for i, p in enumerate(products, 1):
                print(f"  {i}. {p['title']} - {p['price']}")
        
        # Wait a bit so you can see the page
        print("\nBrowser will close in 5 seconds...")
        time.sleep(5)
        
        context.close()
        browser.close()
        
        # Normalize and insert
        if products:
            normalized = [normalize_product(p) for p in products]
            supabase_products = []
            for p in normalized:
                supabase_products.append({
                    "name": p["title"],
                    "price": p["price"],
                    "source": p.get("source", "Alibaba"),
                })

            print("\nInserting products into Supabase...")
            try:
                inserted = insert_products_supabase(supabase_products)
                print(f"✔ {len(inserted)} products inserted into Supabase.")
            except Exception as e:
                print(f"❌ Failed to insert products: {e}")
        else:
            print("\n⚠ No products to insert. Check the browser window to see if CAPTCHA appeared.")

if __name__ == "__main__":
    query = "power bank"  # Change this
    max_results = 5       # Change this
    run_bot_visible(query=query, max_results=max_results)

