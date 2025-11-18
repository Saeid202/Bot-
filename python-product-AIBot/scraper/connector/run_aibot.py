from scraper.alibaba_scraper import AlibabaScraper #from the scraper folder access alibaba_scraper and import he AlibabaScraper class
from scraper.normalize import normalize_product
from connector.website_api import (
    start_import_job,
    insert_imported_products,
    complete_import_job
)

def run_bot(query="power bank", max_results=5):
    print("Scraping products...")
    scraper = AlibabaScraper()
    raw_products = scraper.run(query, max_results)

    print(f"Scraped {len(raw_products)} products.")

    normalized = [normalize_product(p) for p in raw_products]

    print("Connecting to your website...")
    job_id = start_import_job(query, "alibaba", max_results)

    print(f"Import job created: {job_id}")
    insert_imported_products(job_id, normalized)
    complete_import_job(job_id)

    print("✔ Import completed!")
    print(f"✔ {len(normalized)} products inserted into your Seller Dashboard")

if __name__ == "__main__":
    run_bot()