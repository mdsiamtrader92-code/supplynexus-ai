"""Calls the four MCP tool functions directly (no MCP client needed). Backend must be running."""
import json
import mcp_tools
for name in ("get_shipment_status", "list_alerts", "verify_audit_chain", "explain_shipment", "find_similar_incidents"):
    print("\n==", name)
    print(json.dumps(getattr(mcp_tools, name)(), indent=2))
