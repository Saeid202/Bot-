"""Factory to create appropriate scraper based on URL/site type"""
from typing import Optional
from .site_detector import detect_site_from_url, get_all_supported_sites
from .base_scraper import BaseScraper


def create_scraper(url: Optional[str] = None, site_name: Optional[str] = None) -> BaseScraper:
    """
    Create appropriate scraper based on URL or site name
    
    Args:
        url: Product listing page URL (used for auto-detection)
        site_name: Explicit site name (overrides URL detection)
        
    Returns:
        BaseScraper instance for the detected/selected site
        
    Raises:
        ValueError: If site cannot be determined or is not supported
        ImportError: If site-specific scraper cannot be imported
    """
    # Determine site name
    if site_name:
        detected_site = site_name
    elif url:
        detected_site = detect_site_from_url(url)
        if not detected_site:
            # Use generic scraper for unknown sites
            detected_site = 'Generic'
    else:
        raise ValueError("Either 'url' or 'site_name' must be provided")
    
    # Import and create appropriate scraper
    try:
        if detected_site == 'Amazon':
            from .sites.amazon_scraper import AmazonScraper
            return AmazonScraper()
        
        elif detected_site == 'eBay':
            from .sites.ebay_scraper import eBayScraper
            return eBayScraper()
        
        elif detected_site == 'Alibaba':
            from .sites.alibaba_scraper import AlibabaScraper
            return AlibabaScraper()
        
        elif detected_site == 'AliExpress':
            from .sites.aliexpress_scraper import AliExpressScraper
            return AliExpressScraper()
        
        elif detected_site == 'Generic':
            from .sites.generic_scraper import GenericScraper
            return GenericScraper()
        
        else:
            # Fallback to generic scraper
            from .sites.generic_scraper import GenericScraper
            return GenericScraper()
            
    except ImportError as e:
        # If specific scraper not available, use generic
        try:
            from .sites.generic_scraper import GenericScraper
            return GenericScraper()
        except ImportError:
            raise ImportError(f"Could not import scraper for {detected_site}: {e}")


def get_scraper_for_site(site_name: str) -> BaseScraper:
    """
    Get scraper for a specific site name
    
    Args:
        site_name: Name of the e-commerce site
        
    Returns:
        BaseScraper instance
    """
    return create_scraper(site_name=site_name)

