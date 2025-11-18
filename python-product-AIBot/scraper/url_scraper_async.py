"""Async version of URL scraper - uses factory pattern for multi-site support"""
import sys
import asyncio
from typing import Optional

# CRITICAL: Set event loop policy BEFORE importing Playwright on Windows
if sys.platform == 'win32':
    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from .scraper_factory import create_scraper


def scrape_from_url_sync(url: str, max_results: int = 10, site_name: Optional[str] = None):
    """
    Synchronous wrapper for async scraper using factory pattern
    
    Args:
        url: Product listing page URL
        max_results: Maximum number of products to extract
        site_name: Optional site name to override auto-detection
        
    Returns:
        List of product dictionaries
    """
    # Create new event loop with proper policy
    if sys.platform == 'win32':
        if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Create new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Use factory to get appropriate scraper
        scraper = create_scraper(url=url, site_name=site_name)
        return loop.run_until_complete(scraper.scrape_from_url(url, max_results))
    finally:
        loop.close()

