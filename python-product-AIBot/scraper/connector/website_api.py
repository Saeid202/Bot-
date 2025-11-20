import os
import requests
from typing import Iterable, Mapping, Any

# Make the API base configurable via env var for testing and deployment.
BASE = os.getenv("SCRAPER_API_BASE", "https://localhost:3000/dashboard/products")


def _post(path: str, json: Mapping[str, Any], timeout: int = 10):
    url = f"{BASE.rstrip('/')}/{path.lstrip('/')}"
    try:
        r = requests.post(url, json=json, timeout=timeout)
    except TypeError:
        # Fallback for tests or stubs that don't accept `timeout` kwarg
        r = requests.post(url, json=json)
    r.raise_for_status()
    try:
        return r.json()
    except ValueError:
        # Non-JSON response
        return None


def start_import_job(query: str, marketplace: str, max_results: int, timeout: int = 10) -> str:
    """Start an import job on the backend and return the jobId.

    Raises RuntimeError if the response doesn't include a jobId.
    """
    data = _post("start", {"query": query, "marketplace": marketplace, "maxResults": max_results}, timeout=timeout)
    if not data or "jobId" not in data:
        raise RuntimeError("start_import_job: backend did not return jobId")
    return data["jobId"]


def insert_imported_products(job_id: str, products: Iterable[Mapping[str, Any]], timeout: int = 10) -> None:
    """Send scraped products to the backend for the given job."""
    _post("insert-products", {"jobId": job_id, "products": list(products)}, timeout=timeout)


def complete_import_job(job_id: str, timeout: int = 10) -> None:
    """Mark the import job complete on the backend."""
    _post("complete", {"jobId": job_id}, timeout=timeout)