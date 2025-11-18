"""Tests for site detection functionality"""
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1] / "python-product-AIBot"
sys.path.insert(0, str(ROOT))

from scraper.site_detector import detect_site_from_url, get_all_supported_sites, is_supported_site


def test_detect_amazon():
    """Test Amazon URL detection"""
    assert detect_site_from_url("https://www.amazon.com/s?k=laptop") == "Amazon"
    assert detect_site_from_url("https://amazon.co.uk/product") == "Amazon"
    assert detect_site_from_url("https://www.amazon.de/item") == "Amazon"


def test_detect_ebay():
    """Test eBay URL detection"""
    assert detect_site_from_url("https://www.ebay.com/sch/i.html") == "eBay"
    assert detect_site_from_url("https://ebay.co.uk/item") == "eBay"


def test_detect_alibaba():
    """Test Alibaba URL detection"""
    assert detect_site_from_url("https://www.alibaba.com/trade/search") == "Alibaba"


def test_detect_aliexpress():
    """Test AliExpress URL detection"""
    assert detect_site_from_url("https://www.aliexpress.com/item") == "AliExpress"


def test_unknown_site():
    """Test unknown site returns None"""
    assert detect_site_from_url("https://www.unknown-site.com") is None


def test_get_supported_sites():
    """Test getting all supported sites"""
    sites = get_all_supported_sites()
    assert isinstance(sites, list)
    assert "Amazon" in sites
    assert "eBay" in sites
    assert "Alibaba" in sites


def test_is_supported_site():
    """Test is_supported_site function"""
    assert is_supported_site("https://www.amazon.com") is True
    assert is_supported_site("https://www.unknown.com") is False

