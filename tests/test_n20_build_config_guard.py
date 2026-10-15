"""Checkpoint C'' muc 4: kiem tra chot chan cau hinh trong
scripts/build_features_v2_N20.py::verify_config_guard() - phat hien lan 3
mot loi cau hinh tuong tu (quen truyen config N20 vao load_rq1_trajectories,
xem Checkpoint C' muc 6) bi bat qua doi chieu tay; test nay dam bao chot
chan KHONG bi xoa/lam yeu di trong tuong lai ma khong ai biet.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_features_v2_N20 import (  # noqa: E402
    CONFIG_N20_PATH,
    REQUIRED_DEX_ADDRESSES,
    verify_config_guard,
)


def test_config_n20_path_exists():
    assert CONFIG_N20_PATH.exists(), f"{CONFIG_N20_PATH} phải tồn tại để chốt chặn có ý nghĩa."


def test_config_n20_contains_required_universal_router_addresses():
    config = verify_config_guard(CONFIG_N20_PATH)
    missing = REQUIRED_DEX_ADDRESSES - set(config.allowlist)
    assert not missing, f"configs/data_N20.yaml thiếu địa chỉ Universal Router: {missing}"


def test_guard_rejects_wrong_config_path(tmp_path):
    fake_path = tmp_path / "data_fake.yaml"
    fake_path.write_text("trajectory:\n  max_depth: 1\n  time_horizon_hours: 1\n  min_tainted_share: 0.05\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        verify_config_guard(fake_path)


def test_guard_rejects_config_missing_universal_router(tmp_path, monkeypatch):
    """Giả lập trường hợp data_N20.yaml bị sửa nhầm, mất allowlist Universal
    Router — chốt chặn PHẢI raise, không im lặng dùng config thiếu."""
    import scripts.build_features_v2_N20 as mod

    broken = tmp_path / "data_N20.yaml"
    broken.write_text(
        "trajectory:\n  max_depth: 6\n  time_horizon_hours: 72\n  min_tainted_share: 0.05\n"
        "dex_allowlist:\n  - \"0x7a250d5630b4cf539739df2c5dacb4c659f2488d\"\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "CONFIG_N20_PATH", broken)
    with pytest.raises(AssertionError):
        mod.verify_config_guard(broken)
