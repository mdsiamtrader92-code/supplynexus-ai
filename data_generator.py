"""Synthetic shipment journey generator (all data is simulated)."""
import numpy as np
import pandas as pd
from assumptions import NORMAL, TRANSIT_BASELINE, FEATURES, ANOMALY_SHARE, ANOMALY_TYPES, SEED


def _normal(rng, n):
    N = NORMAL
    transit = rng.normal(N["transit_hours"]["mean"], N["transit_hours"]["std"], n)
    return pd.DataFrame({
        "qty_discrepancy_pct": np.abs(rng.normal(0, N["qty_discrepancy_pct"]["scale"], n)),
        "rfid_gps_distance_km": np.abs(rng.normal(N["rfid_gps_distance_km"]["mean"], N["rfid_gps_distance_km"]["std"], n)),
        "route_deviation_km": np.abs(rng.normal(N["route_deviation_km"]["mean"], N["route_deviation_km"]["std"], n)),
        "transit_hours": transit,
        "checkpoint_dwell_min": np.clip(rng.normal(N["checkpoint_dwell_min"]["mean"], N["checkpoint_dwell_min"]["std"], n), 20, None),
        "scan_gap_min": np.clip(rng.normal(N["scan_gap_min"]["mean"], N["scan_gap_min"]["std"], n), 5, None),
    })


def _inject(rng, df, kind):
    """Make rows anomalous. Magnitudes are assumptions, chosen to be clearly abnormal but varied."""
    n = len(df)
    if kind in ("quantity", "combined"):
        df["qty_discrepancy_pct"] = rng.uniform(2, 15, n)
    if kind in ("sensor_mismatch", "combined"):
        df["rfid_gps_distance_km"] = rng.uniform(8, 80, n)
        df["scan_gap_min"] = df["scan_gap_min"] * rng.uniform(1.0, 3.0, n)
    if kind in ("route_deviation", "combined"):
        df["route_deviation_km"] = rng.uniform(10, 60, n)
    if kind in ("delay", "combined"):
        df["transit_hours"] = TRANSIT_BASELINE["mean"] + rng.uniform(2.0, 5.0, n) * TRANSIT_BASELINE["std"]
        df["checkpoint_dwell_min"] = df["checkpoint_dwell_min"] * rng.uniform(1.5, 3.5, n)
    return df


def generate(n=2000, anomaly_share=ANOMALY_SHARE, seed=SEED):
    rng = np.random.default_rng(seed)
    df = _normal(rng, n)
    df["label"] = 0
    df["anomaly_type"] = "none"
    k = int(n * anomaly_share)
    idx = rng.choice(n, k, replace=False)
    kinds = rng.choice(ANOMALY_TYPES, k)
    for kind in ANOMALY_TYPES:
        sel = idx[kinds == kind]
        if len(sel):
            df.loc[sel] = _inject(rng, df.loc[sel].copy(), kind)
            df.loc[sel, "label"] = 1
            df.loc[sel, "anomaly_type"] = kind
    df["transit_time_zscore"] = (df["transit_hours"] - TRANSIT_BASELINE["mean"]) / TRANSIT_BASELINE["std"]
    return df[FEATURES + ["label", "anomaly_type"]]


if __name__ == "__main__":
    d = generate()
    d.to_csv("synthetic_journeys.csv", index=False)
    print(d.describe().round(2))
    print(d["anomaly_type"].value_counts())
