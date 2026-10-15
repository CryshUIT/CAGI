# Han che da biet: builder mo rong qua hub ngoai allowlist (2026-10-14)

**Trang thai: GHI NHAN HAN CHE, KHONG sua du lieu freeze.** Phat hien trong
qua trinh mo rong dataset N=20 -> N=30, nhung AP DUNG CHO CA N=15 (xem bang
duoi) — day la gioi han CO HE THONG cua phuong phap, khong phai loi rieng
cua 1 incident/dot mo rong nao.

## Mo ta han che

`src/trajectories/builder.py::build_trajectory` mo rong trajectory **forward-
only** tu seed, bam theo frontier (dst cua moi action duoc chap nhan tro
thanh frontier ke tiep) toi `max_depth=6`. Khi 1 incident co dong tien phuc
tap (flash loan, nhieu buoc swap/chuyen doi), frontier co the **cham toi 1
dia chi/contract CO DO KET NOI RAT CAO trong do thi giao dich chung** (vi,
market-maker, DEX router pho bien) **KHONG lien quan truc tiep den incident**
— frontier tiep tuc mo rong QUA dia chi do, keo theo RAT NHIEU dia chi/
giao dich cua NGUOI DUNG KHAC khong lien quan vao trajectory, lam "phinh"
so action mot cach gia tao (khong phan anh dung hanh vi cua ke tan cong).

Day la **CUNG CO CHE** da duoc ghi nhan truoc day trong
`metadata/annotation_guide.md` (muc "Mixer/DEX router = endpoint, KHONG
phai hop de tiep tuc trace", bug thuc da sua 2026-08-13 lien quan
PancakeSwap Router/Tornado Cash) — nhung **van con ap dung cho BAT KY
contract/vi CO DO KET NOI CAO nao CHUA duoc allowlist** (allowlist chi
ngan duoc viec mo rong QUA cac dia chi DA BIET truoc, khong the ngan truoc
cho moi hub chua tung gap).

## Vi du cu the da xac nhan

| Incident | n_action | Hub gay phinh | Da xac nhan nhan |
|---|---|---|---|
| **ronin_bridge_2022** (N=15, da freeze) | 1.625 | `0x0000006daea1723962647b7e189d311d757fb793` | **Wintermute 1** (market maker lon) |
| **radiant_capital_arbitrum_2024** (N=15, da freeze) | 248 | `0x111111125421ca6dc452d289314280a0f8842a65` | **1inch: Aggregation Router V6** (DEX router THAT, verified, nhung KHAC voi "1inch v4" da allowlist — chua tung duoc them) |
| inverse_finance_2022_jun (N=30, moi) | 11.592 | Nhieu dia chi (khong co 1 hub duy nhat chiem uu the — top10 chi 24,6%), gom **Hotbit 9, HTX 2, FTX 1** (vi CEX) + **Polygon ERC20 Bridge, Bancor Master Vault V3** (giao thuc THAT nhung qua pho bien) | Xem `N30_inverse_explosion_channel_analysis_2026-10-14.md` |
| **easyfi_2021 (N=30, moi, lo 2)** | **16.560-17.166** (dao dong theo lan build do cache) | **LON HON Inverse Finance** - chua phan tich chi tiet top hub (uu tien thap vi khong anh huong ranh gioi cung); biet ro: 2.166 action `swap`, 269 trong so do cham TRUC TIEP Uniswap V2 Router (dat cong 3), n_processed ~2.369 dia chi | Phat hien 2026-10-15 khi kiem tra provenance lo 2. De xuat them sensitivity "N tru EasyFi" tuong tu da lam cho Inverse (xem predeclaration v7). |

## Bang top-1 hub (khong tinh seed/allowlist) cho TOAN BO 15 incident v1.0

(Dia chi chua tra cuu nhan duoc ghi nguyen dang, chi 2 dong tren da xac
nhan nhan cu the — KHONG suy doan nhan cho cac dia chi con lai)

| Incident | n_action | Top-1 hub (dia chi) | % tong luot cham |
|---|---|---|---|
| ronin_bridge_2022 | 1.625 | 0x0000006daea1723962647b7e189d311d757fb793 (Wintermute 1) | 11,4% |
| qbridge_qubit_2022 | 698 | 0x5afef8567414f29f0f927a0f2787b188624c10e2 | 9,8% |
| paraluni_2022 | 511 | 0x61eb789d75a95caa3ff50ed7e47b96c132fec082 | 10,3% |
| bsc_token_hub_2022 | 362 | 0x46ed8b4afee29ca391f70d22b3e046e914ec8f4f | 8,7% |
| wault_finance_2021 | 190 | 0xf2ce52e3d0eb5d237341c9a75ca24647d87d7e55 | 39,2% |
| radiant_capital_arbitrum_2024 | 248 | 0x111111125421ca6dc452d289314280a0f8842a65 (1inch V6) | 21,0% |
| xkingdom_2024 | 73 | 0x82af49447d8a07e3bd95bd0d56f35241523fbab1 | 37,0% |
| magic_abracadabra_arbitrum_2025 | 88 | 0x7c8fef8ea9b1fe46a7689bfb8149341c90431d38 | 22,7% |
| utopiasphere_2024 | 37 | 0x92b7807bf19b7dddf89b706143896d05228f3121 | 17,6% |
| hackerdao_2022 | 35 | 0x776c91b0048745df496a77299911b835f8424fa3 | 18,6% |
| chibi_finance_2023 | 40 | 0xfc506aaa1340b4dedffd88be278bee058952d674 | 33,8% |
| deltaprime_arbitrum_2024 | 23 | 0xea3123e9d9911199a6711321d1277285e6d4f3ec | 37,0% |
| wooppv2_2024 | 16 | 0xb59d04d9957c9e266dff5c4173d4d2324eb029ad | 31,2% |
| new_free_dao_2022 | 12 | (khong co — toan bo action di toi allowlist/seed) | 0,0% |
| feg_bridge_2024 | 9 | (khong co — toan bo action di toi allowlist/seed) | 0,0% |

## Ket luan

- Day la **han che CO HE THONG**, khong phai loi phat sinh tu dot mo rong
  N30 hay 1 incident cu the. **KHONG sua du lieu freeze (N=15, N=20)**.
- **Khuyen nghi cho paper/thesis**: neu nhan phan bien/lam camera-ready, can
  biet ro `radiant_capital_arbitrum_2024` (1 trong 15 incident chinh thuc
  cua N=15) co "lo hong allowlist" voi 1inch V6 — tra loi thang ve han che
  nay thay vi phu nhan, dua vao chinh file nay + comment code co san trong
  `annotation_guide.md` lam bang chung da nhan dien tu truoc (khong phai
  moi phat hien sau khi co phan bien).
- Quy tac "allowlist completion" (v7) da duoc SIET LAI de tranh lap lai:
  chi them contract nam trong dong tien THAT cua CHINH incident dang xu ly,
  khong them chi vi no la hub gap o do sau.

## Han che moi: vong mine v2_complexity phu thuoc THU TU xu ly qua global_excluded (2026-10-15)

**Trang thai: GHI NHAN HAN CHE, KHONG sua thuat toan, KHONG xu ly lai.**

Vong mine "v2_complexity" (he thong, TARGET=10/incident, dung CHINH cach
tinh `compute_min_candidate_events`/`max_candidates_checked=150` nhu da
dung o N20) cho 5 incident lo 1 N30 dat yield **rat khong deu**:

| incident | mining contract | accepted/target | checked | rejected |
|---|---|---|---|---|
| dough_finance_2024 | Tornado Cash Router | 9/10 | 85 | 76 |
| prisma_finance_2024 | Tornado Cash Router | **1/10** | 75 | 74 |
| uranium_finance_2021 | Uniswap V2 Router | 10/10 | 62 | 52 |
| 0xinfini_2025 | Uniswap Universal Router v2 | 10/10 | 99 | 89 |
| inverse_finance_2022_jun | Tornado Cash Router | **1/10** | 150 | 149 |

Khong co loi/truncation API nao (xem
`results/reports/mining_v2complexity_truncation_log_N30_batch1_2026-10-14.json`,
tat ca `truncated=false`) — day la ket qua TU NHIEN cua thuat toan khi
`max_candidates_checked=150` bi cham voi ty le reject cao.

**Nguyen nhan co kha nang cao nhat**: ca 3 incident Dough, Prisma, Inverse
deu dung CUNG 1 mining contract (Tornado Cash Router). Script xu ly theo
THU TU `IDS_ORDER = [dough, prisma, uranium, 0xinfini, inverse]` va tich
luy `global_excluded` (dia chi da duoc accept o incident truoc se bi loai
khoi candidate pool cua incident sau) — vi vay Dough (xu ly truoc, cung
mining contract) co the da "dung truoc" mot phan candidate chat luong tot
nhat quanh Tornado Cash Router, khien Prisma va dac biet Inverse (xu ly
sau, cung mining contract) con lai candidate pool ngheo hon. Day la he qua
TU NHIEN cua co che chong trung lap dia chi giua cac incident (dung muc
dich, tranh 1 dia chi lam negative cho > 1 incident) ket hop VOI thu tu xu
ly va viec nhieu incident chia se 1 mining contract — KHONG phai loi code,
nhung can luu y khi doc ket qua: yield thap cua Prisma/Inverse KHONG phan
anh "incident nay kho tim negative hon ve ban chat", ma mot phan do thu tu
xu ly.

**Khuyen nghi cho paper/thesis**: neu bao cao yield mining theo incident,
can chu thich ro nguyen nhan nay, tranh suy dien sai ve do phuc tap/do kho
tim negative cua tung incident rieng le.

## Han che moi: protocol_map_N20.yaml / protocol_map_N30.yaml CHI la tai lieu tham khao, KHONG duoc pipeline doc (2026-10-15)

**Trang thai: GHI NHAN HAN CHE, KHONG sua `metadata/protocol_map.yaml` goc,
KHONG sua `load_protocol_map()`.**

Phat hien khi kiem tra provenance Popsicle Finance (lo 2): moi call site cua
`load_protocol_map()` trong code (`src/pipeline/incident_pipeline.py:323`,
`src/collect/hard_negative_miner.py:229,394`) deu goi **KHONG truyen path**,
nen LUON doc `DEFAULT_PROTOCOL_MAP_PATH = metadata/protocol_map.yaml` (file
GOC v1.0) - khong co co che nao tro sang `protocol_map_N20.yaml` hay
`protocol_map_N30.yaml`. Dieu nay DA duoc ghi nhan 1 PHAN truoc day (xem
`results/reports/dataset_expansion_N20_checkpointCprime_2026-10-14.md`,
muc "section dexes KHONG duoc chuong trinh doc") nhung chi cho muc `dexes:`
- lan nay xac nhan dung cho CA mục `mixers_exit_services:`/`bridges:`.

**Vi sao `dexes:` khong sao nhung `mixers_exit_services:`/`bridges:` co van
de**: viec 1 giao dich co duoc "giu lai" trong trajectory (bypass
`value_share`) CHI phu thuoc `config.allowlist` (hop nhat tu
`configs/data_N30.yaml`) - hoat dong DUNG cho ca dex/bridge/mixer. NHUNG
viec gan NHAN `event_type` ("mixer_or_exit"/"bridge_deposit" thay vi
"transfer" thuong) lai phu thuoc RIENG vao `mixer_address_index`/
`bridge_address_index`, xay dung TRUC TIEP tu `load_protocol_map()` - LUON
la file goc. Ket qua: 1 contract moi them vao `dex_allowlist` cua
`configs/data_N30.yaml` VAN hoat dong dung (giao dich duoc giu, khong bi
loc theo value_share) vi khong can nhan dac biet; nhung 1 contract moi them
vao `mixer_allowlist`/`bridge_allowlist` SE duoc giu lai dung, nhung KHONG
duoc gan nhan "mixer_or_exit"/"bridge_deposit" - van la "transfer" thuong.

**Anh huong thuc te (da ra soat toan bo cac muc da them vao
`protocol_map_N20.yaml`/`protocol_map_N30.yaml` tu truoc den nay)**:

| Muc da them | File | Loai | Co anh huong endpoint_confirmed khong? |
|---|---|---|---|
| Uniswap: Universal Router v2 | protocol_map_N20.yaml | dex | KHONG - dex, chi can counterparty_allowed |
| Uniswap: Universal Router (v1.2) | protocol_map_N20.yaml | dex | KHONG |
| KyberSwap: Meta Aggregation Router v2 | protocol_map_N30.yaml | dex | KHONG |
| MetaSwap | protocol_map_N30.yaml | dex | KHONG |
| SushiSwap: RouteProcessor3_2 | protocol_map_N30.yaml | dex | KHONG |
| **TornadoProxy** | protocol_map_N30.yaml | **mixer** | **CO** - Popsicle Finance co giao dich THAT toi TornadoProxy (duoc giu lai trong trajectory nho `config.allowlist`), nhung KHONG duoc gan "mixer_or_exit" nen `endpoint_confirmed` cua Popsicle van la False du bao cao doc lap (SlowMist/BlockSec) xac nhan ro rang rua tien qua day. |

**Xac nhan**: TRUOC phat hien nay, KHONG co co/flag/endpoint_confirmed nao
cua bat ky incident (tu N=15 den N=30 lo 1) phu thuoc vao 1 trong 5 muc
dex da them - vi tat ca deu la dex, khong anh huong co che gan nhan. Chi
TornadoProxy (muc mixer duy nhat da them) bi anh huong, va duoc xu ly bang
cach giu `endpoint_confirmed=False` cho Popsicle Finance (ghi ro ly do
trong registry), KHONG sua code/file goc de "fix" theo.

**Quet cache (chi bao cao, KHONG sua)**: ra soat toan bo 973 hard-negative
hien co (536 v1.0 main + 110 v1.0 v2c + 125 N20 main + 46 N20 v2c + 125 N30
lo1 main + 31 N30 lo1 v2c) xem co giao dich nao (to/from) toi TornadoProxy
(0x722122df12d4e14e13ac3b6895a86e84145b6967) hay khong - ket qua: **0/973**.
Khong phat hien negative nao vo tinh da dung mixer ma bo loc mining khong
nhan dien.

## Bang day du so negative theo incident va vong mine (N30, lo 1, 2026-10-15)

| incident | main (muc tieu=25) | v2_complexity (muc tieu=10) | tong |
|---|---|---|---|
| dough_finance_2024 | 25 | 9 | 34 |
| prisma_finance_2024 | 25 | 1 | 26 |
| uranium_finance_2021 | 25 | 10 | 35 |
| 0xinfini_2025 | 25 | 10 | 35 |
| inverse_finance_2022_jun | 25 | 1 | 26 |
| **Tong moi (lo 1 N30)** | **125** | **31** | **156** |

Cong voi so negative cu (536 v1.0 + 125 N20 main + 110 v1.0 v2c + 46 N20
v2c = 817) va 5 hard-negative-control goc, tong negative trong
`features_v2_N30.parquet` (sau khi loai cac dong rong/khong dung duoc) la
**931** — xem bang doi chieu day du theo nguon trong bao cao chinh
(`N30_batch1_negative_accounting_2026-10-15.md`).
