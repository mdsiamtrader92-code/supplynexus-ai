"""SupplyNexus AI backend. Run:  python -m uvicorn app:app --port 8000
Then open http://localhost:8000  (API docs at http://localhost:8000/docs)
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import engine
import explain
import api_logic
import rag

BASE = Path(__file__).parent
app = FastAPI(title="SupplyNexus AI API", version="0.3")


class StateIn(BaseModel):
    qty: bool = False
    mism: bool = False
    route: bool = False
    delay: bool = False
    pos: int = 0
    dec: str | None = None


class AuditIn(BaseModel):
    type: str
    data: str
    ts: str


class Flags(BaseModel):
    qty: bool = False
    mism: bool = False
    route: bool = False
    delay: bool = False


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "simulation"}


@app.post("/api/evaluate")
def evaluate(f: Flags):
    return engine.evaluate(f.qty, f.mism, f.route, f.delay)


@app.post("/api/explain")
def explain_endpoint(f: Flags):
    flags = f.model_dump()
    ev = engine.evaluate(f.qty, f.mism, f.route, f.delay)
    return explain.enhance(flags, ev)


@app.get("/api/state")
def get_state():
    return api_logic.get_state()


@app.post("/api/state")
def set_state(s: StateIn):
    return api_logic.set_state(s.model_dump())


@app.post("/api/audit")
def audit_append(a: AuditIn):
    return api_logic.audit_append(a.type, a.data, a.ts)


@app.post("/api/audit/reset")
def audit_reset():
    return api_logic.audit_reset()


@app.get("/api/audit")
def audit_list():
    return api_logic.audit_list()


@app.get("/api/audit/verify")
def audit_verify():
    return api_logic.audit_verify()


@app.get("/api/alerts")
def alerts():
    return api_logic.alerts()


@app.post("/api/similar")
def similar(f: Flags):
    return {"method": "TF-IDF keyword similarity + signal-tag match over synthetic incident notes",
            "items": rag.retrieve(f.model_dump())}


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")
