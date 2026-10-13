import json, os, socket, subprocess, sys, time, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
fails = []; passed = 0
def check(name, cond):
    global passed
    if cond: passed += 1
    else: fails.append(name)
# data integrity
d = json.load(open("playbooks.json"))
check("100 merchants", len(d) >= 100)
import re
NAV = re.compile(r"sign in help|help center join|join netflix|skip to|cookie|explore premium|install app|help center|©|was this (article )?helpful|related articles|-->|'>|heading-label|a country must be selected|getting started|\u200b|\ufeff", re.I)
dirty = [k for k, v in d.items() for t in (v["evidence_excerpts"] + (v["steps"] or [])) if NAV.search(t)]
check("no nav boilerplate in excerpts/steps " + str(dirty[:5]), not dirty)
for k, v in d.items():
    ok = v["source_url"].startswith("https://") and v["verified_date"] and (v["steps"] or len(v["evidence_excerpts"]) >= 2)
    if not ok: fails.append("bad playbook " + k)
passed += 1
msgs = [{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2026-07-28","capabilities":{},"clientInfo":{"name":"t","version":"0"}}},
 {"jsonrpc":"2.0","method":"notifications/initialized"},
 {"jsonrpc":"2.0","id":2,"method":"tools/list"},
 {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"find_cancel_path","arguments":{"merchant":"netflix"}}},
 {"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"find_cancel_path","arguments":{"merchant":"Totally Unknown Co"}}},
 {"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"list_merchants","arguments":{"query":"you"}}},
 {"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"nope","arguments":{}}},
 {"jsonrpc":"2.0","id":7,"method":"bogus"}]
def verify(rs, tag):
    by = {r["id"]: r for r in rs}
    check(tag+" no reply to notification", len(rs) == 7)
    check(tag+" protocol version", by[1]["result"]["protocolVersion"] == "2026-07-28")
    tools = by[2]["result"]["tools"]
    check(tag+" titles+annotations", all(t.get("title") and t["annotations"].get("readOnlyHint") is True and t["annotations"].get("destructiveHint") is False for t in tools))
    n = by[3]["result"]["structuredContent"]; check(tag+" netflix found", n["found"] and n["source_url"].startswith("https://help.netflix.com"))
    check(tag+" unknown not found", by[4]["result"]["structuredContent"]["found"] is False)
    check(tag+" list filter", "YouTube TV" in by[5]["result"]["structuredContent"]["merchants"])
    check(tag+" unknown tool err", by[6]["error"]["code"] == -32602)
    check(tag+" unknown method err", by[7]["error"]["code"] == -32601)
# stdio
out = subprocess.run([sys.executable, "server.py"], input="\n".join(map(json.dumps, msgs)), capture_output=True, text=True, timeout=20).stdout
verify([json.loads(l) for l in out.splitlines()], "stdio")
# http
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
p = subprocess.Popen([sys.executable, "server.py", "--http"], env={**os.environ, "PORT": str(port)}, stderr=subprocess.DEVNULL)
try:
    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try: urllib.request.urlopen(base + "/healthz", timeout=1); break
        except Exception: time.sleep(0.1)
    def post(body, origin=None):
        h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2026-07-28"}
        if origin: h["Origin"] = origin
        req = urllib.request.Request(base + "/mcp", data=json.dumps(body).encode(), headers=h, method="POST")
        try:
            r = urllib.request.urlopen(req, timeout=5); raw = r.read(); return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e: return e.code, None
    rs = []
    for m in msgs:
        code, body = post(m)
        if "id" not in m: check("http notification 202", code == 202)
        else: rs.append(body)
    verify(rs, "http")
    check("http batch", len(post(msgs[2:4])[1]) == 2)
    check("http bad origin 403", post(msgs[2], origin="https://evil.example")[0] == 403)
    check("http claude origin ok", post(msgs[2], origin="https://claude.ai")[0] == 200)
    try: urllib.request.urlopen(base + "/mcp", timeout=2); code = 200
    except urllib.error.HTTPError as e: code = e.code
    check("http GET /mcp 405", code == 405)
finally:
    p.terminate()
print(f"PASS {passed}" + (f"  FAIL {len(fails)}: {fails}" if fails else "  FAIL 0"))
sys.exit(1 if fails else 0)
