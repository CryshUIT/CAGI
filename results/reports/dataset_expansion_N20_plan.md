# Ke hoach mo rong dataset tu N=15 len ~N=20 — Giai doan 1+2 (2026-10-14)

**TRANG THAI 2026-10-14 (cap nhat lan 2)**: Nguoi dung DA CHOT danh sach
Batch A + quy tac dung. Phan "Giai doan 1 (ban dau)" ben duoi giu nguyen lam
ho so; cac muc **9-13 la cap nhat moi** sau khi nguoi dung xac nhan. **VAN
CHUA ghi de `incident_registry.csv` chinh thuc/freeze v1.0** — moi thu thap
du lieu that se dung 1 file registry MOI rieng (`metadata/incident_registry_N20.csv`),
tao khi bat dau xu ly incident dau tien.

## 1. Hien trang (doc tu incident_registry.csv + incident_candidates_amlguard.csv + configs/data.yaml)

- **15 incident chinh thuc hien tai** (eval_tier=primary, dung trong
  `features_v2.parquet`/`main_table.csv`): ronin_bridge_2022,
  qbridge_qubit_2022, feg_bridge_2024, deltaprime_arbitrum_2024,
  bsc_token_hub_2022, chibi_finance_2023, wooppv2_2024, utopiasphere_2024,
  xkingdom_2024, wault_finance_2021, paraluni_2022, radiant_capital_arbitrum_2024,
  magic_abracadabra_arbitrum_2025, hackerdao_2022, new_free_dao_2022.
  Ngoai ra `circulate_2023` ton tai trong registry voi `eval_tier=auxiliary_low_evidence`
  (gate yeu nhat, KHONG tinh vao N=15/RQ1 chinh).
- **Pool ung vien AMLGuard**: 82 dong (`metadata/incident_candidates_amlguard.csv`).
  Phan theo chain: ETH=55, BSC=14, Arbitrum=6, FTM=3, Optimism=2, Polygon=1,
  BASE=1 — chi 3 chain dau nam trong pham vi ky thuat hien tai
  (`configs/data.yaml::chains`), con lai 7 FTM/Optimism/Polygon/BASE
  NGOAI SCOPE (khong co collector).
- **Da sang loc truoc day** (co `screening_note`), trong 3 chain ho tro —
  23 dong:
  - 3 `STRONG_CANDIDATE_bridge_in_name` (Ronin Bridge, FEG Bridge — ca hai
    DA co trong 15 incident; **XPEXE Bridge — DA dieu tra va LOAI**, xem
    `experiments/logs/excluded_candidates.md`: khong tim duoc bao cao cong
    khai nao xac nhan ton tai incident nay, du dia chi co hoat dong on-chain
    that dang nghi).
  - 19 `CHECK_MANUALLY_non_eth_chain` (BSC/Arbitrum): 13 da duoc dung (12
    trong 15 chinh thuc + circulate_2023 auxiliary), 4 da LOAI co ghi ro ly
    do (Redruby DAO — khong co bao cao cong khai; Whale Loans — tien khong
    roi vi attacker; Novo Defi — gioi han kien truc `min_tainted_share` loai
    het 30 giao dich smurfing hop le; LianGo — dia chi khong khop thoi
    diem, da thay bang CirculateBUSD). **Con lai 2 dong CHUA TUNG duoc dieu
    tra**: Loser Coin, Revisiting.
- **52 dong ETH hoan toan CHUA TUNG duoc sang loc** (khong co screening_note
  nao) — day la pool chinh cho vong mo rong nay. Danh sach day du: xem
  Section 2.

## 2. Ket qua sang loc nhanh (WebSearch, 2026-10-14) — CHUA thu thap du lieu, chi tra cuu bao cao cong khai

Da tra cuu 9 ung vien trong 52 dong ETH chua sang loc (chon theo do noi
tieng/kha nang co bao cao doc lap ro rang) + 2 dong BSC con lai
(Loser Coin, Revisiting). KHONG chon/loai dua tren "mo hinh chay tot hay
xau" — chi dua tren provenance/chat luong du lieu nhu yeu cau.

### Ung vien DE XUAT (xep theo do tin cay, dia chi khop CHINH XAC voi CSV)

| # | Ten | Chain | Seed address (khop CSV) | Nguon bao cao | Bang chung bridge/DEX/mixer | Rui ro |
|---|---|---|---|---|---|---|
| 1 | **Beanstalk Farms** | eth | 0x1c5dcdd006ea78a7e4783f9e6021c32935a10fb4 | CertiK ("Revisiting Beanstalk Farms Exploit") | Attacker doi token -> ETH -> **Tornado Cash** (xac nhan) | Flash loan $1B qua Aave — khoi luong du lieu outbound co the lon (nhieu tx chuyen doi tai san truoc khi toi Tornado); can kiem tra window 72h co du bat duoc buoc Tornado Cash khong |
| 2 | **Zunami Protocol** | eth | 0x5f4C21c9Bb73c8B4a296cC256C0cDe324dB146DF | CertiK + Beosin + PeckShield (3 nguon doc lap) | Flash loan thao tung gia SDT qua **SushiSwap** (DEX that) -> toan bo tien qua **Tornado Cash** | Thap — bang chung ro rang nhat trong nhom, ca DEX va mixer deu xac nhan cung 1 incident, co kha nang endpoint nam trong 72h (deployer gui settlement message chi 3 ngay sau) |
| 3 | **Onyx Protocol** | eth | 0x085bDfF2C522e8637D4154039Db8746bb8642BfF | CertiK ("Post Mortem: Onyx Protocol") + SharkTeam + MetaTrust | ~1140/1164 ETH qua **Tornado Cash** | Thap — "empty pool attack" tren Compound V2 fork, co the can chuoi giao dich dai (mint/redeem lap lai) truoc khi toi mixer |
| 4 | **Cork Protocol** | eth | 0xEA6f30e360192bae715599E15e2F765B49E4da98 | CertiK + SlowMist + QuillAudits + rekt.news | wstETH -> **ETH qua 8 giao dich swap** (DEX that, MistTrack xac nhan) | Trung binh — KHONG thay bang chung mixer/bridge tiep theo trong ket qua tim kiem (chi co buoc swap), endpoint co the KHONG nam trong trace (tien dung lai dang ETH) |
| 5 | **Hedgey Finance** | eth (CSV) nhung thiet hai chinh ($42.6M/$44.7M) tren **arbitrum** | 0xded2b1a426e1b7d415a40bcad44e98f47181dda2 | CertiK ("Hedgey Finance Incident Analysis") + CUBE3.AI | Flash loan Balancer, $1.3M USDC (mainnet) — phan Arbitrum lon hon nhieu nhung CAN XAC MINH RIENG dia chi/chain_primary truoc khi dua vao (ca 2 chain dung CHUNG dia chi attacker theo etherscan) | **Trung binh-cao** — truong hop 2-chain phuc tap (giong radiant_capital_arbitrum_2024), can quyet dinh chain_primary + co the phai tach thanh "chi lay phan ETH" hoac "chi lay phan Arbitrum" (lon hon, nhung can kiem tra rieng tren Arbiscan) |
| 6 | **Cream Finance** | eth | 0x24354d31bc9d90f62fe5f2454709c32049cf866b | CertiK (tracked, nhieu bai dua tin) | $130M rut tu market — **chua xac nhan duoc bang chung bridge/DEX/mixer ro rang TRONG VAI NGAY DAU** (chi thay 1 lan chuyen 365 ETH **16 THANG SAU**, qua muon de nam trong window 72h) | **Cao** — rui ro lon nhat ve endpoint: co the KHONG co hoat dong outbound ro rang trong 72h dau, giong truong hop Whale Loans da bi loai |
| 7 | **Harvest Finance** | eth | 0xf224ab004461540778a914ea397c589b677e27bb | SlowMist ("Analysis of Harvest.Finance's Hacked Event") | 20 ETH qua Tornado Cash ("subsequent attack fee") + tien "eventually swapped to BTC" | **Trung binh-cao** — chu "eventually" cho thay co the keo dai qua 72h; day la vu 2020 (ngoai khung 2021-2025 hien tai cua paper — CAN quyet dinh co mo rong pham vi thoi gian khong) |

### Ung vien KHONG de xuat (da tra cuu, khong du dieu kien hoac rui ro qua cao)

| Ten | Ly do loai |
|---|---|
| **0xInfini (2025)** | Dia chi trong CSV (`0x3ac96134...`) la dia chi TRUNG GIAN duoc cap quyen allowlist, KHONG phai dia chi nhan tien cuoi (`0xfcC8Ad91...` theo bao cao) — seed khong khop ro vai tro "attacker wallet" chinh, can xac dinh lai dia chi seed dung truoc khi dua vao, de lai cho vong sau |
| **Prisma Finance (2024)** | **CANH BAO QUAN TRONG**: 3 dia chi attacker thuc te tim duoc qua WebSearch (`0xd996073019c7...`, `0x7Fe83f45e0f5...`, `0x7C9FC6E2B908...`) **KHONG khop** voi dia chi trong CSV (`0x7E39E3B3ff7A...`) — co kha nang CSV gan sai dia chi cho incident nay. KHONG dua vao de xuat tru khi doi chieu lai duoc nguon goc |
| **Loser Coin (BSC)** | CertiK co report nhung quy mo rat nho (flash loan arbitrage, 3 user bi anh huong), KHONG co bang chung bridge/DEX/mixer "thoat" sau exploit — loi nhuan duoc swap ngay trong cung giao dich flash loan roi dung lai, giong pattern da bi loai o Whale Loans/Novo Defi (duoi nguong gate) |
| **Revisiting (BSC)** | KHONG tim duoc bat ky bao cao cong khai nao xac nhan ton tai 1 incident ten "Revisiting" — dia chi chi thay co hoat dong deploy contract, khong co nguon doc lap nao quy thuoc exploit |
| **Euler Finance, Curve Finance, BadgerDAO, Polynetwork** (chua tra cuu sau, de xuat KHONG uu tien) | Theo hieu biet chung: Euler/Polynetwork co hoan tra toan bo/phan lon quy cho attacker (whitehat return) — KHO co "outbound trajectory thoat" co y nghia; BadgerDAO la phishing frontend (nhieu nan nhan, khong phai 1 seed-wallet exploit don) — khac cau truc du an hien tai (1 seed = 1 attacker). Can tra cuu rieng neu danh sach 7 ung vien tren khong du. |

## 3. Uu tien theo endpoint (RQ2/lead-time)

Theo yeu cau nguoi dung, danh dau ro: trong 7 ung vien de xuat, **Zunami
Protocol va Onyx Protocol co kha nang cao nhat co endpoint (mixer) nam
TRONG cua so trace 72h** (ca hai co bao cao cu the ve Tornado Cash xay ra
gan nhu ngay sau exploit). Cork Protocol co bang chung DEX ro nhung CHUA
thay endpoint tiep theo. Beanstalk co endpoint nhung co the can window dai
hon do khoi luong giao dich flash loan lon. Cream Finance va Harvest
Finance la 2 ung vien RUI RO CAO nhat ve endpoint (co dau hieu outbound
xay ra NGOAI 72h). Day la UU TIEN de co endpoint, KHONG phai tieu chi
loai/giu — quyet dinh cuoi van dua theo provenance nhu Section 2.

## 4. Chi phi API va rui ro quota

- **Tat ca 7 ung vien de xuat deu la chain ETH** (hoac ETH+Arbitrum cho
  Hedgey) — dung Etherscan V2, **KHONG dung NodeReal/BSC** (nguon bottleneck
  quota da gap o lan N=15 truoc). Day la loi diem lon: giam han rui ro
  quota so voi lan mo rong truoc.
- Etherscan free-tier gioi han 10,000 record/call (da co phan trang tu dong
  trong `EtherscanClient`, khong can thay doi).
- **CHUA kiem tra duoc quota/API key hien tai con dung duoc khong** — viec
  nay can test thuc te (1 call nho) ngay dau Giai doan 2, KHONG the xac
  nhan truoc ma khong goi API (ngoai pham vi Giai doan 1 — "KHONG thu thap
  du lieu").
- Hedgey Finance (neu lay ca phan Arbitrum) can them Arbiscan — cung ho
  tro san trong `configs/data.yaml::chains`, khong can ha tang moi.
- Uoc tinh so dia chi can mo rong: tuong tu cac incident hien tai (2-6 dia
  chi trung gian/incident dua theo max_depth=6), khong co ly do nghi ngo
  ung vien nao can mo rong bat thuong nhieu hon, TRU Beanstalk (flash loan
  $1B co the tao nhieu nhanh giao dich trung gian hon binh thuong — can
  theo doi khi crawl thuc te).

## 5. De xuat cuoi (muc tieu ~5 incident moi dat chuan, co du phong)

**Khuyen nghi thu tu uu tien nếu phải chọn ~5 trên 7**: Zunami Protocol >
Onyx Protocol > Beanstalk Farms > Cork Protocol > Hedgey Finance (can quyet
dinh chain_primary truoc) — day la 5 co bang chung manh nhat VA it rui ro
endpoint nhat. Cream Finance va Harvest Finance giu lai lam **du phong**
(rank 6-7) neu 1 trong 5 incident tren khi dieu tra sau (Giai doan 2, truoc
khi them vao registry) hoa ra khong dat gate bridge/DEX/mixer that.

**KHONG de xuat dua vao danh sach ngay**: 0xInfini (seed sai vai tro),
Prisma Finance (dia chi khong khop CSV — co the CSV sai), Loser Coin,
Revisiting (khong du evidence).

## 6. Buoc tiep theo (CHI lam sau khi nguoi dung xac nhan)

1. Nguoi dung chon ra tu danh sach 7 (hoac yeu cau tra cuu them ung vien
   khac trong 52 dong ETH chua sang loc, hoac trong cac vu nam ngoai pool
   AMLGuard).
2. Voi tung ung vien duoc chon: kiem tra thuc te qua API (khong chi
   WebSearch) truoc khi them vao registry — dung chinh quy trinh "Checklist
   them 1 incident moi" da co san (`metadata/annotation_guide.md` muc 8).
3. Tao version du lieu moi tach biet (vd `features_v2_N20.parquet`,
   `incident_registry_N20.csv`), KHONG dong vao freeze v1.0/15-incident
   hien tai.

## Xac nhan: KHONG file N=15/freeze v1.0 nao bi thay doi trong Giai doan 1 nay

Chi doc (`Read`/pandas `read_csv`), khong co lenh `Write`/`Edit` nao chay
tren `incident_registry.csv`, `configs/data.yaml`, `protocol_map.yaml`,
hay bat ky file freeze/N=15 nao trong qua trinh lam bao cao nay.

---

## 9. Danh sach CHOT (nguoi dung xac nhan 2026-10-14)

### Batch A — thu tu xu ly (xep hang, bat buoc tuan tu)

| Thu tu | Incident | Chain | Seed address | Ghi chu quyet dinh |
|---|---|---|---|---|
| 1 | Zunami Protocol | eth | 0x5f4C21c9Bb73c8B4a296cC256C0cDe324dB146DF | — |
| 2 | Onyx Protocol | eth | 0x085bDfF2C522e8637D4154039Db8746bb8642BfF | — |
| 3 | Beanstalk Farms | eth | 0x1c5dcdd006ea78a7e4783f9e6021c32935a10fb4 | — |
| 4 | Hedgey Finance | eth | 0xded2b1a426e1b7d415a40bcad44e98f47181dda2 | **chain_primary = "eth" (CHOT, ghi vao registry N20 ngay khi tao dong)**. Ly do: dia chi attacker giong nhau tren ca 2 chain nhung CSV goc liet ke ETH; phan Arbitrum ($42.6M) lon hon nhieu nhung KHONG dua vao outbound trajectory chinh — chi dung phan ETH ($2.1M, $1.3M USDC flash loan Balancer) de giu dung schema "1 chain_primary/incident" hien tai (giong cach radiant_capital_arbitrum_2024/chibi_finance_2023 de ngo phan chain khac). Neu muon lay ca phan Arbitrum, phai lam incident RIENG (ngoai pham vi Batch A). |
| 5 | Cork Protocol | eth | 0xEA6f30e360192bae715599E15e2F765B49E4da98 | **Endpoint CHUA xac nhan** (chi co bang chung swap wstETH->ETH, khong thay mixer/bridge tiep theo trong bao cao cong khai da tra cuu) — ghi ro: **KHONG dua incident nay vao tap tinh lead-time/RQ2** tru khi qua trinh thu thap du lieu that tim duoc exit ro rang trong trace. Van tinh vao RQ1 (chi can co bridge/DEX trong trajectory, khong bat buoc endpoint). |

### Loai khoi Batch A (ghi ro ly do, theo yeu cau nguoi dung)

| Incident | Ly do loai |
|---|---|
| **Cream Finance** | Bang chung outbound (chuyen 365 ETH) chi xuat hien **16 THANG SAU** exploit trong bao cao da tra cuu — ngoai cua so trace 72h (`time_horizon_hours: 72` trong `configs/data.yaml`, khong doi tham so de "thich nghi"). Khong tim duoc bang chung nao khac ve hoat dong outbound TRONG 72h dau. |
| **Harvest Finance** | (1) Tu "eventually swapped to BTC" trong bao cao SlowMist cho thay buoc thoat chinh co the xay ra ngoai 72h; (2) vu nay xay ra 2020-10-26, **ngoai khung thoi gian 2021-2025 cua paper hien tai** (15 incident hien co deu tu 2021 tro di) — mo rong pham vi thoi gian la quyet dinh lon hon pham vi "mo rong N", khong tu quyet dinh thay nguoi dung. |

### Backup moi sang loc (de du N=8, theo yeu cau "sang them 3-4 ung vien")

Da sang loc them trong 52 dong ETH chua screen + 2 ung vien duoc "re-seed"
theo yeu cau. Ket qua:

| Hang backup | Incident | Seed address | Evidence | Ket luan |
|---|---|---|---|---|
| 1 | **Dough Finance** | 0x2913d90D94C9833B11a3E77F136da03075c04a0F | Nhieu nguon doc lap (post-mortem chinh thuc, SolidityScan, Verichains, dehacker_security) — dia chi khop CSV CHINH XAC ("Dough Exploiter 2"). Tien laundered qua **Tornado Cash theo lo 100 ETH NGAY TRONG NGAY 1** — endpoint RAT RO, manh hon ca 5 candidate trong Batch A | **MANH, co the xem xet dua vao Batch A thay Cork neu Cork khong dat gate endpoint khi thu thap thuc te** |
| 2 | **0xInfini** | 0x3ac96134Fb0e42a52D33045AeE50b89790f05Ed0 | **RE-SEED CHECK (theo yeu cau)**: tra cuu sau hon xac nhan dia chi nay (dung dia chi trong CSV, KHONG can doi) **nhan truc tiep ~49.5M USDC tu exploit** (khong chi la dia chi duoc cap quyen nhu nham lan o Giai doan 1) — xac nhan NHAT QUAN qua CertiK + Cyvers + Blocksec + PeckShield (4 nguon doc lap). Dia chi duoc Tornado Cash cap gas truoc khi tan cong (endpoint o DAU vao, khong phai dau ra) + swap USDC->DAI->ETH (DEX). Tien chuyen tiep sang dia chi khac (`0xfcC8Ad91...`) sau do, CHUA dung lai hoan toan | **Dung lai dia chi CSV, KHONG loai** — sua ket luan Giai doan 1 (qua than trong nham) |
| 3 | **Prisma Finance** | 0x7E39E3B3ff7ADef2613d5Cc49558EAB74B9a4202 | **RE-SEED CHECK (theo yeu cau)**: nguon chinh xac hon (crypto.news/ZachXBT/ibtimes/Bitget, dieu tra on-chain chi tiet hon ket qua tim kiem dau) xac nhan dia chi NAY (khop CSV CHINH XAC) la dia chi "0x77/Trung" — 3 dia chi tim duoc o Giai doan 1 la DO KET QUA TIM KIEM DAU khong day du/chinh xac, KHONG phai CSV sai. CertiK + PeckShield + ZachXBT deu xac nhan. Toan bo quy chuyen vao **Tornado Cash NGAY TRONG NGAY** sau khi tuyen bo "whitehat" roi doi y | **Dung lai dia chi CSV, KHONG loai** — sua ket luan Giai doan 1 (danh gia ban dau "CSV co the sai" la SAI, do thieu du lieu tim kiem) |

Da loai (khong dua vao backup, giu nguyen tieu chi provenance):

| Incident | Ly do loai |
|---|---|
| DEGO/Cocos Finance | PeckShield+Beosin xac nhan exploit that (private key compromise, $14.4M qua ETH/BSC/Cronos) nhung KHONG tim duoc bang chung ve diem thoat (bridge/mixer) sau khi rut tu Uniswap/PancakeSwap — chi co buoc rut tien, chua co buoc "roi khoi" |
| Warp Finance | Da hoan tra 75% quy ($5.85M/$7.7M) — tuong tu Whale Loans/Novo Defi da loai truoc, khong co "outbound trajectory thoat" co y nghia; dia chi attacker la SMART CONTRACT khong phai EOA don gian |
| Seneca/SenecaUSD | Hacker da tra lai >80% quy (5.3M/6.4M) sau khi project thuong luong — tuong tu Euler/Polynetwork (loai theo tieu chi chung o Giai doan 1), khong con "exit" that de dung |
| Fisher | Dia chi trong CSV thuc te la 1 dia chi phishing khong lien quan (`Fake_Phishing186943` theo Etherscan label), KHONG tim duoc bao cao nao xac nhan ton tai incident "Fisher" — co the CSV gan sai ten/dia chi |

**Danh sach cuoi cung (8 ung vien, dung yeu cau)**: 5 Batch A (Zunami, Onyx,
Beanstalk, Hedgey, Cork) + 3 backup (Dough Finance, 0xInfini, Prisma
Finance).

## 10. Quy tac dung (CHOT truoc khi chay, ghi lai de doi chieu sau)

1. Xu ly **TUAN TU theo dung thu tu xep hang** o Section 9 (Zunami → Onyx →
   Beanstalk → Hedgey → Cork → [backup theo thu tu neu can] Dough Finance →
   0xInfini → Prisma Finance).
2. Voi MOI incident, thu tu bat buoc trong incident do:
   a. **Cong provenance**: xac minh start_block/dia chi seed/exit khop bao
      cao cong khai BANG DU LIEU ON-CHAIN THAT (khong chi WebSearch) —
      CHUA duoc tinh la "dat" chi vi WebSearch tim thay bao cao.
   b. CHI SAU KHI dat cong provenance moi duoc tien hanh khai thac hard
      negative (buoc ton quota nhieu nhat) cho incident do.
   c. Neu KHONG dat cong provenance (khong khop on-chai, hoac khong du
      bridge/DEX/mixer evidence nhu da gap voi Novo Defi/Whale Loans) —
      LOAI, chuyen sang candidate tiep theo trong hang, GHI vao
      `experiments/logs/excluded_candidates.md` (file dung chung voi N=15,
      ghi them muc moi, khong tao file rieng).
3. **Diem dung**: dat 20 incident dat chuan (15 hien tai + 5 incident moi
   dat chuan) la DU — KHONG vuot qua 22 (15 + 7) du con candidate trong
   hang. Neu Batch A (5) deu dat chuan, DA DU 20 — chi dung backup khi co
   it nhat 1 trong Batch A bi loai o buoc cong provenance.
4. Khong dua ket qua model/RQ1 vao qua trinh quyet dinh giu/loai — chi
   provenance + chat luong du lieu (nhu da lam voi N=15).

## 11. Kiem tra API key truoc khi crawl (2026-10-14)

Da goi 1 request THAT qua `EtherscanClient.fetch_normal_txs()` (dia chi
Zunami attacker, block 17900000-17910000, incident_id="quota_test_2026-10-14")
— **THANH CONG**, tra ve 35 dong, 1.16s. API key `ETHERSCAN_API_KEY` trong
`.env` dang hoat dong binh thuong, khong bi khoa/het quota. Cache test duoc
ghi tai `data/raw/eth/0x5f4c21c9bb73c8b4a296cc256c0cde324db146df/` (nam
trong `.gitignore::data/raw/*`, khong anh huong gi incident thuc khi
Zunami duoc xu ly chinh thuc - cache nay se duoc TAI SU DUNG, khong phai
goi lai, vi cung dia chi/block range).

## 12. Uoc tinh ngan sach request

- Theo kinh nghiem N=15 (nguoi dung neu "vai nghin response moi incident"):
  moi dia chi thuong can 3 loai goi (txlist/tokentx/txlistinternal), moi
  loai co the can nhieu "trang" (page) neu dia chi hoat dong manh (gioi
  han 10.000 record/trang). Voi max_depth=6 va thuong 2-6 dia chi/incident
  (dua theo 15 incident hien tai), uoc tinh THO: ~6-18 lan goi API "binh
  thuong"/incident, co the TANG MANH cho cac vu flash loan khoi luong lon
  (Beanstalk $1B flash loan, Dough Finance Tornado Cash nhieu lo) — CHUA
  co so lieu chinh xac, chi xac nhan duoc khi thu thap thuc te tung
  incident.
- Toan bo 8 candidate deu la **chain ETH** (Hedgey chi lay phan ETH theo
  quyet dinh Section 9) — dung 1 nguon API duy nhat (Etherscan V2), KHONG
  dung NodeReal/BSC (nguon quota da can kiet o lan N=15 truoc) — **rui ro
  quota THAP HON RO RET so voi lan mo rong truoc**.
- `rate_limit_per_sec: 2` (configs/data.yaml) da duoc EtherscanClient tu
  dong tuan thu — khong can chinh gi. Etherscan free-tier hien dai khong
  co gioi han ngay cung (chi gioi han giay), nen "chia theo ngay" CHI can
  thiet neu qua trinh crawl 1 incident bi loi lien tuc do gioi han giay
  (rate limit 429) — se theo doi va bao cao neu gap, khong du doan truoc.
- **Hanh dong**: se theo doi so luong request THAT khi xu ly Zunami (candidate
  dau tien) va bao cao lai con so cu the, thay vi tiep tuc uoc tinh suong.

## 13. Buoc tiep theo ngay sau bao cao nay

Bat dau xu ly **Zunami Protocol** (candidate #1) qua cong provenance that
(Section 10, buoc 2a) — tao `metadata/incident_registry_N20.csv` (copy 15
dong hien tai + them dong Zunami SAU KHI qua cong) va bao cao ket qua
truoc khi chuyen sang Onyx Protocol.

---

## 14. KET QUA Batch A — ca 5/5 incident DAT CONG PROVENANCE (2026-10-14)

Da xu ly tuan tu dung thu tu xep hang (Section 10), kiem tra THAT qua
`EtherscanClient` (khong chi WebSearch) cho tung incident. **CA 5/5 DAT**
— dat diem dung 20 incident (15 cu + 5 moi) theo dung Quy tac dung muc
10.3. **KHONG xu ly 3 backup** (Dough Finance, 0xInfini, Prisma Finance) —
dung lai o 20, dung vuot qua theo dung quy tac da CHOT.

| # | Incident | start_block xac nhan | Bang chung on-chain THAT | Endpoint |
|---|---|---|---|---|
| 1 | Zunami Protocol | 17908899 (CSV lech 4 block) | 1183.8 ETH → Tornado Cash (30 deposit, ~48 phut sau start) — khop GAN DUNG bao cao (~1178 ETH) | **Confirmed** |
| 2 | Onyx Protocol | 18476508 | Qua trung gian 2-hop: 1140.0 ETH → Tornado Cash — khop TUYET DOI bao cao | **Confirmed** |
| 3 | Beanstalk Farms | 14595304 (CSV lech 4 block) | DEX truc tiep (Uniswap V2, 145 ETH) + 24,849.1 ETH → Tornado Cash (271 lan, ~27.6h) — khop gan dung $76M loi nhuan bao cao | **Confirmed** |
| 4 | Hedgey Finance | 19687845 | Flash loan Balancer 1,303,910 USDC (khop CHINH XAC "1.3m USDC") + swap truc tiep toi 1 DEX aggregator CHUA xac minh ten | **KHONG tim thay** (chi kiem tra 72h tu dia chi seed, khong thay Tornado Cash/bridge) |
| 5 | Cork Protocol | 22524843 (khop CSV) | execute() truc tiep toi Uniswap Universal Router (dia chi chinh thuc), nhan lai 1 wstETH | **KHONG tim thay** (khoi luong lon 3760 wstETH bao cao co the nam o hop dong trung gian chua dieu tra sau o buoc nay) |

**Ghi chu quan trong ve Hedgey/Cork**: ca hai PASS gate RQ1 (co DEX action
THAT trong trajectory) nhung **endpoint_confirmed=False** — dung theo
quyet dinh da CHOT truoc khi crawl (Section 9), **KHONG dua 2 incident nay
vao tap tinh lead-time/RQ2**, chi dung cho RQ1. Day la ket qua DUNG NHU DU
DOAN trong Giai doan 1 (ca hai da duoc danh dau "rui ro endpoint" truoc
khi thu thap du lieu that).

### File da tao/sua trong buoc nay

- **Moi, chua duoc dung o dau khac**: `metadata/incident_registry_N20.csv`
  (26 dong: 21 dong cu + 5 incident moi). **KHONG ghi de**
  `metadata/incident_registry.csv` goc (xac nhan qua `git diff --stat`:
  khong co thay doi).
- `configs/data.yaml`, `protocol_map.yaml`: **CHUA SUA** — Uniswap
  Universal Router (Cork) va DEX aggregator cua Hedgey **CHUA duoc them
  vao `dex_allowlist`** (can lam truoc khi chay feature extraction chinh
  thuc cho 2 incident nay, vi builder chi giu lai DEX da allowlist).
- Cache test API (`data/raw/eth/.../*_provenance_check*`) — nam trong
  `.gitignore`, se duoc TAI SU DUNG (khong goi lai) khi chay pipeline
  chinh thuc cho cung dia chi/block range.

## 15. Viec CHUA lam (dung lai o day, cho xac nhan truoc khi tiep tuc)

Theo dung tinh than "dung truoc buoc ton quota nhieu nhat" (Quy tac dung
muc 10.2b) va thong le cua du an (moi incident moi lich su deu phat sinh
it nhat 1 van de can quyet dinh cua nguoi dung khi chay pipeline day du —
vd bug decoder bsc_token_hub_2022, bug value_share Radiant Capital), CHUA
thuc hien:

1. **Chay `expand_and_build_trajectory`/pipeline chinh thuc** cho 5
   incident moi (se dung nhieu quota hon dang ke so voi 5 lan kiem tra
   nho da lam, va se tu dong phat hien cac dia chi trung gian khac can
   them vao allowlist).
2. **Them Uniswap Universal Router (Cork) + xac minh ten DEX aggregator
   cua Hedgey** vao `dex_allowlist` (`configs/data.yaml`) + `protocol_map.yaml`
   — can lam TRUOC buoc 1.
3. **Khai thac hard-negative** cho ca 5 incident (dung quy trinh cu: 1
   contract bridge/DEX/mixer da verify, cung ngay, dia chi khac, khong
   split/fan-out bat thuong).
4. **Trich feature** (`build_features_v2.py` tuong duong, phien ban N20
   rieng) + kiem tra prefix-invariant.
5. **Chay lai RQ1/RQ2** tren N=20 (script rieng, KHONG dung main_table.csv/
   oof_predictions_v1.csv goc).

**De nghi**: xac nhan co muon tiep tuc ngay 4 buoc tren khong (se ton
nhieu quota API hon + thoi gian xu ly dai hon dang ke so voi buoc kiem tra
provenance vua xong), hay muon xem lai 5 incident da duoc xac nhan truoc
(vd kiem tra ky hon nguon von cua Hedgey/Cork truoc khi quyet dinh co giu
endpoint_confirmed=False vinh vien hay tiep tuc dieu tra sau).
