import requests

BASE = "https://localhost:3000/api/scraper" # -> change it back to this or the website URL "https://cargoplus.site/api/scraper"

def start_import_job(query, marketplace, max_results):
    # sends a POST req to /api/scraper/start & returns the jobId
    r = requests.post(
        f"{BASE}/start",
        json={
            "query": query,
            "marketplace": marketplace,
            "maxResults": max_results
        }
    )
    r.raise_for_status()
    return r.json()["jobId"]

def insert_imported_products(job_id, products):
    # sends scraped product data to /api/scraper/insert-products
    # (sends all products to backend)
    r = requests.post(
        f"{BASE}/insert-products",
        json={
            "jobId": job_id,
            "products": products
        }
    )
    r.raise_for_status()

def complete_import_job(job_id):
    # sends a POST req to /api/scraper/complete telling backend job is done
    r = requests.post(
        f"{BASE}/complete",
        json={"jobId": job_id}
    )
    r.raise_for_status() #returns & checks for status error codes 