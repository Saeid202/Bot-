import types
import pytest

import connector.website_api as website_api


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

    import connector.website_api as wa
    monkeypatch.setattr(wa, "requests", types.SimpleNamespace(post=fake_post))

    wa.insert_imported_products("job-1", [{"title": "a"}])
    wa.complete_import_job("job-1")

    assert any(u.endswith("/insert-products") for u, _ in calls)
    assert any(u.endswith("/complete") for u, _ in calls)
