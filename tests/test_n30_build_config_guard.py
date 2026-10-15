"""N30: kiem tra chot chan cau hinh trong
scripts/build_features_v2_N30.py::verify_config_guard() - cung nguyen tac
da ap dung cho N20 (xem tests/test_n20_build_config_guard.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_features_v2_N30 import (  # noqa: E402
    CONFIG_N30_PATH,
    REQUIRED_DEX_ADDRESSES,
    verify_config_guard,
)


def test_config_n30_path_exists():
    assert CONFIG_N30_PATH.exists()


def test_config_n30_contains_all_required_dex_addresses():
    config = verify_config_guard(CONFIG_N30_PATH)
    missing = REQUIRED_DEX_ADDRESSES - set(config.allowlist)
    assert not missing, f"configs/data_N30.yaml thiếu: {missing}"


def test_guard_rejects_wrong_config_path(tmp_path):
    fake_path = tmp_path / "data_fake.yaml"
    fake_path.write_text("trajectory:\n  max_depth: 1\n  time_horizon_hours: 1\n  min_tainted_share: 0.05\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        verify_config_guard(fake_path)


def test_guard_rejects_config_missing_kyberswap(tmp_path, monkeypatch):
    import scripts.build_features_v2_N30 as mod

    broken = tmp_path / "data_N30.yaml"
    broken.write_text(
        "trajectory:\n  max_depth: 6\n  time_horizon_hours: 72\n  min_tainted_share: 0.05\n"
        "dex_allowlist:\n"
        "  - \"0x66a9893cc07d91d95644aedd05d03f95e1dba8af\"\n"
        "  - \"0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad\"\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "CONFIG_N30_PATH", broken)
    with pytest.raises(AssertionError):
        mod.verify_config_guard(broken)
