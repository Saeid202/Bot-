"""Alibaba.com product scraper"""
import asyncio
import random
from typing import List, Dict
from ..base_scraper import BaseScraper


class AlibabaScraper(BaseScraper):
    """Scraper for Alibaba.com product listings"""
    
    def __init__(self):
        super().__init__('Alibaba')
    
    async def scrape_from_url(self, url: str, max_results: int = 10) -> List[Dict]:
        """
        Scrape products from Alibaba.com
        
        Args:
            url: Alibaba product listing page URL
            max_results: Maximum number of products to extract
            
        Returns:
            List of product dictionaries
        """
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser, context = await self._create_browser_context(p)
            page = await context.new_page()
            await self._set_headers(page)
            
            # Navigate to URL
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))
            
            # Wait for content to load
            items = []
            selectors = [
                ".organic-gallery-offer-card",
                ".gallery-offer-card",
                "[data-content='product']",
                ".offer-card",
                ".product-card"
            ]
            
            # Try to find products
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    items = await page.locator(selector).all()
                    if len(items) > 0:
                        break
                except:
                    continue
            
            if len(items) == 0:
                await page.wait_for_timeout(3000)
                for selector in selectors:
                    items = await page.locator(selector).all()
                    if len(items) > 0:
                        break
            
            products = []
            for item in items[:max_results]:
                try:
                    product = await self._extract_product(item, url)
                    if product:
                        products.append(product)
                except Exception:
                    continue
            
            await context.close()
            await browser.close()
            return products
    
    async def _extract_product(self, item, base_url: str) -> Dict:
        """Extract product information from a single item element"""
        product = {
            'title': '',
            'price': '',
            'description': '',
            'images': [],
            'rating': None,
            'review_count': None,
            'availability': '',
            'url': base_url,
            'source': 'Alibaba',
            'currency': None
        }
        
        # Extract title
        try:
            title = await item.locator(".element-title-normal_content").inner_text()
            product['title'] = title.strip() if title else ''
        except:
            try:
                title = await item.locator(".element-title, .title, h2, h3, [class*='title']").first.inner_text()
                product['title'] = title.strip() if title else ''
            except:
                pass
        
        # Extract price
        try:
            price = await item.locator(".element-offer-price-normal_price").inner_text()
            product['price'] = self._normalize_price(price) or ''
        except:
            try:
                price = await item.locator(".price, [class*='price'], [class*='Price']").first.inner_text()
                product['price'] = self._normalize_price(price) or ''
            except:
                pass
        
        # Extract images
        try:
            img_elements = await item.locator("img").all()
            for img in img_elements[:3]:  # Limit to first 3 images
                try:
                    img_url = await img.get_attribute("src")
                    if img_url and img_url.startswith('http'):
                        product['images'].append(img_url)
                except:
                    pass
        except:
            pass
        
        # Extract rating (if available)
        try:
            rating_elem = await item.locator("[class*='rating'], [class*='star'], .rating").first
            rating_text = await rating_elem.inner_text()
            product['rating'] = self._normalize_rating(rating_text)
        except:
            pass
        
        # Extract product URL
        try:
            link = await item.locator("a").first
            href = await link.get_attribute("href")
            if href:
                if href.startswith('http'):
                    product['url'] = href
                elif href.startswith('/'):
                    from urllib.parse import urljoin
                    product['url'] = urljoin(base_url, href)
        except:
            pass
        
        # Only return if we have at least title or price
        if product['title'] or product['price']:
            return product
        return None

