"""The four read-only tools exposed over MCP. They call the local SupplyNexus backend.

READ-ONLY by design: no tool can change a shipment, record a human decision, or edit the audit log.
The AI agent can look and explain. Only the human operator decides.
"""
import json
import os
import urllib.request

BASE = os.environ.get("SNX_API", "http://localhost:8000")


def _get(path):
    with urllib.request.urlopen(BASE + path, timeout=15) as r:
        return json.loads(r.read())


def _post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())


def _safe(fn):
    try:
        return fn()
    except Exception:
        return {"error": f"SupplyNexus backend not reachable at {BASE}. Start it with: python -m uvicorn app:app --port 8000"}


def get_shipment_status():
    return _safe(lambda: _get("/api/state"))


def list_alerts():
    return _safe(lambda: _get("/api/alerts"))


def verify_audit_chain():
    return _safe(lambda: _get("/api/audit/verify"))


def explain_shipment():
    def go():
        flags = _get("/api/state")["scenario_flags"]
        return _post("/api/explain", flags)
    return _safe(go)


def find_similar_incidents():
    def go():
        flags = _get("/api/state")["scenario_flags"]
        return _post("/api/similar", flags)
    return _safe(go)
