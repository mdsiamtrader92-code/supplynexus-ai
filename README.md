# SupplyNexus AI

Explainable, simulation-based supply chain intelligence for the **Supply Chain Nexus** challenge (IndustrySphere AI). Team **CodeNova**.

> Traditional tracking answers "where is the shipment?". SupplyNexus AI also answers: can we trust the tracking data, what is abnormal, why is it risky, and what should a human check next. **AI recommends, the human decides.**

**Important:** this is a simulated prototype. All RFID, GPS and AIS data is synthetic. No real hardware or data source is connected. Model metrics are measured on synthetic data and are **not** real-world accuracy.

## Links
- Demo video: [add YouTube link here]
- Live demo: [https://supplynexus-ai.onrender.com/]

## What it does
Flow: Track, Verify, Trust, Detect, Explain, Alert, Decide, Audit, on one shipment (Gazipur factory, Dhaka ICD, Chattogram Port, Colombo, Hamburg).

- **Rule engine** (deterministic): quantity, RFID vs GPS, route, delay. Same input, same risk. Risk bands: LOW below 30, MEDIUM 30 to 59, HIGH 60 and above.
- **Sensor trust**: starts at 100, drops when RFID and GPS disagree. Quantity problems raise risk but do not lower sensor trust.
- **Confidence (signal agreement)**: share of 5 signals supporting the anomaly. A simple heuristic, not a calibrated probability.
- **Isolation Forest** (scikit-learn) shown beside the rules. It never changes the risk score.
- **Explanation**: template text always works. Optional local LLM (Ollama, Qwen2.5 1.5B) rewrites it; a guardrail rejects invented or spelled-out numbers and falls back to the template.
- **Similar past cases**: TF-IDF keyword retrieval plus a signal-tag match over 8 synthetic incident notes. Suggested checks are shown exactly as written.
- **Human decision**: Continue, Investigate or Hold. Nothing is stopped automatically.
- **Audit**: SHA-256 hash chain with a tamper test and restore.
- **MCP server** (read-only, 5 tools): get_shipment_status, list_alerts, verify_audit_chain, explain_shipment, find_similar_incidents.

## Run locally
```
pip install -r requirements.txt
python train.py
python -m uvicorn app:app --port 8000
```
Open http://localhost:8000 (API docs at /docs). Optional: install Ollama and run `ollama pull qwen2.5:1.5b` for local explanations. Optional MCP server: `python mcp_server.py`, self test: `python mcp_selftest.py`.

## Files
| File | Purpose |
|---|---|
| app.py | FastAPI backend, serves the page and the API |
| engine.py, risk_engine.py | rules plus ML scoring |
| data_generator.py, assumptions.py, train.py | synthetic data (all values are team assumptions), training, evaluation |
| explain.py | template and local LLM explanation with guardrail |
| rag.py, knowledge/incidents.json | similar-case retrieval over synthetic notes |
| api_logic.py | server-side state and audit chain mirror |
| mcp_server.py, mcp_tools.py | read-only MCP server |
| static/index.html | the interactive dashboard |

## Honest limits
Synthetic data and simulated sensors. ML metrics are on synthetic data. Confidence is a heuristic. State is in memory and resets on restart. Retrieval is keyword based (no embeddings, no vector database). The hosted version has no local LLM and no MCP server.

## Production path
Replace the simulation source with RFID, GPS, AIS and TMS/ERP adapters feeding the same events; add a relational database, authentication and roles; retrain on real shipment history.
