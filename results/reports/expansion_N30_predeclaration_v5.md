# Khai bao truoc — Mo rong N=20 -> N=30 — PHIEN BAN 5 (2026-10-14)

## Changelog so voi v1-v4

- v1-v4: giu nguyen (hash xem cac file tuong ung).
- **v5 (file nay)**: cho phep 1 ngoai le DUY NHAT doi voi rang buoc "khong
  doi code": sua 1 bug crash THAT trong decoder (khong phai doi quy tac/
  tham so nghiep vu).

## Nguyen tac cho phep sua decoder (CO HIEU LUC TU FILE NAY)

**"Sửa lỗi crash trong decoder chỉ được phép khi KHÔNG đổi đầu ra của dữ
liệu đã xử lý VÀ áp dụng đồng nhất cho mọi incident."**

Ap dung cho: `src/normalize/decoder.py::decode_internal_tx_row` — bo qua
dong `txlistinternal` co `to==""` (contract-creation internal call, gay
crash `pydantic ValidationError` khi build `inverse_finance_2022_jun`) hoac
`from==""` (phong ngua, chua gap tren du lieu that). Logic MOI ap dung
**DONG NHAT cho MOI incident** (khong rieng Inverse Finance) — khong co
"if incident_id == X" dac biet nao trong code.

## Bang chung khong doi dau ra (da chay THAT, 2026-10-14)

| Pham vi | Ket qua SAU KHI sua |
|---|---|
| 15 incident v1.0 (dung config N20) | **15/15 khop CHINH XAC** so n_actions da biet |
| 536 hard-negative v1.0 | Build thanh cong toan bo 536/536, khong crash moi |
| 5 incident N20 (dung config N30) | **5/5 khop CHINH XAC** (Hedgey=755 nhu da bao cao, cac incident khac khong doi) |
| 125+46 hard-negative N20 | Build thanh cong toan bo 171/171, khong crash moi |
| 4 incident batch-1 da xu ly (Dough/0xInfini/Prisma/Uranium) | **4/4 khop CHINH XAC**, khong doi |
| `inverse_finance_2022_jun` | Tu CRASH -> chay duoc, n_actions=11.592, n_processed=1.615 dia chi, n_mixer_or_exit=14, n_bridge=51 |

**Quet toan bo cache hien co** (~4.000 file moi loai txlist/tokentx/
txlistinternal) xac nhan: CHI CO 2 dong `to==""` (value!=0, isError!=1)
trong TOAN BO du lieu da fetch, CA HAI deu thuoc cache cua
`inverse_finance_2022_jun` — day la **bang chung hinh thuc** rang fix nay
**TOAN HOC KHONG THE anh huong** bat ky incident nao khac (vi logic chi re
nhanh moi khi gap dieu kien nay, khong tim thay o noi khac). `from==""`:
0/~4.000 file — chua gap tren du lieu that, chi la phong ngua.

## Diff va hash

- Diff day du: `results/reports/decoder_internal_tx_fix_2026-10-14.diff`
  (46 dong them, 2 dong sua, 2 file: `decoder.py`, `incident_pipeline.py`).
- SHA-256 cua `src/normalize/decoder.py` SAU KHI sua:
  `3b746854b7863890c391c1af06600f2334cb8513d8140e3a23979e1a79255a6a`
  (se ghi vao manifest N30 cuoi cung).

## Thong ke dong bi bo qua (ghi theo yeu cau, per-incident)

| Incident | So dong bo qua | Tong gia tri ETH |
|---|---|---|
| inverse_finance_2022_jun | 2 | 3,196496 ETH |

(Tat ca incident khac: 0 dong bi bo qua.)

## Test moi

4 test them vao `tests/test_decoders.py`:
`test_decode_internal_tx_row_skips_contract_creation_empty_to`,
`test_decode_internal_tx_row_skips_empty_from_defensive`,
`test_decode_internal_tx_row_records_skip_stats_per_incident` — da PASS.

## Ra soat 2 decoder con lai (chi bao cao, KHONG sua — khong crash tren du lieu da cache)

- `decode_normal_tx_row` (txlist): quet ~3.952 file, **0 dong** co `to==""`
  voi `value!=0` — KHONG sua.
- `decode_tokentx_row` (tokentx): quet ~3.928 file, **0 dong** co `to==""`
  hoac `from==""` — KHONG sua.

## Buoc tiep theo

Tiep tuc Phase 2 theo thu tu da khai bao (mine negative cho 5 ung vien
batch 1), pytest toan bo, roi tiep tuc lo tiep theo.
