# Ke hoach phan tich N=30 — PHIEN BAN 2 (2026-10-15)

**CHI la ke hoach/pre-declaration — CHUA chay bat ky model/RQ1/RQ2 nao.**

## Changelog so voi v1

- **v1**: `results/reports/analysis_plan_N30.md` (SHA-256:
  `0b44c9942ecd355c1302ad7ef5e678ada7440e1530a922b86d79eb4da75e2fe2`).
  **GIU NGUYEN, khong sua ngam.**
- **v2 (file nay)**: LAM RO lai dinh nghia va danh sach cho sensitivity
  (c) va cho "bang chung yeu" (muc dung o bao cao tom tat, khong phai
  trong v1 nhung lien quan truc tiep muc tieu RQ2 cua sensitivity (d)),
  sau khi dung CO CHE (khong phai suy doan) de kiem tra lai TOAN BO 30
  incident duoi config_N20.yaml va config_N30.yaml (chi dung cache, 0
  quota). **Giao thuc phan tich CHINH (model/split/metric/kiem dinh/4
  moc cong don) KHONG DOI MOT CHU NAO so voi v1. VAN DUNG DUNG 4
  sensitivity (a)(b)(c)(d), KHONG them sensitivity moi.**

## Phat hien dan den sua (bang chung)

Chay `expand_and_build_trajectory` cho TOAN BO 30 incident duoi CA
`configs/data_N20.yaml` VA `configs/data_N30.yaml` (chi dung cache
`do_collect=False`, khong goi API), so sanh `n_actions` va CHUOI
`event_type` day du (khong chi so luong):

| incident_id | n20 | n30 | khac |
|---|---|---|---|
| hedgey_finance_2024 | 662 | 755 | **CO** |
| prisma_finance_2024 | 68 | 70 | **CO** |
| uranium_finance_2021 | 39 | 64 | **CO** |
| popsicle_finance_2021 | 866 | 980 | **CO** |
| heco_htx_2023 | 1555 | 1557 | **CO** |
| easyfi_2021 | 16557 | 16560 | **CO** |
| (24 incident con lai) | = | = | khong |

Cach ly tung dia chi moi them (KyberSwap, MetaSwap, RouteProcessor3_2,
TornadoProxy) bang `dataclasses.replace()` tren `TrajectoryConfig` tu
baseline `data_N20.yaml`, xac nhan dung 1 nguyen nhan cho moi truong
hop:

| incident_id | nguyen nhan | co phai "dung truc tiep" (du kien tu dau) khong |
|---|---|---|
| prisma_finance_2024 | KyberSwap | CO - them chinh vi Prisma |
| popsicle_finance_2021 | TornadoProxy | CO - them chinh vi Popsicle |
| heco_htx_2023 | SushiSwap RouteProcessor3_2 (MetaSwap rieng le KHONG gay doi) | CO - them chinh vi HECO |
| **hedgey_finance_2024** | KyberSwap | **KHONG** - KyberSwap them cho Prisma, Hedgey la ANH HUONG PHU (cross-contamination) |
| **uranium_finance_2021** | TornadoProxy | **KHONG** - TornadoProxy them cho Popsicle, Uranium la ANH HUONG PHU |
| **easyfi_2021** | MetaSwap+RouteProcessor3_2 | **KHONG** - them cho HECO, EasyFi la ANH HUONG PHU |

### Sua 1 khang dinh SAI truoc day

Comment cu trong `configs/data_N30.yaml` (dong KyberSwap) ghi: *"da thay
o Hedgey Finance truoc do (N20, chua them vi khong anh huong ket qua
Hedgey)"*. Kiem tra lai bang CO CHE (khong phai suy doan) cho thay
khang dinh nay **SAI** — KyberSwap THAT SU doi Hedgey tu 662 len 755
action (+93, ~14%). Da sua comment trong `configs/data_N30.yaml`
(2026-10-15) de ghi nhan dung su that, **KHONG go KyberSwap khoi
allowlist** (van can thiet cho Prisma, da qua kiem tra khong doi 612
negative v1.0 — chi nam trong danh sach sensitivity (c) nhu moi incident
khac bi anh huong).

### Tai sao Uranium nam trong danh sach (c) — giai thich co che

`allowlist` trong `TrajectoryConfig` la **TOAN CUC cho ca config**,
khong gan rieng theo incident. Khi them `TornadoProxy` de phuc vu dung
tieu chi v7 cho Popsicle Finance (dia chi nam trong dong tien THAT cua
Popsicle), dia chi nay cung tro thanh "counterparty_allowed=True" cho
**BAT KY incident khac** ma frontier cua no TINH CO cham toi cung dia
chi — bat ke co lien quan noi dung toi Popsicle hay khong. Uranium
Finance (dung Uniswap V2 lam dau ra, khong lien quan Tornado Cash/
TornadoProxy ve noi dung) tinh co co 1 nhanh frontier cham TornadoProxy
o do sau nao do, va cac giao dich do TRUOC KIA bi loc boi `value_share`
(qua nho de duoc giu, giong co che "bot phat tan nhieu giao dich nho"
da phat hien o `beanstalk_hnc20007` truoc day) nhung SAU KHI them
TornadoProxy, cac giao dich nay duoc giu lai VI counterparty duoc
allowlist (bo qua kiem tra value_share hoan toan) — tang tu 39 len 64
action (+25). Day la **CUNG 1 CO CHE** da giai thich cho Hedgey/EasyFi
o tren, chi khac incident bi anh huong phu.

## Sensitivity (c) — danh sach CHINH THUC (sua, thay 2 bang 6 incident)

**Thay cho danh sach 2 incident (hedgey_finance_2024,
uranium_finance_2021) trong v1**, danh sach DAY DU va DUNG (xac nhan
bang rebuild toan bo 30 incident, khong con incident nao khac):

`hedgey_finance_2024, prisma_finance_2024, uranium_finance_2021,
popsicle_finance_2021, heco_htx_2023, easyfi_2021` — **6 incident**.

## Sensitivity (a) — n_actions <= 2

Ap dung CHO DUNG 1 incident: `cork_protocol_2025` (n_actions=1). Da ra
soat toan bo 30 incident, khong co incident nao khac <=2.

## Sensitivity (b) — n_actions > 5.000

Ap dung cho DUNG 2 incident: `inverse_finance_2022_jun` (11.592),
`easyfi_2021` (16.557-16.560 tuy cau hinh/lan build). Da ra soat toan
bo 30, khong co incident thu 3 nao >5.000 (ke tiep la heco_htx_2023 voi
1.555-1.557, con xa nguong).

## Co che "bang chung yeu" — DINH NGHIA CO HOC (sua lai cho dong nhat)

**Quy tac duy nhat, ap dung CO HOC cho ca 30 incident (khong suy doan
tung ca)**:

```
weak_evidence(incident) = (endpoint_confirmed == False)
                           AND (mixer_families KHAC rong/null)
```

Nghia la: incident duoc gan co "bang chung yeu" KHI VA CHI KHI pipeline
KHONG tu dong xac nhan endpoint (`endpoint_confirmed=False`) **VA** co
mot gia tri CU THE duoc dien vao truong `mixer_families` cua registry
(bao cao hoac on-chain co de cap toi 1 mixer/exit-service, du khong
duoc tu dong xac nhan) — phan biet voi truong hop KHONG co bat ky de
cap mixer nao ca (vd Cork/Ronin/Qbridge/Hedgey — "khong dat cong" vi
thieu du lieu/doi do allowlist, KHAC ve ban chat voi "co bao cao mixer
nhung khong xac nhan duoc").

**Ap dung quy tac nay cho ca 30 incident, ket qua (SUA so voi bao cao
tom tat truoc)**:

`hackerdao_2022, uranium_finance_2021, thorchain2_2021,
popsicle_finance_2021, heco_htx_2023, easyfi_2021` — **6 incident**.

**Thay doi so voi bao cao tom tat 2026-10-15 truoc do**:
- **LOAI BO** `cork_protocol_2025` khoi danh sach "bang chung yeu" —
  Cork KHONG co gia tri nao trong `mixer_families` (truong hop "trajectory
  qua ngan de xac nhan", KHAC ve ban chat voi "co bao cao mixer nhung
  khong xac nhan duoc").
- **THEM** `easyfi_2021` vao danh sach — truong `mixer_families` cua
  EasyFi co gia tri (mo ta bao cao goc "dark pool" khong xac dinh duoc
  ten cu the), nen theo quy tac co hoc (chi kiem tra "khac rong/null",
  khong xet do cu the/ro rang cua noi dung) VAN duoc tinh la "co bao cao
  nhung chua xac nhan".
- Da sua 1 khoang trong du lieu: `thorchain2_2021` truoc do co
  `mixer_families` de TRONG (NaN) trong `incident_registry_N30.csv` du
  phan "notes" co mo ta Tornado Cash — day la SAI SOT nhap lieu (khong
  phai quyet dinh), da dien lai cho khop voi notes TRUOC KHI tinh lai
  quy tac tren (neu khong sua, thorchain2_2021 se SAI bi loai khoi danh
  sach du van "co bao cao mixer" theo chinh noi dung notes cua no).

## Giao thuc chinh, 4 moc cong don, dinh nghia (a)(b)(d) con lai

**KHONG DOI so voi v1** — xem `analysis_plan_N30.md` muc "Giao thuc
chinh", "Moc cong don", va dinh nghia (d) (RQ2 chi tren incident co
endpoint la mixer). Chi (c) va dinh nghia "bang chung yeu" duoc lam ro
lai o file nay.

## Xac nhan khong them sensitivity moi

File nay CHI lam ro dinh nghia/danh sach cho (c) va cho co che gan co
"bang chung yeu" — **VAN DUNG DUNG 4 sensitivity (a)(b)(c)(d) da khai
bao trong v1, khong them, khong doi giao thuc phan tich chinh**.

---
*(SHA-256 cua chinh file v2 nay: xem
`results/reports/analysis_plan_N30_v2_selfhash.json`)*
