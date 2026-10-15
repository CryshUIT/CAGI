# Khai bao truoc — Mo rong N=20 -> N=30 — PHIEN BAN 6 (2026-10-14)

## Changelog so voi v1-v5

v1-v5: giu nguyen (hash xem cac file tuong ung). **v6 (file nay)**: chot
giao thuc RQ2 cho Checkpoint D (chua chay), va xuat bang endpoint day du.

## Giao thuc RQ2 (CHOT, chua chay - chi khai bao truoc)

- **Phan tich CHINH**: tren MOI incident co `endpoint_confirmed=True` theo
  DUNG quy tac v1.0 da trich dan (xem
  `N30_uranium_endpoint_inverse_checks_2026-10-14.md` muc 2) — khong phan
  biet mixer/bridge/report-only, dung dong nhat cho ca incident cu va moi.
- **Sensitivity**: CHI tren incident co endpoint LA MIXER (loai bridge va
  report-only) — so sanh ket qua 2 tap de xem ket luan co nhay cam voi loai
  endpoint khong.
- KHONG doi cach tinh lead-time/false-alert-rate nao khac.

## Bang day du: moi incident co endpoint, loai endpoint, ty le gia tri

| Incident | endpoint_confirmed | Loai endpoint | Gia tri tren-chain | Bao cao cong khai | Ty le | Do tin cay |
|---|---|---|---|---|---|---|
| feg_bridge_2024 | True | mixer (Tornado Cash) | 162 ETH | Chua xac dinh tong thiet hai USD rieng | Chua tinh | Trung binh |
| deltaprime_arbitrum_2024 | True | bridge (Across) | 2.967 WBTC | "2.96 WBTC bridged" | ~100% | Cao |
| bsc_token_hub_2022 | True | lending (Venus, khac loai mixer/bridge) | 900.000,1 BNB | "900.000 BNB deposited" | ~100% | Cao |
| chibi_finance_2023 | True | bridge (Stargate+Multichain) | 556,42 ETH | "556 ETH total removed" | ~100% | Cao |
| wooppv2_2024 | True | bridge (Stargate) | 200,12 ETH | 1 phan cua tong thiet hai lon hon | Khong ap dung truc tiep | Thap (bang chung cuc bo) |
| utopiasphere_2024 | True | bridge (LI.FI) | 1.071,5 BNB (+USDC/USDT) | "~1071.53 BNB" | ~100% (phan BNB) | Cao |
| xkingdom_2024 | True | bridge (Stargate) | 106,25 ETH | "100.008 ETH" | ~106% | Cao |
| wault_finance_2021 | True | **report-only** (KHONG co action on-chain) | — | SlowMist xac nhan qua van ban | N/A | Theo bao cao, khong doi chieu on-chain duoc |
| paraluni_2022 | True | **report-only** (KHONG co action on-chain) | — | CertiK/SlowMist xac nhan qua van ban | N/A | Theo bao cao, khong doi chieu on-chain duoc |
| radiant_capital_arbitrum_2024 | True | bridge (LI.FI, nhung 12,29 ETH chi la phi gas) | 12,29 ETH (**KHONG DANG TIN CAY - nghi la phi, khong phai tai san chinh**) | "~11.977-12.127,7 ETH" | **KHONG TINH DUOC (sai loai tai san)** | **Khong dang tin cay** |
| magic_abracadabra_arbitrum_2025 | True | bridge (Stargate, nhung 0,31 ETH chi la phi LayerZero) | 0,31 ETH + 55 ZRO (**KHONG DANG TIN CAY**) | "lo 500 ETH" | **KHONG TINH DUOC (sai loai tai san)** | **Khong dang tin cay** |
| new_free_dao_2022 | True | mixer (TornadoProxyLight) | 930 BNB | "11.544" (don vi khong ro) | Khong quy doi duoc | Thap |
| hackerdao_2022 | **False** | mixer (Tornado, chi 0,4 BNB) | 0,4 BNB | Tong ~200 BNB | ~0,2% ("dust", DA CO SAN trong v1.0) | Thap (va DA la False) |
| **Dough Finance (moi)** | True | mixer (Tornado Cash) | 600 ETH (6x100) | "lo 100 ETH" | **~100%** | Cao |
| **Prisma Finance (moi)** | True | mixer (Tornado Cash) | 3.240 ETH | "3257 ETH (~$11,1M)" | **~99,5%** | Cao |
| **Inverse Finance (moi)** | True | mixer (Tornado Cash) | 1.000,0 ETH | "sent 1.000 ETH" | **100%** | Cao |
| **0xInfini (moi)** | True | bridge (LI.FI) | 15.062 USDC | Tong thiet hai ~$49,5 TRIEU | **~0,03%** | **VUNG XAM — thap hon ca hackerdao (0,2%), nhung CO bang chung bridge THAT (khac hackerdao khong xac nhan dia chi tren-chain). KHONG DOI CO, chi ghi chu.** |
| Uranium Finance (moi) | False | khong co mixer/bridge, CO DEX (Uniswap V2) | — (xem muc rieng Uranium) | — | — | Dat gate qua DEX, khong phai mixer/bridge |

**Ghi chu 0xInfini (theo yeu cau, KHONG doi co)**: ty le 0,03% la THAP NHAT
trong toan bo bang (kem ca hackerdao da duoc chap nhan la False o muc ty le
cao hon). Day la **vung xam ro rang** — giu nguyen `endpoint_confirmed=True`
VI co bang chung bridge THAT toi dia chi da verify (LI.FI Diamond), khac voi
hackerdao (khong xac nhan duoc dia chi tren-chain cu the cho rieng mixer
event). Neu nguoi dung muon ap dung tieu chi nghiem ngat hon (vd ty le toi
thieu), day la quyet dinh CUA NGUOI DUNG, khong phai quy tac da co san.

## Buoc tiep theo

Cho phan hoi nguoi dung ve: (1) co dong allowlist them Polygon Bridge/
Bancor Vault (chi anh huong Inverse, incident moi) hay khong; (2) co dong
allowlist them 1inch V6 (anh huong `radiant_capital_arbitrum_2024`, **incident
N=15 DA FREEZE** - rui ro cao hon nhieu, can quyet dinh rieng) hay khong;
(3) xac nhan cach xu ly vung xam 0xInfini. Mining batch 1 (Dough/Prisma/
Inverse) van dang chay nen cho den khi hoan tat.
