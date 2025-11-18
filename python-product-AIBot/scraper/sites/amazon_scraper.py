"""Amazon.com product scraper"""
import asyncio
import random
from typing import List, Dict
from ..base_scraper import BaseScraper


class AmazonScraper(BaseScraper):
    """Scraper for Amazon.com product listings"""
    
    def __init__(self):
        super().__init__('Amazon')
    
    async def scrape_from_url(self, url: str, max_results: int = 10) -> List[Dict]:
        """
        Scrape products from Amazon.com
        
        Args:
            url: Amazon product listing or search results page URL
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
            is_search_page = 's?' in url or '/s?' in url or '/s/' in url
            
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
        """Scrape products from Amazon search results page"""
        products = []
        
        # Amazon search results selectors
        selectors = [
            "[data-component-type='s-search-result']",
            ".s-result-item",
            "[data-asin]",
            ".s-card-container"
        ]
        
        items = []
        # Try waiting for selectors with longer timeout
        for selector in selectors:
            try:
                await page.wait_for_selector(selector, timeout=10000, state='visible')
                items = await page.locator(selector).all()
                if len(items) > 0:
                    break
            except:
                continue
        
        # If still no items, wait longer and try again
        if len(items) == 0:
            await page.wait_for_timeout(5000)
            # Scroll down to trigger lazy loading
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
        """Scrape single product page"""
        product = {
            'title': '',
            'price': '',
            'description': '',
            'images': [],
            'rating': None,
            'review_count': None,
            'availability': '',
            'url': url,
            'source': 'Amazon',
            'currency': 'USD'
        }
        
        # Extract title
        try:
            title = await page.locator("#productTitle, h1.a-size-large").first.inner_text()
            product['title'] = title.strip()
        except:
            pass
        
        # Extract price
        try:
            price_selectors = [
                ".a-price .a-offscreen",
                "#priceblock_ourprice",
                "#priceblock_dealprice",
                ".a-price-whole",
                "[data-a-color='price'] .a-offscreen"
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
            desc = await page.locator("#productDescription, #feature-bullets").first.inner_text()
            product['description'] = desc.strip()[:500]  # Limit description length
        except:
            pass
        
        # Extract images
        try:
            img_elements = await page.locator("#landingImage, #imgBlkFront, .a-dynamic-image").all()
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
            rating_text = await page.locator("#acrPopover .a-icon-alt, .a-icon-star .a-icon-alt").first.inner_text()
            product['rating'] = self._normalize_rating(rating_text)
        except:
            pass
        
        # Extract review count
        try:
            review_text = await page.locator("#acrCustomerReviewText, #acrCustomerReviewLink").first.inner_text()
            product['review_count'] = self._normalize_review_count(review_text)
        except:
            pass
        
        # Extract availability
        try:
            availability = await page.locator("#availability span").first.inner_text()
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
            'source': 'Amazon',
            'currency': 'USD'
        }
        
        # Extract title and URL
        try:
            title_elem = await item.locator("h2 a, .s-title-instructions-style a").first
            product['title'] = (await title_elem.inner_text()).strip()
            href = await title_elem.get_attribute("href")
            if href:
                if href.startswith('http'):
                    product['url'] = href
                elif href.startswith('/'):
                    from urllib.parse import urljoin
                    product['url'] = urljoin('https://www.amazon.com', href)
        except:
            pass
        
        # Extract price
        try:
            price = await item.locator(".a-price .a-offscreen, .a-price-whole").first.inner_text()
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
            rating_text = await item.locator(".a-icon-alt").first.inner_text()
            product['rating'] = self._normalize_rating(rating_text)
        except:
            pass
        
        # Extract review count
        try:
            review_text = await item.locator("a .a-size-base").first.inner_text()
            product['review_count'] = self._normalize_review_count(review_text)
        except:
            pass
        
        return product if product['title'] else None

