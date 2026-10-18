"""Score the two demo scenarios with the trained model and compare with the rules."""
import joblib
import pandas as pd
from assumptions import TRANSIT_BASELINE
from risk_engine import rule_risk

bundle = joblib.load("isolation_forest.joblib")
model, FEATURES = bundle["model"], bundle["features"]

def z(hours):
    return (hours - TRANSIT_BASELINE["mean"]) / TRANSIT_BASELINE["std"]

# name: (features, rule flags)
cases = {
    "Normal shipment": (dict(qty_discrepancy_pct=0.05, rfid_gps_distance_km=0.4, route_deviation_km=1.2,
                             transit_time_zscore=0.1, checkpoint_dwell_min=240, scan_gap_min=60),
                        dict(qty_discrepancy_pct=0.05, rfid_gps_mismatch=False, route_deviation=False, delay=False)),
    "Scenario 1 (quantity + sensor mismatch)": (dict(qty_discrepancy_pct=8.0, rfid_gps_distance_km=38, route_deviation_km=1.5,
                             transit_time_zscore=0.3, checkpoint_dwell_min=260, scan_gap_min=120),
                        dict(qty_discrepancy_pct=8.0, rfid_gps_mismatch=True, route_deviation=False, delay=False)),
    "Scenario 2 (route deviation + delay)": (dict(qty_discrepancy_pct=0.05, rfid_gps_distance_km=0.5, route_deviation_km=24,
                             transit_time_zscore=z(96 + 3.0 * 8), checkpoint_dwell_min=520, scan_gap_min=65),
                        dict(qty_discrepancy_pct=0.05, rfid_gps_mismatch=False, route_deviation=True, delay=True)),
}

for name, (feat, flags) in cases.items():
    X = pd.DataFrame([feat])[FEATURES]
    ml_score = float(-model.score_samples(X)[0])
    ml_flag = model.predict(X)[0] == -1
    r = rule_risk(**flags)
    print(f"\n{name}")
    print(f"  Rules : risk={r['risk']} ({r['band']}), trust={r['trust']}, confidence={r['confidence']}")
    print(f"  ML    : anomaly score={ml_score:.3f}, flagged={ml_flag}")
    if ml_flag and r["risk"] < 30:
        print("  -> ML-only flag: human review recommended")
