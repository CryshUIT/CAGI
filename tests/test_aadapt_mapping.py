"""Test cho src/features/aadapt_mapping.py — dam bao mapping AADAPT luon
khop DAY DU voi danh sach feature motif that trong configs/features.yaml,
va khong co ID la (typo) so voi Table 2 (tab:aadapt) cua bai. Neu sau nay
ai doi ten/them/bot feature motif ma khong cap nhat mapping, test nay se
bao loi thay vi am tham sai (dung yeu cau cua nguoi dung)."""
from __future__ import annotations

from pathlib import Path

import yaml

from src.features.aadapt_mapping import (
    AADAPT_TECHNIQUES,
    MOTIF_FEATURE_TO_AADAPT,
    NON_MOTIF_FEATURE_TO_AADAPT,
    TECHNIQUES_WITHOUT_FEATURE_MATCH,
    get_aadapt_ids,
    format_aadapt_ids,
)

ROOT = Path(__file__).resolve().parents[1]
VALID_AADAPT_IDS = set(AADAPT_TECHNIQUES.keys())


def _motif_columns_from_config() -> set:
    """Doc dung configs/features.yaml::feature_groups.motif, ghep thanh ten
    cot that (prefix 'motif_') - KHONG doan/hardcode lai danh sach o day,
    de test tu dong bat loi neu config doi."""
    cfg = yaml.safe_load((ROOT / "configs" / "features.yaml").read_text(encoding="utf-8"))
    motif_names = cfg["feature_groups"]["motif"]
    return {f"motif_{name}" for name in motif_names}


def test_every_config_motif_column_is_covered_by_mapping_or_documented_absent():
    """Moi cot motif_* dinh nghia trong configs/features.yaml phai co mat
    trong MOTIF_FEATURE_TO_AADAPT (khong duoc am tham thieu)."""
    config_motifs = _motif_columns_from_config()
    mapped_motifs = set(MOTIF_FEATURE_TO_AADAPT.keys())
    missing = config_motifs - mapped_motifs
    assert not missing, (
        f"Cac cot motif sau co trong configs/features.yaml nhung CHUA duoc anh xa AADAPT: "
        f"{sorted(missing)} - can them vao MOTIF_FEATURE_TO_AADAPT hoac ghi ro ly do khong map."
    )


def test_mapping_does_not_reference_unknown_motif_columns():
    """MOTIF_FEATURE_TO_AADAPT khong duoc chua ten cot khong ton tai trong
    config (tranh mapping "ma" tro toi feature da bi xoa/doi ten)."""
    config_motifs = _motif_columns_from_config()
    mapped_motifs = set(MOTIF_FEATURE_TO_AADAPT.keys())
    extra = mapped_motifs - config_motifs
    assert not extra, f"MOTIF_FEATURE_TO_AADAPT tham chieu cot khong con trong config: {sorted(extra)}"


def test_all_referenced_aadapt_ids_are_valid_table2_ids():
    """Moi AADAPT ID xuat hien trong bat ky mapping nao (motif hoac non-motif)
    deu phai la 1 trong dung 7 ID cua Table 2 - khong co ID la/typo."""
    all_ids = set()
    for ids in MOTIF_FEATURE_TO_AADAPT.values():
        all_ids.update(ids)
    for ids in NON_MOTIF_FEATURE_TO_AADAPT.values():
        all_ids.update(ids)
    invalid = all_ids - VALID_AADAPT_IDS
    assert not invalid, f"ID khong nam trong Table 2 (tab:aadapt): {sorted(invalid)}"


def test_every_table2_technique_is_either_mapped_or_explicitly_documented_absent():
    """Moi 1 trong 7 AADAPT ID cua Table 2 phai xuat hien it nhat 1 lan
    trong mapping (motif hoac non-motif), HOAC nam trong danh sach
    TECHNIQUES_WITHOUT_FEATURE_MATCH (thieu co chu dich, khong phai bo sot)."""
    all_mapped_ids = set()
    for ids in MOTIF_FEATURE_TO_AADAPT.values():
        all_mapped_ids.update(ids)
    for ids in NON_MOTIF_FEATURE_TO_AADAPT.values():
        all_mapped_ids.update(ids)

    for technique_id in AADAPT_TECHNIQUES:
        covered = technique_id in all_mapped_ids
        documented_absent = technique_id in TECHNIQUES_WITHOUT_FEATURE_MATCH
        assert covered or documented_absent, (
            f"{technique_id} khong co trong mapping VA khong nam trong "
            f"TECHNIQUES_WITHOUT_FEATURE_MATCH - thieu sot am tham, can xu ly."
        )
        # khong duoc vua co mapping vua bi liet vao "khong co feature khop"
        assert not (covered and documented_absent), (
            f"{technique_id} vua duoc mapping vua nam trong TECHNIQUES_WITHOUT_FEATURE_MATCH - mau thuan."
        )


def test_get_aadapt_ids_known_and_unknown_feature():
    assert get_aadapt_ids("motif_split") == ["ADT3028", "ADT3028.005", "ADT3030.003"]
    assert get_aadapt_ids("motif_bridge_then_swap") == ["ADT3005"]
    assert get_aadapt_ids("action_count_mixer_or_exit_ratio") == ["ADT3030", "ADT3030.003"]
    assert get_aadapt_ids("log_amount_mean") == []  # feature co thuc nhung khong lien quan AADAPT


def test_format_aadapt_ids_empty_case():
    assert format_aadapt_ids("burstiness") == "—"
    assert format_aadapt_ids("motif_peel_like_chain") == "ADT3028.005"


def test_bridge_context_excluded_motifs_still_traceable_in_mapping():
    """motif_bridge_then_swap/motif_nested_bridge bi loai khoi feature set
    cua M1 chinh thuc (BRIDGE_CONTEXT_COLS_EXCLUDED) nhung VAN phai con trong
    mapping nay (de traceable neu include_bridge_context=True) - test nay
    xac nhan module khong vo tinh xoa mat chung."""
    assert "motif_bridge_then_swap" in MOTIF_FEATURE_TO_AADAPT
    assert "motif_nested_bridge" in MOTIF_FEATURE_TO_AADAPT
