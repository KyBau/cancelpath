#!/usr/bin/env python3
"""CancelPath MCP server: read-only, verified cancellation playbooks for 100+ subscriptions.
Transports: stdio (default) and stateless Streamable HTTP (`--http`, POST /mcp, JSON responses).
Zero dependencies (Python 3.10+). No auth (public data), no user data stored, no outbound calls."""
import json, os, re, sys, difflib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
HERE = os.path.dirname(os.path.abspath(__file__))
PLAYBOOKS = json.load(open(os.path.join(HERE, "playbooks.json")))
VERSION = "0.2.0"
SUPPORTED = ["2026-07-28", "2025-11-25", "2025-06-18", "2025-03-26"]
RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
TOOLS = [
 {"name": "find_cancel_path", "title": "Find how to cancel a subscription",
  "description": "Look up the official cancellation steps for one subscription or membership (e.g. 'Netflix', 'Adobe', 'Peloton'). "
   "Returns the merchant's own help-page URL, the date it was verified, and either steps or verbatim excerpts from that page. "
   "Read-only: it never logs in, contacts the merchant, or cancels anything. If no verified playbook exists it says so and suggests close matches.",
  "inputSchema": {"type": "object", "properties": {"merchant": {"type": "string", "description": "Merchant or subscription name, e.g. 'YouTube TV'."}}, "required": ["merchant"], "additionalProperties": False},
  "annotations": {"title": "Find how to cancel a subscription", **RO}},
 {"name": "list_merchants", "title": "List supported subscriptions",
  "description": "List merchants that have a verified cancellation playbook. Optional 'query' filters by substring. Read-only.",
  "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "Optional case-insensitive filter."}}, "additionalProperties": False},
  "annotations": {"title": "List supported subscriptions", **RO}},
]
def _norm(s): return re.sub(r"[^a-z0-9]+", "", s.lower())
_IDX = {_norm(v["merchant"]): k for k, v in PLAYBOOKS.items()} | {_norm(k): k for k in PLAYBOOKS}
def find(merchant):
    q = _norm(merchant or "")
    if not q: return {"found": False, "error": "merchant is required"}
    key = _IDX.get(q) or next((k for n, k in _IDX.items() if len(q) >= 3 and (q in n or n in q)), None)
    if key:
        p = PLAYBOOKS[key]
        return {"found": True, "id": key, **p,
                "disclaimer": "If you subscribed through Apple, Google Play, Amazon or a carrier, cancel with that billing provider instead."}
    close = difflib.get_close_matches(q, list(_IDX), n=3, cutoff=0.6)
    return {"found": False, "merchant": merchant, "suggestions": sorted({PLAYBOOKS[_IDX[c]]["merchant"] for c in close}),
            "advice": "No verified playbook. Check the merchant's account/billing settings or official help center."}
def listm(query=None):
    names = sorted(v["merchant"] for v in PLAYBOOKS.values())
    if query: names = [n for n in names if query.lower() in n.lower()]
    return {"count": len(names), "merchants": names}
def call_tool(name, args):
    if name == "find_cancel_path": return find(args.get("merchant", ""))
    if name == "list_merchants": return listm(args.get("query"))
    raise KeyError(name)
def handle(req):
    if not isinstance(req, dict) or req.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
    mid, meth, p = req.get("id"), req.get("method"), req.get("params") or {}
    if "id" not in req: return None  # notification
    if meth == "initialize":
        v = p.get("protocolVersion"); v = v if v in SUPPORTED else SUPPORTED[0]
        r = {"protocolVersion": v, "capabilities": {"tools": {"listChanged": False}},
             "serverInfo": {"name": "cancelpath", "title": "CancelPath", "version": VERSION},
             "instructions": "Use find_cancel_path when a user asks how to cancel a subscription. Always show the source_url and verified_date. This server cannot perform cancellations."}
    elif meth == "ping": r = {}
    elif meth == "tools/list": r = {"tools": TOOLS}
    elif meth == "tools/call":
        try: data = call_tool(p.get("name"), p.get("arguments") or {})
        except KeyError: return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"Unknown tool: {p.get('name')}"}}
        r = {"content": [{"type": "text", "text": json.dumps(data, indent=1)}], "structuredContent": data, "isError": False}
    else: return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Method not found: {meth}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": r}
ALLOWED_ORIGINS = [o for o in os.environ.get("CANCELPATH_ALLOWED_ORIGINS", "https://claude.ai,https://claude.com,https://grok.com,https://muse.ai").split(",") if o]
class H(BaseHTTPRequestHandler):
    server_version = "cancelpath/" + VERSION
    def _send(self, code, body=None, ctype="application/json"):
        b = b"" if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass  # no request logging (privacy)
    def _origin_ok(self):
        o = self.headers.get("Origin")
        return o is None or o in ALLOWED_ORIGINS or o.startswith("http://localhost") or o.startswith("http://127.0.0.1")
    def do_GET(self):
        if self.path == "/healthz": return self._send(200, {"ok": True, "merchants": len(PLAYBOOKS), "version": VERSION})
        if self.path.startswith("/mcp"): return self._send(405, {"error": "SSE stream not offered; POST JSON-RPC to /mcp"})
        if self.path in ("/", "/privacy"):
            return self._send(200, open(os.path.join(HERE, "PRIVACY.md"), "rb").read(), "text/markdown; charset=utf-8")
        self._send(404, {"error": "not found"})
    def do_DELETE(self): self._send(405, {"error": "stateless server; no sessions"})
    def do_POST(self):
        if not self.path.startswith("/mcp"): return self._send(404, {"error": "not found"})
        if not self._origin_ok(): return self._send(403, {"error": "origin not allowed"})
        n = int(self.headers.get("Content-Length") or 0)
        if n > 64_000: return self._send(413, {"error": "payload too large"})
        try: msg = json.loads(self.rfile.read(n) or b"null")
        except json.JSONDecodeError: return self._send(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
        if isinstance(msg, list):
            out = [r for r in (handle(m) for m in msg) if r]
        else: out = handle(msg)
        if not out: return self._send(202)
        self._send(200, out)
def serve_http(host, port):
    print(f"CancelPath MCP on http://{host}:{port}/mcp ({len(PLAYBOOKS)} merchants)", file=sys.stderr, flush=True)
    ThreadingHTTPServer((host, port), H).serve_forever()
def serve_stdio():
    for line in sys.stdin:
        if not line.strip(): continue
        try: out = handle(json.loads(line))
        except json.JSONDecodeError: out = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        if out: print(json.dumps(out), flush=True)
if __name__ == "__main__":
    if "--http" in sys.argv:
        serve_http(os.environ.get("HOST", "127.0.0.1"), int(os.environ.get("PORT", "8787")))
    else: serve_stdio()
