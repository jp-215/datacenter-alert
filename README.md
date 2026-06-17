# 🏢 datacenter-alert

A daily news alert for **data center activity in the SF Bay Area** — new builds,
expansions, hyperscaler projects, power/grid deals, and zoning news. Pulls from Google
News RSS (no paid APIs, no runtime dependencies), formats a concise digest, and posts it
to a Discord webhook. Ships with a **GitHub Actions workflow that runs it daily in the
cloud for free** — no server to host.

## How it works

```
  queries (Bay Area DC terms)
        │
        ▼
  Google News RSS  ──►  parse + filter (recency)  ──►  dedupe  ──►  rank  ──►  top N
        │                                                                        │
        └──────────────────────────────  format digest  ◄────────────────────────┘
                                                │
                                  print  +  POST to Discord webhook
```

Everything except the HTTP fetch is pure and unit-tested; the fetch is injectable so the
whole pipeline runs offline in CI.

## Quickstart (local)

```bash
# No dependencies needed to run — uses only the Python standard library.
python -m dc_alert.cli                 # print today's digest to the terminal
python -m dc_alert.cli --hours 24 --limit 5

# To post to Discord, set a webhook and pass --post:
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python -m dc_alert.cli --post
```

## Run it daily in the cloud (free)

1. Push this repo to GitHub (already done if you're reading it there).
2. Create a Discord webhook: **Server Settings → Integrations → Webhooks → New Webhook**,
   copy the URL.
3. Add it as a repo secret: **Settings → Secrets and variables → Actions → New repository
   secret**, name it `DISCORD_WEBHOOK_URL`.
4. That's it — `.github/workflows/alert.yml` runs every morning (~8:07am PT) and posts the
   digest. You can also trigger it manually from the **Actions** tab (Run workflow).

> Note: GitHub disables scheduled workflows on repos with no activity for 60 days — a
> manual run or any commit re-arms it.

## Configuration

All optional, via environment variables (see `.env.example`):

| Var | Default | Meaning |
|-----|---------|---------|
| `DISCORD_WEBHOOK_URL` | — | Where to post; if unset, prints only |
| `DC_ALERT_QUERIES` | Bay Area DC terms | `;`-separated search queries |
| `DC_ALERT_REGION` | `SF Bay Area` | Label in the digest header |
| `DC_ALERT_LOOKBACK_HOURS` | `48` | Recency window |
| `DC_ALERT_MAX_ITEMS` | `6` | Max stories per digest |

## Development

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

CI (`.github/workflows/ci.yml`) runs ruff + pytest on Python 3.10–3.12.

## Roadmap
- Optional LLM pass to add a one-line "why it matters" per story.
- De-dup across days (don't repeat yesterday's items).
- More regions / configurable source feeds.

---

*Built by the JayBot mesh. 🤖*
