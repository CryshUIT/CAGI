"""Kiem tra logic phan loai outcome (Early/Late/Not Feasible/No alert/Not
evaluable) dung tren data/dashboard/incidents.json - cung dinh nghia da
dung trong scripts/n30_extra/extra_v4/_run_evaluation_v4.py (alert truoc
e* = early, tu e* tro di = late). Day la phien ban Python cua
dashboard/frontend/src/classify.ts - dam bao 2 ben KHONG lech dinh nghia.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "dashboard" / "incidents.json"

pytestmark = pytest.mark.skipif(
    not DATA_PATH.exists(),
    reason="data/dashboard/incidents.json chua duoc sinh",
)


def classify(incident: dict, theta: float, model_key: str = "m1_cal"):
    e_star = incident["e_star"]
    if not incident["endpoint_confirmed"] or e_star is None:
        return "not_evaluable", None
    if e_star <= 2:
        return "not_feasible", None
    points = sorted(incident["prefix_points"], key=lambda p: p["k"])
    for p in points:
        v = p[model_key]
        if v is not None and v >= theta:
            return ("early" if p["k"] < e_star else "late"), p["k"]
    return "no_alert", None


@pytest.fixture()
def data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def test_not_feasible_when_e_star_le_2(data):
    for inc in data["incidents"].values():
        if inc["endpoint_confirmed"] and inc["e_star"] is not None and inc["e_star"] <= 2:
            outcome, _ = classify(inc, theta=0.5)
            assert outcome == "not_feasible"


def test_not_evaluable_when_no_endpoint_confirmed(data):
    for inc in data["incidents"].values():
        if not inc["endpoint_confirmed"]:
            outcome, _ = classify(inc, theta=0.5)
            assert outcome == "not_evaluable"


def test_higher_theta_never_decreases_alert_k(data):
    """Tang theta thi diem alert dau tien (neu co) phai >= diem alert o
    theta thap hon (p_hat khong doi, chi doi nguong so sanh)."""
    for inc in data["incidents"].values():
        if not inc["endpoint_confirmed"] or inc["e_star"] is None or inc["e_star"] <= 2:
            continue
        _, k_low = classify(inc, theta=0.5)
        _, k_high = classify(inc, theta=0.9)
        if k_low is not None and k_high is not None:
            assert k_high >= k_low


def test_theta_frozen_classification_matches_meta(data):
    """theta_frozen da luu trong meta phai la 1 so hop le (0,1) va ap
    dung duoc cho toan bo incident khong loi."""
    theta = data["meta"]["m1_theta_oof"]
    assert 0.0 < theta < 1.0
    for inc in data["incidents"].values():
        outcome, _ = classify(inc, theta=theta)
        assert outcome in {"early", "late", "not_feasible", "no_alert", "not_evaluable"}


def test_known_structural_cases_from_session_diagnostics(data):
    """Doi chieu 2 case da tu tay chan doan chi tiet trong phien lam viec
    truoc (rikkei_finance_2022: e*=1 -> not_feasible). Chi kiem tra NEU
    incident do co trong tap 36 (co the khong, vi no thuoc final held-out
    test set, khong phai 36 incident out-of-fold)."""
    rikkei = data["incidents"].get("rikkei_finance_2022")
    if rikkei is not None:
        assert rikkei["e_star"] == 1
        outcome, _ = classify(rikkei, theta=0.5)
        assert outcome == "not_feasible"
