# -*- coding: utf-8 -*-
"""FastAPI backend cho CAGI-ED SOC Dashboard - Phan 1 (36 incident
historical, out-of-fold). CHI DOC file JSON tinh da sinh san
(data/dashboard/incidents.json qua scripts/dashboard/generate_oof_dashboard_data.py)
- KHONG tinh toan lai, KHONG goi mang, KHONG retrain. Bind localhost only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "dashboard" / "incidents.json"
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

app = FastAPI(title="CAGI-ED SOC Dashboard API", version="1.0.0-demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

_cache: Optional[dict] = None


def load_data() -> dict:
    global _cache
    if _cache is None:
        if not DATA_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail=(
                    "data/dashboard/incidents.json chua duoc sinh. Chay: "
                    "python scripts/dashboard/generate_oof_dashboard_data.py"
                ),
            )
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return _cache


@app.get("/api/meta")
def get_meta():
    return load_data()["meta"]


@app.get("/api/incidents")
def list_incidents():
    data = load_data()
    out = []
    for iid, inc in data["incidents"].items():
        out.append({
            "incident_id": inc["incident_id"],
            "name": inc["name"],
            "chain": inc["chain"],
            "endpoint_confirmed": inc["endpoint_confirmed"],
            "e_star": inc["e_star"],
            "n_actions_total": inc["n_actions_total"],
            "label": inc["label"],
        })
    return out


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str):
    data = load_data()
    if incident_id not in data["incidents"]:
        raise HTTPException(status_code=404, detail=f"Khong tim thay incident: {incident_id}")
    return data["incidents"][incident_id]


@app.get("/api/new-analysis")
def new_analysis_status():
    return {
        "enabled": False,
        "message": "Chua duoc bat trong ban build nay (Phan 2). Phan 1 chi ho tro 36 incident lich su, out-of-fold.",
    }


@app.get("/healthz")
def healthz():
    ok = DATA_PATH.exists()
    return {"status": "ok" if ok else "degraded", "data_file_exists": ok}


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        """SPA fallback: moi route client-side (vd /investigation/:id) deu
        tra ve index.html, React Router tu xu ly phia client. File tinh
        (favicon...) van duoc tim truoc neu ton tai."""
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(FRONTEND_DIST / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8420)
