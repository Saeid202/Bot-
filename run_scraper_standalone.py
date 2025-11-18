"""Standalone script to run scraper - called as subprocess"""
import sys
import os

# CRITICAL: Set event loop policy BEFORE any imports on Windows
# Python 3.13+ requires explicit policy for subprocess support
if sys.platform == 'win32':
    # Set environment variable first (before asyncio is imported anywhere)
    os.environ['PYTHONASYNCIODEBUG'] = '1'
    
    import asyncio
    # Use ProactorEventLoop which supports subprocess creation
    # This is required for Playwright to create subprocesses
    try:
        policy = asyncio.WindowsProactorEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)
    except AttributeError:
        # Fallback for older Python versions
        try:
            policy = asyncio.WindowsSelectorEventLoopPolicy()
            asyncio.set_event_loop_policy(policy)
        except AttributeError:
            pass

import json
from pathlib import Path

# Add the project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python-product-AIBot"))

from scraper.url_scraper_async import scrape_from_url_sync

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Missing arguments: url and max_results required"}))
        sys.exit(1)
    
    url = sys.argv[1]
    max_results = int(sys.argv[2])
    site_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        # Use factory-based scraper with optional site override
        products = scrape_from_url_sync(url, max_results, site_name=site_name)
        result = {"success": True, "products": products}
        print(json.dumps(result))
    except Exception as e:
        import traceback
        result = {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(result))
        sys.exit(1)

