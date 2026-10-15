# Khai bao truoc — Mo rong N=20 -> N=30 — PHIEN BAN 4 (2026-10-14)

## Changelog so voi v1/v2/v3

- v1: `expansion_N30_predeclaration.md` (hash `3fdb2606...8794`). GIU NGUYEN.
- v2: `expansion_N30_predeclaration_v2.md` (ghi hash plan.md). GIU NGUYEN.
- v3: `expansion_N30_predeclaration_v3.md` (sap lai thu tu 13 ung vien +
  victim_type + chain_primary). GIU NGUYEN.
- **v4 (file nay)**: quyet dinh xu ly phat hien "allowlist completion" lam
  doi trajectory Hedgey (662->755 action) khi them KyberSwap Meta
  Aggregation Router v2 vao allowlist N30.

## Quyet dinh: chon huong (1) — chap nhan so moi, ghi quy tac "allowlist completion"

1. **Allowlist N30 la MOT cau hinh DUY NHAT cho toan dataset** — khong co
   allowlist rieng theo incident. Khi 1 contract duoc xac minh qua
   provenance cua BAT KY ung vien nao, no ap dung CHO TOAN BO dataset dang
   build boi config do (nhat quan, khong "chinh tay" rieng tung incident).
2. Chi them contract vao allowlist **VI LY DO PROVENANCE** (contract nam
   trong dong tien THAT cua 1 ung vien dang xu ly, co nhan/nguon xac minh
   doc lap). KyberSwap Meta Aggregation Router v2
   (`0x6131b5fae19ea4f9d964eac0408e4408b66337b5`): nguon da ghi trong
   `protocol_map_N30.yaml` — nhan Etherscan "KyberSwap: Meta Aggregation
   Router v2" (contract da verify). **Nguon chinh thuc KyberSwap**: trang
   GitHub `KyberNetwork/kyberswap-dapp-contracts` liet ke dia chi
   MetaAggregationRouterV2 tren nhieu chain — CHUA tim duoc 1 trang docs
   chinh thuc rieng liet ke dia chi theo chain nhu Uniswap (`docs.kyberswap.com`
   khong co trang "deployments" tuong duong da kiem tra duoc) — **giu
   nguyen muc do xac minh la "nhan Etherscan + contract verified", GHI RO
   gioi han nay**, tuong tu truong hop Universal Router v1.2 variant o N20.
3. **Moi lan them 1 contract vao allowlist, BAT BUOC chay kiem tra dong
   nhat theo 2 TANG**:
   - **Tang 1 (ranh gioi CUNG, khong duoc doi)**: 15 incident v1.0 (freeze
     goc) + 536 hard-negative "quy tac chinh" cua v1.0. Trajectory VA
     feature **PHAI GIONG HET**. **Bat ky khac biet nao: DUNG**, bao cao,
     khong tu sua.
   - **Tang 2 (ranh gioi MEM, duoc phep doi co kiem soat)**: 5 incident da
     them o N=20 (Zunami, Onyx, Beanstalk, Hedgey, Cork) + hard-negative cua
     chung (125 "quy tac chinh" + 46 "v2_complexity"). Khac biet **DUOC
     CHAP NHAN** nhung PHAI lap bang diff day du (n_actions, co truoc/sau,
     endpoint_confirmed, so prefix row, so dong positive, action them/mat
     cu the) TRUOC khi tiep tuc — **KHONG tu sua tay**.
4. Ket qua N=20 DA FREEZE (dung config N20, khong co KyberSwap) **GIU
   NGUYEN lam tham chieu, KHONG ghi de**. Khi bao cao N=30 cuoi cung, moc
   cong don "N=20" se duoc **TINH LAI duoi config N30** (co KyberSwap) rieng
   biet voi ban N20 goc da freeze — ca hai se duoc trinh bay canh nhau, ghi
   ro dung config nao.
5. **Sensitivity moi khai bao truoc**: bo cac incident co trajectory **DOI
   do allowlist completion** (hien tai: `hedgey_finance_2024`) — bao cao
   song song co/khong co incident nay, tuong tu sensitivity N=19 bo Cork.

## Quy tac dung GIU NGUYEN (khong doi)

Dich N=30, sang toi da 20 ung vien moi, N cuoi = 20+so dat, khong ha chuan,
khong mo rong them sau dot nay, khong chon/loai theo ket qua mo hinh.

## Buoc tiep theo

a. Xuat bang diff Hedgey.
b. Kiem tra dong nhat Tang 1 (536 negative v1.0) VA Tang 2 (125+46 negative
   N20) duoi config N30.
c. Neu Tang 1 sach: tiep tuc Phase 2 theo thu tu da khai bao (v3). Neu Tang
   1 co khac biet: DUNG, bao cao.
