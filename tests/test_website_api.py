import types
import sys
from pathlib import Path

# `pytest` is only needed when running under pytest; allow running this file
# directly without pytest installed.
try:
    import pytest
except ModuleNotFoundError:
    pytest = None

# Import the module under test. When running this file directly (not via
# pytest), `conftest.py` is not loaded so `scraper` may not be on `sys.path` and
# `requests` may not be installed. Provide safe fallbacks in that case.
try:
    import scraper.connector.website_api as website_api
except ModuleNotFoundError:
    ROOT = Path(__file__).resolve().parents[1] / "python-product-AIBot"
    sys.path.insert(0, str(ROOT))
    # Ensure a minimal `requests` exists so importing website_api won't fail.
    try:
        import requests  # type: ignore
    except ModuleNotFoundError:
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

    import scraper.connector.website_api as website_api


class DummyResponse:
    def __init__(self, status=200, payload=None):
        self._payload = payload or {}

    def raise_for_status(self):
        if self._payload.get("raise", False):
            raise Exception("status error")

    def json(self):
        return self._payload


def test_start_import_job(monkeypatch):
    def fake_post(url, json):
        assert url.endswith("/start")
        assert json["query"] == "x"
        return DummyResponse(payload={"jobId": "job-123"})

    monkeypatch.setattr(website_api, "requests", types.SimpleNamespace(post=fake_post))
    job = website_api.start_import_job("x", "alibaba", 3)
    assert job == "job-123"


def test_insert_and_complete(monkeypatch):
    calls = []

    def fake_post(url, json):
        calls.append((url, json))
        return DummyResponse()

    import scraper.connector.website_api as wa
    monkeypatch.setattr(wa, "requests", types.SimpleNamespace(post=fake_post))

    wa.insert_imported_products("job-1", [{"title": "a"}])
    wa.complete_import_job("job-1")

    assert any(u.endswith("/insert-products") for u, _ in calls)
    assert any(u.endswith("/complete") for u, _ in calls)
