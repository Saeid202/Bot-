"""Generic scraper for unknown e-commerce sites"""
import asyncio
import random
from typing import List, Dict
from ..base_scraper import BaseScraper


class GenericScraper(BaseScraper):
    """Generic scraper for unknown or unsupported e-commerce sites"""
    
    def __init__(self):
        super().__init__('Generic')
    
    async def scrape_from_url(self, url: str, max_results: int = 10) -> List[Dict]:
        """
        Generic scraper that tries to extract products using common selectors
        
        Args:
            url: Product listing page URL
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
            
            # Try common product selectors
            selectors = [
                "[data-product-id]",
                "[data-product]",
                ".product",
                ".product-item",
                ".product-card",
                ".item",
                "[class*='product']",
                "[class*='item']",
                "[class*='card']",
                "article",
                ".goods",
                ".commodity",
                ".listing",
                "li",  # List items might contain products
                "tr",  # Table rows might contain products
                "div[class*='list']",  # List containers
                "div[class*='grid']",  # Grid containers
            ]
            
            items = []
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    found_items = await page.locator(selector).all()
                    # Only use if we found a reasonable number (not too many, not too few)
                    if 1 <= len(found_items) <= 100:
                        items = found_items
                        break
                except:
                    continue
            
            # If no items found, try looking for links that might be products
            if len(items) == 0:
                # Scroll to trigger any lazy loading
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                await asyncio.sleep(2)
                await page.wait_for_timeout(3000)
                
                # Try to find product links
                try:
                    # Look for links with product-related keywords
                    product_links = await page.locator("a[href*='product'], a[href*='item'], a[href*='detail'], a[href*='goods'], a[href*='Product']").all()
                    if len(product_links) > 0:
                        # Use these links directly as items
                        items = product_links[:max_results * 2]
                except:
                    pass
                
                # Last resort: try all links that have text and images
                if len(items) == 0:
                    try:
                        all_links = await page.locator("a").all()
                        potential_items = []
                        for link in all_links[:100]:  # Check first 100 links
                            try:
                                text = await link.inner_text()
                                has_img = await link.locator("img").count() > 0
                                href = await link.get_attribute("href")
                                # If link has text, image, and valid href, it might be a product
                                # Or if link text is substantial (likely product name)
                                if href and text and len(text.strip()) > 3:
                                    # Prefer links with images, but also accept text-only if substantial
                                    if has_img or len(text.strip()) > 10:
                                        potential_items.append(link)
                            except:
                                continue
                        if len(potential_items) > 0:
                            items = potential_items[:max_results]
                    except:
                        pass
                
                # Final fallback: extract any substantial links as potential products
                if len(items) == 0:
                    try:
                        # Get all links and filter for substantial ones
                        all_links = await page.locator("a[href]").all()
                        for link in all_links[:max_results * 2]:
                            try:
                                text = await link.inner_text()
                                href = await link.get_attribute("href")
                                # Skip navigation, footer, header links
                                if (href and text and len(text.strip()) > 5 and 
                                    not any(skip in href.lower() for skip in ['#', 'javascript:', 'mailto:', 'tel:']) and
                                    not any(skip in text.lower() for skip in ['home', 'about', 'contact', 'login', 'register', 'cart', 'search'])):
                                    items.append(link)
                                    if len(items) >= max_results:
                                        break
                            except:
                                continue
                    except:
                        pass
            
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
        """Extract product using generic selectors"""
        product = {
            'title': '',
            'price': '',
            'description': '',
            'images': [],
            'rating': None,
            'review_count': None,
            'availability': '',
            'url': base_url,
            'source': 'Generic',
            'currency': None
        }
        
        # Extract title (try common title selectors)
        title_selectors = [
            "h1", "h2", "h3", "h4",
            ".title", ".product-title", ".item-title",
            "[class*='title']", "[class*='name']",
            "a",  # If item is a link, use link text
            "span[class*='title']", "div[class*='title']"
        ]
        for selector in title_selectors:
            try:
                title_elem = await item.locator(selector).first
                title = await title_elem.inner_text()
                if title and len(title.strip()) > 0:
                    product['title'] = title.strip()
                    break
            except:
                continue
        
        # If still no title and item is a link, try getting text from the link itself
        if not product['title']:
            try:
                # Check if the item itself is a link or contains a link
                if await item.evaluate("el => el.tagName === 'A'") or await item.locator("a").count() > 0:
                    link = item if await item.evaluate("el => el.tagName === 'A'") else await item.locator("a").first
                    title = await link.inner_text()
                    if title and len(title.strip()) > 0:
                        product['title'] = title.strip()
            except:
                pass
        
        # Extract price (try common price selectors)
        price_selectors = [
            ".price", ".product-price", ".item-price",
            "[class*='price']", "[class*='cost']", "[class*='amount']"
        ]
        for selector in price_selectors:
            try:
                price = await item.locator(selector).first.inner_text()
                if price:
                    product['price'] = self._normalize_price(price) or ''
                    break
            except:
                continue
        
        # Extract images
        try:
            img_elements = await item.locator("img").all()
            for img in img_elements[:3]:
                try:
                    img_url = await img.get_attribute("src")
                    if not img_url:
                        img_url = await img.get_attribute("data-src")  # Lazy loaded images
                    if img_url:
                        # Handle relative URLs
                        if img_url.startswith('http'):
                            product['images'].append(img_url)
                        elif img_url.startswith('/'):
                            from urllib.parse import urljoin
                            product['images'].append(urljoin(base_url, img_url))
                except:
                    pass
        except:
            pass
        
        # Extract product URL
        try:
            # Check if item itself is a link
            if await item.evaluate("el => el.tagName === 'A'"):
                href = await item.get_attribute("href")
            else:
                link = await item.locator("a").first
                href = await link.get_attribute("href")
            
            if href:
                if href.startswith('http'):
                    product['url'] = href
                elif href.startswith('/') or href.startswith('./'):
                    from urllib.parse import urljoin
                    product['url'] = urljoin(base_url, href)
                else:
                    # Relative URL
                    from urllib.parse import urljoin
                    product['url'] = urljoin(base_url, href)
        except:
            pass
        
        # Try to detect source from URL
        from ..site_detector import detect_site_from_url
        detected = detect_site_from_url(base_url)
        if detected:
            product['source'] = detected
        
        return product if product['title'] or product['price'] else None

