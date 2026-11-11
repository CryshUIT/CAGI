# CAGI-ED SOC Dashboard (Phần 1 — 36 incident lịch sử)

Dashboard local, chỉ hiển thị kết quả **đã có sẵn** (out-of-fold, 36
incident dùng để đóng băng model) — không gọi mạng, không huấn luyện lại,
không bịa dữ liệu. Xem `AUDIT.md` ở gốc repo để biết chi tiết nguồn dữ
liệu từng mục.

## Khởi động nhanh

**macOS/Linux (hoặc Git Bash trên Windows) — có `make`:**

```bash
# Từ gốc repo:
make demo
```

**Windows PowerShell — KHÔNG có `make` sẵn, chạy 3 lệnh sau (từ gốc repo):**

```powershell
python scripts\dashboard\generate_oof_dashboard_data.py
cd dashboard\frontend; npm install; npm run build; cd ..\..
python dashboard\backend\app.py
```

Cả 2 cách đều: (1) sinh `data/dashboard/incidents.json` (nếu đã có cache
`data/dashboard/_loio_shap_cache.pkl` từ lần chạy trước, bước này CHỈ
lắp ráp lại JSON — vài giây; nếu chưa có cache, chạy LOIO+SHAP thật từ
đầu — có thể mất 15-20 phút), (2) build frontend ra static files,
(3) chạy FastAPI phục vụ cả API lẫn frontend tại
**http://127.0.0.1:8420** (chỉ bind localhost).

Nếu `data/dashboard/incidents.json` và `dashboard/frontend/dist/` đã có
sẵn (đã chạy 1 lần trước đó), chỉ cần chạy bước 3 (`python dashboard\backend\app.py`
hoặc `cd dashboard/backend && python app.py`).

Chế độ phát triển (hot reload frontend): chạy `python dashboard/backend/app.py`
ở 1 terminal, rồi `cd dashboard/frontend && npm run dev` ở terminal khác —
Vite dev server (port 5173) proxy `/api` sang FastAPI (port 8420).

## Biến môi trường

- `VITE_API_BASE` (frontend, optional): mặc định `/api` — chỉ cần đổi
  nếu phục vụ API ở domain/path khác.

## Giới hạn đã biết (known limitations)

- **Chỉ hỗ trợ 36 incident lịch sử** (đã dùng để đóng băng model) —
  "New Analysis" (incident hoàn toàn mới) hiển thị rõ trạng thái "chưa
  bật" (Phần 2).
- OOF per-prefix + SHAP cho 36 incident **không có sẵn trước khi chạy
  `generate_oof_dashboard_data.py`** — script này chạy lại đúng quy
  trình LOIO/Platt/SHAP đã dùng xuyên suốt dự án (không đổi tham số,
  không đổi định nghĩa) và lưu kết quả per-row lần đầu tiên — xem
  `AUDIT.md` mục 3.
- Granularity của biểu đồ p̂_k chỉ có 8 điểm chuẩn mỗi trajectory
  (`ratio_25/50/75/100`, `k_2/3/5/7`) — KHÔNG có điểm cho mọi k liên
  tục, vì đây là granularity duy nhất dự án từng tính và lưu chính thức.
  Không nội suy/bịa thêm điểm.
- Flow Graph dùng layout lưới đơn giản (không force-directed) để tránh
  phụ thuộc thêm thư viện ngoài danh sách cho phép.
- Explainability chỉ hiển thị khi có alert (model vượt ngưỡng ở ít
  nhất 1 prefix) — nếu không có alert, trang hiện rõ trạng thái rỗng,
  không suy diễn.
