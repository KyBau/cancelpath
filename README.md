# CancelPath MCP
Read-only MCP server with **101 verified cancellation playbooks** (Netflix, Adobe, Peloton, ChatGPT, Microsoft 365…).
Each entry stores the merchant's **own help-page URL** and a **verified date** (2026-10-13). Merchants that couldn't be verified on an official page were left out rather than guessed.
It **never logs in, contacts merchants, or cancels anything.**

## Tools
| Tool | Title | Annotations |
|---|---|---|
| `find_cancel_path(merchant)` | Find how to cancel a subscription | readOnlyHint=true, destructiveHint=false, idempotentHint=true, openWorldHint=false |
| `list_merchants(query?)` | List supported subscriptions | same |
Results come back as both `structuredContent` and JSON text.

## Run locally
```bash
python3 server.py                 # stdio
PORT=8787 python3 server.py --http # Streamable HTTP (stateless) at http://127.0.0.1:8787/mcp, health at /healthz
python3 test_server.py            # 23 checks, stdio + HTTP
```
MCP 2026-07-28 alignment: stateless core (no session IDs, every POST is self-contained), JSON responses to POST, 405 on GET/DELETE, Origin validation, no auth (public data), version negotiation with fallback to 2025-xx versions.

## Add as a custom connector
Every host needs a **public HTTPS URL**. For testing, a tunnel to a local server works: `cloudflared tunnel --url http://localhost:8787` (Streamable HTTP works over Cloudflare quick tunnels), then use `https://<id>.trycloudflare.com/mcp`.
- **Claude:** Settings → Connectors → Add custom connector → paste the `/mcp` URL → no auth. Call both tools from a chat (the directory requires that you test each tool).
- **Grok:** grok.com/connectors → New Connector → Custom → paste the URL (docs.x.ai/grok/connectors). Business plans: an admin adds it in console.x.ai first.
- **Muse:** ask Muse to "add a custom connector" and give it the URL. Meta doesn't review custom connectors (Meta Help Center).
- **Claude Desktop (local stdio):** add to `claude_desktop_config.json`: `{"mcpServers":{"cancelpath":{"command":"python3","args":["/abs/path/server.py"]}}}`

## Data provenance
`playbooks.json` fields: `source_url`, `verified_date`, `verification_method`:
- `official_help_api`: the article came from the merchant's own Zendesk help-center API
- `official_page_fetch`: the merchant page was fetched directly
- `official_page_via_search`: the official page's content was read through a web-search fetch

The first two store verbatim `evidence_excerpts`. Search-verified entries store paraphrased `steps`. Re-verification scripts are in `build/`.

## Deploy (not done)
`render.yaml` (Render free tier, native Python; Render injects PORT) or `Dockerfile` or `fly.toml`. See CLAUDE_SUBMISSION.md for the accounts and approvals still needed.

## Privacy Policy
See [PRIVACY.md](PRIVACY.md). Summary: no personal data collected, no request logging, no third-party sharing, nothing retained. Contact: kylebauer@mail.grokbot.com.
