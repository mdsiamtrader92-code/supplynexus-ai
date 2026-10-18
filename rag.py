"""Retrieval over a small knowledge base of SYNTHETIC incident notes (written by the team for the demo).

Method: TF-IDF keyword similarity plus a signal-tag match bonus (scikit-learn, numpy). This is not neural embedding search.
Results are suggested checks for the human operator. The LLM is not used here, so the
checks are shown exactly as written and cannot be changed or invented.
"""
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_DOCS = json.loads((Path(__file__).parent / "knowledge" / "incidents.json").read_text(encoding="utf-8"))
_TEXT = [f"{d['title']}. {d['finding']} {' '.join(d['checks'])} {' '.join(d['tags'])}" for d in _DOCS]
_VEC = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
_MATRIX = _VEC.fit_transform(_TEXT)

PHRASES = {
    "qty": "quantity shortfall unverified units packing list recount cartons",
    "mism": "RFID GPS disagree position mismatch tag read tracking data sensor",
    "route": "route deviation left planned route diversion",
    "delay": "delay behind schedule late arrival congestion",
}


def query_from_flags(flags):
    return " ".join(PHRASES[k] for k in PHRASES if flags.get(k))


TAGS = {"qty": "quantity", "mism": "sensor_mismatch", "route": "route", "delay": "delay"}


def _tag_overlap(active, doc_tags):
    """Jaccard overlap between the active signals and an incident's tags (1.0 = same combination)."""
    a, d = set(active), set(doc_tags)
    return len(a & d) / len(a | d) if (a | d) else 0.0


def retrieve(flags, k=2, min_score=0.08):
    q = query_from_flags(flags)
    if not q:
        return []
    active = [TAGS[x] for x in TAGS if flags.get(x)]
    kw = cosine_similarity(_VEC.transform([q]), _MATRIX)[0]
    # hybrid score: keyword similarity plus a bonus when the combination of signals is the same
    sims = kw + 0.3 * __import__("numpy").array([_tag_overlap(active, d["tags"]) for d in _DOCS])
    order = sims.argsort()[::-1][:k]
    return [{"id": _DOCS[i]["id"], "title": _DOCS[i]["title"], "finding": _DOCS[i]["finding"],
             "checks": _DOCS[i]["checks"], "score": round(float(sims[i]), 3)}
            for i in order if sims[i] >= min_score]
