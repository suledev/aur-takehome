import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure repo root parent is on sys.path so `import aurora` works when tests run
ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

# Prevent network calls during import/populate
@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def dummy_get(*args, **kwargs):
        class DummyResponse:
            def raise_for_status(self):
                return
            def json(self):
                return {"items": []}
        return DummyResponse()

    monkeypatch.setattr("requests.get", dummy_get)

@pytest.fixture
def client():
    # Import inside fixture so sys.path modifications above are effective
    from aurora.app.api import app
    return TestClient(app)
