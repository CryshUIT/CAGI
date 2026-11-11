"""Test cho CAGI-ED SOC Dashboard (dashboard/backend/app.py) - Phan 1,
36 incident historical. Kiem tra: khong goi mang, serve dung du lieu da
luu (data/dashboard/incidents.json), xu ly dung trang thai thieu du lieu.
"""
from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "dashboard" / "incidents.json"

pytestmark = pytest.mark.skipif(
    not DATA_PATH.exists(),
    reason="data/dashboard/incidents.json chua duoc sinh (chay scripts/dashboard/generate_oof_dashboard_data.py)",
)


@pytest.fixture()
def client():
    import sys
    sys.path.insert(0, str(ROOT / "dashboard" / "backend"))
    import importlib

    import app as dashboard_app  # type: ignore
    importlib.reload(dashboard_app)
    from fastapi.testclient import TestClient
    return TestClient(dashboard_app.app)


def test_no_network_calls_during_request(client, monkeypatch):
    """Dashboard Mode A (36 incident historical) KHONG duoc goi mang KHI
    XU LY REQUEST - chi doc file JSON da sinh san. Chi chan ket noi toi
    dia chi KHONG PHAI loopback (127.0.0.1/localhost) - TestClient cua
    FastAPI (qua httpx ASGITransport) co the tu tao socket noi bo
    (loopback) cho co che internal cua no, KHONG phai goi mang that ra
    ngoai; chan ca loopback se bao false positive."""
    real_connect = socket.socket.connect

    def _guarded_connect(self, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise AssertionError(
                f"Phat hien goi mang THAT toi dia chi ngoai ({address}) trong luc xu ly request dashboard - VI PHAM Mode A."
            )
        return real_connect(self, address, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
    resp = client.get("/api/incidents")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_served_predictions_equal_saved_oof(client):
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    any_id = next(iter(raw["incidents"].keys()))
    resp = client.get(f"/api/incidents/{any_id}")
    assert resp.status_code == 200
    served = resp.json()
    saved = raw["incidents"][any_id]
    assert served["prefix_points"] == saved["prefix_points"]
    assert served["e_star"] == saved["e_star"]


def test_meta_matches_saved_file(client):
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    resp = client.get("/api/meta")
    assert resp.status_code == 200
    assert resp.json() == raw["meta"]


def test_unknown_incident_returns_404(client):
    resp = client.get("/api/incidents/this_incident_does_not_exist_12345")
    assert resp.status_code == 404


def test_new_analysis_explicitly_disabled(client):
    resp = client.get("/api/new-analysis")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is False


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["data_file_exists"] is True
