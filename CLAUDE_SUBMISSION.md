# Claude Connectors Directory — submission draft (NOT submitted)
Portal: claude.ai/directory/manage → Submit new → MCP connector. Source: https://claude.com/docs/connectors/building/submission (read 2026-10-13).

## Connection
- URL: `https://<deployed-host>/mcp` (pending deploy). Single URL.

## Listing
- **Name (≤100):** CancelPath
- **One-liner (≤200):** Official, source-linked steps to cancel 100+ subscriptions — Netflix to Adobe — verified against each company's own help page. Read-only; never touches your accounts.
- **Description (≤2000):** CancelPath helps Claude answer "how do I cancel X?" with the merchant's own instructions instead of guesses. Each of 101 playbooks links to the company's official help page and shows the date it was verified, along with steps or verbatim excerpts. It reminds users that subscriptions billed through Apple, Google Play, Amazon or a carrier must be cancelled with that provider. CancelPath is strictly read-only. It needs no login, never contacts merchants, never cancels anything, and stores no personal data. Two tools: find_cancel_path (lookup with fuzzy matching and suggestions) and list_merchants (browse or filter coverage).
- **Categories:** Productivity; Finance; Shopping (pick ≤5 from the portal list)
- **Documentation URL:** public README (GitHub repo or /docs on host) — TBD
- **Privacy policy URL:** `https://<host>/privacy` (served by the server) — needs contact email
- **Support contact:** kylebauer@mail.grokbot.com
- **Icon:** icon.png (512x512)
- **Slug (permanent):** `cancelpath`

## Use cases
1. "How do I cancel my Peloton membership?" → steps + official link.
2. "Which of my subscriptions can you help me cancel?" → list_merchants.
3. Pair with an email connector: Claude finds receipts, then CancelPath gives the exit steps.
- Prerequisites: none. Reads data only (no writes).

## Company
- Company name/website: TBD. Docs don't state an LLC is required; individual name may be allowed (unverified — confirm in portal).

## Authentication
- **No authentication** (public data).

## Data handling
- API: our own (static curated dataset). No personal health data. No sponsored content.

## Test & launch
- No test account needed (no auth). Reviewer steps: add the URL as a custom connector, then ask "How do I cancel Netflix?" and "List subscriptions you cover that include 'you'". Confirm both tools were run in Claude (required checkbox).

## Compliance (7 acknowledgments)
Directory guidelines; first-party API usage (N/A, own data); financial transactions (none; read-only, no payments); AI media generation (none); prompt injection (static data, no untrusted fetched content); conversation data collection (none); public documentation (README). Kyle must personally confirm each one.

---
# Requirement checklist (Claude directory + MCP 2026-07-28)
| # | Requirement | Status | Evidence / gap |
|---|---|---|---|
| 1 | Remote server over HTTPS | **FAIL (pending)** | Streamable HTTP works locally; needs deploy + TLS (Render/Fly give HTTPS) |
| 2 | Streamable HTTP transport | PASS | `server.py --http`, POST /mcp, tests |
| 3 | Stateless core (2026-07-28) | PASS | no session IDs; GET/DELETE → 405 |
| 4 | Auth: OAuth for user accounts, or none for public data | PASS | no auth; public data only |
| 5 | Every tool has `title` | PASS | tool + annotations.title |
| 6 | `readOnlyHint` / `destructiveHint` on every tool | PASS | readOnly=true, destructive=false (tested) |
| 7 | Clear tool names & descriptions | PASS | descriptions state scope + read-only limits |
| 8 | Tested as custom connector in Claude | **FAIL (pending)** | needs public URL + Kyle's Claude account |
| 9 | Documentation URL | **FAIL (pending)** | README written; needs public hosting |
| 10 | Privacy policy URL (covers collection/usage/sharing/retention/contact) | PASS (pending host) | PRIVACY.md at /privacy, contact kylebauer@mail.grokbot.com |
| 11 | Support contact | PASS | kylebauer@mail.grokbot.com |
| 12 | Icon | PASS | icon.svg in repo; icon.png 512x512 via make_icon.py (upload PNG in portal) |
| 13 | Test account for reviewers | N/A–PASS | no auth |
| 14 | Paid Claude plan to submit | UNKNOWN | does Kyle have Pro/Max? |
| 15 | Directory terms & policy compliance | PASS (self-assessed) | read-only, accurate, no payments |
| 16 | Allowed link URIs | N/A | server doesn't use ui/open-link (URLs returned as text; third-party domains couldn't be listed anyway) |
| 17 | MCP App screenshots | N/A | not an MCP App |
| 18 | Input validation / safety | PASS | 64KB cap, Origin check, unknown tool/method errors |
| 19 | Data accuracy maintained | PARTIAL | verified 2026-10-13; needs a monthly re-verify job (`build/` scripts) |
