.PHONY: demo demo-data demo-build demo-backend demo-frontend-dev

# Sinh du lieu OOF+SHAP that cho dashboard (chi can chay 1 lan, hoac khi
# features_v2_N37.parquet thay doi). Khong goi mang, khong sua pipeline.
demo-data:
	python scripts/dashboard/generate_oof_dashboard_data.py

# Build frontend (React/Vite) thanh static files.
demo-build:
	cd dashboard/frontend && npm install && npm run build

# Chay backend FastAPI (phuc vu ca API lan static frontend da build),
# chi bind localhost.
demo-backend:
	cd dashboard/backend && python app.py

# Lenh demo chinh: dam bao da co du lieu + frontend build, roi chay server.
demo: demo-data demo-build demo-backend

# Che do phat trien frontend (hot reload), can chay demo-backend o 1
# terminal khac truoc (port 8420).
demo-frontend-dev:
	cd dashboard/frontend && npm run dev
