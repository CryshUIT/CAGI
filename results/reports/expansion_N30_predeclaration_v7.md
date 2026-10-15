# Khai bao truoc — Mo rong N=20 -> N=30 — PHIEN BAN 7 (2026-10-14)

## Changelog so voi v1-v6

v1-v6: giu nguyen. **v7 (file nay)**: chot quy tac "allowlist completion"
chat che hon, quyet dinh KHONG them gi lan nay, them sensitivity moi.

## Lam ro quy tac "allowlist completion" (thay the dinh nghia long leo o v4)

Chi duoc them 1 contract vao allowlist N30 KHI VA CHI KHI CA 2 dieu kien
sau DEU dung:

1. Contract do nam **TRUC TIEP trong dong tien DA XAC MINH cua CHINH
   incident dang xu ly** (khong phai "gap o do sau X khi mo rong frontier"
   — vd KyberSwap cua Prisma la seed GOI TRUC TIEP, khong phai dia chi gap
   tinh co o hop thu 4-6).
2. Viec them KHONG lam doi dau ra cua 15 incident v1.0 + 536 negative da
   freeze (kiem tra dong nhat Tang 1 PHAI sach truoc khi chap nhan).

**KHONG duoc them 1 contract chi vi no la "hub" gap o do sau 4-6 khi mo
rong frontier** (du la router/bridge/vault da verify) — day la nguyen nhan
chinh gay bung no (Inverse, va tiem an o Radiant qua 1inch V6), **KHONG
PHAI dong tien cua chinh incident dang xu ly ma la giao diem ngau nhien
trong do thi giao dich chung**.

## Quyet dinh LAN NAY: KHONG them gi

- **KHONG** them 1inch: Aggregation Router V6 (cham `radiant_capital_arbitrum_2024`
  — incident N=15 DA FREEZE, vi pham dieu kien 1: day la hub gap o do sau,
  khong phai dong tien THAT cua Radiant ma la giao diem voi 1 DEX pho bien).
- **KHONG** them Polygon (Matic): ERC20 Bridge, Bancor: Master Vault V3
  (cham Inverse Finance o do sau 4-6, vi pham dieu kien 1 tuong tu).
- **KHONG** them bat ky vi CEX/market-maker nao (Hotbit, HTX, FTX,
  Wintermute) — day khong phai "sink" giao thuc, khong bao gio hop le de
  allowlist du o muc do sau nao.

KyberSwap Meta Aggregation Router v2 (da them o v4, cho Prisma Finance) VAN
GIU NGUYEN — dat ca 2 dieu kien (seed Prisma goi TRUC TIEP swap() toi do,
da kiem tra dong nhat sach voi 15+536).

## File hanh che moi

`results/reports/known_builder_limitations.md` — ghi nhan gioi han co he
thong cua builder (bung no qua hub ngoai allowlist), KHONG sua du lieu
freeze. Xem file do cho chi tiet day du.

## Sensitivity moi khai bao truoc

**Bo Inverse Finance** (ngoai N=19 bo Cork da co) — ly do: trajectory cuc
lon (11.592 action) co the chi phoi ket qua pooled khong tuong xung voi 1
incident. Bao cao song song: N=20 (chinh, N20 gốc), N=19 (bo Cork), **N
-1-Inverse (bo Inverse, nếu Inverse nam trong tap N cuoi)**, và tổ hợp nếu
ca Cork+Inverse đều bị loại trong 1 sensitivity gộp.

## Phan bo n_actions (cap nhat lien tuc, bao cao tai thoi diem nay)

Se tinh lai chinh xac o buoc freeze cuoi cung (sau khi het lo 2), kem min/
trung vi/max va danh sach incident >1.000 action.

## Buoc tiep theo

1. Hoan tat mining Uranium + 0xInfini (lo 1, dang tam dung).
2. Feature build (config N30, co chot chan), test tai tao (gioi han 20
   incident N20 cu phai khop CHINH XAC — tru Hedgey da duoc chap nhan
   khac biet o v4), pytest toan bo.
3. Lo 2: Lendhub, THORChain-2, Popsicle, HECO, EasyFi (theo dung thu tu da
   khai bao v3), roi CeFi (Kronos, BitMart, Liquid) neu con cho.
4. Freeze registry, tinh SHA-256 manifest, bao cao mo ta. KHONG chay model.
