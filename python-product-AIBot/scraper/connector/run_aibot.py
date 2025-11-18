import sys
from pathlib import Path
# Allow running this file directly by patching sys.path if needed

try:
    from scraper.alibaba_scraper import AlibabaScraper
    from scraper.normalize import normalize_product
except ModuleNotFoundError:
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))
    from scraper.alibaba_scraper import AlibabaScraper
    from scraper.normalize import normalize_product

# Supabase config and insert function (always defined)
import requests
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


def run_bot(query="power bank", max_results=5):
    print("Scraping products...")
    scraper = AlibabaScraper()
    raw_products = scraper.run(query, max_results)

    print(f"Scraped {len(raw_products)} products.")

    normalized = [normalize_product(p) for p in raw_products]

    # Map normalized fields to Supabase columns (adjust as needed)
    supabase_products = []
    for p in normalized:
        supabase_products.append({
            "name": p["title"],
            "price": p["price"],
            "source": p.get("source", "Alibaba"),
            # Add more fields here if needed
        })

    print("Inserting products into Supabase...")
    try:
        inserted = insert_products_supabase(supabase_products)
        print(f"✔ {len(inserted)} products inserted into Supabase.")
    except Exception as e:
        print(f"❌ Failed to insert products: {e}")

if __name__ == "__main__":
    run_bot()