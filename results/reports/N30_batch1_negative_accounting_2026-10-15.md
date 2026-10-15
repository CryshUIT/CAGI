# Doi chieu so negative trong features_v2_N30.parquet va features_v2_N20.parquet (2026-10-15)

**Phuong phap**: doc truc tiep tu parquet da build (`source_id`, `kind`,
`group_id`), loai trung lap theo prefix (lay 1 dong/trajectory), roi phan
loai tung `source_id` theo file registry GOC (chua merge) ma no xuat hien
lan dau (vi.0 main/v2c, N20 main/v2c moi, N30 batch1 main/v2c moi). Khong
suy doan - moi dong deu duoc xac dinh bang truy van tap hop (set
membership) voi cac file CSV goc tren dia.

## features_v2_N30.parquet (dot mo rong N=20 -> N=30, lo 1)

Tong trajectory: 956 (positive=25, negative=931).

| Nguon | So luong | Giai thich |
|---|---|---|
| v1.0 hard-negative chinh (536 dong goc) | 500 | 36 dong rong/khong dung duoc (`rong` trong code = trajectory_len=0) |
| v1.0 hard-negative v2_complexity (110 dong goc) | 107 | 3 dong rong |
| N20 hard-negative chinh moi (125 dong) | 122 | 3 dong rong |
| N20 hard-negative v2_complexity moi (46 dong) | 44 | 2 dong rong |
| N30 lo 1 hard-negative chinh moi (125 dong: 75+50) | 122 | 3 dong rong |
| N30 lo 1 hard-negative v2_complexity moi (31 dong) | 31 | 0 dong rong |
| hard-negative-control goc (5 incident v1.0: ronin/qbridge/feg/deltaprime/bsc_token_hub) | 5 | khong co dong rong |
| **Tong** | **931** | **Khop CHINH XAC voi so negative trong build log, 0 dong KHONG XAC DINH** |

**Khong co "68 negative du"** — gia thiet nay trong cau hoi khong dung voi
du lieu thuc te; 931 da duoc giai thich day du boi 7 nguon tren, khong con
phan du nao can lam ro.

So dong rong theo nguon (de tham khao, khong anh huong ket qua cuoi):
v1.0 main 36/536, v1.0 v2c 3/110, N20 main 3/125, N20 v2c 2/46, N30 batch1
main 3/125, N30 batch1 v2c 0/31. Tong 47 dong rong tren tong 973 dong raw
(536+110+125+46+125+31), khop voi 2 log mining: "[hard_negative_mined]
744/764 usable (rong: 20)" + "[hard_negative_mined_v2_complexity] 182/187
usable (rong: 5)" sau khi loai 22 dong thuoc `circulate_2023` (eval_tier
auxiliary, bi loai khoi main-round combined truoc khi tinh "764 xem xet";
973 - 22 (circulate trong main) = 951, khong khop 764+187=951 ✓.

## features_v2_N20.parquet (dot mo rong N=15 -> N=20)

Tong trajectory: 798 (positive=20, negative=778).

| Nguon | So luong |
|---|---|
| v1.0 hard-negative chinh (536 dong goc) | 500 |
| v1.0 hard-negative v2_complexity (110 dong goc) | 107 |
| N20 hard-negative chinh moi (125 dong) | 122 |
| N20 hard-negative v2_complexity moi (46 dong) | 44 |
| hard-negative-control goc | 5 |
| **Tong** | **778** |

**LUU Y QUAN TRONG**: cau hoi nhac so **752** cho N20 - kiem tra truc
tiep tu `features_v2_N20.parquet` (file da freeze, dang dung lam baseline
so sanh cho ca batch 1 N30) cho ra **778 negative** (va 798 trajectory
tong, 4247 prefix row), KHONG phai 752. Da kiem tra lai nhieu lan, khong
tim thay cach tinh nao trong code/log cho ra dung so 752. Day co the la
nham lan/nho sai tu truoc - BAO CAO THANG theo yeu cau, khong tu dieu
chinh so cho khop 752. Neu can, co the kiem tra lai nguon cua so 752 (vi
du: co phai dang nham voi mot con so khac nhu "752" o buoc trung gian
nao do truoc khi lam sach "rong"?) - nhung voi du lieu hien co tren dia,
778 la so dung, khop 100% voi 5 nguon tren.

## Vong mine v2_complexity co yield khong deu (N30 lo 1)

Xem chi tiet va giai thich nguyen nhan (thu tu xu ly + chia se mining
contract qua `global_excluded`) trong
`results/reports/known_builder_limitations.md` (muc moi them 2026-10-15).
