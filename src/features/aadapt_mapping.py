"""Ánh xạ tĩnh, traceable từ feature/motif THẬT của CAGI sang technique ID
của MITRE AADAPT (github.com/mitre/AADAPT, adapt-data/data/techniques.yaml).

Nguồn của mapping: đúng bảng Table 2 (`tab:aadapt`) trong bài — cột "CAGI
observable" của bảng đó liệt kê cụm từ mô tả tín hiệu quan sát được; module
này khớp NGƯỢC LẠI mỗi cụm từ đó với đúng tên cột feature thật đang tồn tại
trong pipeline (`configs/features.yaml` nhóm `motif`, cộng feature
`action_count_mixer_or_exit(_ratio)` ở nhóm `semantic_action` cho 2 kỹ
thuật không có motif tương ứng — xem `_NON_MOTIF_MATCHES` bên dưới).

QUAN TRỌNG — 1 feature có thể map tới NHIỀU AADAPT ID (many-to-many), vì
Table 2 của bài dùng lại cùng 1 quan sát (vd "split") cho nhiều kỹ thuật/
sub-kỹ thuật khác nhau (ADT3028 và ADT3028.005 đều nhắc "split"). Mỗi mapping
đều trích dẫn ĐÚNG cụm từ trong Table 2 làm căn cứ (xem docstring từng biến),
không tự suy diễn thêm.

KHÔNG map được (để ngỏ, có chủ đích — xem TECHNIQUES_WITHOUT_FEATURE_MATCH):
- ADT3028.001 (Anonymous Wallets — "chains of fresh intermediary addresses"):
  không có feature nào trong pipeline theo dõi được TÍNH MỚI (fresh/first-seen)
  của 1 địa chỉ — `unique_counterparties`/`branch_count`/`fan_out`/`path_depth`
  chỉ đếm SỐ LƯỢNG/cấu trúc kết nối, không phân biệt địa chỉ đã từng xuất
  hiện ở nơi khác hay chưa. Không ép feature không liên quan vào đây.

LƯU Ý VỀ M1 CHÍNH THỨC (không phải lỗi của module này): `motif_bridge_then_swap`
và `motif_nested_bridge` nằm trong `BRIDGE_CONTEXT_COLS_EXCLUDED`
(`src/models/baselines.py`) — bị loại khỏi feature set của M1 chính thức từ
2026-08-28 (gây overfitting theo protocol cụ thể, xem
`results/reports/bridge_context_ablation_investigation.md`). Mapping cho
ADT3005 (Cross-Chain Swaps/Hopping) vẫn được định nghĩa đầy đủ ở đây để
traceable/dùng lại nếu `include_bridge_context=True`, nhưng SẼ KHÔNG BAO GIỜ
xuất hiện trong SHAP contribution của 1 alert M1 chính thức, vì XGBoost
`pred_contribs` chỉ tính trên đúng `model.feature_cols_` đã fit — không phải
lỗi thiếu sót của mapping.
"""
from __future__ import annotations

from typing import Dict, List, NamedTuple


class AadaptTechnique(NamedTuple):
    technique_id: str
    name: str
    cagi_observable: str  # nguyên văn cột "CAGI observable" trong Table 2 của bài


# Đúng 7 dòng của Table 2 (tab:aadapt) — ID/tên đã verify khớp catalogue
# chính thức MITRE AADAPT, KHÔNG cần verify lại (theo yêu cầu).
AADAPT_TECHNIQUES: Dict[str, AadaptTechnique] = {
    "ADT3005": AadaptTechnique(
        "ADT3005", "Cross-Chain Swaps (Hopping)",
        "bridge→swap, nested bridge hops, chain change",
    ),
    "ADT3028": AadaptTechnique(
        "ADT3028", "Siphon Funds",
        "split, fan-out, many counterparties",
    ),
    "ADT3028.001": AadaptTechnique(
        "ADT3028.001", "Anonymous Wallets",
        "chains of fresh intermediary addresses",
    ),
    "ADT3028.003": AadaptTechnique(
        "ADT3028.003", "Layering",
        "swap→split, rapid token pivot, repeated transfer/swap",
    ),
    "ADT3028.005": AadaptTechnique(
        "ADT3028.005", "Peel Chains",
        "peel-like chain, repeated split",
    ),
    "ADT3030": AadaptTechnique(
        "ADT3030", "Use Anonymizing Services",
        "mixer-or-exit interaction, abrupt flow end",
    ),
    "ADT3030.003": AadaptTechnique(
        "ADT3030.003", "Tumblers",
        "mixer deposit, merge/split around mixer",
    ),
}

# Feature motif THẬT (tên cột trong features_v2.parquet, prefix "motif_" +
# tên trong configs/features.yaml::feature_groups.motif) -> danh sach
# AADAPT ID. Moi dong trich dan DUNG cum tu trong cot "CAGI observable"
# lam can cu (khong tu bia).
MOTIF_FEATURE_TO_AADAPT: Dict[str, List[str]] = {
    # "bridge -> swap" -> ADT3005
    "motif_bridge_then_swap": ["ADT3005"],
    # "nested bridge hops" -> ADT3005
    "motif_nested_bridge": ["ADT3005"],
    # "split, fan-out" (ADT3028) + "repeated split" (ADT3028.005) +
    # "merge/split around mixer" (ADT3030.003, dong-quan-sat voi motif_merge)
    "motif_split": ["ADT3028", "ADT3028.005", "ADT3030.003"],
    # "merge/split around mixer" - CHI xuat hien trong mo ta ADT3030.003,
    # khong co cho nao khac trong Table 2 nhac "merge" - khong ep vao
    # ADT3028 (mo ta ADT3028 chi noi "split, fan-out", khong noi "merge").
    "motif_merge": ["ADT3030.003"],
    # "peel-like chain" -> ADT3028.005
    "motif_peel_like_chain": ["ADT3028.005"],
    # "swap -> split" -> ADT3028.003
    "motif_swap_then_split": ["ADT3028.003"],
    # "rapid token pivot" -> ADT3028.003
    "motif_rapid_token_pivot": ["ADT3028.003"],
}

# 2 ky thuat KHONG co feature "motif" tuong ung truc tiep (task buoc 3) -
# kiem tra cheo sang nhom feature khac (semantic_action) neu khop ngu nghia
# hon. "action_count_mixer_or_exit(_ratio)" khop TRUC TIEP theo ten voi
# "mixer-or-exit interaction" (ADT3030) va "mixer deposit" (ADT3030.003,
# action_type=mixer_or_exit trong event_schema CHINH LA hanh dong nap vao
# mixer/dich vu thoat - xem configs/features.yaml::event_schema).
NON_MOTIF_FEATURE_TO_AADAPT: Dict[str, List[str]] = {
    "action_count_mixer_or_exit_ratio": ["ADT3030", "ADT3030.003"],
    "action_count_mixer_or_exit": ["ADT3030", "ADT3030.003"],
}

# ADT3028.001 (Anonymous Wallets) CO CHU DICH khong nam trong 2 dict tren -
# xem docstring dau file. Liet ke tuong minh o day de test/code khac kiem
# tra duoc "day la thieu co chu dich, khong phai bo sot".
TECHNIQUES_WITHOUT_FEATURE_MATCH: List[str] = ["ADT3028.001"]


def get_aadapt_ids(feature_name: str) -> List[str]:
    """Tra ve danh sach AADAPT ID cho 1 ten cot feature that (motif hoac
    action_count_mixer_or_exit*). Tra ve [] neu feature khong co anh xa
    (vd khong lien quan toi rua tien co the truy vet duoc, hoac la 1 trong
    nhung feature khong nam trong Table 2)."""
    return MOTIF_FEATURE_TO_AADAPT.get(feature_name) or NON_MOTIF_FEATURE_TO_AADAPT.get(feature_name, [])


def format_aadapt_ids(feature_name: str) -> str:
    """Chuoi hien thi cho report (vd 'ADT3028, ADT3028.005') - rong neu
    khong co anh xa."""
    ids = get_aadapt_ids(feature_name)
    return ", ".join(ids) if ids else "—"
