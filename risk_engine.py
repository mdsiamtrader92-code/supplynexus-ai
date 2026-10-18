"""Rule-based risk engine, a Python mirror of the logic in the web demo (deterministic)."""

def rule_risk(qty_discrepancy_pct, rfid_gps_mismatch, route_deviation, delay):
    qty_short = qty_discrepancy_pct >= 1.0
    parts = []
    if qty_short:
        parts.append(("Quantity discrepancy", 20 + min(15, round(qty_discrepancy_pct))))
    if rfid_gps_mismatch:
        parts.append(("RFID/GPS mismatch", 35))
    if route_deviation:
        parts.append(("Route deviation", 20))
    if delay:
        parts.append(("Delay", 15))
    risk = min(100, sum(p[1] for p in parts))
    trust = 100 - (55 if rfid_gps_mismatch else 0)
    support = sum([bool(rfid_gps_mismatch) * 2, qty_short, bool(route_deviation), bool(delay)])
    conf = round(support / 5 * 100) if support else None
    band = "HIGH" if risk >= 60 else "MEDIUM" if risk >= 30 else "LOW"
    return {"risk": risk, "band": band, "trust": trust, "confidence": conf, "parts": parts}
