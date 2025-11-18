"""eBay.com product scraper"""
import asyncio
import random
from typing import List, Dict
from ..base_scraper import BaseScraper


class eBayScraper(BaseScraper):
    """Scraper for eBay.com product listings"""
    
    def __init__(self):
        super().__init__('eBay')
    
    async def scrape_from_url(self, url: str, max_results: int = 10) -> List[Dict]:
        """
        Scrape products from eBay.com
        
        Args:
            url: eBay search results or product listing page URL
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
            await asyncio.sleep(random.uniform(3, 6))
            
            # Check for CAPTCHA
            page_title = await page.title()
            if "captcha" in page_title.lower() or "robot" in page_title.lower():
                await context.close()
                await browser.close()
                return []
            
            # Determine if this is a search results page or product page
            is_search_page = '/sch/' in url or '/b/' in url or 'nkw=' in url
            
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
        """Scrape products from eBay search results"""
        products = []
        
        # eBay search results selectors
        selectors = [
            ".s-item",
            "[data-view]",
            ".srp-results .s-item"
        ]
        
        items = []
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=10000, state='visible')
                items = await page.locator(selector).all()
                if len(items) > 0:
                    break
            except:
                continue
        
        if len(items) == 0:
            await page.wait_for_timeout(5000)
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(2)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            
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
        """Scrape single eBay product page"""
        product = {
            'title': '',
            'price': '',
            'description': '',
            'images': [],
            'rating': None,
            'review_count': None,
            'availability': '',
            'url': url,
            'source': 'eBay',
            'currency': 'USD'
        }
        
        # Extract title
        try:
            title = await page.locator("#x-item-title-label, h1.it-ttl").first.inner_text()
            product['title'] = title.strip()
        except:
            pass
        
        # Extract price
        try:
            price_selectors = [
                "#prcIsum",
                ".notranslate",
                "#mm-saleDscPrc"
            ]
            for selector in price_selectors:
                try:
                    price = await page.locator(selector).first.inner_text()
                    if price:
                        product['price'] = self._normalize_price(price)
                        break
                except:
                    continue
        except:
            pass
        
        # Extract description
        try:
            desc = await page.locator("#desc_wrapper_ctr, .u-flL.condText").first.inner_text()
            product['description'] = desc.strip()[:500]
        except:
            pass
        
        # Extract images
        try:
            img_elements = await page.locator("#vi_main_img_fs img, #icImg").all()
            for img in img_elements[:5]:
                try:
                    img_url = await img.get_attribute("src")
                    if img_url and 'http' in img_url:
                        product['images'].append(img_url)
                except:
                    pass
        except:
            pass
        
        # Extract availability (eBay shows quantity or "Buy It Now")
        try:
            availability = await page.locator("#qtySubTxt, .u-flL.condText").first.inner_text()
            product['availability'] = availability.strip()
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
            'source': 'eBay',
            'currency': 'USD'
        }
        
        # Extract title and URL
        try:
            title_elem = await item.locator("h3 a, .s-item__title a").first
            product['title'] = (await title_elem.inner_text()).strip()
            href = await title_elem.get_attribute("href")
            if href:
                if href.startswith('http'):
                    product['url'] = href
                elif href.startswith('/'):
                    from urllib.parse import urljoin
                    product['url'] = urljoin('https://www.ebay.com', href)
        except:
            pass
        
        # Extract price
        try:
            price = await item.locator(".s-item__price, .s-item__detail--primary").first.inner_text()
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
        
        return product if product['title'] else None

