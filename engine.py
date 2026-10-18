"""Combines the rule engine and the Isolation Forest for one shipment.

The ML score is shown NEXT TO the rule result. It never changes the risk score,
so the same input always gives the same risk (deterministic).
"""
from pathlib import Path
import joblib
import pandas as pd
from assumptions import TRANSIT_BASELINE
from risk_engine import rule_risk

_bundle = joblib.load(Path(__file__).parent / "isolation_forest.joblib")
_model, _features = _bundle["model"], _bundle["features"]


def _z(hours):
    return (hours - TRANSIT_BASELINE["mean"]) / TRANSIT_BASELINE["std"]


def features_from_flags(qty, mism, route, delay):
    """Turn the demo's scenario switches into model features (illustrative simulated values)."""
    return {
        "qty_discrepancy_pct": 8.0 if qty else 0.05,
        "rfid_gps_distance_km": 38.0 if mism else 0.4,
        "route_deviation_km": 24.0 if route else 1.2,
        "transit_time_zscore": _z(96 + 3.0 * 8) if delay else 0.1,
        "checkpoint_dwell_min": 520.0 if delay else 240.0,
        "scan_gap_min": 120.0 if mism else 60.0,
    }


def evaluate(qty=False, mism=False, route=False, delay=False):
    rules = rule_risk(8.0 if qty else 0.0, mism, route, delay)
    X = pd.DataFrame([features_from_flags(qty, mism, route, delay)])[_features]
    ml_score = float(-_model.score_samples(X)[0])
    ml_flag = bool(_model.predict(X)[0] == -1)
    rules_review = rules["risk"] >= 60 or (rules["confidence"] is not None and rules["confidence"] < 50)
    ml_only = ml_flag and not rules_review
    return {
        "rules": {k: v for k, v in rules.items() if k != "parts"},
        "ml_score": round(ml_score, 3),
        "ml_flag": ml_flag,
        "ml_only": ml_only,
        "note": "ML score is advisory. Trained on synthetic data only.",
    }
