"""Train an Isolation Forest on synthetic journeys and evaluate it honestly.

Training is unsupervised (labels are NOT used to fit). Labels exist only because
we injected the anomalies ourselves, so we can measure detection on a held-out set.
The numbers below describe SYNTHETIC data. They are not real-world accuracy.
"""
import json
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from assumptions import FEATURES, ANOMALY_SHARE, SEED
from data_generator import generate

train = generate(n=3000, seed=SEED)
test = generate(n=1000, seed=SEED + 1)   # different seed = held-out data

model = IsolationForest(n_estimators=200, contamination=ANOMALY_SHARE, random_state=SEED)
model.fit(train[FEATURES])               # labels not used

def score(df):
    return -model.score_samples(df[FEATURES])   # higher = more anomalous

pred = (model.predict(test[FEATURES]) == -1).astype(int)
s = score(test)
tn, fp, fn, tp = confusion_matrix(test["label"], pred).ravel()
per_type = {}
for t in sorted(test["anomaly_type"].unique()):
    if t == "none":
        continue
    m = test["anomaly_type"] == t
    per_type[t] = round(float(pred[m].mean()), 3)

metrics = {
    "note": "Evaluated on held-out SYNTHETIC data. Not real-world accuracy.",
    "train_rows": len(train), "test_rows": len(test),
    "precision": round(precision_score(test["label"], pred), 3),
    "recall": round(recall_score(test["label"], pred), 3),
    "f1": round(f1_score(test["label"], pred), 3),
    "roc_auc": round(roc_auc_score(test["label"], s), 3),
    "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    "recall_by_anomaly_type": per_type,
}
joblib.dump({"model": model, "features": FEATURES}, "isolation_forest.joblib")
json.dump(metrics, open("metrics.json", "w"), indent=2)
print(json.dumps(metrics, indent=2))
