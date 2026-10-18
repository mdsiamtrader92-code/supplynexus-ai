"""SupplyNexus MCP server (read-only). Run: python mcp_server.py
Needs the backend running first:  python -m uvicorn app:app --port 8000

Works with mcp 2.x (MCPServer) and falls back to mcp 1.x (FastMCP).
When run directly it talks over stdio and waits silently for an MCP client. That is normal.
"""
try:
    from mcp.server.mcpserver import MCPServer          # mcp 2.x
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer  # mcp 1.x
import mcp_tools

mcp = MCPServer("supplynexus")


@mcp.tool()
def get_shipment_status() -> dict:
    """Current status of shipment SNX-001: checkpoint, risk, sensor trust, confidence, ML score, human review. Read-only. Data is simulated."""
    return mcp_tools.get_shipment_status()


@mcp.tool()
def list_alerts() -> dict:
    """Active alerts for the shipment with severity, reasons and any recorded human decision. Read-only."""
    return mcp_tools.list_alerts()


@mcp.tool()
def verify_audit_chain() -> dict:
    """Verify the SHA-256 hash chain of the audit log and report whether it is intact. Read-only."""
    return mcp_tools.verify_audit_chain()


@mcp.tool()
def explain_shipment() -> dict:
    """Plain-language explanation of the current shipment risk (template, or local AI with a number guardrail). Read-only."""
    return mcp_tools.explain_shipment()


@mcp.tool()
def find_similar_incidents() -> dict:
    """Similar past cases (synthetic examples) with suggested checks for the current shipment situation. Read-only. Suggestions only; the human decides."""
    return mcp_tools.find_similar_incidents()


if __name__ == "__main__":
    mcp.run()
