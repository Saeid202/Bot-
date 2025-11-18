import types
import sys
from pathlib import Path

# Ensure the package is importable when running this file directly
try:
    from scraper.alibaba_scraper import AlibabaScraper
except ModuleNotFoundError:
    ROOT = Path(__file__).resolve().parents[1] / "python-product-AIBot"
    sys.path.insert(0, str(ROOT))
    from scraper.alibaba_scraper import AlibabaScraper


class FakeLocator:
    def __init__(self, text):
        self._text = text

    def inner_text(self):
        return self._text


class FakeItem:
    def __init__(self, title, price):
        self._title = title
        self._price = price

    def locator(self, sel):
        # Support both original selectors and fallback selectors
        if "title" in sel or "element-title" in sel:
            return FakeLocator(self._title)
        if "price" in sel or "element-offer-price" in sel:
            return FakeLocator(self._price)
        # For fallback selectors like "h2, .title, [class*='title']"
        if any(x in sel for x in ["title", "h2"]):
            class FakeLocatorWithFirst:
                def __init__(self, text):
                    self._text = text
                def first(self):
                    return FakeLocator(self._text)
            return FakeLocatorWithFirst(self._title)
        if "price" in sel:
            class FakeLocatorWithFirst:
                def __init__(self, text):
                    self._text = text
                def first(self):
                    return FakeLocator(self._text)
            return FakeLocatorWithFirst(self._price)
        return FakeLocator("")


class FakePage:
    def __init__(self, items):
        self._items = items
        self._headers = {}

    def goto(self, url, wait_until=None, timeout=None):
        self._url = url

    def wait_for_timeout(self, t):
        pass
    
    def wait_for_selector(self, selector, timeout=None):
        # Simulate finding items
        pass

    def set_extra_http_headers(self, headers):
        self._headers = headers

    def locator(self, sel):
        # return an object with .all() returning items
        class L:
            def __init__(self, items):
                self._items = items

            def all(self):
                return self._items

        return L(self._items)


class FakeContext:
    def __init__(self, items):
        self._items = items
    
    def new_page(self):
        return FakePage(self._items)
    
    def add_init_script(self, script):
        pass
    
    def close(self):
        pass


class FakeBrowser:
    def __init__(self, items):
        self._items = items

    def new_context(self, **kwargs):
        return FakeContext(self._items)

    def close(self):
        pass


class FakeChromium:
    def __init__(self, items):
        self._items = items

    def launch(self, headless=True, args=None):
        return FakeBrowser(self._items)


class FakePlaywright:
    def __init__(self, items):
        self.chromium = FakeChromium(items)


class FakeCtxManager:
    def __init__(self, items):
        self._items = items

    def __enter__(self):
        return FakePlaywright(self._items)

    def __exit__(self, exc_type, exc, tb):
        return False


def test_alibaba_scraper_monkeypatch(monkeypatch):
    fake_items = [FakeItem("T1", "$1"), FakeItem("T2", "$2")]

    def fake_sync_playwright():
        return FakeCtxManager(fake_items)

    import scraper.alibaba_scraper as mod
    monkeypatch.setattr(mod, "sync_playwright", fake_sync_playwright)

    s = AlibabaScraper()
    products = s.run("phone", max_results=1)
    assert isinstance(products, list)
    assert products[0]["title"] == "T1"
    assert products[0]["price"] == "$1"
