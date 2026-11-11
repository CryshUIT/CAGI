# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT_REPORTS = ROOT / "results" / "reports" / "extra_v4"
OUT_TABLES = ROOT / "results" / "tables" / "extra_v4"

FILES = [
    "metadata/incident_registry_final_heldout.csv",
    "configs/data_final_heldout.yaml",
    "metadata/hard_negative_registry_final_heldout_new.csv",
    "metadata/hard_negative_registry_bsc2_new.csv",
    "data/processed/harvest_finance_2020_events.json",
    "data/processed/rari_capital_fuse_2022_events.json",
    "data/processed/curve_crv_eth_attacker_2023_events.json",
    "data/processed/pancakebunny_2021_events.json",
    "data/processed/rikkei_finance_2022_events.json",
    "data/processed/features_v2_final_heldout_new.parquet",
    "results/reports/extra_v4/M1_FROZEN_final_N36.pkl",
    "results/reports/extra_v4/M1_FROZEN_final_N36_platt_calibrator.pkl",
    "results/reports/extra_v4/M1_FROZEN_final_N36_metadata.json",
    "results/reports/extra_v4/B3prime_FROZEN_final_N36.pkl",
    "results/reports/extra_v4/B3prime_FROZEN_final_N36_platt_calibrator.pkl",
    "results/reports/extra_v4/B3prime_FROZEN_final_N36_metadata.json",
    "results/reports/extra_v4/final_heldout_thresholds_declaration_2026-11-05.md",
    "results/reports/extra_v4/final_heldout_candidates_proposal_2026-11-05.md",
    "results/reports/extra_v4/decision_log_final_heldout_2026-11-05.md",
    "results/reports/extra_v4/verify_final_heldout_9_raw.json",
    "results/reports/extra_v4/collect_final_heldout_3_summary.json",
    "results/reports/extra_v4/collect_bsc4_summary.json",
    "results/reports/extra_v4/collect_allbridge_rikkei_summary.json",
    "results/tables/extra_v4/final_heldout_test_results.csv",
]

manifest = {}
for rel in FILES:
    p = ROOT / rel
    manifest[rel] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None

(OUT_REPORTS / "final_heldout_files_sha256.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Da luu sha256 manifest ({sum(1 for v in manifest.values() if v)}/{len(manifest)} file)")

results = pd.read_csv(OUT_TABLES / "final_heldout_test_results.csv")

lines = []
lines.append("SUMMARY_final_heldout - Kiem dinh cuoi (final held-out) cho M1 (va B3') - 2026-11-05")
lines.append("")
lines.append("=== 1. Danh sach da chot ===")
lines.append("9 incident nguoi dung chot giu (loai Euler Finance, Meerkat Finance - nguon yeu):")
lines.append("Harvest Finance, PancakeBunny, Orion Protocol, Curve CRV/ETH attacker, Spartan Protocol, "
              "Rikkei Finance, Allbridge, Cream Finance (hack 3), Rari Capital Fuse/TribeDAO.")
lines.append("")
lines.append("=== 2. Qua trinh xac minh + thu thap - NHIEU incident bi loai, ly do THAT ===")
lines.append("- LOAI do seed/tx KHONG DON NHAT (nhieu ung vien, khong the xac dinh tx chinh): "
              "Orion Protocol (tx hash nguon thuc ra la dia chi 42 ky tu; 20 tx ung vien khong co cai "
              "noi bat), Cream Finance (206 tx ung vien lap lai, khong co 1 tx noi bat).")
lines.append("- LOAI do trajectory RONG sau khi thu thap: Harvest Finance (0 action, du tx khai thac "
              "xac nhan dung seed/ngay) - khong co du lieu de test.")
lines.append("- LOAI do THU THAP TIMEOUT THAT (>35-40 phut khong tien trien o buoc decode/ghep hanh "
              "dong cho dia chi co khoi luong giao dich cuc lon, xay ra 2 lan doc lap cho Spartan "
              "Protocol): Spartan Protocol, Allbridge. KHONG phai do seed/tx sai hay do quota - BSC API "
              "van hoat dong binh thuong cho cac lenh goi khac cung luc.")
lines.append("- GIU va TEST DUOC: rari_capital_fuse_2022, curve_crv_eth_attacker_2023 (eth), "
              "pancakebunny_2021, rikkei_finance_2022 (bsc).")
lines.append("")
lines.append("** FINAL HELD-OUT SET THUC TE DUNG DE TEST: 4/9 incident (44%). Ty le loai cao (56%) can "
              "nhan manh, KHONG che giau - chu yeu do kho khan thuc te trong thu thap du lieu on-chain "
              "cho incident cu/lon, khong phai do model hay do thiet ke thu nghiem. **")
lines.append("")
lines.append("=== 3. Dong bang mo hinh (TRUOC khi xem incident moi) ===")
lines.append("M1: train tren 36 group (30 N30 + 6 N37), theta_frozen=0.963865 (OUT-OF-FOLD qua "
              "LeaveOneGroupOut, KHONG phai in-sample - xem final_heldout_thresholds_declaration).")
lines.append("B3prime: cung co che, theta_frozen=0.969481.")
lines.append("Nguong da khai bao TRUOC (khong doi sau khi xem ket qua): 0.5 (CHINH, so voi v3), 0.7, 0.9, theta_frozen.")
lines.append("")
lines.append("=== 4. Hard-negative (muc tieu 50, +-7 ngay doi xung) ===")
lines.append("rari_capital_fuse_2022: 50/50 (dat target).")
lines.append("curve_crv_eth_attacker_2023: 3/50 ** DUOI TARGET, DANH DAU ** (chi 7 candidate trong cua so).")
lines.append("pancakebunny_2021: 4/50 ** DUOI TARGET, DANH DAU ** (chi 20 candidate trong cua so).")
lines.append("rikkei_finance_2022: 0/50 ** DUOI TARGET NGHIEM TRONG ** - TOAN BO 150 candidate kiem tra "
              "deu BI LOAI boi tieu chi cau truc (min_candidate_events/fan_out) - KHONG co hard-negative "
              "nao cho incident nay. Khong ha tieu chi de ep du so luong (dung quy tac cu).")
lines.append("")
lines.append("=== 5. Ket qua test (MOT LAN, model DA DONG BANG, KHONG tune lai) ===")
lines.append(results.to_string(index=False))
lines.append("")
lines.append("** KET QUA XAU/QUAN TRONG NHAT CAN NEU RO **:")
lines.append("- CA 2 incident co endpoint xac nhan (rari_capital_fuse_2022: Tornado Cash ETH; "
             "rikkei_finance_2022: TornadoProxyLight BSC) deu cho ket qua 'late_detection' hoac "
             "'never_alerted' o TAT CA 4 nguong, KHONG CO truong hop 'detected_before_endpoint' nao "
             "trong toan bo final held-out set. Day la tin hieu LAP LAI tren 2 incident DOC LAP (2 chain "
             "khac nhau, 2 co che khac nhau) - dang tin hon ket luan truoc chi dua tren 1 incident.")
lines.append("- rikkei_finance_2022: KHONG tinh duoc PR-AUC/FAR (0 hard-negative) - chi co lead time, "
             "va lead time AM o moi nguong dat duoc (M1: -0.036h; B3': -0.045h den -0.35h), 'never_alerted' "
             "o nguong cao.")
lines.append("- pancakebunny_2021: PR-AUC rat cao (M1=0.9861, B3'=1.0) nhung KHONG co endpoint xac nhan - "
             "mau nho (8 positive, 11 negative) - PR-AUC cao co the chi phan anh su khac biet cau truc ro "
             "ret giua trajectory tan cong va hard-negative ngau nhien, khong phai bang chung ve kha nang "
             "phat hien som.")
lines.append("- curve_crv_eth_attacker_2023: mau cuc nho (4 positive, 4 negative), khong co endpoint - "
             "PR-AUC (M1=0.8929) KHONG CO Y NGHIA THONG KE.")
lines.append("- Pooled PR-AUC tren CA 4 incident: M1=0.8494, B3'=0.8358 (deu vuot B0=0.1795 ro ret) - "
             "nhung con so nay bi chi phoi boi incident de nhat (pancakebunny) va khong phan anh dung "
             "kha nang phat hien SOM (xem cac diem lead-time am o tren).")
lines.append("")
lines.append("=== 6. Ket luan trung thuc ===")
lines.append("Kiem dinh final held-out nay KHONG the coi la bang chung manh cho kha nang tong quat hoa "
             "cua M1 tren incident hoan toan moi - ty le loai cao (56%) chu yeu do kho khan thu thap du "
             "lieu on-chain cho incident cu (seed/tx khong con ro rang sau nhieu nam) va mot vai dia chi "
             "co khoi luong giao dich qua lon khien buoc decode khong hoan thanh trong thoi gian hop ly. "
             "PHAT HIEN QUAN TRONG NHAT, lap lai tren CA 2 incident co endpoint xac nhan doc lap: mo hinh "
             "(ca M1 va B3') chi phat hien SAU KHI tien da roi khoi he thong (mixer/exit), KHONG phai "
             "TRUOC nhu muc tieu 'early detection' cua du an - day la mot HAN CHE THUC CHAT can dieu tra "
             "them trong cac nghien cuu tiep theo (vd: xem lai nguong theta, hoac ban chat feature co "
             "the thien ve phat hien 'da xay ra' hon la 'dang xay ra').")
lines.append("")
lines.append("features_v2_N30.parquet va cac bang v3 (N=30) KHONG bi dong cham trong toan bo qua trinh nay.")

(OUT_REPORTS / "SUMMARY_final_heldout.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"Da luu {OUT_REPORTS / 'SUMMARY_final_heldout.txt'}")
