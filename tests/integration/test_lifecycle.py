import sqlite3
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine

from aurora.data import db as db_mod
from aurora.data import defs as defs_mod
import aurora.data.client as client_mod
from aurora.app.api import app


def _db_tables(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    rows = {r[0] for r in cur.fetchall()}
    conn.close()
    return rows


def test_init_db_creates_tables(tmp_path, monkeypatch):
    db_file = tmp_path / "init.db"
    db_path = str(db_file)
    monkeypatch.setattr(defs_mod, "DATABASE_URL", f"sqlite:///{db_path}")

    db_mod.init_db()

    tables = _db_tables(db_path)
    assert "message" in tables
    assert "message_fts" in tables


def test_populate_db_inserts_rows(tmp_path, monkeypatch):
    db_file = tmp_path / "pop.db"
    db_path = str(db_file)
    monkeypatch.setattr(defs_mod, "DATABASE_URL", f"sqlite:///{db_path}")

    def fake_get(*args, **kwargs):
        class DummyResp:
            def raise_for_status(self):
                return

            def json(self):
                return {
                    "items": [
                        {
                            "id": "10",
                            "user_id": "u10",
                            "user_name": "eve",
                            "timestamp": "2020-05-01T00:00:00",
                            "message": "alpha"
                        },
                        {
                            "id": "11",
                            "user_id": "u11",
                            "user_name": "mallory",
                            "timestamp": "2020-05-02T00:00:00",
                            "message": "beta"
                        },
                    ]
                }

        return DummyResp()

    monkeypatch.setattr("requests.get", fake_get)

    db_mod.init_db()
    db_mod.populate_db()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, user_name, message FROM message ORDER BY id")
    rows = cur.fetchall()
    conn.close()

    assert len(rows) == 2
    assert rows[0][0] == "10"
    assert rows[0][2] == "alpha"


def test_app_startup_runs_init_and_populate(tmp_path, monkeypatch):
    db_file = tmp_path / "appstart.db"
    db_path = str(db_file)
    monkeypatch.setattr(defs_mod, "DATABASE_URL", f"sqlite:///{db_path}")

    client_mod.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    def fake_get(*args, **kwargs):
        class DummyResp:
            def raise_for_status(self):
                return

            def json(self):
                return {
                    "items": [
                        {
                            "id": "21",
                            "user_id": "u21",
                            "user_name": "trent",
                            "timestamp": "2021-01-01T00:00:00",
                            "message": "startup-msg"
                        }
                    ]
                }

        return DummyResp()

    monkeypatch.setattr("requests.get", fake_get)

    with TestClient(app) as client:
        resp = client.get("/search?q=startup-msg")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id FROM message WHERE id = ?", ("21",))
    found = cur.fetchone()
    conn.close()
    assert found is not None
