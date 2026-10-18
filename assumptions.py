"""
Every number here is a TEAM ASSUMPTION used to build synthetic data.
None of these are measured real-world statistics. Replace them with values
from stakeholder interviews or real shipment history when available.
Route: Gazipur factory -> Dhaka ICD -> Chattogram Port -> Colombo -> Hamburg.
"""
SEED = 42

NORMAL = {
    "qty_discrepancy_pct": {"scale": 0.15},          # normal journeys: tiny counting noise
    "rfid_gps_distance_km": {"mean": 0.4, "std": 0.25},
    "route_deviation_km": {"mean": 1.5, "std": 1.0},
    "transit_hours": {"mean": 96.0, "std": 8.0},      # factory -> port leg (assumption)
    "checkpoint_dwell_min": {"mean": 240.0, "std": 50.0},
    "scan_gap_min": {"mean": 60.0, "std": 10.0},
}

# Baseline used to turn transit time into a z-score
TRANSIT_BASELINE = {"mean": NORMAL["transit_hours"]["mean"], "std": NORMAL["transit_hours"]["std"]}

FEATURES = [
    "qty_discrepancy_pct",
    "rfid_gps_distance_km",
    "route_deviation_km",
    "transit_time_zscore",
    "checkpoint_dwell_min",
    "scan_gap_min",
]

ANOMALY_SHARE = 0.05       # share of injected anomalies in the data
ANOMALY_TYPES = ["quantity", "sensor_mismatch", "route_deviation", "delay", "combined"]
