# Khai bao mo rong N30 - v8 (2026-10-15)

Giu nguyen TOAN BO noi dung v1-v7 (xem cac file `expansion_N30_predeclaration_v{1..7}.md`).
Muc nay CHI bo sung quyet dinh moi, khong sua/xoa noi dung cu.

## Quyet dinh: them 2 contract DEX vao allowlist cho HECO Chain/HTX

**Boi canh**: khi kiem tra provenance cho HECO Chain/HTX (lo 2, ung vien thu 4
theo thu tu da khai bao: Lendhub, THORChain-2, Popsicle, HECO, EasyFi), phat
hien phan lon tien danh cap ($63M) **nam im** tai 1 dia chi holding, chi thuc
su rua qua Tornado Cash **tu thang 3/2024** (~4 thang sau vu hack,
2023-11-22) - ngoai window tracking thuc te (`time_horizon_hours: 72` trong
`configs/data_N30.yaml`). Tuy nhien, 1 nhanh vi phu (duoc seed cap gas de
phan tan rieng 619,000 USDC danh cap) co goi truc tiep toi 2 DEX router THAT,
DA VERIFY, trong **cung ngay voi vu hack**:

- `0x881d40237659c251811cec9c364ef91dc08d300c` — **MetaSwap**, router
  aggregator CHINH THUC cua MetaMask Swaps. Xac nhan qua Etherscan API
  `getsourcecode` (ContractName="MetaSwap", verified source), cong voi
  tai lieu ho tro chinh thuc cua MetaMask ve tinh nang "MetaMask Swaps"
  (aggregator noi bo).
- `0x5550d13389bb70f45fcef58f19f6b6e87f6e747d` — **SushiSwap:
  RouteProcessor3_2**. Xac nhan qua Etherscan API `getsourcecode`
  (ContractName="RouteProcessor3_2", verified source) - phien ban ke
  nhiem cua RouteProcessor2 (contract SushiSwap bi khai thac 04/2023,
  dia chi KHAC: `0x044b75f554b886a065b9567891e45c79542d7357`).

**Quyet dinh**: THEM ca 2 vao `dex_allowlist` cua `configs/data_N30.yaml` +
muc tuong ung trong `metadata/protocol_map_N30.yaml`.

**Ly do (theo dung quy tac v7)**: ca 2 contract nay nam **TRUC TIEP trong
dong tien THAT cua CHINH incident dang xu ly** (HECO Chain/HTX) - seed goi
truc tiep (qua 1 hop trung gian la vi phu nhan 1 loai token cu the, KHONG
phai "hub gap o do sau qua frontier expansion khong lien quan"), dung tieu
chi (a) cua quy tac v7. Da kiem tra tieu chi (b) (khong doi ket qua v1.0)
truoc khi quyet dinh cuoi cung - xem muc kiem tra duoi day.

**QUAN TRONG - quyet dinh nay KHONG phu thuoc vao viec dat N=30**: viec them
2 contract tren duoc thuc hien DU HECO co duoc tinh la "dat cong provenance
day du" hay khong - day la quyet dinh ve TINH DUNG cua allowlist (phan anh
dung dong tien THAT cua HECO), tach biet khoi quyet dinh rieng ve
`endpoint_confirmed` cua HECO (xem muc duoi, van la **False**).

## SHA-256 sau khi sua (2026-10-15)

- `configs/data_N30.yaml`: `0aa832973b3c7e57e2247054b00b9c25cd33f63805a7963a6bf54735621a6a20`
- `metadata/protocol_map_N30.yaml`: `8f567f17eeebc0d3ca2c428b91707dfd57e38fb18fe9033775d4cc65843b3082`

## Ket qua kiem tra dong nhat sau khi them allowlist

Xem ket qua chi tiet (pass/fail, so sanh 612 negative v1.0, bang diff cho
N20/lo1 neu co) trong phan bao cao chinh tiep theo cung ngay - thuc hien
NGAY SAU khi ghi file nay, truoc khi tiep tuc mining HECO.

## HECO Chain/HTX: endpoint_confirmed = False (quyet dinh cuoi)

Du da them allowlist, HECO VAN duoc ghi `endpoint_confirmed=False` vi:
- Nhanh DEX (MetaSwap/RouteProcessor3_2) CHI la 1 phan nho gia tri tong
  thiet hai (619,000 USDC trong tong ~$86.6M, ty le xem bang chi tiet o
  bao cao cuoi).
- Rua tien CHINH (qua Tornado Cash, >$100M) xay ra NGOAI window tracking
  72h, khong duoc builder bat duoc.
- Danh dau: "trace 72h chu yeu la nhanh phu, rua tien chinh ngoai cua so" -
  dua vao CUNG danh sach bang chung YEU voi Cork Protocol va Uranium
  Finance trong bao cao tong ket cuoi dot mo rong.
