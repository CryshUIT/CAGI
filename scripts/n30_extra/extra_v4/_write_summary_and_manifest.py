# -*- coding: utf-8 -*-
"""Viet SUMMARY_v4.txt + SHA-256 manifest cho toan bo file N37 (v4_heldout)."""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT_REPORTS = ROOT / "results" / "reports" / "extra_v4"
OUT_TABLES = ROOT / "results" / "tables" / "extra_v4"

FILES_FOR_MANIFEST = [
    "metadata/incident_registry_N37.csv",
    "configs/data_N37.yaml",
    "data/processed/features_v2_N37.parquet",
    "configs/features_v2_computed_N37.json",
    "metadata/hard_negative_registry_v2_complexity_N37_new.csv",
    "metadata/hard_negative_registry_v2_complexity_N37_combined.csv",
    "metadata/hard_negative_registry_N37_combined.csv",
    "data/processed/sturdy_finance_2023_events.json",
    "data/processed/jimbos_protocol_2023_events.json",
    "data/processed/rodeo_finance_2023_events.json",
    "data/processed/sentiment_protocol_2023_events.json",
    "data/processed/pike_finance_2024_events.json",
    "data/processed/uwu_lend_2024_events.json",
    "results/reports/extra_v4/decision_log_2026-11-04.md",
    "results/reports/extra_v4/collect_v4_heldout_summary.json",
    "results/reports/extra_v4/mining_v2complexity_truncation_log_N37_2026-11-05.json",
    "results/tables/extra_v4/held_out_v4_summary.csv",
    "results/tables/extra_v4/held_out_v4_per_incident.csv",
    "results/tables/extra_v4/held_out_v4_lead_time.csv",
    "results/tables/extra_v4/v4_pooled_loio_summary.csv",
    "results/reports/extra_v4/evaluation_v4_raw_results.json",
]

manifest = {}
for rel in FILES_FOR_MANIFEST:
    p = ROOT / rel
    if p.exists():
        manifest[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    else:
        manifest[rel] = None

(OUT_REPORTS / "extra_v4_files_sha256.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Da luu {OUT_REPORTS / 'extra_v4_files_sha256.json'} ({sum(1 for v in manifest.values() if v)} / {len(manifest)} file)")

reg = pd.read_csv(ROOT / "metadata" / "incident_registry_N37.csv")
v4 = reg[reg.eval_tier == "v4_heldout"]
usable = v4[v4.incident_id != "fortress_protocol_2022"]

feat = pd.read_parquet(ROOT / "data" / "processed" / "features_v2_N37.parquet")
held_summary = pd.read_csv(OUT_TABLES / "held_out_v4_summary.csv")
held_per_inc = pd.read_csv(OUT_TABLES / "held_out_v4_per_incident.csv")
pooled_summary = pd.read_csv(OUT_TABLES / "v4_pooled_loio_summary.csv")

lines = []
lines.append("SUMMARY_v4 - N=37 (v4_heldout) mo rong dataset, danh gia held-out + pooled LOIO")
lines.append("Ngay chay: 2026-11-05. Khong dung de hoi nguoi dung trong luc chay (chi dao N=37).")
lines.append("")
lines.append("=== 1. So incident cuoi cung ===")
lines.append(f"Da de xuat: 7 incident moi. Thu thap THANH CONG: 6/7 "
              f"(fortress_protocol_2022 BI LOAI - loi thu thap thuc BscTraceAPIError, "
              f"thu lai doc lap 1 lan van loi GIONG, khong sua code de ep qua).")
lines.append(f"Tong incident SU DUNG trong N37: 30 (cu, N30) + 6 (moi) = 36 incident "
              f"(+ 1 dong registry bi loai, van GIU trong registry theo append-only, "
              f"KHONG dung trong feature build/evaluation).")
lines.append("")
lines.append("=== 2. Phan bo chain (6 incident moi usable) ===")
lines.append(usable.groupby("chain_primary").size().to_string())
lines.append("")
lines.append("=== 3. Hard-negative moi da mine (v2_complexity, +-7 ngay doi xung) ===")
lines.append("Tong 50 hard-negative moi (10+10+3+7+10+10 cho 6 incident, "
              "rodeo/sentiment duoi target=10 vi het candidate trong max_checked=150, "
              "KHONG ha tieu chi de ep du).")
lines.append("0 dia chi hard-negative trung giua bat ky 2 incident (cu hoac moi).")
lines.append("")
lines.append("=== 4. So action / so dong prefix / %% positive ===")
n_total = len(feat)
n_pos = int((feat.label == 1).sum())
lines.append(f"Tong dong prefix (sau khi tinh feature, TRUOC dedupe danh gia): {n_total}")
lines.append(f"%% positive (dong): {n_pos/n_total:.4%} ({n_pos}/{n_total})")
for iid in ["sturdy_finance_2023", "jimbos_protocol_2023", "rodeo_finance_2023",
            "sentiment_protocol_2023", "pike_finance_2024", "uwu_lend_2024"]:
    sub = feat[(feat.source_id == iid) & (feat.prefix_label == "ratio_100")]
    n_actions = int(sub["trajectory_len"].iloc[0]) if len(sub) else None
    lines.append(f"  {iid:28s} n_actions(trajectory_len, luc build cuoi) = {n_actions}")
lines.append("")
lines.append("=== 5. Endpoint xac nhan (6 incident moi) ===")
for _, r in usable.iterrows():
    lines.append(f"  {r['incident_id']:28s} endpoint_confirmed={r['endpoint_confirmed']} "
                 f"endpoint_basis={r['endpoint_basis']} type={r['type_of_first_endpoint_action']} "
                 f"n_mixer_or_exit={r['n_mixer_or_exit']} n_bridge_deposit={r['n_bridge_deposit']}")
lines.append("3/6 co endpoint_confirmed=True (sturdy, jimbos, rodeo). 3/6 KHONG (sentiment, "
              "pike, uwu_lend) - TRANG THAI NAY DA CO SAN VA HOP LE trong N30 (10/30 incident cu "
              "cung endpoint_confirmed=False) - KHONG dung lam ly do loai incident.")
lines.append("")
lines.append("=== 6. Ket qua (a) HELD-OUT (train 30 cu, test 6 moi, M1/B3' DONG BANG) ===")
lines.append(held_summary.to_string(index=False))
lines.append("")
lines.append("Per-incident PR-AUC (held-out):")
lines.append(held_per_inc.to_string(index=False))
lines.append("")
lines.append("** KET QUA XAU/CAN CHU Y (theo dung yeu cau neu trung thuc) **:")
lines.append("- pike_finance_2024: PR-AUC RAT THAP (M1=0.077, B3'=0.10) - vi trajectory CHI CO "
             "1 action (dot USDC qua CCTP, frontier dung lai o do - DUNG hanh vi trace, khong phai "
             "loi) nen gan nhu KHONG CO feature de phan biet voi hard-negative. Day la incident "
             "YEU NHAT trong 6 incident moi.")
lines.append("- Pooled PR-AUC held-out RAT CAO (~0.97) NHUNG mau nho va de: 4/6 incident co "
             "PR-AUC=1.0 tuyet doi (jimbos/rodeo/sentiment/uwu_lend) voi so hard-negative MOI "
             "RAT IT (10-45 dong) - KHONG nen dien giai day la bang chung manh, chi la quan sat "
             "post-hoc tren N nho.")
lines.append("- EDR (ty le phat hien TRUOC endpoint) chi tinh duoc tren 3/6 incident co endpoint "
             "xac nhan (eligible_te=3) - mau RAT NHO, CI khong dang ke.")
lines.append("- Median lead time RAT NGAN (0.02-0.13 gio, duoi 8 phut) - NGAN HON DANG KE so voi "
             "da so incident N30 cu (thuong vai gio den vai ngay) - canh bao alert bat len GAN SAT "
             "endpoint, khong som nhu ky vong.")
lines.append("")
lines.append("=== 7. Ket qua (b) v4 POOLED LOIO (36 group, bootstrap 2000, seed=42) ===")
lines.append(pooled_summary.to_string(index=False))
lines.append("")
lines.append("So sanh voi v3 (N=30, dong bang, KHONG doi): M1=0.7762, B3'=0.7266 (tu "
             "oof_M1.parquet / run_extra_N30_exploratory.py). v4 pooled (N=36): M1~0.779, "
             "B3'~0.727 - THAY DOI RAT NHO (trong khoang nhieu). CI 95%% VAN CHONG LAN RAT LON "
             "giua M1 va B3' - KHONG CO BANG CHUNG THONG KE MOI cho thay M1 vuot B3' o N=36, "
             "NHAT QUAN voi ket luan da co tu truoc (M1 khong vuot B3 ve thong ke o N nho).")
lines.append("")
lines.append("=== 8. Incident bi loai giua chung va ly do ===")
lines.append("- Level Finance, Unizen, Moby Trade: LOAI TRUOC KHI THU THAP (thieu provenance xac "
             "thuc - tx hash khong day du / nhan dia chi mau thuan / tx chi la transferOwnership) - "
             "KHONG lien quan ket qua mo hinh.")
lines.append("- fortress_protocol_2022: LOAI SAU KHI DA XAC MINH DIA CHI/TX NHUNG THAT BAI o buoc "
             "THU THAP THAT (BscTraceAPIError, het 5 lan retry, thu lai doc lap van loi GIONG) - "
             "loi THAT trong goi API, KHONG sua code decode/trace de ep qua, KHONG thay bang "
             "incident khac (dung quy tac du phong da chot).")
lines.append("")
lines.append("=== 9. Diem CHUA CHAC CHAN / han che da phat hien ===")
lines.append("- Trong luc kiem tra hash bat buoc (features_v2_N30.parquet khong doi), phat hien "
             "cache cua MOT SO hard-negative thuoc easyfi_2021 (incident N30 CU, KHONG lien quan "
             "N37) co dau hieu TRO LECH qua nhieu lan fetch (non-deterministic qua thoi gian/API "
             "pagination) - DA refetch do_collect=True va PHUC HOI du lieu khong rong, nhung "
             "features_v2_N37.parquet VAN khong byte-identical 100%% voi features_v2_N30.parquet "
             "dong bang (lech ~29/5973 = 0.49%% dong, CHI trong pham vi hard-negative cua "
             "easyfi_2021). features_v2_N30.parquet GOC HOAN TOAN KHONG BI DONG (chi dung file "
             "TAM de so sanh roi xoa) - moi bang v3 cu van giu nguyen, khong anh huong.")
lines.append("- jimbos/rodeo/sentiment_protocol_2023 cung cho thay n_actions KHAC NHAU giua lan "
             "thu thap dau (do_collect=True, luc viet decision_log muc 2) va lan build feature "
             "cuoi (do_collect=False doc cache, muc 6 o tren) - CUNG hien tuong tro du lieu cache "
             "qua thoi gian nhu easyfi_2021, KHONG phai do sua code. So lieu trong features_v2_N37.parquet "
             "(dung de danh gia) la nguon THAT SU CUOI CUNG, khong phai so lieu in luc thu thap dau.")
lines.append("- sentiment_protocol_2023 dung dia chi 1inch v4 AggregationRouter CHUA duoc verify "
             "rieng cho chain arbitrum trong protocol_map.yaml (chi co 'eth') de mining hard-negative "
             "- dia chi THAT xuat hien 302/511 action trong trajectory chinh, nhung KHONG chinh thuc "
             "'verified' theo quy uoc cu - ghi ro de nguoi dung tu danh gia.")
lines.append("- Target_v2_complexity rodeo_finance_2023 (3/10) va sentiment_protocol_2023 (7/10) "
             "khong dat target=10 do het candidate trong 150 checked - mau hard-negative cho 2 "
             "incident nay NHO HON cac incident khac.")
lines.append("")
lines.append("=== Ghi chu ===")
lines.append("Tat ca ket qua TREN DAY la TU CHAY THAT (khong uoc tinh). Xem SHA-256 manifest tai "
             "results/reports/extra_v4/extra_v4_files_sha256.json va decision_log day du tai "
             "results/reports/extra_v4/decision_log_2026-11-04.md.")

(OUT_REPORTS / "SUMMARY_v4.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"Da luu {OUT_REPORTS / 'SUMMARY_v4.txt'}")
