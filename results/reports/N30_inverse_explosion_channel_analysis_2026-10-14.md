# N30 — Kenh bung no Inverse Finance + doi chieu N=15 (2026-10-14)

## 1. Top 15 contract KHONG thuoc allowlist ma Inverse mo rong qua nhieu nhat

| # | Dia chi | So dia chi MOI sinh ra | Nhan Etherscan | Vai tro |
|---|---|---|---|---|
| 1 | 0x0000...0000 | 180 | Null address | Burn/mint, khong phai contract that |
| 2 | 0x562680a4dc... | 148 | **Hotbit 9** | **CEX hot wallet** |
| 3 | 0xe93381fb4c... | 106 | **HTX 2** | **CEX hot wallet** (Huobi) |
| 4 | 0x65a8f07bd9... | 100 | Khong co nhan | Vi thuong, giu nhieu token |
| 5 | 0x40ec5b33f5... | 73 | **Polygon (Matic): ERC20 Bridge** | **Bridge da verify (chinh thuc)** |
| 6 | 0xbf5ae133b9... | 64 | Khong co nhan | Vi thuong (NFT/token) |
| 7 | 0x2faf487a44... | 58 | **FTX 1** | **CEX hot wallet** |
| 8 | 0xd54e4f8a55... | 53 | Khong co nhan ro rang | Vi da-chain hoat dong manh |
| 9 | 0x649765821d... | 44 | **Bancor: Master Vault V3** | **Vault DeFi da verify (chinh thuc)** |
| 10 | 0x88ad095186... | 31 | Khong co nhan | Vi thuong, giu nhieu token |
| 11-15 | (con lai) | 24-27 | Chua tra cuu chi tiet | — |

**Ket luan quan trong — premise khong hoan toan dung**: top 15 **KHONG PHAI
toan bo la DEX/aggregator router** nhu nghi van ban dau. Day la **HON HOP**:
- **2/15 la verified protocol/bridge THAT** (Polygon ERC20 Bridge, Bancor
  Master Vault V3) — ung vien hop le cho "allowlist completion" NEU ap
  dung dung nguyen tac provenance.
- **3/15 la CEX hot wallet** (Hotbit, HTX, FTX) — **KHONG NEN them vao
  allowlist** (day khong phai "sink" giao thuc, ma la vi tap trung giao
  dich cua san giao dich — hang trieu nguoi dung khong lien quan deu cham
  toi cac dia chi nay, allowlist chung se khong phan anh dung ban chat
  "endpoint" ma chi la "diem giao nhau ngau nhien trong do thi giao dich").
- **Con lai (khong nhan)**: vi thuong hoat dong manh, khong phai contract.

**Khuyen nghi (chi la khuyen nghi, chua thuc hien)**: KHONG nen allowlist
blanket ca 15 dia chi nay. Neu muon, CHI nen xem xet 2 dia chi verified
protocol that su (Polygon Bridge, Bancor Vault) theo dung nguyen tac
provenance cua v4 — NHUNG ca 2 deu la ha tang CUC KY pho bien (ai cung co
the bridge sang Polygon hoac dung Bancor), nen them vao CO THE lam
Inverse Finance BUNG NO THEM (giong co che da gay bung no truoc day voi
PancakeSwap Router/Tornado Cash truoc khi duoc allowlist dung cach - xem
`annotation_guide.md` muc "Mixer/DEX router = endpoint, KHONG phai hop de
tiep tuc trace"). **CHUA THUC HIEN buoc nay — cho quyet dinh nguoi dung**
truoc khi dong cham allowlist them.

## 2. Doi chieu N=15 (chi bao cao, KHONG doi gi)

| Incident | n_action | Top-1 KHONG-allowlist (% tong luot cham) | Top-10 KHONG-allowlist (% tong luot cham) |
|---|---|---|---|
| ronin_bridge_2022 | 1.625 | **Wintermute 1** (11,4%) | 52,3% |
| qbridge_qubit_2022 | 698 | 0x5afef856... (9,8%, chua tra cuu nhan) | 42,2% |
| paraluni_2022 | 511 | 0x61eb789d... (10,3%, chua tra cuu) | 47,1% |
| bsc_token_hub_2022 | 362 | seed chinh no (11,2%) | 43,5% |
| xkingdom_2024 | 73 | 0x82af4944... (Arbitrum: chua tra cuu, 37,0%) | 67,8% |
| wault_finance_2021 | 190 | 0xf2ce52e3... (chua tra cuu, 39,2%) | 78,9% |
| radiant_capital_arbitrum_2024 | 248 | **0x111111125421ca6dc452d289314280a0f8842a65 = "1inch: Aggregation Router V6" (XAC NHAN qua Etherscan) — DAY LA CONTRACT KHAC voi "1inch v4" da allowlist (0x1111111254fb6c44bac0bed2854e76f90643097d), KHONG PHAI loi case-sensitivity. CHUA co trong allowlist. 104/248 touch (21,0%)** | 85,5% |
| (cac incident con lai, <100 action) | — | Phan lon la chinh seed (do do dai qua nho de co "hub" that su) | — |

**Ket luan muc 2**: **CO, N=15 CUNG bi anh huong boi CUNG CO CHE** —
`ronin_bridge_2022` (incident LON NHAT trong N=15, 1.625 action) cham toi
**"Wintermute 1"** (market maker lon, cung loai thuc the voi Hotbit/HTX/FTX
cua Inverse — "hub" giao dich cao, khong phai dia chi dac thu cho incident).
Khac biet chinh la **QUY MO**: Ronin (1.625 action, top10 chiem 52,3%) nho
hon nhieu so voi Inverse (11.592 action, top10 CHI chiem 24,6% — phan tan
RONG HON, khong tap trung vao 1-2 hub nhu Ronin).

**Day la 1 PHAT HIEN DANG GHI VAO PHAN HAN CHE CUA BAI** (dung nhu nguoi
dung da du doan): co che "cham toi hub giao dich/market-maker lon gay phinh
trajectory" **da ton tai TU N=15**, khong phai dac thu rieng cua Inverse
Finance hay N30. KHONG can sua du lieu freeze — day la 1 gioi han CO HE
THONG cua phuong phap "bounded value-flow expansion forward-only" khi ap
dung cho cac vu co dong tien phuc tap/giao dich voi ha tang thanh khoan
lon, da duoc ghi nhan tu truoc (vd comment code ve PancakeSwap Router) va
nen duoc neu trong phan Limitations/Discussion cua paper/thesis.

### CANH BAO RIENG — phat hien ngoai y muon can quyet dinh ngay

Khac voi Wintermute (Ronin, khong phai contract giao thuc, khong nen
allowlist), **`1inch: Aggregation Router V6` o Radiant Capital LA 1 DEX
router THAT, DA VERIFY, dung chinh nguyen tac provenance da ap dung cho
KyberSwap/Universal Router**. Day la **incident THUOC N=15 da freeze** —
neu them contract nay vao allowlist va no lam thay doi trajectory cua
`radiant_capital_arbitrum_2024`, day se la **1 diem dung lon theo dung quy
tac v4** (Tang 1 — ranh gioi CUNG, pham vi 15+536). **CHUA them, CHUA kiem
tra** — bao cao rieng de nguoi dung quyet dinh TRUOC khi dong vao, vi day
la rui ro cham truc tiep vao du lieu N=15 da freeze (khac voi Polygon
Bridge/Bancor Vault chi lien quan Inverse Finance, 1 incident MOI).

## Buoc tiep theo (CHUA lam, cho quyet dinh)

- KHONG tu them Polygon Bridge/Bancor Vault vao allowlist (du ve nguyen tac
  co the hop le) - rui ro bung no them qua lon, can nguoi dung xac nhan.
- Mining batch 1 (Dough/Prisma/Inverse) van dang chay nen, se bao cao khi
  xong.
