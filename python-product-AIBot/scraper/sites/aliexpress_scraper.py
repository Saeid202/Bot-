"""AliExpress.com product scraper"""
import asyncio
import random
from typing import List, Dict
from ..base_scraper import BaseScraper


class AliExpressScraper(BaseScraper):
    """Scraper for AliExpress.com product listings"""
    
    def __init__(self):
        super().__init__('AliExpress')
    
    async def scrape_from_url(self, url: str, max_results: int = 10) -> List[Dict]:
        """
        Scrape products from AliExpress.com
        
        Args:
            url: AliExpress product listing or search results page URL
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
            
            # Determine if this is a search results page or product page
            is_search_page = '/wholesale' in url or '/search' in url or 'SearchText=' in url
            
            if is_search_page:
                products = await self._scrape_search_results(page, max_results, url)
            else:
                # Single product page
                product = await self._scrape_product_page(page, url)
                products = [product] if product else []
            
            await context.close()
            await browser.close()
            return products
    
    async def _scrape_search_results(self, page, max_results: int, base_url: str) -> List[Dict]:
        """Scrape products from AliExpress search results"""
        products = []
        
        # AliExpress search results selectors
        selectors = [
            ".list--gallery--C2f2tvm",
            "[data-product-id]",
            ".gallery-offer-card",
            ".list-item"
        ]
        
        items = []
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
        
        for item in items[:max_results]:
            try:
                product = await self._extract_search_result_item(item, base_url)
                if product:
                    products.append(product)
            except Exception:
                continue
        
        return products
    
    async def _scrape_product_page(self, page, url: str) -> Dict:
        """Scrape single AliExpress product page"""
        product = {
            'title': '',
            'price': '',
            'description': '',
            'images': [],
            'rating': None,
            'review_count': None,
            'availability': '',
            'url': url,
            'source': 'AliExpress',
            'currency': 'USD'
        }
        
        # Extract title
        try:
            title = await page.locator("h1.product-title-text").first.inner_text()
            product['title'] = title.strip()
        except:
            try:
                title = await page.locator("h1").first.inner_text()
                product['title'] = title.strip()
            except:
                pass
        
        # Extract price
        try:
            price = await page.locator(".notranslate, .price-current").first.inner_text()
            product['price'] = self._normalize_price(price) or ''
        except:
            pass
        
        # Extract description
        try:
            desc = await page.locator("#product-description, .product-description").first.inner_text()
            product['description'] = desc.strip()[:500]
        except:
            pass
        
        # Extract images
        try:
            img_elements = await page.locator(".images-view-item img, .product-image img").all()
            for img in img_elements[:5]:
                try:
                    img_url = await img.get_attribute("src")
                    if img_url and 'http' in img_url:
                        product['images'].append(img_url)
                except:
                    pass
        except:
            pass
        
        # Extract rating
        try:
            rating_text = await page.locator(".overview-rating-average, .rating-value").first.inner_text()
            product['rating'] = self._normalize_rating(rating_text)
        except:
            pass
        
        # Extract review count
        try:
            review_text = await page.locator(".product-reviewer-reviews, .reviews-count").first.inner_text()
            product['review_count'] = self._normalize_review_count(review_text)
        except:
            pass
        
        return product if product['title'] else None
    
    async def _extract_search_result_item(self, item, base_url: str) -> Dict:
        """Extract product from search result item"""
        product = {
            'title': '',
            'price': '',
            'description': '',
            'images': [],
            'rating': None,
            'review_count': None,
            'availability': '',
            'url': base_url,
            'source': 'AliExpress',
            'currency': 'USD'
        }
        
        # Extract title and URL
        try:
            title_elem = await item.locator("a, h3 a").first
            product['title'] = (await title_elem.inner_text()).strip()
            href = await title_elem.get_attribute("href")
            if href:
                if href.startswith('http'):
                    product['url'] = href
                elif href.startswith('/'):
                    from urllib.parse import urljoin
                    product['url'] = urljoin('https://www.aliexpress.com', href)
        except:
            pass
        
        # Extract price
        try:
            price = await item.locator(".price, .price-current, [class*='price']").first.inner_text()
            product['price'] = self._normalize_price(price) or ''
        except:
            pass
        
        # Extract images
        try:
            img = await item.locator("img").first
            img_url = await img.get_attribute("src")
            if img_url and 'http' in img_url:
                product['images'].append(img_url)
        except:
            pass
        
        # Extract rating
        try:
            rating_text = await item.locator("[class*='rating'], [class*='star']").first.inner_text()
            product['rating'] = self._normalize_rating(rating_text)
        except:
            pass
        
        return product if product['title'] else None

