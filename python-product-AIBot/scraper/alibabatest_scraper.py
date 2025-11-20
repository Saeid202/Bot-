import time
import random
import json
import logging
from typing import List, Dict, Optional

import requests
from typing import TYPE_CHECKING
import importlib

# Playwright (sync) - import dynamically so the script remains importable in envs without Playwright
if TYPE_CHECKING:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError  # type: ignore

try:
    _pw_mod = importlib.import_module("playwright.sync_api")
    sync_playwright = _pw_mod.sync_playwright
    PlaywrightTimeoutError = _pw_mod.TimeoutError
except Exception:
    sync_playwright = None
    class PlaywrightTimeoutError(Exception):
        pass

# ---------- Configuration ----------
BASE = "https://localhost3000/dashboard/products"  # your seller-center endpoints
HEADLESS = False   # Run visible browser to allow manual CAPTCHA solving
MAX_PRODUCTS = 20  # limit scrapes per job run
DELAY_RANGE = (4.0, 9.0)  # random delay between main actions (seconds)
SCROLL_PAUSE = (1.5, 3.5)  # pause between scroll steps
NAV_TIMEOUT = 30_000  # navigation timeout (ms)
PRODUCT_SELECTOR = "div.list-no-v2-outter div.list-item"  # may need adjustment
# Optional proxy (if you use one ethically). Example: "http://user:pass@host:port"
PROXY = None  # e.g. "http://username:password@123.123.123.123:8000" or None to skip

# A small pool of common user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
]

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------- Helpers for import job API ----------

try:
    from connector.website_api import start_import_job, insert_imported_products, complete_import_job  # type: ignore
    logging.info("Using connector.website_api functions for job handling.")
except Exception:
    logging.info("connector.website_api not found; falling back to direct HTTP calls to the API endpoints.")

    def start_import_job(query: str, max_results: int, marketplace: str) -> str:
        r = requests.post(f"{BASE}/start", json={
            "query": query,
            "marketplace": marketplace,
            "maxResults": max_results
        }, timeout=30)
        r.raise_for_status()
        return r.json().get("jobId")

    def insert_imported_products(job_id: str, normalized: List[Dict]):
        r = requests.post(f"{BASE}/insert-products", json={
            "jobId": job_id,
            "products": normalized
        }, timeout=60)
        r.raise_for_status()
        return r.json()

    def complete_import_job(job_id: str):
        r = requests.post(f"{BASE}/complete", json={"jobId": job_id}, timeout=30)
        r.raise_for_status()
        return r.json()


# ---------- CAPTCHA detection ----------
def detect_captcha(page_content: str) -> bool:
    """
    Simple heuristic: check for common words and fragments.
    This is intentionally conservative. Adjust if needed.
    """
    content = page_content.lower()
    if "captcha" in content or "verify" in content or "are you human" in content or "please verify" in content:
        return True
    return False


# ---------- Normalization ----------
def normalize_product(raw: Dict) -> Dict:
    """
    Convert raw scraped product data to a normalized dict that your Seller Center expects.
    Adjust fields as needed.
    """
    return {
        "title": raw.get("title") or raw.get("name") or "",
        "price": raw.get("price") or raw.get("price_text") or "",
        "currency": raw.get("currency") or "",
        "description": raw.get("description") or "",
        "images": raw.get("images") or [],
        "url": raw.get("url") or "",
        "source": raw.get("source") or "alibaba",
    }


# ---------- Scraper core ----------
def human_like_sleep():
    time.sleep(random.uniform(*DELAY_RANGE))


def random_user_agent():
    return random.choice(USER_AGENTS)


def humane_scroll(page, steps=6):
    """
    Scroll down to emulate a human reading/listing products.
    """
    for i in range(steps):
        # scroll a random length
        page.evaluate("window.scrollBy(0, document.body.scrollHeight / %s)" % random.randint(6, 12))
        time.sleep(random.uniform(*SCROLL_PAUSE))


def extract_products_from_listing(page) -> List[Dict]:
    """
    Extract product details from the listing page. This is a generic approach and may require
    adjustments to selectors to match Alibaba's DOM or the subdomain you're targeting.
    """
    products = []
    # Wait for listing container - gentle timeout
    try:
        page.wait_for_selector(PRODUCT_SELECTOR, timeout=7_000)
    except PlaywrightTimeoutError:
        logging.info("No product list container found with selector; returning empty list.")
        return products

    items = page.query_selector_all(PRODUCT_SELECTOR)
    logging.info(f"Found {len(items)} items in listing DOM (may contain sponsored/ads).")

    for idx, item in enumerate(items):
        if len(products) >= MAX_PRODUCTS:
            break
        try:
            title_el = item.query_selector("h2, h3, .title, .item-title")
            title = title_el.inner_text().strip() if title_el else ""

            url_el = item.query_selector("a")
            url = url_el.get_attribute("href") if url_el else ""
            # normalize relative URLs
            if url and url.startswith("/"):
                url = "https://www.alibaba.com" + url

            price_el = item.query_selector(".price, .price-current, .item-price")
            price = price_el.inner_text().strip() if price_el else ""

            img_el = item.query_selector("img")
            img_url = img_el.get_attribute("src") if img_el else None

            product = {
                "title": title,
                "price": price,
                "images": [img_url] if img_url else [],
                "url": url,
                "raw_html_snippet": item.inner_html()[:1000]  
            }

            products.append(product)
        except Exception as e:
            logging.exception("Error extracting single item: %s", e)
            continue

    return products


def fetch_product_detail(page, product_url: str) -> Dict:
    """
    Optionally visit product page for more details (longer delays).
    """
    try:
        page.goto(product_url, timeout=NAV_TIMEOUT)
    except PlaywrightTimeoutError:
        logging.warning("Timeout navigating to product page: %s", product_url)
        return {}
    time.sleep(random.uniform(2.5, 5.5))
    # If captcha detected on product page, return empty and let main flow handle it
    if detect_captcha(page.content()):
        return {}

    # Try to extract meaningful fields
    detail = {}
    try:
        # Adjust selectors based on actual product page structure
        title_el = page.query_selector("h1, .product-title, .module-title")
        detail["title"] = title_el.inner_text().strip() if title_el else None
        price_el = page.query_selector(".price, .product-price")
        detail["price"] = price_el.inner_text().strip() if price_el else None
        desc_el = page.query_selector("#product-description, .description, .product-description")
        detail["description"] = desc_el.inner_text().strip() if desc_el else None
        imgs = [img.get_attribute("src") for img in page.query_selector_all("img")[:6]]
        detail["images"] = [u for u in imgs if u]
    except Exception:
        logging.exception("Failed to extract product detail.")
    return detail


def scrape_alibaba(query: str, marketplace: str = "Alibaba", max_results: int = 10, headless: Optional[bool] = None):
    """
    Main entry. Starts a job, scrapes product listings, optionally visits product pages,
    normalizes data and sends it to the import API endpoints.
    """
    headless = HEADLESS if headless is None else headless
    user_agent = random_user_agent()

    job_id = None
    try:
        job_id = start_import_job(query, max_results, marketplace)
        logging.info("Started import job: %s", job_id)
    except Exception as e:
        logging.exception("Failed to start import job: %s", e)
        return

    scraped_normalized = []
    # If Playwright is not available, fall back to a lightweight HTTP-only scraper
    search_url = f"https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&SearchText={requests.utils.requote_uri(query)}"
    if sync_playwright is None:
        logging.warning("Playwright not available; using HTTP fallback (best-effort parsing).")
        try:
            r = requests.get(search_url, timeout=15)
            html = r.text
        except Exception as e:
            logging.exception("HTTP fallback failed to fetch search page: %s", e)
            return

        # Very small, permissive parser: find anchors and nearby price patterns
        import re
        anchors = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]{5,200})<', html, flags=re.I)
        products = []
        seen = set()
        price_re = re.compile(r"\$\s?\d[\d,\.]*")
        for href, text in anchors:
            if len(products) >= max_results:
                break
            title = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', text)).strip()
            if not title or title.lower().startswith('shop'):
                continue
            # Normalize URL
            url = href
            if url.startswith('/'):
                url = 'https://www.alibaba.com' + url
            if url in seen:
                continue
            seen.add(url)

            # find a price near the anchor position
            idx = html.find(text)
            nearby = html[max(0, idx-300): idx+300] if idx != -1 else html
            price_match = price_re.search(nearby)
            price = price_match.group(0) if price_match else ''

            products.append({
                'title': title,
                'price': price,
                'url': url,
                'images': [],
            })

        logging.info('HTTP fallback extracted %d candidate products', len(products))

        scraped_normalized = [normalize_product(p) for p in products[:max_results]]
        if scraped_normalized:
            try:
                logging.info('Inserting %d products for job %s', len(scraped_normalized), job_id)
                insert_resp = insert_imported_products(job_id, scraped_normalized)
                logging.info('Insert response: %s', str(insert_resp)[:200])
            except Exception as e:
                logging.exception('Failed to insert imported products via HTTP fallback: %s', e)

        try:
            complete_import_job(job_id)
            logging.info('Completed import job: %s', job_id)
        except Exception:
            logging.exception('Failed to mark job complete.')

        logging.info('HTTP fallback scrape run finished.')
        return

    with sync_playwright() as p:
        launch_kwargs = {"headless": headless}
        if PROXY:
            launch_kwargs["proxy"] = {"server": PROXY}

        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.set_default_navigation_timeout(NAV_TIMEOUT)

        # Build search URL for Alibaba - may need adjustments depending on country / subdomain
        search_url = f"https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&SearchText={requests.utils.requote_uri(query)}"
        logging.info("Navigating to %s", search_url)

        try:
            page.goto(search_url, timeout=NAV_TIMEOUT)
        except PlaywrightTimeoutError:
            logging.error("Timeout loading search page.")
            browser.close()
            return

        # Basic anti-bot humanization
        humane_scroll(page, steps=random.randint(4, 9))
        human_like_sleep()

        # Detect CAPTCHA
        if detect_captcha(page.content()):
            logging.warning("CAPTCHA detected on search page! Opening browser for manual solve.")
            print("\n=== CAPTCHA DETECTED ===")
            print("Please solve the CAPTCHA in the opened browser window. After solving, press ENTER here to continue.")
            input("Press ENTER after you have solved the challenge in the browser...")
            # After user presses enter, re-check
            if detect_captcha(page.content()):
                logging.error("CAPTCHA still detected after manual attempt. Aborting scraping to avoid violating terms.")
                browser.close()
                return
            logging.info("CAPTCHA solved (or not present). Continuing.")

        # Extract listing items
        products = extract_products_from_listing(page)
        logging.info("Extracted %s candidate products from listing.", len(products))

        # Optionally visit product pages for richer data
        for pidx, item in enumerate(products):
            if len(scraped_normalized) >= max_results:
                break

            # Randomize per-product wait and actions
            time.sleep(random.uniform(1.5, 3.5))
            # if item URL exists and looks valid, visit it for details
            if item.get("url"):
                detail = fetch_product_detail(page, item["url"])
                if detail and detect_captcha(page.content()):
                    # if visiting product triggered captcha, ask user to solve
                    logging.warning("CAPTCHA detected while visiting product detail. Pausing for manual solve.")
                    print("\n=== CAPTCHA ON PRODUCT PAGE ===")
                    input("Solve CAPTCHA (if present) and press ENTER to continue...")
                    if detect_captcha(page.content()):
                        logging.error("CAPTCHA still present after manual solve; skipping this product.")
                        continue
                # merge detail into item
                item.update(detail or {})

            normalized = normalize_product(item)
            scraped_normalized.append(normalized)
            logging.info("Product normalized: %s", normalized.get("title")[:60])

            # Gentle random delay before next product
            time.sleep(random.uniform(2.0, 5.0))

        # close browser gracefully
        browser.close()

    # Insert into your system
    if scraped_normalized:
        try:
            logging.info("Inserting %d products for job %s", len(scraped_normalized), job_id)
            insert_resp = insert_imported_products(job_id, scraped_normalized)
            logging.info("Insert response: %s", str(insert_resp)[:200])
        except Exception as e:
            logging.exception("Failed to insert imported products: %s", e)

    # Complete job
    try:
        complete_import_job(job_id)
        logging.info("Completed import job: %s", job_id)
    except Exception:
        logging.exception("Failed to mark job complete.")

    logging.info("Scrape run finished.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ethical Alibaba scraper (manual CAPTCHA handling).")
    parser.add_argument("--query", "-q", required=True, help="Search query (e.g., 'laptop case')")
    parser.add_argument("--max", "-m", type=int, default=10, help="Maximum products to scrape")
    parser.add_argument("--market", default="Alibaba", help="Marketplace name")
    parser.add_argument("--headless", action="store_true", help="Force headless (not recommended if CAPTCHAs appear)")
    args = parser.parse_args()

    # If --headless provided, override default HEADLESS
    headless_flag = True if args.headless else False if not HEADLESS else HEADLESS

    logging.info("Starting ethical scraper for query: %s max=%d", args.query, args.max)
    scrape_alibaba(args.query, marketplace=args.market, max_results=args.max, headless=headless_flag)