# Khai bao truoc — Mo rong N=20 -> N=30 — PHIEN BAN 3 (2026-10-14)

## Changelog so voi v1/v2

- **v1**: `results/reports/expansion_N30_predeclaration.md`
  (SHA-256: `3fdb2606f7eef4c0288e3b0a3e885d3a317383d55eb79db9342c476bc4b78794`).
  **GIU NGUYEN.**
- **v2**: `results/reports/expansion_N30_predeclaration_v2.md` — ghi SHA-256
  cua `dataset_expansion_N30_plan.md`
  (`9927d0468863d118377b73623d03d31ba2ed80ce3cedd6ffb023885bebfc3d08`).
  **GIU NGUYEN.**
- **v3 (file nay)**: **SAP LAI THU TU XEP HANG** cua 13 ung vien. **Ly do**:
  chua co du lieu thu thap that va chua co ket qua mo hinh nao (nen day
  KHONG phai "chon theo ket qua mo hinh") — thu tu o v1/v2 tu mau thuan voi
  chinh tieu chi do tin cay da neu trong bang (vd xep DeFi protocol ro rang
  (Uranium, Inverse, Lendhub) ngang hang voi CeFi custodial (Kronos,
  BitMart) chi vi "rui ro trung binh" ma khong tach nhom, va chua uu tien
  ro rang 3 ung vien DA qua kiem tra provenance/re-seed tu dot N20 (Dough,
  0xInfini, Prisma) len dau nhom cung muc rui ro).

## Quy tac sap xep MOI (ap dung 1 lan, CO DINH sau day)

(a) DeFi protocol/bridge TRUOC, CeFi custodial (Kronos, BitMart, Liquid) XEP
SAU CUNG.
(b) Trong moi nhom, rui ro TANG DAN (Thap -> Trung binh -> Cao).
(c) Cung muc rui ro: ung vien DA qua kiem tra provenance/re-seed o dot N20
(Dough Finance, 0xInfini, Prisma Finance) xep TRUOC.
(d) Con lai giu nguyen thu tu tuong doi cua v1/v2.

## Thu tu MOI (CO DINH tu luc nay — xem muc "Cam ket" cuoi file)

| # moi | Incident | victim_type | Rui ro | # cu (v1/v2) |
|---|---|---|---|---|
| 1 | Dough Finance | defi_protocol | Thap | 11 |
| 2 | 0xInfini | defi_protocol | Thap | 12 |
| 3 | Prisma Finance | defi_protocol | Thap | 13 |
| 4 | Uranium Finance | defi_protocol | Thap | 1 |
| 5 | Inverse Finance (16/06/2022) | defi_protocol | Thap | 2 |
| 6 | Lendhub | defi_protocol | Thap | 3 |
| 7 | THORChain (vu 2) | bridge | Trung binh | 4 |
| 8 | Popsicle Finance | defi_protocol | Trung binh | 5 |
| 9 | HECO Chain/HTX | bridge | Trung binh | 8 |
| 10 | EasyFi | defi_protocol | Cao | 9 |
| 11 | Kronos Research | cefi_custodial | Trung binh | 6 |
| 12 | BitMart | cefi_custodial | Trung binh | 7 |
| 13 | Liquid Exchange | cefi_custodial | Cao | 10 |

(Lendhub — da xac minh on-chain THAT: dia chi seed co hoat dong THAT tren
Ethereum mainnet dung tai block 16386495 CSV, bao gom giao dich toi contract
USDT (0xdac17f95...) — xac nhan chain=eth hop le, KHONG loai.)

## victim_type cho TOAN BO 20 incident HIEN CO (can cu bao cao goc, KHONG dua ket qua)

| incident_id | victim_type |
|---|---|
| ronin_bridge_2022 | bridge |
| qbridge_qubit_2022 | bridge |
| feg_bridge_2024 | bridge |
| deltaprime_arbitrum_2024 | defi_protocol |
| bsc_token_hub_2022 | bridge |
| chibi_finance_2023 | defi_protocol |
| wooppv2_2024 | defi_protocol |
| utopiasphere_2024 | defi_protocol |
| xkingdom_2024 | defi_protocol |
| wault_finance_2021 | defi_protocol |
| paraluni_2022 | defi_protocol |
| radiant_capital_arbitrum_2024 | defi_protocol |
| magic_abracadabra_arbitrum_2025 | defi_protocol |
| hackerdao_2022 | defi_protocol |
| new_free_dao_2022 | defi_protocol |
| zunami_protocol_2023 | defi_protocol |
| onyx_protocol_2023 | defi_protocol |
| beanstalk_farms_2022 | defi_protocol |
| hedgey_finance_2024 | defi_protocol |
| cork_protocol_2025 | defi_protocol |

**Nhan xet**: ca 20 incident hien co deu la `defi_protocol` hoac `bridge` —
KHONG co `cefi_custodial` nao trong N=20. Day la pham tru MOI chi xuat hien
vi 3 ung vien N30 (Kronos, BitMart, Liquid) la cac to chuc tap trung
(trading firm/exchange), khac ban chat voi toan bo dataset hien co.

**Khai bao truoc (trich dan tu bang phan tich D)**: phan tich CHINH gom
TOAN BO incident dat cong provenance (bat ke victim_type). **Sensitivity bo
sung moi**: loai toan bo `cefi_custodial` (neu co incident nao dat cong va
duoc dua vao N30), so sanh voi phan tich chinh — giong tinh than sensitivity
N=19 bo Cork da lam o dot truoc.

## chain_primary ghi truoc (CHOT truoc khi thu thap)

- **Uranium Finance**: `chain_primary = bsc` (vu hack chinh xay ra tren
  BSC — "Uranium Finance project on BSC" — se dung NodeReal/BscTrace).
- **EasyFi**: `chain_primary = eth` (nhanh Polygon KHONG duoc theo doi —
  gioi han ro rang, giong cach Hedgey chi lay phan ETH o dot N20).
- **Lendhub**: da xac minh on-chain, `chain_primary = eth` (xem muc tren).

## Quy tac dung GIU NGUYEN (khong doi)

Dich N=30, sang toi da 20 ung vien moi, N cuoi = 20 + so dat (khong ha
chuan), khong mo rong them sau dot nay.

## Cam ket

Thu tu 13 ung vien o tren **CO DINH ke tu file nay**. Chi hoan doi neu 1
ung vien KHONG qua cong provenance (ghi ro ly do gan voi incident_id, luu
vao bao cao freeze N30 cuoi cung).
