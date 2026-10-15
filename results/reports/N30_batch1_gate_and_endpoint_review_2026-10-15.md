# N30 Batch 1 — Ra soat cong provenance Uranium, dinh nghia endpoint, kiem tra bung no Inverse (2026-10-15)

## 1. Uranium Finance — cong provenance (3)

Trajectory 39 action: `Counter({'transfer': 32, 'swap': 5, 'merge': 2})`.

Action dau tien (index 0, block 12327461): `swap` tu seed
(`0xc614...06ec`) toi **`0x7a250d5630b4cf539739df2c5dacb4c659f2488d`
(Uniswap V2 Router — DA CO trong dex_allowlist)**. Day la **action sink da
xac minh THAT** — gate (3) **DAT** (co dong tien qua DEX da xac minh trong
allowlist).

**Ket luan: GIU LAI Uranium Finance voi `endpoint_confirmed=False`** (nhu
da dat) — KHONG loai, vi gate (3) thoa man qua DEX (Uniswap V2), du khong
tim thay mixer/bridge rieng trong cua so 72h.

## 2. Dinh nghia endpoint_confirmed — trich nguyen van + ap dung thong nhat

### Quy tac van ban (nguyen van, `metadata/annotation_guide.md` muc 3)

> "Theo `threat_model.md` mục 4: endpoint hợp lệ là **known mixer, public
> exit-service label, hoặc kết thúc trajectory được report xác nhận**.
> Không khẳng định cash-out chỉ vì địa chỉ 'giống' CEX."

**KHONG CO nguong gia tri/ty le % nao duoc neu trong van ban nay hay bat ky
noi nao khac trong code/tai lieu du an.** (`threat_model.md` goc khong con
ton tai trong repo hien tai — chi con ban paraphrase trong
annotation_guide.md nay). Quy tac la **DINH TINH THUAN TUY**: can MOT su
kien khop loai (mixer/bridge/exit-service da xac minh) xuat hien, bat ke
gia tri.

### Ty le gia tri endpoint / tong thiet hai bao cao — toan bo incident co endpoint_confirmed=True

| Incident | Endpoint xac nhan | Gia tri endpoint | Tong thiet hai bao cao | Ty le uoc tinh | Xac minh on-chain hay chi theo van ban bao cao? |
|---|---|---|---|---|---|
| feg_bridge_2024 | Tornado Cash (13/15 action) | Phan lon trajectory | khong ro so chinh xac | Cao (da so action) | **On-chain** |
| deltaprime_arbitrum_2024 | Across Protocol (bridge) | 2,967 WBTC | 2,96 WBTC (crypto.news) | **~100%** | **On-chain** |
| bsc_token_hub_2022 | BSC Token Hub (provenance, KHONG phai exit) | 2.000.000 BNB VAO seed | "2M BNB minted" (Halborn/Elliptic) | **~100%** (nhung day la PROVENANCE, khong phai EXIT) | **On-chain** |
| chibi_finance_2023 | Multichain+Stargate (bridge) | 556,4 ETH | ~556 ETH (CertiK) | **~100%** | **On-chain** |
| wooppv2_2024 | Stargate (bridge) | 200,117 ETH | ~2.000 ETH chuyen tiep theo PeckShield (evidence PHU, ngoai trajectory) | **~10% cua evidence phu, khong ro % cua TONG thiet hai goc** | **On-chain** (nhung CHI MOT PHAN nho cua dong tien) |
| utopiasphere_2024 | LI.FI (bridge) | 1.071,53 BNB | ~$521k (quy doi ~ gan khop) | **~100%** | **On-chain** |
| xkingdom_2024 | Tornado Cash (qua dia chi trung gian, NGOAI trajectory chinh) | 453 ETH | Khop "swapped back to ETH and deposited into Tornado Cash" (CertiK) | **~100% (cua rieng doan nay)** | **On-chain, NHUNG la "bang chung bo sung" ngoai trajectory chinh thuc** |
| wault_finance_2021 | Tornado Cash + bridge | — | "100 ETH funding, cross-chained" (SlowMist) | **Khong do duoc** | **CHI theo van ban bao cao — KHONG tu trace doc lap** (confidence ha xuong "medium" vi ly do nay) |
| paraluni_2022 | Tornado Cash (12 lan, 660 ETH theo bao cao) | — | "$1,7M" tong, swap trong trajectory (1187 BNB) la "MOT PHAN" | **Khong do duoc, PARTIAL (tu nhan trong notes)** | **CHI theo van ban bao cao cho phan mixer/bridge** |
| radiant_capital_arbitrum_2024 | LI.FI (56 bridge_deposit) | ~12.127,7 ETH | Khop "tuyet doi" (5 nguon) | **~100%** | **On-chain** |
| magic_abracadabra_arbitrum_2025 | Stargate (bridge) | 500 ETH (theo lo) | ~$3M tong | **~50-60%** uoc tinh (gia ETH luc do) | **On-chain** |
| new_free_dao_2022 | TornadoProxyLight (12/12 action) | Toan bo trajectory | "khop chinh xac bao cao" | **~100%** | **On-chain** |

**Ket luan quan trong**: trong 12 incident da co endpoint_confirmed=True o
v1.0, **it nhat 2 incident (wault_finance_2021, paraluni_2022) dua HOAN
TOAN hoac MOT PHAN vao VAN BAN BAO CAO, KHONG tu trace doc lap duoc tren-
chain** — va **it nhat 1 incident (wooppv2_2024) chi capture duoc 1 PHAN
NHO** cua tong dong tien thuc te (200/~2000+ ETH). Quy tac da duoc ap dung
**RAT LINH HOAT** tu truoc, khong co tien le nao doi hoi ty le % toi thieu.

### Ap dung cho ung vien moi

| Incident moi | Gia tri endpoint | Tong thiet hai bao cao | Ty le | Xac minh |
|---|---|---|---|---|
| dough_finance_2024 | 600 ETH (6x100 ETH Tornado Cash) | ~$1,87M (gia ETH thang 7/2024 ~$3.200 => ~1.87M) | **~100%** (khop mau "lo 100 ETH") | **On-chain, manh** |
| 0xinfini_2025 | 9,62 USDC (bridge LI.FI) | $49,5M | **~0,00002%** (dust) | **On-chain, nhung RAT NHO** |

**0xInfini co thoa quy tac khong?** Theo DUNG van ban quy tac (dinh tinh,
khong nguong %) VA theo CACH DA AP DUNG cho wooppv2_2024 (cung chi capture
1 PHAN NHO cua dong tien, van duoc tinh True) — **CO, thoa man** ve mat ky
thuat/tien le. Day la truong hop **"endpoint dust"** ro ret nhat tu truoc
den nay (ty le nho hon wooppv2 rat nhieu). **KHONG tu dong doi quy tac**
theo dung yeu cau — chi bao cao ro rang de nguoi dung quyet dinh co muon
dat 1 nguong moi (vd >=X% hoac >=X USD) ap dung DONG NHAT cho CA 15 incident
cu LAN moi hay khong (neu co, se la 1 thay doi quy tac MOI, can quyet dinh
rieng, se anh huong ca wooppv2_2024 dang co san).

## 3. Inverse Finance — kiem tra bung no (CHI BAO CAO, khong doi builder/khong loai)

- **Tong**: 11.592 action, 1.615 dia chi distinct da xu ly (processed).
- **Top 10 dia chi theo so lan xuat hien** (src hoac dst), tren tong 23.184
  luot nhac (moi action gop 2 luot: src+dst):

| Dia chi | So lan | % tong luot |
|---|---|---|
| 0x28c6c06298d514db089934071355e5743bf21d60 | 1.025 | 4,42% |
| 0x0000...0000 (null, mint/burn) | 903 | 3,89% |
| 0x1111111254fb6c44bac0bed2854e76f90643097d (1inch v4, DA allowlist) | 598 | 2,58% |
| 0xd54e4f8a55247487dd7c8c59f14ee5c0c2889477 | 567 | 2,45% |
| 0x6cc5f688a315f3dc28a7781717a9a798a59fda7b | 475 | 2,05% |
| 0xf16e9b0d03470827a95cdfd0cb8a8a3b46969b91 | 460 | 1,98% |
| 0x2faf487a4414fe77e2327f0bf4ae2a264a776ad2 | 435 | 1,88% |
| 0xdef171fe48cf0115b1d80b88dc8eab59176fee57 (Velora/ParaSwap, DA allowlist) | 430 | 1,85% |
| 0x220bda5c8994804ac96ebe4df184d25e5c2196d4 | 415 | 1,79% |
| 0xe93381fb4c4f14bda253907b18fad305d799241a | 399 | 1,72% |

**Top 10 CHI chiem 24,62% tong luot nhac — KHONG co 1 "hub" duy nhat chiem
uu the** (dia chi cao nhat chi 4,42%). Day la **bung no DIEN RONG qua
NHIEU dia chi** (he sinh thai Curve/SushiSwap/Aave/1inch/ParaSwap lien ket
cheo chat), **KHONG PHAI bung no qua 1 hub trung tam duy nhat**.

- **Do sau BFS**: gioi han boi `max_depth=6` (cau hinh, khong doi). Khong
  co co che hien co de trich xuat chinh xac do sau tung dia chi ma khong
  sua code (chi co the xac nhan: 1.615 dia chi duoc xu ly trong toi da 7
  vong lap — `max_iterations+1`), **khong du de ket luan "da cham tran
  max_depth hay hoi tu tu nhien truoc do"** — can instrument them neu muon
  biet chinh xac, **CHUA LAM** (ngoai pham vi "chi bao cao").

**Ket luan muc 3**: Inverse Finance bung no la THAT, dien rong (khong qua 1
hub), phan anh dac thu flash loan $27.000 WBTC cham vao nhieu pool
Curve/Aave/1inch khac nhau — **khong phai loi builder**, chi la ban chat
giao dich. Giu nguyen, khong sua, khong loai.
