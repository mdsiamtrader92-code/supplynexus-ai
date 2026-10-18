"""Explanation layer: template first, optional local LLM (Ollama) on top.

The LLM only REWRITES facts that the rule engine already produced. It never
calculates or changes risk. If Ollama is missing, slow, or its output adds
numbers that are not in the facts, we fall back to the template text.
"""
import json
import os
import re
import urllib.request

OLLAMA_URL = os.environ.get("SNX_OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.environ.get("SNX_MODEL", "qwen2.5:1.5b")


def review_level(ev):
    r = ev["rules"]
    if r["risk"] >= 60:
        return "Required"
    if (r["confidence"] is not None and r["confidence"] < 50) or ev.get("ml_only"):
        return "Recommended"
    return "None"


def facts(flags, ev):
    r = ev["rules"]
    f = []
    if flags.get("qty"):
        f.append("unverified units: 80; total units: 1000; discrepancy: 8%")
    if flags.get("mism"):
        f.append(f"RFID and GPS disagree about the shipment position, so sensor trust is {r['trust']} out of 100")
    if flags.get("route"):
        f.append("the shipment left its planned route")
    if flags.get("delay"):
        f.append("the shipment is behind schedule")
    f.append(f"risk score is {r['risk']} out of 100 ({r['band']})")
    if r["confidence"] is not None:
        f.append(f"signal agreement is {r['confidence']}%")
    f.append(f"human review: {review_level(ev).lower()}")
    return f


def template(flags, ev):
    r = ev["rules"]
    if not any(flags.get(k) for k in ("qty", "mism", "route", "delay")):
        return "All signals agree and the quantity matches. No action needed."
    s = []
    if flags.get("qty"):
        s.append("80 units are unverified (8% of the shipment).")
    if flags.get("mism"):
        s.append("RFID and GPS disagree about where the shipment is, so the tracking data is less reliable.")
    if flags.get("route"):
        s.append("The shipment left its planned route.")
    if flags.get("delay"):
        s.append("It is behind the expected schedule.")
    s.append(f"It is classified {r['band']} risk with {r['confidence']}% signal agreement.")
    lvl = review_level(ev)
    s.append("Human investigation is required." if lvl == "Required"
             else "Agreement between signals is low, so a human should review it." if lvl == "Recommended" else "")
    return " ".join(x for x in s if x)


WORD_NUMBERS = re.compile(
    r"\b(zero|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
    r"seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|"
    r"million|half|quarter|double|triple)\b", re.I)


def _acceptable(out, fact_text, flags, ev):
    """Guardrail: only digits that appear in the facts, no spelled-out numbers,
    and the key figures (risk score, unverified units) must be present as digits."""
    if not _numbers(out) <= _numbers(fact_text):
        return False
    if WORD_NUMBERS.search(out):
        return False
    if str(ev["rules"]["risk"]) not in _numbers(out):
        return False
    if flags.get("qty") and "80" not in _numbers(out):
        return False
    return True


def _numbers(text):
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def enhance(flags, ev, timeout=25):
    base = template(flags, ev)
    if not any(flags.get(k) for k in ("qty", "mism", "route", "delay")):
        return {"text": base, "source": "Template (no anomaly)"}
    fact_text = "; ".join(facts(flags, ev))
    prompt = (
        "You write short alerts for a logistics operator. Rewrite the facts below as 2 or 3 plain sentences. "
        "Use ONLY these facts. Write every number exactly as digits as given; never spell numbers as words. "
        "Do not add numbers, causes, blame, or new claims. "
        "Do not make the decision; say the human operator decides.\n\nFacts: " + fact_text
    )
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0.2, "num_predict": 120}}).encode()
    try:
        req = urllib.request.Request(OLLAMA_URL, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            out = json.loads(resp.read())["response"].strip()
    except Exception:
        return {"text": base, "source": "Template (local AI not available)"}
    if not out or not _acceptable(out, fact_text, flags, ev):
        return {"text": base, "source": "Template (AI output rejected: numbers did not match the facts)"}
    return {"text": out, "source": f"Local AI ({MODEL})"}
