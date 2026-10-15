# Checkpoint C'' — dong bo cac vong mine he thong + chot chan cau hinh (2026-10-14)

**KET LUAN: tat ca dieu kien chay D deu THOA. Da chay Checkpoint D (xem
`results/reports/checkpointD_N20_results_2026-10-14.md`).**

## 1. Cac vong mine cua v1.0 — phan loai HE THONG vs AD HOC

| Vong | Tieu chi/tham so | He thong hay ad hoc? | Pham vi ap dung thuc te (15 incident cu) |
|---|---|---|---|
| **"Chinh" (mac dinh)** | `target_count=25`, `max_candidates_checked=150`, qua `mine_hard_negatives_for_incident` | **HE THONG** — 1 vong duy nhat ap dung cho MOI incident khi moi them vao (comment code: "khop quy uoc target_per_incident da dung cho 11 incident cu, vong mine dau tien") | Ca 15/15 (con so cuoi dao dong 22-70 do cong don them cac vong re-mine ben duoi cho 5 incident dau) |
| **"v2_complexity"** | `target_count=10`, tieu chi do phuc tap `compute_min_candidate_events` (log-scale theo do dai positive), qua `scripts/mine_hard_negatives_v2_complexity.py` | **HE THONG VE THIET KE** (vong lap qua TAT CA incident `eval_tier=primary,label=1` TAI THOI DIEM chay script, khong cherry-pick) — **NHUNG PHU SONG KHONG DAY DU** vi 4 incident (radiant_capital, magic_abracadabra, hackerdao, new_free_dao) duoc them vao registry SAU KHI script nay da chay (Tuan 5 dot 2, truoc 2026-08-27) nen CHUA TUNG duoc ap dung | 11/15 (radiant/magic/hackerdao/new_free_dao **CHUA CO** vong nay — day la 1 khoang trong CO SAN trong chinh v1.0, khong phai dac thu cua N20) |
| **Control thu cong** | Tim 1 giao dich benign THAT khop cau truc (tay, dua tren bao cao cong khai + doi chieu on-chain), KHONG qua `mine_hard_negatives_for_incident` | **THUAN TUY AD HOC/THU CONG** — khong co code/tham so co dinh nao, moi lan la 1 qua trinh nghien cuu rieng | **CHI 5/15** (ronin, qbridge, feg, deltaprime, bsc_token_hub — 5 incident DAU TIEN cua du an). 10 incident sau (chibi tro di) KHONG co control rieng. **Tong 5, KHONG phai moi incident 1 cai.** |
| **Re-mine bo sung (bug-fix driven)** | Vd `run_hard_negative_remine_all_after_bug34_fix.py` (toan bo 5 incident dau, do bug anh huong MOI chain), `run_hard_negative_remine_bsc_after_merge_fix.py` (chi 2 incident BSC, bug dac thu BSC) | **AD HOC, gan voi 1 bug cu the tai 1 thoi diem cu the** — KHONG phai quy trinh chung mo ta trong paper, chi la lich su debug | Chi anh huong 5 incident dau (giai thich tai sao con so cuoi cua ho cao hon han 25: 69,35,31,70,69) |

**Ket luan muc 1**: CHI co **"vong chinh" (25) VA "v2_complexity" (10)** la cac vong **CO HE THONG** (co code + tham so co dinh, y dinh ap dung chung) — day la 2 vong CAN dong bo cho 5 incident N20 theo dung yeu cau. "Control thu cong" va "re-mine bug-fix" la AD HOC, **KHONG duoc nhan ban** (dung theo yeu cau).

## 2. Dong bo cho 5 incident moi — da thuc hien

- **Vong "chinh" (25)**: DA LAM tu Checkpoint B (125 dong, 25/incident, 5/5 sach).
- **Vong "v2_complexity" (10)**: **MOI thuc hien o Checkpoint C''**, dung CHINH code
  (`mine_hard_negatives_for_incident`, `compute_min_candidate_events`) va tham so
  (`target_count=10, max_candidates_checked=150`) nhu ban goc. Ket qua:

| Incident | positive_len | min_candidate_events | checked | accepted | Ghi chu |
|---|---|---|---|---|---|
| zunami_protocol_2023 | 31 | 2 | 109 | **10/10** | Du target |
| onyx_protocol_2023 | 16 | 2 | 73 | **10/10** | Du target |
| beanstalk_farms_2022 | 440→443* | 7 | 80 | **10/10** | Du target |
| hedgey_finance_2024 | 661→662* | 9 | 150 | **6/10** | Cham `max_candidates_checked=150` TRUOC khi du target — **KHONG phai truncation/quota**, la NANG SUAT TU NHIEN (giong 1 so incident cu cung khong luon dat du 25, vd gia tri thap nhat la 22) |
| cork_protocol_2025 | 1 | 1 | 100 | **10/10** | Du target |

**0/5 bi truncated** (khong co loi `max_windows=200` nao). Tong **46 dong moi**
(`metadata/hard_negative_registry_v2_complexity_N20.csv`), gop voi 110 dong cu
thanh `hard_negative_registry_v2_complexity_N20_combined.csv` (156 dong).

*Xem muc "Phat hien phu" ben duoi ve ly do positive_len doi (440->443, 661->662).

### Ngan sach quota (uoc tinh truoc khi chay)

Dung LAI chinh xac 5 contract da dung o Checkpoint B (Tornado Cash Router x2,
Uniswap V2 Router, Universal Router x2) — da xac nhan AN TOAN xa cap (toi da
~17% cap 200-window) trong dry-run truoc do. `target_count=10` (nho hon 25)
nen rui ro quota THAP HON lan truoc — khong can lay mau lai.

## 3. Config o buoc mine Checkpoint B

**Da xac nhan**: ham `_passes_structural_filter`/`fetch_contract_counterparties`/
`mine_hard_negatives_for_incident` **KHONG NHAN THAM SO `config`/allowlist O
DAU CA** — chi dung `protocol_map.yaml` (bridge_index/mixer_index, KHONG dung
`dex_allowlist`). Universal Router la 1 DEX (khong phai bridge/mixer), nen
section "dexes" cua `protocol_map.yaml` (dau goc hay N20) **khong anh huong
gi den buoc CHON negative** (chi anh huong buoc XAY DUNG trajectory sau do,
da sua o Checkpoint C'). **Ket luan: tap 125 negative cua Checkpoint B KHONG
BI ANH HUONG boi loi cau hinh** — khong can chay lai, khong thay doi.

## 4. Chot chan cau hinh (them vao code)

Da them ham `verify_config_guard()` trong `scripts/build_features_v2_N20.py`,
goi o dau `main()`:
- `assert` duong dan config dung bang `CONFIG_N20_PATH` (`configs/data_N20.yaml`).
- `assert` allowlist chua CA 2 dia chi Universal Router bat buoc.
- Neu vi pham: **raise AssertionError ngay, dung chay tiep** (khong im lang
  dung config sai).
- SHA-256 cua chinh file config duoc ghi vao `configs/features_v2_computed_N20.json`
  (field `config_sha256`, `config_path_used`, `config_allowlist_verified_contains`).

**Test moi**: `tests/test_n20_build_config_guard.py` (4 test): xac nhan file
config ton tai + chua 2 dia chi bat buoc; xac nhan chot chan RAISE khi duong
dan sai; xac nhan chot chan RAISE khi allowlist bi lam mat Universal Router
(mo phong qua `monkeypatch`).

### Phat hien phu (regression tu-phat-hien qua chinh pytest)

Khi moi viet test tren, **IMPORT `scripts.build_features_v2_N20`** (de lay
`CONFIG_N20_PATH`/`verify_config_guard`) da VO TINH kich hoat cac dong
monkeypatch `dataset_builder.REGISTRY_PATH = ...` (luc do con dat o MUC
MODULE, chay ngay khi import) — lam **2 test cua
`tests/test_n20_reproduces_v1.py` FAIL** (test "default path" khong con dung
default vi bi 1 file test KHAC import va mutate global state truoc do trong
CUNG session pytest). Phat hien qua CHINH `pytest tests/ -v` (dung theo quy
tac bat buoc "sua code xong phai chay pytest"). **Da sua**: chuyen toan bo
monkeypatch vao trong ham `main()` (khong con chay khi import module) — chay
lai `pytest tests/`: **211/211 PASS**.

## 5. Cork — so prefix row

Trajectory 1-action cua Cork sinh ra **4 prefix row** (`ratio_25`, `ratio_50`,
`ratio_75`, `ratio_100` — TAT CA deu co `prefix_len=1, trajectory_len=1`,
trung nhau vi toan bo trajectory chi co 1 action duy nhat). **CA 4 deu
label=1** (positive). KHONG sinh duoc bucket `k_2/k_3/k_5/k_7` (yeu cau >=2
action). **Quyet dinh CHOT giu nguyen**: Cork van nam trong phan tich
CHINH (da qua cong provenance), sensitivity N=19 bo Cork lam doi chieu.

## 6. Dong bang lai (SHA-256 manifest cap nhat)

Tep: `results/reports/freeze_N20_manifest_2026-10-14.json` (da ghi de, bao
gom CA file moi: `hard_negative_registry_v2_complexity_N20.csv`,
`hard_negative_registry_v2_complexity_N20_combined.csv`,
`tests/test_n20_build_config_guard.py`, va `scripts/build_features_v2_N20.py`
voi hash MOI sau khi sua regression muc 4).

`analysis_plan_N20.md` **KHONG bi sua ngam** — ban v1 giu nguyen, tao
`analysis_plan_N20_v2.md` voi changelog rieng (xem file do).

### Endpoint-confirmed vs so incident danh gia duoc lead time (2 dinh nghia khac nhau)

| Dinh nghia | So luong | Giai thich |
|---|---|---|
| **`endpoint_confirmed=True`** (co trong registry) | **15/20** | Co nguon cong khai xac nhan DOC LAP loai endpoint (bridge/mixer/lending) — CHUA chac trajectory da xay dung THAT SU chua terminal action tuong ung |
| **`endpoint_confirmed=True` VA co terminal action THAT trong trajectory da build** (dieu kien CAN, kiem tra duoc KHONG CAN chay model) | **13/20** | 10/15 cu (feg, deltaprime, bsc_token_hub, chibi, wooppv2, utopiasphere, xkingdom, radiant, magic, new_free_dao) + 3/5 moi (Zunami, Onyx, Beanstalk) — wault_finance_2021 va paraluni_2022 (cu) CO co nhung KHONG tim thay terminal action that su trong trajectory da decode |
| **So incident THAT SU co lead_time tinh duoc (dieu kien DU, phu thuoc model)** | **9/15 (cu, theo `lead_time_full15_2026-09-22.csv` da co)** + **CHUA BIET cho 5 incident moi** | Doi hoi model thuc su bat duoc alert TRUOC/SAU endpoint — CHI biet duoc SAU khi chay Checkpoint D (vd `wooppv2_2024` du dat dieu kien can nhung roi vao "never_alerted") |

Doi chieu: 13/20 (dieu kien can) khop CHINH XAC voi tinh toan doc lap tu
`action_count_bridge_deposit/mixer_or_exit/lending_*` tren `features_v2_N20.parquet`.

## Phat hien phu quan trong — tai sao Beanstalk/Hedgey doi n_actions (440->443, 661->662)

Khi chay lai feature build SAU buoc mine v2_complexity (muc 2), 2 incident
**POSITIVE** nay tang them vai action (440->443, 661->662) **DU KHONG CO GI
THAY DOI VE BAN THAN TRAJECTORY CUA CHUNG** — da dieu tra va xac nhan day la
HANH VI THAT (khong phai non-determinism ngau nhien, da kiem tra lai 2 LAN,
cho ra CUNG 1 ket qua on dinh) gay ra boi CACH CACHE DUOC CHIA SE: buoc mine
v2_complexity goi `fetch_contract_counterparties` (do_collect=True) cho
CHINH dia chi contract (Uniswap V2 Router cho Beanstalk, Universal Router
cho Hedgey) MA positive trajectory cua chinh incident do CUNG cham toi trong
qua trinh mo rong frontier (frontier reach toi 11/102 dia chi tuong ung) —
2 lan goi nay CUNG SCOPE boi `(chain, address, incident_id)`, nen lan fetch
SAU (cua mining, voi cua so ±7 ngay RONG HON cua so 72h cua trajectory) DA
GHI DE cache CU boi du lieu MOI/DAY DU HON cho chinh dia chi do, lam loi ra
vai giao dich THAT (tren-chain, khong fabricated) ma truoc do CHUA tung
duoc nhin thay. Day la 1 **tinh chat co that cua he thong cache chia se
theo (dia chi, incident_id)**, khong phai loi/fabrication — can luu y cho
tuong lai (vd neu muon dam bao positive trajectory "dong bang" tuyet doi,
nen build CHUNG mot lan sau khi TAT CA cac vong mine da hoan tat, dung
truoc khi dang lai).

## Xac nhan dieu kien chay D

- [x] Muc 2 (v2_complexity cho 5 incident moi): hoan tat, 0/5 truncated.
- [x] Muc 3 (tap negative chinh 125 dong): KHONG doi (xac nhan bang phan
  tich code, khong can chay lai).
- [x] `pytest tests/`: **211/211 PASS** (sau khi sua regression tu-phat-hien).
- [x] Test tai tao (`test_n20_reproduces_v1.py`): **3/3 PASS**.

**→ Tat ca dieu kien THOA. Tien hanh Checkpoint D theo
`results/reports/analysis_plan_N20_v2.md`.**
