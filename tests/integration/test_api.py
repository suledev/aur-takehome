import time
import pytest

import aurora.data.client as client_mod


def test_search_endpoint_returns_empty(client, monkeypatch):
    def fake_search(query_text, limit=10, offset=0):
        return [{"id": "1", "user_id": "u1", "user_name": "alice", "timestamp": "2020-01-01T00:00:00", "message": "hello"}]

    monkeypatch.setattr(client_mod, "search_messages", fake_search)

    resp = client.get("/search?q=hello")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert isinstance(data["results"], list)
    assert data["results"][0]["message"] == "hello"


def test_search_basic_returns_results(client, monkeypatch):
    def fake_search(query_text, limit=10, offset=0):
        return [
            {"id": "1", "user_id": "u1", "user_name": "alice", "timestamp": "2020-01-01T00:00:00", "message": "hello"},
            {"id": "2", "user_id": "u2", "user_name": "bob", "timestamp": "2020-01-02T00:00:00", "message": "world"},
        ]

    monkeypatch.setattr(client_mod, "search_messages", fake_search)

    resp = client.get("/search?q=hello")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["message"] == "hello"


def test_search_pagination_forwards_limit_and_offset(client, monkeypatch):
    captured = {}

    def fake_search(query_text, limit=10, offset=0):
        captured["query_text"] = query_text
        captured["limit"] = limit
        captured["offset"] = offset
        return []

    monkeypatch.setattr(client_mod, "search_messages", fake_search)

    resp = client.get("/search?q=test&limit=5&offset=15")
    assert resp.status_code == 200
    assert captured["query_text"] == "test"
    assert captured["limit"] == 5
    assert captured["offset"] == 15


def test_search_validation_q_min_length(client):
    resp = client.get("/search?q=")
    assert resp.status_code == 422


def test_search_validation_limit_bounds(client):
    resp = client.get("/search?q=hi&limit=101")
    assert resp.status_code == 422


def test_search_handles_internal_error(client, monkeypatch):
    def broken_search(query_text, limit=10, offset=0):
        raise RuntimeError("boom")

    monkeypatch.setattr(client_mod, "search_messages", broken_search)

    resp = client.get("/search?q=error")
    assert resp.status_code == 500
    body = resp.json()
    assert "internal error" in body.get("detail", "")


def test_process_time_header_is_set(client, monkeypatch):
    def fake_search(query_text, limit=10, offset=0):
        time.sleep(0.01)
        return []

    monkeypatch.setattr(client_mod, "search_messages", fake_search)

    resp = client.get("/search?q=hi")
    assert resp.status_code == 200
    assert "X-Process-Time" in resp.headers
    pt = float(resp.headers["X-Process-Time"])
    assert pt >= 0.0
