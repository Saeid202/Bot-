"""URL parsing and site detection logic"""
from urllib.parse import urlparse
from typing import Optional, Dict, List


# Mapping of domains to site names
DOMAIN_MAPPING = {
    'amazon.com': 'Amazon',
    'amazon.co.uk': 'Amazon',
    'amazon.de': 'Amazon',
    'amazon.fr': 'Amazon',
    'amazon.it': 'Amazon',
    'amazon.es': 'Amazon',
    'amazon.ca': 'Amazon',
    'amazon.com.au': 'Amazon',
    'amazon.in': 'Amazon',
    'amazon.jp': 'Amazon',
    'amazon.com.mx': 'Amazon',
    'amazon.com.br': 'Amazon',
    
    'ebay.com': 'eBay',
    'ebay.co.uk': 'eBay',
    'ebay.de': 'eBay',
    'ebay.fr': 'eBay',
    'ebay.it': 'eBay',
    'ebay.es': 'eBay',
    'ebay.ca': 'eBay',
    'ebay.com.au': 'eBay',
    
    'alibaba.com': 'Alibaba',
    'aliexpress.com': 'AliExpress',
    'aliexpress.us': 'AliExpress',
    
    'walmart.com': 'Walmart',
    'target.com': 'Target',
    'bestbuy.com': 'Best Buy',
    'etsy.com': 'Etsy',
    'shopify.com': 'Shopify',
    'shopify.store': 'Shopify',
}


def detect_site_from_url(url: str) -> Optional[str]:
    """
    Detect e-commerce site from URL
    
    Args:
        url: Product listing or product page URL
        
    Returns:
        Site name (e.g., 'Amazon', 'eBay') or None if unknown
    """
    if not url:
        return None
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check exact match first
        if domain in DOMAIN_MAPPING:
            return DOMAIN_MAPPING[domain]
        
        # Check if domain contains any of our known domains
        for known_domain, site_name in DOMAIN_MAPPING.items():
            if known_domain in domain:
                return site_name
        
        # Check for subdomains (e.g., shop.example.com)
        parts = domain.split('.')
        if len(parts) >= 2:
            # Check domain without first subdomain
            base_domain = '.'.join(parts[-2:])
            if base_domain in DOMAIN_MAPPING:
                return DOMAIN_MAPPING[base_domain]
        
    except Exception:
        pass
    
    return None


def get_site_info(url: str) -> Dict[str, Optional[str]]:
    """
    Get site information from URL
    
    Args:
        url: Product listing or product page URL
        
    Returns:
        Dictionary with 'site' (site name) and 'domain' (domain name)
    """
    site = detect_site_from_url(url)
    domain = None
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
    except Exception:
        pass
    
    return {
        'site': site,
        'domain': domain
    }


def is_supported_site(url: str) -> bool:
    """
    Check if the URL is from a supported e-commerce site
    
    Args:
        url: Product listing or product page URL
        
    Returns:
        True if site is supported, False otherwise
    """
    return detect_site_from_url(url) is not None


def get_all_supported_sites() -> List[str]:
    """
    Get list of all supported site names
    
    Returns:
        List of unique site names
    """
    return sorted(list(set(DOMAIN_MAPPING.values())))

