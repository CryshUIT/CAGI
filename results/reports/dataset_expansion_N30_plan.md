# Ke hoach mo rong N=20 -> N=30 — Giai doan 1 (kiem ke + de xuat, 2026-10-14)

**TRANG THAI: CHUA thu thap du lieu, CHUA doi registry/config/protocol_map
nao. Day la bao cao de nguoi dung duyet TRUOC khi vao Giai doan 2.**

Xem `results/reports/expansion_N30_predeclaration.md` (SHA-256:
`3fdb2606f7eef4c0288e3b0a3e885d3a317383d55eb79db9342c476bc4b78794`) cho cam
ket ve dich cuoi/quy tac dung da viet TRUOC khi lam bao cao nay.

## 1. Kiem ke kho ung vien con lai

`metadata/incident_candidates_amlguard.csv` co 75 dong trong 3 chain ho tro
(eth/bsc/arbitrum). Da dung/da loai/da sang loc o cac dot truoc: 36 dong (15
incident N20 hien co + cac ung vien da WebSearch truoc do: XPEXE Bridge,
Redruby DAO, Whale Loans, Novo Defi, LianGo, Loser Coin, Revisiting, Harvest
Finance, Orbit Chain, Cream Finance, Warp Finance, Seneca, DEGO/Cocos,
Fisher — tat ca da co ket luan ghi trong
`experiments/logs/excluded_candidates.md` hoac cac bao cao N20 truoc).

**Con lai 39 dong chua tung sang loc** (xem danh sach day du trong
`metadata/incident_candidates_amlguard.csv`, loc `Chain in [ETH,BSC,Arbitrum]`
va khong trung ten voi danh sach da dung).

**Du phong cu da xac minh (tu dot N20, CHUA dung)**: Dough Finance,
0xInfini, Prisma Finance — ca 3 da qua Buoc 1 provenance (dia chi khop CSV,
nguon doc lap nhat quan, xem
`results/reports/dataset_expansion_N20_plan.md` muc 9) nhung CHUA thu thap
du lieu that (chua qua Buoc 2-3 on-chain).

## 2. Sang loc so bo (WebSearch, chua thu thap du lieu that)

Da tra cuu 15 ung vien moi trong 39 dong con lai (uu tien nhung vu 2021+ co
kha nang la 1 seed/1 attacker ro rang, loai truoc cac vu truoc 2021 hoac
multi-victim-phishing khong khop cau truc du an).

### Ung vien DE XUAT, xep hang (dia chi khop CHINH XAC CSV, tru khi ghi chu)

| # | Ten | Chain | Seed address | Nguon | Bang chung bridge/DEX/mixer | Rui ro |
|---|---|---|---|---|---|---|
| 1 | **Uranium Finance** | bsc/eth | 0xc61429117038a1f13881dd7410b80771f28e06ec | Halborn + CertiK + PeckShield + US authorities (ke tan cong da bi buoc toi) | Tornado Cash (vi dang nghi hoat dong lai qua mixer) | Thap — ke tan cong DA BI DANH DANH TINH, bang chung mixer ro |
| 2 | **Inverse Finance (16/06/2022)** | eth | 0x7b792e49f640676b3706d666075e903b3a4deec6 | CertiK (2 incident analysis rieng, dung ban thang 6) | SushiSwap/Curve (DEX THAT) + Tornado Cash (vao+ra) | Thap — ca DEX va mixer deu xac nhan ro, dia chi khop CHINH XAC |
| 3 | **Lendhub** | eth | 0x9d0163e76bbcf776001e639d65f573949a53ab03 | Halborn + CertiK | Tornado Cash (nhan 100 ETH, gui 1100 ETH ra) | Thap — mixer ca 2 chieu xac nhan ro |
| 4 | **THORChain (16/07/2021, vu thu 2)** | eth | 0x3a196410a0f5facd08fd7880a4b8551cd085c031 | SlowMist + Halborn + TRM Labs + rekt.news | Chuoi dia chi trung gian da trace (SlowMist), chua xac nhan DEX/mixer cu the tu ket qua tim kiem | Trung binh — can dieu tra sau truoc khi crawl that |
| 5 | **Popsicle Finance** | eth | 0xf9e3d08196f76f5078882d98941b71c0884bea52 | Halborn + BlockSec + CoinDesk | Tornado Cash cap gas DAU VAO (xac nhan), buoc thoat CHUA ro tu ket qua tim kiem | Trung binh — can dieu tra sau |
| 6 | **Kronos Research** | eth | 0x2b0502fdab4e221dcd492c058255d2073d50a3ae | CertiK + SlowMist + Halborn | Tornado Cash (xac nhan "hacker shifts funds to Tornado Cash") | Trung binh — day la cong ty trading (API-key compromise), KHONG phai giao thuc DeFi thuan tuy, nhung van la 1 seed/1 attacker ro rang |
| 7 | **BitMart** | eth | 0x39fb0dcd13945b835d47410ae0de7181d3edf270 | MerkleScience + Tookey + CoinMarketCap | 1inch + PancakeSwap (DEX) + Tornado Cash (mixer) - CA HAI loai bang chung | Trung binh — day la san giao dich (exchange hot-wallet), khong phai DeFi protocol, nhung mau hinh on-chain (DEX+mixer) rat ro |
| 8 | **HECO Chain/HTX** | eth | 0xfc146d1caf6ba1d1ce6dcb5b35dcbf895f50b0c4 | Halborn + Hacken + CNBC | Compromise truc tiep bridge operator (tuong tu bsc_token_hub_2022 da co), $63M con nam o 1 dia chi khac | Trung binh — mau hinh tuong tu incident da co trong dataset (bridge key compromise), dong tien phuc tap (nhieu dia chi) |
| 9 | **EasyFi** | eth/polygon | 0x83a2eb63b6cc296529468afa85dbde4a469d8b37 | Halborn (top 10 DeFi hacks 2021) | KHONG tim thay bang chung buoc thoat (bridge/DEX/mixer) tu ket qua tim kiem — attacker "khong bi xac dinh danh tinh, quy khong thu hoi duoc" | Cao — thieu bang chung exit ro rang, can dieu tra sau truoc khi xep hang cao hon |
| 10 | **Liquid Exchange** | eth | 0x5578840aae68682a9779623fa9e8714802b59946 | MerkleScience + TRM Labs + Cointelegraph | Chuyen doi nhanh qua DEX (ERC20->ETH), mixer CHUA xac nhan tu ket qua tim kiem | Cao — day la san giao dich (khong phai DeFi), bang chung thoat chua day du |
| 11 | **Dough Finance** (du phong cu) | eth | 0x2913d90D94C9833B11a3E77F136da03075c04a0F | (da xac minh o dot N20) | Tornado Cash NGAY TRONG NGAY 1, theo lo 100 ETH | Thap — da xac minh ky, chi chua thu thap |
| 12 | **0xInfini** (du phong cu) | eth | 0x3ac96134Fb0e42a52D33045AeE50b89790f05Ed0 | (da xac minh o dot N20, re-seed check PASS) | Tornado Cash (gas dau vao) + DEX (USDC->DAI->ETH) | Thap — da xac minh ky |
| 13 | **Prisma Finance** (du phong cu) | eth | 0x7E39E3B3ff7ADef2613d5Cc49558EAB74B9a4202 | (da xac minh o dot N20, re-seed check PASS) | Tornado Cash NGAY TRONG NGAY | Thap — da xac minh ky |

### Loai so bo (khong dua vao danh sach, ghi ly do)

| Ten | Ly do loai |
|---|---|
| Vulcan Forged | Multi-victim (148 vi bi xam nhap private key qua Venly) — khong khop mau "1 seed = 1 ke tan cong" cua du an, giong Whale Loans/BadgerDAO da loai truoc |
| AscendEX | Exchange hot-wallet breach, DA HOAN TRA toan bo cho khach hang — tuong tu Euler/Polynetwork (da loai truoc vi "khong con exit that") |
| LCX | Exchange hot-wallet, 60% da bi dong bang/thu hoi trong 20 ngay — exit khong con ro rang |
| Cashio | Exploit GOC xay ra tren Solana (ngoai scope chain), phia ETH chi la diem den sau Wormhole — tuong tu cach Chibi Finance de ngo phan khac chain, nhung o day phan CHINH lai o ngoai scope |
| RiskOnBlast | Chain "Blast" (L2 rieng) — NGOAI PHAM VI KY THUAT (`configs/data.yaml::chains` chi co eth/bsc/arbitrum) |
| OKK DEX (OKX DEX) | Quy mo nho ($2,7M/$430k - so lieu khong nhat quan giua nguon), proxy-admin cu the cua 1 san giao dich, it dien hinh |
| Inverse Finance (02/04/2022) | **CANH BAO**: dia chi CSV (0x8B4C1083...) KHONG duoc xac nhan trong ket qua tim kiem (CertiK khong nhac den dia chi nay cu the) — co the CSV sai, loai cho den khi xac minh lai duoc qua nguon khac |
| THORChain (29/06/2021, vu thu 1) | Bang chung yeu hon 2 vu sau (chi neu dia chi dang muc, khong co nguon ro bang vu thu 2/3) |

## 3. Chi phi API va quota

Tat ca 13 ung vien de xuat **deu la chain ETH** (Uranium Finance tuy mang
ten BSC-related nhung Heist address/BlockNumber trong CSV o cot ETH — can
xac minh lai chain chinh xac o Buoc 1 that su khi thu thap). Tiep tuc dung
Etherscan V2 — KHONG dung NodeReal/BSC (tranh nut that quota da gap o lan
dau N=15). Chua kiem tra quota con lai that su (khong co endpoint truy van
truc tiep) — se test 1 call nho truoc moi lo nhu da lam o N20.

## 4. Du doan so incident dat chuan

Dua tren ty le dat cong provenance thuc te o dot N20 (5/5 trong 5 ung vien
hang dau duoc chon = 100%, nhung ca dot N20 ban dau da sang loc ky truoc khi
xep hang), uoc tinh THAN TRONG: trong 13 ung vien xep hang tren, 6 ung vien
"Rui ro thap" (Uranium, Inverse-June, Lendhub, Dough, 0xInfini, Prisma) RAT
CO KHA NANG dat cong (bang chung da ro tu WebSearch, giong hinh mau da
thanh cong o N20). 4 ung vien "Trung binh" (THORChain-2, Popsicle, Kronos,
BitMart, HECO Chain — thuc ra la 5) can dieu tra sau o Buoc 1 that su truoc
khi chac chan. 2 ung vien "Cao" (EasyFi, Liquid Exchange) nhieu kha nang
KHONG dat (thieu bang chung exit).

**Uoc tinh: ~8-11/13 co the dat cong provenance**, tuc **N cuoi du kien
khoang 28-31** — **CO THE DU de dat N=30**, nhung **KHONG CHAC CHAN 100%**
(dung theo quy tac Buoc 0: neu <10/20 ung vien MOI dat, dung o N=20+so dat,
khong ha chuan). Kho hien tai (39 ung vien chua sang loc + 3 du phong) CO
VE DU, nhung Giai doan 2 se xac nhan chinh xac qua kiem tra on-chain THAT.

## 5. De xuat thu tu xu ly (Giai doan 2, lam theo lo 5)

**Lo 1**: Uranium Finance, Inverse Finance (16/06/2022), Lendhub, Dough
Finance, 0xInfini (5 ung vien "rui ro thap" dau tien theo thu tu).

**Lo 2** (de cham N=30 hoac gan N=30): Prisma Finance, THORChain-2, Popsicle
Finance, Kronos Research, BitMart.

**Du phong tiep theo neu lo 1-2 co ung vien khong dat**: HECO Chain/HTX,
roi den EasyFi/Liquid Exchange (chi dung neu that su can, da ghi ro rui ro
cao hon).

## Buoc tiep theo

**DUNG tai day, cho nguoi dung duyet danh sach xep hang va thu tu lo truoc
khi vao Giai doan 2** (thu thap du lieu that, qua cong provenance tung ung
vien mot theo dung ky luat da ap dung o dot N20).
