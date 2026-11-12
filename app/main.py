"""API de FINIA-RECON."""
import csv
import io
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel

from app.ai_agent import FinancialReconciliationAgent
from app.business_rules import evaluate_rules
from app.reconciliation import build_summary
from app.storage import init_db, save_run, list_cases, update_case, list_runs, latest_run

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
STATIC_DIR = BASE_DIR / "static"
app = FastAPI(title="FINIA-RECON API", version="2.0.0", description="Plataforma inteligente de conciliación financiera")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/health")
def health():
    return {"application": "FINIA-RECON", "status": "ONLINE", "ai_configured": bool(os.getenv("OPENAI_API_KEY"))}

async def read_source(upload: Optional[UploadFile], fallback_name: str):
    if upload is None:
        path = BASE_DIR / "data" / fallback_name
        return json.loads(path.read_text(encoding="utf-8"))
    raw = await upload.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(413, "El archivo supera el límite de 10 MB.")
    suffix = Path(upload.filename or "").suffix.lower()
    try:
        if suffix == ".json":
            records = json.loads(raw.decode("utf-8-sig"))
        elif suffix == ".csv":
            records = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        elif suffix in {".xlsx", ".xls"}:
            import pandas as pd
            records = pd.read_excel(io.BytesIO(raw)).fillna("").to_dict(orient="records")
        else:
            raise HTTPException(415, "Formato no soportado. Utiliza JSON, CSV o Excel.")
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(400, f"No se pudo leer {upload.filename}: {exc}") from exc
    if not isinstance(records, list):
        raise HTTPException(400, f"{upload.filename} debe contener una lista de transacciones.")
    return records

@app.post("/api/reconcile")
async def reconcile(internal_file: Optional[UploadFile] = File(default=None), processor_file: Optional[UploadFile] = File(default=None)):
    internal = await read_source(internal_file, "internal.json")
    processor = await read_source(processor_file, "processor.json")
    report_rows = evaluate_rules(internal, processor)
    summary = build_summary(report_rows)
    report = {
        "project": "FINIA-RECON", "process": "FINANCIAL_RECONCILIATION",
        "sources": {"internal_records": len(internal), "processor_records": len(processor)},
        "summary": summary, "transactions": report_rows,
    }
    analysis = FinancialReconciliationAgent().analyze(report)
    run_id = save_run(report, analysis)
    report["run_id"] = run_id
    return {"success": True, "report": report, "analysis": analysis}

@app.get("/api/latest")
def latest():
    return {"item": latest_run()}

@app.get("/api/cases")
def cases(status: Optional[str] = None):
    allowed = {"OPEN", "IN_PROGRESS", "RESOLVED", "DISMISSED"}
    if status and status not in allowed:
        raise HTTPException(400, "Estado de caso no válido.")
    return {"items": list_cases(status)}

class CaseUpdate(BaseModel):
    status: str

@app.patch("/api/cases/{case_id}")
def case_update(case_id: int, payload: CaseUpdate):
    if payload.status not in {"OPEN", "IN_PROGRESS", "RESOLVED", "DISMISSED"}:
        raise HTTPException(400, "Estado de caso no válido.")
    if not update_case(case_id, payload.status):
        raise HTTPException(404, "Caso no encontrado.")
    return {"success": True, "case_id": case_id, "status": payload.status}

@app.get("/api/history")
def history():
    return {"items": list_runs()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
