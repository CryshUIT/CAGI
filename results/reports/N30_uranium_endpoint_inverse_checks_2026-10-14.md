# N30 — Uranium gate, dinh nghia endpoint, Inverse explosion (2026-10-14)

## 1. Uranium Finance — cong provenance (3)

Trajectory 39 action: `{'transfer': 32, 'swap': 5, 'merge': 2}`.

**CO action sink toi DEX da xac minh**: hanh dong DAU TIEN (block 12327461)
la `swap` tu seed truc tiep toi `0x7a250d5630b4cf539739df2c5dacb4c659f2488d`
(**Uniswap V2 Router, DA CO trong dex_allowlist**). 4 swap con lai di toi
dia chi CHUA verify (BASK/YAXIS/LUSD3CRV-f/ust3CRV pools, khong trong
allowlist).

**Ket luan**: DAT cong provenance (3) qua 1 DEX action da xac minh. **GIU
LAI Uranium Finance voi `endpoint_confirmed=False`** (dung nhu da sua) —
KHONG loai, vi co it nhat 1 sink hop le.

## 2. Dinh nghia endpoint_confirmed — trich nguyen van + ap dung dong nhat

**Nguon**: `metadata/annotation_guide.md` muc 3, trich dan `threat_model.md`
muc 4 (file nay hien KHONG con ton tai rieng trong repo, chi con duoc trich
lai trong annotation_guide.md):

> "endpoint hợp lệ là **known mixer, public exit-service label, hoặc kết
> thúc trajectory được report xác nhận**. Không khẳng định cash-out chỉ vì
> địa chỉ 'giống' CEX."

**KHONG CO nguong gia tri hay yeu cau doi chieu chinh xac so tien voi bao
cao** trong dinh nghia nay.

**Bang chung precedent CO SAN trong v1.0** (khong phai do toi dat ra):
`wault_finance_2021` va `paraluni_2022` **DA duoc dat `endpoint_confirmed=
True` TU TRUOC MA KHONG CO BAT KY action mixer/bridge/lending nao trong
trajectory da build** (xac nhan lai: ca 2 incident nay `grep` ra "KHONG co
endpoint action nao trong trajectory" o buoc kiem tra nay) — ly do da ghi
ro trong `notes`: gioi han kien truc decoder voi AnySwap burn-to-bridge doi
dau (external call value=0 khong duoc decode). Day la **endpoint_confirmed
=True dua HOAN TOAN tren xac nhan tu bao cao cong khai**, khong doi hoi
bang chung on-chain trung khop.

### Bang ty le gia tri endpoint vs bao cao cong khai (16 incident co endpoint action tren-chain)

| Incident | Endpoint tren-chain (token, so luong THAT) | So sanh voi bao cao | Ty le |
|---|---|---|---|
| feg_bridge_2024 | 162 ETH (Tornado Cash) | Chua xac dinh chinh xac tong thiet hai USD cong khai cho rieng FEG SmartBridge o buoc nay | Chua tinh |
| deltaprime_arbitrum_2024 | 2,967 WBTC (Across bridge) | Bao cao: "2.96 WBTC bridged to Ethereum" | **~100%** (khop dung bao cao, day la CHINH luong duoc bao cao, khong phai tong thiet hai rieng) |
| chibi_finance_2023 | 556,42 ETH (Stargate+Multichain) | CertiK: "556 ETH total removed" | **~100%** |
| wooppv2_2024 | 200,12 ETH (Stargate) | 1 phan cua tong thiet hai lon hon (nhieu token khac), day la LUONG BRIDGE cu the duoc bao cao | Khong ap dung truc tiep (bang chung cuc bo) |
| utopiasphere_2024 | 1.071,5 BNB + 232 USDC + 3.098 USDT (LI.FI) | CertiK: "~1071.53 BNB" bridge | **~100%** cho phan BNB |
| xkingdom_2024 | 106,25 ETH (Stargate) | Bao cao: "100.008 ETH" | **~106%** (gan dung, chenh do gom them cac hop sau) |
| radiant_capital_arbitrum_2024 | 12,29 ETH (LI.FI) | Bao cao: "~11.977-12.127,7 ETH" | **CANH BAO: ~0,1%** — day CHI LA PHI GAS native ETH kem theo moi lan goi LI.FI, **KHONG PHAI** tai san chinh duoc bridge (tai san chinh la ERC20, khong duoc gom vao query nay) — **KHONG the dung ty le nay de danh gia**, can phan biet "phi giao dich" voi "tai san bridge" |
| magic_abracadabra_arbitrum_2025 | 0,31 ETH + 55 ZRO (LayerZero) | Bao cao: "bridge qua Stargate theo lo 500 ETH" | **CANH BAO: <0,1%** — tuong tu Radiant, day co the la phi LayerZero, KHONG phai tai san chinh |
| new_free_dao_2022 | 930 BNB (TornadoProxyLight) | Bao cao: "11,544" (don vi khong ro, co the la USD) | Khong quy doi duoc chinh xac |
| hackerdao_2022 | 0,4 BNB (Tornado, theo bao cao CertiK) | Tong thiet hai ~200 BNB | **~0,2% — DA LA CASE "DUST" CO SAN TRONG v1.0**, van dat `endpoint_confirmed=False` (khong phai True) |
| **0xInfini (MOI)** | **15.062 USDC (LI.FI Diamond)** | **Tong thiet hai bao cao ~$49,5 TRIEU** | **~0,03%** |
| Dough Finance (MOI) | 600 ETH (Tornado Cash, 6x100 ETH) | Bao cao: "laundered in batches of 100 ETH" | **~100%** (khop dung mo ta "theo lo 100 ETH") |
| Prisma Finance (MOI) | 3.240 ETH (Tornado Cash) | Bao cao: "3257 ETH (~$11,1M)" | **~99,5%** |
| Inverse Finance (MOI) | 1.000,0 ETH (Tornado Cash, xac nhan truoc) | Bao cao: "sent 1,000 ETH to Tornado Cash" | **100% (khop tuyet doi)** |
| ronin_bridge_2022, qbridge_qubit_2022, bsc_token_hub_2022(mixer rieng), wault_finance_2021, paraluni_2022 | Khong co mixer/bridge action (bsc_token_hub co lending 900.000 BNB -> Venus, khac loai) | — | Khong co ty le (khong tim thay endpoint action) |

**Ket luan quan trong**: v1.0 **KHONG co nguong gia tri toi thieu**, va **DA
CO san 1 ca dust-scale** (hackerdao_2022, ~0,2%) **nhung van dat
endpoint_confirmed=False** (khong phai True) cho ca do — nghia la trong
thuc te, du "khong co nguong chinh thuc", CACH AP DUNG THUC TE da ngam
nghieng ve `False` cho cac truong hop ty le cuc nho/khong chac chan, con
`True` duoc danh cho cac truong hop **ty le cao (~100%, khop gan dung voi
con so bao cao)** HOAC **duoc report xac nhan ro rang** (du khong khop
on-chain, nhu wault/paraluni). **0xInfini (~0,03%) nam Ở GIUA 2 nhom nay**
— thap hon ca hackerdao (~0,2%) — **toi GIU endpoint_confirmed=True cho
0xInfini vi CO bang chung bridge THAT (LI.FI Diamond, dia chi da verify,
khac hackerdao chi dua vao bao cao khong xac nhan tren-chain cho dung dia
chi do)**, nhung ghi ro day la quyet dinh CO THE CAN XEM LAI boi nguoi dung
— **KHONG tu y doi quy tac/dinh nghia**, chi bao cao trung thuc su mau
thuan nay de nguoi dung quyet dinh.

## 3. Inverse Finance — kiem tra bung no

- Phan bo theo dia chi (top 10/1.615 dia chi, theo so luot xuat hien
  src+dst trong 11.592 action, tong 23.184 luot cham): **dia chi cao nhat
  chi chiem 4,42%**, **top 10 CONG LAI chi chiem 24,62%** tong luot cham.
  **KHONG CO 1 hub duy nhat chiem uu the** — phan bo tuong doi DEU, khong
  tap trung.
- Phan bo theo do sau BFS (tu seed, max_depth=6 + 1 vong xac nhan):

  | Do sau | So dia chi moi |
  |---|---|
  | 0 (seed) | 1 |
  | 1 | 4 |
  | 2 | 12 |
  | 3 | 17 |
  | 4 | **197** |
  | 5 | **540** |
  | 6 | **851** |
  | 7 | 427 |

**Ket luan**: day la **BUNG NO DANG MU HANH THEO CAP SO NHAN tu do sau 4**
(khong phai qua 1 hub don le) — mau hinh dien hinh khi trajectory cham toi
ha tang DeFi dung chung rat nhieu nguoi dung (SushiSwap/Curve/1inch/
ParaSwap — thay trong top 10 co `0x1111112...` 1inch v4 va `0xdef171fe...`
ParaSwap/Velora, ca hai DA CO trong dex_allowlist nhung builder van tiep
tuc mo rong QUA cac dia chi KHAC cham toi chung o cac hop truoc do chua
allowlist). Day la he qua TU NHIEN cua `max_depth=6` ap dung cho 1 giao
dich flash-loan phuc tap cham vao ha tang DeFi lon (Aave/Curve) — **KHONG
sua builder, KHONG loai incident**, chi bao cao nhu yeu cau.
