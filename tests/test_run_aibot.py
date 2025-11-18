import builtins
from types import SimpleNamespace
import sys
from pathlib import Path

# Allow running this test file directly (conftest isn't loaded when run as a script)
try:
    import scraper.connector.run_aibot as run_mod
except ModuleNotFoundError:
    ROOT = Path(__file__).resolve().parents[1] / "python-product-AIBot"
    sys.path.insert(0, str(ROOT))
    # If `requests` isn't installed in the environment, provide a minimal stub so
    # importing `run_aibot` (which imports `website_api`) won't fail.
    import types
    import types as _types
    fake_requests = _types.ModuleType("requests")
    def _fake_post(*args, **kwargs):
        class R:
            def raise_for_status(self):
                return None
            def json(self):
                return {}
        return R()
    fake_requests.post = _fake_post
    sys.modules["requests"] = fake_requests
    import scraper.connector.run_aibot as run_mod


def test_run_bot_happy_path(monkeypatch, capsys):
    # Mock AlibabaScraper.run
    class DummyScraper:
        def run(self, query, max_results=5):
            return [{"title": "Item A", "price": "$1"}]

    monkeypatch.setattr(run_mod, "AlibabaScraper", DummyScraper)

    # Mock Supabase insert function (current implementation uses Supabase directly)
    inserted_products = []

    def fake_insert_products_supabase(products):
        inserted_products.extend(products)
        return products  # Return the products as if they were inserted

    monkeypatch.setattr(run_mod, "insert_products_supabase", fake_insert_products_supabase)

    run_mod.run_bot(query="x", max_results=1)

    captured = capsys.readouterr()
    assert "Scraping products" in captured.out
    assert len(inserted_products) == 1
    assert inserted_products[0]["name"] == "Item A"
    assert inserted_products[0]["price"] == "$1"
    assert inserted_products[0]["source"] == "Alibaba"
