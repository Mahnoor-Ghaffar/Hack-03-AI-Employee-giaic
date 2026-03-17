# Weekly CEO Briefing — Overview

## What It Does

A single Python script (`scripts/weekly_audit.py`) runs every Sunday at 9 AM, pulls data from 6 sources, and delivers two outputs:

1. **Briefing note** saved to `Needs_Action/` (full markdown report)
2. **WhatsApp message** sent to the CEO (concise summary, max 1000 chars)

## How It Works (5 Steps)

1. **Collect** — queries Odoo for invoices/payments/overdue, reads watcher state files for email/WhatsApp/LinkedIn counts, counts vault folder files
2. **Analyze** — calculates overdue aging buckets (1-30, 31-60, 61-90, 90+ days), weekly deltas, escalation levels
3. **Generate action items** — calls Claude CLI to prioritize tasks from the data; falls back to deterministic sort if AI times out
4. **Write briefing** — assembles markdown with YAML frontmatter, 4 sections (Accounting, Communications, Operations, Action Items), saves to vault
5. **Notify** — sends a WhatsApp summary to the CEO via MCP

## Data Sources

| Source | Method | What |
|--------|--------|------|
| Odoo | JSON-RPC | Invoices, payments, overdue aging |
| Gmail / WhatsApp / LinkedIn | Read state JSON files | Message counts + weekly delta |
| Vault folders | File system scan | Done (7-day), Needs_Action, Plans counts |
| Escalation tracker | `sent_reminders.json` | Reminder levels per invoice |

## Key Design Decisions

- **Graceful degradation** — each source is independently try/caught. If Odoo is down, the briefing still generates with the other sections; failed sections show a "Data unavailable" warning. Status becomes `"partial"`.
- **Dedup guard** — `audit_history.json` prevents duplicate runs within 7 days. Bypass with `--force`.
- **AI with fallback** — action items use Claude for prioritization but fall back to a deterministic overdue-first sort on timeout/error.
- **Atomic writes** — state files written via tempfile + rename to prevent corruption.
- **10s sleep increments** — polling loop sleeps in 10s chunks so SIGINT/SIGTERM is handled promptly.

## CLI

```bash
python scripts/weekly_audit.py              # watcher mode (polls every 60s)
python scripts/weekly_audit.py --once       # run now, exit (respects dedup)
python scripts/weekly_audit.py --once --force  # run now, bypass dedup
```

## Config (`scripts/audit_config.json`)

| Key | Default | Purpose |
|-----|---------|---------|
| `schedule_day` | `"Sunday"` | Which day to trigger |
| `schedule_hour` | `9` | Which hour (24h) |
| `ceo_jid` | `"923...@s.whatsapp.net"` | CEO's WhatsApp JID |
| `enabled_sources` | all `true` | Toggle each data source |
| `whatsapp_notification` | `true` | Send WhatsApp or just save note |
| `max_action_items` | `5` | Cap on checklist items |

## Briefing Note Sections

1. **Executive Summary** — one-sentence snapshot
2. **Accounting** — payments received, new invoices, total receivables, overdue aging table with escalation
3. **Communications** — Email, WhatsApp, LinkedIn, HITL approvals (weekly delta + total)
4. **Operations** — vault throughput (completed, pending, awaiting approval)
5. **Action Items** — AI-prioritized checklist

## Key Files

| File | Role |
|------|------|
| `scripts/weekly_audit.py` | Main script (~1280 lines) |
| `scripts/audit_config.json` | Configuration |
| `scripts/audit_history.json` | Run history + dedup (gitignored) |
| `tests/test_weekly_audit.py` | 80+ unit tests |
| `start_system.bat` | Launches it as the 7th watcher service |
