"""Server-side state and audit chain (plain Python, so it can be tested without a web server).

The browser mirrors its events here. The MCP server reads this copy.
State lives in memory and resets when the server restarts (fine for a demo).
"""
import hashlib
import threading
import engine
import explain

_lock = threading.Lock()
STATE = {"qty": False, "mism": False, "route": False, "delay": False, "pos": 0, "dec": None}
AUDIT = []
GENESIS = "0" * 64
CHECKPOINTS = ["Factory, Gazipur", "Dhaka ICD", "Chattogram Port", "Colombo (transshipment)", "Hamburg buyer DC"]


def _hash(prev, etype, data, ts):
    return hashlib.sha256(f"{prev}|{etype}|{data}|{ts}".encode()).hexdigest()


def set_state(d):
    with _lock:
        for k in ("qty", "mism", "route", "delay"):
            STATE[k] = bool(d.get(k, False))
        STATE["pos"] = int(d.get("pos", 0))
        STATE["dec"] = d.get("dec")
    return {"ok": True}


def get_state():
    with _lock:
        s = dict(STATE)
    ev = engine.evaluate(s["qty"], s["mism"], s["route"], s["delay"])
    return {
        "shipment": "SNX-001",
        "route": "Gazipur -> Dhaka ICD -> Chattogram Port -> Colombo -> Hamburg",
        "current_checkpoint": CHECKPOINTS[min(max(s["pos"], 0), 4)],
        "scenario_flags": {k: s[k] for k in ("qty", "mism", "route", "delay")},
        "human_decision": s["dec"],
        "rules": ev["rules"],
        "ml_score": ev["ml_score"],
        "ml_flag": ev["ml_flag"],
        "human_review": explain.review_level(ev),
        "data_source": "simulated",
    }


def audit_reset():
    with _lock:
        AUDIT.clear()
    return {"ok": True}


def audit_append(etype, data, ts):
    with _lock:
        prev = AUDIT[-1]["hash"] if AUDIT else GENESIS
        AUDIT.append({"ts": ts, "type": etype, "data": data, "prev": prev, "hash": _hash(prev, etype, data, ts)})
        return {"ok": True, "count": len(AUDIT)}


def audit_list():
    with _lock:
        return list(AUDIT)


def audit_verify():
    with _lock:
        prev = GENESIS
        for i, e in enumerate(AUDIT):
            if e["prev"] != prev or _hash(prev, e["type"], e["data"], e["ts"]) != e["hash"]:
                return {"intact": False, "broken_at_entry": i + 1, "entries": len(AUDIT)}
            prev = e["hash"]
        return {"intact": True, "broken_at_entry": None, "entries": len(AUDIT),
                "note": "Server-side mirror of the audit log"}


def alerts():
    st = get_state()
    f = st["scenario_flags"]
    reasons = []
    if f["qty"]: reasons.append("quantity discrepancy (80 of 1000 units unverified)")
    if f["mism"]: reasons.append("RFID and GPS positions disagree")
    if f["route"]: reasons.append("route deviation")
    if f["delay"]: reasons.append("delay")
    if not reasons and st["human_review"] == "None":
        return {"active_alerts": [], "note": "No alerts. Confidence is N/A because there is no anomaly."}
    r = st["rules"]
    return {"active_alerts": [{
        "shipment": st["shipment"], "severity": r["band"], "risk": r["risk"], "trust": r["trust"],
        "confidence": r["confidence"], "human_review": st["human_review"], "reasons": reasons,
        "ml_score": st["ml_score"], "human_decision": st["human_decision"],
        "recommended_action": "Investigate" if st["human_review"] == "Required" else "Review",
    }]}
