# CAGI-ED

**Explainable Early Detection of Cross-Chain DeFi Laundering from Temporal Motifs** — phát hiện sớm hoạt động rửa tiền DeFi xuyên chuỗi từ *prefix* (đoạn đầu) của quỹ đạo giao dịch, trước khi tiền tới điểm đến cuối cùng.

## 🖥️ SOC Dashboard — chạy production / deploy

Dashboard trực quan hoá kết quả model (36 incident lịch sử, out-of-fold)
dưới dạng Security Operations Center: biểu đồ xác suất phát hiện theo
thời gian, timeline giao dịch, flow graph, giải thích SHAP + AADAPT.
Chạy hoàn toàn **local, không public internet, không gọi API on-chain
khi phục vụ request** — chỉ cần Python + Node một lần để build.

### Yêu cầu

- Python 3.11+ (đã cài `fastapi`, `uvicorn` — xem `requirements.txt`/`requirements.lock` nếu có, hoặc `pip install fastapi uvicorn pandas numpy scikit-learn xgboost`)
- Node.js 18+ và npm (chỉ cần lúc build frontend, không cần lúc chạy)

### Chạy lần đầu (build + start)

**macOS/Linux/Git Bash (có `make`):**

```bash
make demo
```

**Windows PowerShell (không có `make` sẵn):**

```powershell
python scripts\dashboard\generate_oof_dashboard_data.py   # sinh du lieu (chi can 1 lan)
cd dashboard\frontend; npm install; npm run build; cd ..\..
python dashboard\backend\app.py
```

Sau khi thấy `Application startup complete`, mở trình duyệt:
**http://127.0.0.1:8420**

### Các lần chạy sau (đã build sẵn)

Nếu `data/dashboard/incidents.json` và `dashboard/frontend/dist/` đã tồn
tại (thường có sẵn sau lần build đầu, đã commit kèm repo), chỉ cần:

```powershell
python dashboard\backend\app.py
```

### Chạy nền lâu dài (giữ server sống sau khi đóng terminal)

```powershell
# Windows: chạy nền bằng Start-Process
Start-Process python -ArgumentList "dashboard\backend\app.py" -WindowStyle Hidden
```

```bash
# macOS/Linux: nohup hoặc systemd/pm2 tuỳ hạ tầng
nohup python dashboard/backend/app.py > dashboard.log 2>&1 &
```

### Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `only one usage of each socket address` (port 8420 đang bận) | Đã có 1 tiến trình backend chạy sẵn | Mở thẳng `http://127.0.0.1:8420` (server cũ có thể vẫn đang chạy tốt); nếu muốn khởi động lại: PowerShell chạy `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8420).OwningProcess -Force` rồi chạy lại |
| `make: command not found` | Windows không có `make` mặc định | Dùng khối lệnh PowerShell ở trên thay cho `make demo` |
| Trang trắng / lỗi 404 khi bấm vào 1 incident | `dashboard/frontend/dist/` chưa được build | Chạy lại `cd dashboard/frontend && npm install && npm run build` |

### Phạm vi & giới hạn (quan trọng khi bàn giao)

- Chỉ phân tích **36 incident lịch sử** đã có sẵn kết quả (out-of-fold) —
  **không** gọi mạng, **không** giám sát thời gian thực, **không** dự
  đoán incident mới (mục "New Analysis" hiển thị rõ "chưa bật").
- Server chỉ bind `127.0.0.1` (localhost) — muốn truy cập từ máy khác
  trong mạng LAN/internet cần tự cấu hình thêm (đổi host trong
  `dashboard/backend/app.py`, cân nhắc thêm xác thực) — **không khuyến
  nghị expose thẳng ra internet** vì đây là bản demo nghiên cứu, chưa
  có lớp bảo mật/xác thực người dùng.
- Chi tiết kiến trúc, nguồn dữ liệu, giới hạn kỹ thuật: xem
  `dashboard/README.md`, `AUDIT.md`, `PROGRESS.md`.

## Bối cảnh & đóng góp

Các hệ thống truy vết rửa tiền DeFi hiện có (ví dụ AMLGuard, ISSTA'26) tập trung **trace toàn bộ quỹ đạo** từ seed đã biết đến điểm đến cuối cùng — tức chỉ hoạt động *sau khi* đã biết điểm đến. CAGI-ED chuyển trọng tâm sang bài toán **cảnh báo sớm**: chỉ quan sát một **phần đầu (prefix)** của quỹ đạo — trước khi điểm đến được xác nhận — và dự đoán mức độ rủi ro dựa trên các *typed temporal motif* (mô-típ hành vi có kiểu, theo thời gian: bridge→swap, split/merge, peel-chain...). Ground truth do nhóm **tự trace và tự gán** từ dữ liệu on-chain công khai, đối chiếu báo cáo điều tra công khai độc lập — không sao chép nhãn từ bất kỳ dataset độc quyền nào.

## Kết quả chính (chính thức, N=30, freeze v3 — `results/tables/evaluation_N30_main_table.csv`)

**RQ1 — M1 (typed temporal motif) có vượt B3 (untyped/flat) không?**
Leave-one-incident-out, 30 fold, bootstrap CI 95% mức incident (n_boot=2000, seed=42):

| Model | Mean PR-AUC | 95% CI |
|---|---|---|
| B0 (majority baseline) | 0.0543 | [0.0468, 0.0676] |
| B1 (rule-based) | 0.5148 | [0.4399, 0.5933] |
| B2 (bag-of-actions) | 0.0752 | [0.0610, 0.0987] |
| B3 (untyped/flat) | 0.7543 | [0.6449, 0.8574] |
| **M1 (typed motif)** | **0.7762** | **[0.6567, 0.8979]** |

→ M1 có PR-AUC điểm cao hơn B3, nhưng **CI 95% chồng lấn lớn ở N=30** —
**chưa đủ bằng chứng thống kê để kết luận M1 vượt B3** (xem thảo luận
trong `results/reports/`); đóng góp chính của M1 hiện được định vị lại
ở khả năng diễn giải (typed motif → SHAP → AADAPT, xem phần Dashboard)
hơn là ưu thế PR-AUC tuyệt đối.

**RQ2 — Model có phát hiện được sớm (từ prefix) không?**
PR-AUC (30 fold, bootstrap CI) theo % quỹ đạo đã quan sát — `results/tables/evaluation_N30_table3b_ratio_checkpoints.csv`:

| Mốc prefix | 25% | 50% | 75% | 100% |
|---|---|---|---|---|
| M1 PR-AUC | 0.8415 | 0.9096 | 0.9330 | 0.9282 |
| B3 PR-AUC | 0.7534 | 0.8421 | 0.8426 | 0.7884 |

→ M1 phát hiện tốt ngay ở 25% quỹ đạo đầu tiên (PR-AUC 0.84) và duy trì
khoảng cách PR-AUC dương với B3 ở **mọi** mốc prefix (+0.07 đến +0.14) —
bằng chứng rõ cho tính khả thi early-detection, dù RQ1 (pooled 100%,
N nhỏ) chưa tách biệt rõ 2 model.

### Mở rộng N=36 (exploratory/post-hoc, không thay thế kết quả N=30 ở trên)

Đã mở rộng thêm 6 incident mới (2023–2024) qua cùng pipeline, train lại
LOIO trên 36 group: pooled PR-AUC out-of-fold **M1=0.7790, B3'=0.7271**
(nhất quán với N=30, không đổi kết luận). Model đóng băng từ bước này
(`M1_FROZEN_final_N36.pkl`, `B3prime_FROZEN_final_N36.pkl`) được dùng
để phục vụ **SOC Dashboard** ở trên. Chi tiết: `results/reports/extra_v4/`.

## Cấu trúc dataset chính thức (N=30, freeze v3)

| | Giá trị |
|---|---|
| Incident positive | 30 (2021–2025, báo cáo công khai CertiK/SlowMist/Halborn/Rekt News...) |
| Hard-negative + control dùng được | 1.097 trajectory âm |
| Tổng prefix row | 5.973 (48 feature/dòng) |
| Chain | Ethereum (17), BSC (7), Arbitrum (6) |
| Bridge/mixer đã verify on-chain | Ronin Bridge, QBridge (Qubit), FEG SmartBridge, BSC Token Hub, LI.FI Diamond, Stargate (LayerZero), Across Protocol SpokePool, Multichain (AnySwap), Wormhole Token Bridge, Tornado Cash Router/TornadoProxyLight (mixer) |

## Cấu trúc repo

```
cagi-ed/
├── src/            # Pipeline chính: collect → normalize → trajectories → features → models → evaluation
├── configs/        # Cấu hình model/feature/data (data_N30.yaml, data_N37.yaml, model.yaml, features.yaml)
├── metadata/       # incident_registry_N30/N37.csv, hard_negative_registry*.csv, protocol_map.yaml, split_manifest.json
├── data/           # Dataset đã xử lý (raw cache + *.parquet không commit — quá lớn, xem .gitignore)
├── results/        # tables/, figures/, reports/ — toàn bộ số liệu/hình/báo cáo đã freeze (N=30 + mở rộng N=36)
├── dashboard/      # SOC Dashboard (FastAPI + React) — xem mục deploy ở trên
├── scripts/        # Script tái tạo/mining/đánh giá/dashboard
├── tests/          # 255 test (pytest tests/ -v)
```

## Cách chạy / tái lập (kết quả nghiên cứu N=30)

```bash
pip install -r requirements.lock              # version chinh xac da dung de tao ket qua freeze
python scripts/run_evaluation_N30_v3.py       # tai tao evaluation_N30_main_table.csv (RQ1) + cac bang N30 khac — HOAN TOAN OFFLINE (dung cache data/raw/, data/processed/*.parquet co san)
python -m pytest tests/ -v                     # xac nhan 255/255 test pass (gom ca test dashboard)
```

Lưu ý: `scripts/reproduce_main.sh` là script cũ hơn, tái tạo bản freeze
**N=15** ban đầu (`results/tables/main_table.csv`) — vẫn còn trong repo
để tham khảo lịch sử, nhưng **không phải** nguồn của bảng N=30 ở trên.

**Không cần gọi API on-chain nào** để tái lập kết quả từ dữ liệu đã cache sẵn. Yêu cầu API key chỉ cần nếu muốn thu thập dữ liệu mới từ đầu — không cần cho việc tái lập số liệu đã công bố.

## Nguồn dữ liệu & đạo đức

Toàn bộ dữ liệu on-chain **công khai** (Ethereum/BSC/Arbitrum, qua Etherscan/BscScan API). Nhãn do nhóm **tự trace và tự gán**, đối chiếu báo cáo điều tra công khai (CertiK, SlowMist, Halborn...). **Không dùng ground truth AMLGuard** — dataset của họ chưa công khai tại thời điểm dự án bắt đầu (README AMLGuard ghi "release upon acceptance"); chỉ tham khảo seed list của họ (tên/chain/thời gian) làm gợi ý candidate ban đầu. Không deanonymize danh tính ngoài đời của bất kỳ ai.
