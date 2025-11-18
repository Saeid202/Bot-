"""Tests for scraper factory"""
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1] / "python-product-AIBot"
sys.path.insert(0, str(ROOT))

from scraper.scraper_factory import create_scraper
from scraper.base_scraper import BaseScraper


def test_create_amazon_scraper():
    """Test creating Amazon scraper"""
    scraper = create_scraper(url="https://www.amazon.com/s?k=laptop")
    assert isinstance(scraper, BaseScraper)
    assert scraper.site_name == "Amazon"


def test_create_ebay_scraper():
    """Test creating eBay scraper"""
    scraper = create_scraper(url="https://www.ebay.com/sch/i.html")
    assert isinstance(scraper, BaseScraper)
    assert scraper.site_name == "eBay"


def test_create_alibaba_scraper():
    """Test creating Alibaba scraper"""
    scraper = create_scraper(url="https://www.alibaba.com/trade/search")
    assert isinstance(scraper, BaseScraper)
    assert scraper.site_name == "Alibaba"


def test_create_with_site_name():
    """Test creating scraper with explicit site name"""
    scraper = create_scraper(site_name="Amazon")
    assert isinstance(scraper, BaseScraper)
    assert scraper.site_name == "Amazon"


def test_create_generic_scraper():
    """Test creating generic scraper for unknown site"""
    scraper = create_scraper(url="https://www.unknown-site.com")
    assert isinstance(scraper, BaseScraper)
    assert scraper.site_name == "Generic"

