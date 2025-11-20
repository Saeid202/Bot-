"""Base scraper abstract class for all e-commerce site scrapers"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import sys
import os

# CRITICAL: Set event loop policy BEFORE importing Playwright on Windows
if sys.platform == 'win32':
    import asyncio
    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    elif hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from typing import TYPE_CHECKING
import importlib

if TYPE_CHECKING:
    from playwright.async_api import async_playwright  # type: ignore

try:
    _pw_mod = importlib.import_module("playwright.async_api")
    async_playwright = _pw_mod.async_playwright
except Exception:
    # Playwright may not be installed in test environments; allow
    # tests to import BaseScraper and mock/playwright usage later.
    async_playwright = None


class BaseScraper(ABC):
    """Abstract base class for all e-commerce scrapers"""
    
    def __init__(self, site_name: str):
        """
        Initialize the scraper
        
        Args:
            site_name: Name of the e-commerce site (e.g., 'Amazon', 'eBay')
        """
        self.site_name = site_name
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    @abstractmethod
    async def scrape_from_url(self, url: str, max_results: int = 10) -> List[Dict]:
        """
        Scrape products from a given URL
        
        Args:
            url: The product listing page URL to scrape
            max_results: Maximum number of products to extract
            
        Returns:
            List of product dictionaries with standardized structure:
            {
                'title': str,
                'price': str,
                'description': str (optional),
                'images': List[str] (optional),
                'rating': float (optional),
                'review_count': int (optional),
                'availability': str (optional),
                'url': str,
                'source': str,
                'currency': str (optional)
            }
        """
        pass
    
    async def _create_browser_context(self, playwright):
        """
        Create a browser context with stealth settings
        
        Args:
            playwright: Playwright instance
            
        Returns:
            Browser context with stealth configuration
        """
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=self.user_agent,
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
            color_scheme='light',
        )
        
        # Add stealth scripts
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({ state: 'granted' })
                })
            });
        """)
        
        return browser, context
    
    async def _set_headers(self, page):
        """Set realistic HTTP headers"""
        await page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _normalize_price(self, price_text: str) -> Optional[str]:
        """
        Normalize price text
        
        Args:
            price_text: Raw price text from website
            
        Returns:
            Normalized price string or None
        """
        if not price_text:
            return None
        # Remove extra whitespace
        return ' '.join(price_text.strip().split())
    
    def _normalize_rating(self, rating_text: str) -> Optional[float]:
        """
        Normalize rating to float (0-5 scale)
        
        Args:
            rating_text: Raw rating text
            
        Returns:
            Rating as float or None
        """
        if not rating_text:
            return None
        try:
            # Extract number from text (e.g., "4.5 out of 5" -> 4.5)
            import re
            numbers = re.findall(r'\d+\.?\d*', rating_text)
            if numbers:
                rating = float(numbers[0])
                # If rating seems to be out of 10, convert to 5
                if rating > 5 and rating <= 10:
                    rating = rating / 2
                return min(5.0, max(0.0, rating))
        except (ValueError, TypeError):
            pass
        return None
    
    def _normalize_review_count(self, count_text: str) -> Optional[int]:
        """
        Normalize review count to integer
        
        Args:
            count_text: Raw review count text (e.g., "1,234 reviews")
            
        Returns:
            Review count as integer or None
        """
        if not count_text:
            return None
        try:
            import re
            # Extract numbers, remove commas
            numbers = re.sub(r'[^\d]', '', count_text)
            if numbers:
                return int(numbers)
        except (ValueError, TypeError):
            pass
        return None

