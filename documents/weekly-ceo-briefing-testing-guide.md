# Weekly CEO Briefing — Complete Guide

## What This System Does

Every week, the system automatically:

1. **Pulls accounting data** from Odoo (outstanding invoices, overdue payments, new invoices, payments received)
2. **Counts automation activity** (emails processed, WhatsApp messages handled, LinkedIn posts, HITL approvals)
3. **Measures vault throughput** (items completed, pending, awaiting approval)
4. **Generates AI action items** with specific follow-up recommendations
5. **Writes a briefing note** to `Needs_Action/` in the Obsidian vault
6. **Sends a WhatsApp summary** to the CEO as a notification ping

The CEO can then **check action item checkboxes** in Obsidian to trigger payment reminders — which go through a two-step HITL approval before being sent.

---

## Architecture Overview

```
                        WEEKLY AUDIT (weekly_audit.py)
                                    |
            +-----------+-----------+-----------+
            |           |           |           |
          Odoo      Gmail/WA    Vault       Claude AI
       (invoices,   (message    (file       (action item
        payments,    counts)    counts)     generation)
        overdue)
            |           |           |           |
            +-----------+-----------+-----------+
                                    |
                    +---------------+---------------+
                    |                               |
        Needs_Action/ briefing.md          WhatsApp summary
        (full report + checkboxes)         (condensed notification)
                    |
                    | CEO checks [x] on action item
                    |
        briefing_action_watcher.py detects checkbox
                    |
        Invokes /draft-payment-reminder skill
                    |
        Plans/Reminder_*.md created (draft message)
                    |
                    | CEO reviews, checks [x] APPROVE
                    |
        approval_watcher.py sends via WhatsApp/email
                    |
                Done/ (archived)
```

---

## Key Concepts

### Briefing Sections Explained

| Section | Data Source | What It Shows |
|---------|-----------|---------------|
| **Accounting** | Odoo (live query) | Payments received this week, new invoices issued, total outstanding receivables, overdue aging table |
| **Communications** | Watcher state JSON files | How many emails, WhatsApp messages, LinkedIn posts, and HITL approvals the automation system processed this week |
| **Operations** | Obsidian vault folder counts | Items completed (Done/), pending attention (Needs_Action/), plans awaiting approval (Plans/) |
| **Action Items** | AI-generated from Odoo data | Prioritized to-do list; automatable items have checkboxes, advisory items are plain bullets |

### How Numbers Relate

- **Total Outstanding Receivables** = ALL unpaid invoices (overdue + not-yet-due)
- **Overdue Summary** = invoices past their due date (subset of total outstanding)
- **Not Yet Due** = Total Outstanding - Overdue (invoices within payment terms)
- **New Invoices Issued** = invoices created this week (may overlap with not-yet-due)

Example: Total Outstanding PKR 381,045 = Overdue PKR 202,598 + Not Yet Due PKR 178,447

### Action Items: Automatable vs Advisory

The AI generates two types of action items:

- **Automatable** (checkbox `- [ ]`): Mentions a specific customer with overdue invoices. Checking this triggers the payment reminder workflow.
- **Advisory** (plain bullet `- `): Strategic advice like "review credit terms" — no automation, just a note for the CEO.

### Escalation Levels

Payment reminders escalate in tone:

| Level | Tone | When |
|-------|------|------|
| **gentle** | Friendly reminder | First contact |
| **firm** | Assertive follow-up | After gentle reminder + 7 day cooldown |
| **final** | Formal notice | After firm reminder + 7 day cooldown |

After 3 reminders, no more automatic reminders are sent.

---

## Scripts and Files

### Scripts

| Script | Purpose | Run Mode |
|--------|---------|----------|
| `scripts/weekly_audit.py` | Generates the briefing and sends WhatsApp notification | Scheduled (Sunday 9am) or `--once --force` |
| `scripts/briefing_action_watcher.py` | Watches briefing checkboxes, triggers payment reminder drafts | Continuous polling (10s) |
| `scripts/approval_watcher.py` | Watches Plans/ for approved drafts, sends messages | Continuous polling (10s) |

### State Files (all gitignored)

| File | Written By | Read By | Purpose |
|------|-----------|---------|---------|
| `scripts/briefing_actions.json` | weekly_audit.py | briefing_action_watcher.py | Maps action item checkboxes to structured metadata (customer, invoices, escalation) |
| `scripts/processed_briefing_actions.json` | briefing_action_watcher.py | briefing_action_watcher.py | Tracks which checked items have been processed (prevents double-triggering) |
| `scripts/audit_history.json` | weekly_audit.py | weekly_audit.py | Dedup guard — prevents running more than once per 7 days |
| `scripts/sent_reminders.json` | odoo_watcher.py | weekly_audit.py | Tracks reminder escalation levels and cooldowns per invoice |

### Config

| File | Purpose |
|------|---------|
| `scripts/audit_config.json` | Schedule day/hour, CEO phone, enabled sources, max action items |
| `.env` | `ODOO_PASSWORD` for Odoo authentication |

---

## Prerequisites

- Python 3.14 with `requests` installed (`pip install -r scripts/requirements.txt`)
- Odoo running at `localhost:8069` with valid `.env` credentials
- WhatsApp MCP server configured in Claude Code
- Claude CLI accessible from terminal (`claude -p` must work)
- Watcher state files in `scripts/` (populated by running gmail/whatsapp/odoo watchers)

---

## Testing: End-to-End Walkthrough

### Step 1: Generate the Briefing

```bash
python scripts/weekly_audit.py --once --force
```

**Expected console output:**
```
AUDIT RUN START: 2026-02-19 13:17:44
Authenticated with Odoo as uid=2
New invoices this week: 3
Outstanding invoices: 21 (total PKR 381045.00)
Overdue invoices: 10
Payments received this week: 0 (total PKR 0.00)
Built 3 customer invoice groups for action items
Generated 5 AI action items (3 automatable)
Saved briefing actions metadata to .../briefing_actions.json
Briefing note written to Needs_Action/YYYYMMDD_HHMMSS_Weekly_CEO_Briefing.md
WhatsApp summary sent to 923313777541@s.whatsapp.net
AUDIT RUN COMPLETE — Status: complete — Duration: ~74s
```

**Verify:**
- [ ] CEO receives WhatsApp summary on phone (condensed, under 1000 chars)
- [ ] `Needs_Action/` has a new `*_Weekly_CEO_Briefing.md` file
- [ ] `scripts/briefing_actions.json` exists with metadata for the briefing
- [ ] `scripts/audit_history.json` has a new run entry with `status: complete`

### Step 2: Review the Briefing in Obsidian

Open the briefing file in Obsidian. Verify the structure:

- **Executive Summary** — one-liner with payment and overdue highlights
- **Accounting** — payments received, new invoices, total outstanding, overdue aging table
- **Communications** — table with Email, WhatsApp, LinkedIn, HITL counts
- **Operations** — Done/Needs_Action/Plans file counts
- **Action Items** — mix of checkboxes (automatable) and plain bullets (advisory)

The last item should be a plain bullet (no checkbox) — that's an advisory item.

### Step 3: Start the Briefing Action Watcher

Open a **separate terminal** (not inside Claude Code):

```bash
cd D:\hackathon0-bronze
python scripts/briefing_action_watcher.py
```

**Expected output:**
```
Briefing Action Watcher — starting
Watching: D:\hackathon0-bronze\Needs_Action
Metadata: D:\hackathon0-bronze\scripts\briefing_actions.json
Checking every 10s
```

Leave this running.

### Step 4: Check an Action Item Checkbox

In Obsidian, check one of the automatable action items in the briefing (e.g., "Send second reminder to OpenWood..."). Change `[ ]` to `[x]`.

**Within ~10 seconds**, the watcher terminal should log:

```
Detected checked action item 2 in YYYYMMDD_..._Weekly_CEO_Briefing.md: Send second reminder...
Invoking /draft-payment-reminder for OpenWood...
Reminder drafted for OpenWood — check Plans/ for approval
Action item 2 processed successfully
```

**Verify:**
- [ ] `Plans/` now has a `Reminder_*_OpenWood.md` file
- [ ] The Plan file contains: overdue invoice table, proposed message, APPROVE/EDIT/REJECT checkboxes

### Step 5: Approve the Payment Reminder

Make sure `approval_watcher.py` is running (or start it in another terminal):

```bash
python scripts/approval_watcher.py
```

Open the Plan file in Obsidian. Review the proposed message, then check `[x] **APPROVE**`.

**Within ~10 seconds**, the approval watcher sends the message via WhatsApp or email.

**Verify:**
- [ ] Customer receives the payment reminder
- [ ] Plan file moves from `Plans/` to `Done/`
- [ ] `scripts/sent_reminders.json` is updated with the reminder record

### Step 6: Verify the Full Chain

The complete flow you just tested:

```
weekly_audit.py → briefing in Needs_Action/ + WhatsApp notification
    → CEO checks [x] action item in Obsidian
    → briefing_action_watcher.py creates Plans/Reminder_*.md
    → CEO checks [x] APPROVE in Obsidian
    → approval_watcher.py sends WhatsApp/email to customer
    → Plan file moves to Done/
```

---

## Testing: Dedup Guard

```bash
python scripts/weekly_audit.py --once
```

Should log `"Skipping — already ran within the last 7 days"` and exit. Use `--force` to bypass.

## Testing: Graceful Degradation

**Odoo down** — stop Odoo or change the password in `.env`:
```bash
python scripts/weekly_audit.py --once --force
```
- Briefing generated with `status: partial`, `sources_failed: [odoo]`
- Accounting section shows "Data unavailable" warning
- Other sections render normally

**Missing state file** — rename `processed_emails.json` temporarily:
```bash
mv scripts/processed_emails.json scripts/processed_emails.json.bak
python scripts/weekly_audit.py --once --force
mv scripts/processed_emails.json.bak scripts/processed_emails.json
```
- Email stats show 0, other channels unaffected

## Testing: Schedule Polling

Set `schedule_day` and `schedule_hour` in `audit_config.json` to match now, then:
```bash
python scripts/weekly_audit.py
```
- Within 60s: `"Schedule triggered — running audit"`
- Press `Ctrl+C`: clean exit with `"Shutdown complete"`
- Restore config after testing

## Testing: start_system.bat

Run `start_system.bat` — confirm 8 minimized windows appear:
1. Gmail Watcher
2. WhatsApp Watcher
3. Approval Watcher
4. Sentinel
5. LinkedIn Poster
6. Odoo Watcher
7. Weekly Audit
8. Briefing Action Watcher

---

## Unit Tests

```bash
python -m pytest tests/test_weekly_audit.py -v
```

For coverage:
```bash
python -m pytest tests/test_weekly_audit.py --cov=scripts.weekly_audit --cov-report=term-missing
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Skipping — already ran this week` | Dedup guard | Use `--force` or delete `audit_history.json` |
| Accounting "Data unavailable" | Odoo is down or wrong password | Check Odoo at `localhost:8069` and `.env` |
| No WhatsApp received | Claude CLI or MCP issue | Run `claude -p "test"` in terminal to verify |
| All communication counts zero | State files empty | Run gmail/whatsapp watchers first to populate |
| "No action items" | No overdue invoices in Odoo | Expected behavior — add test invoices |
| Checkbox checked but no Plan created | Watcher not running | Start `briefing_action_watcher.py` in a separate terminal |
| Watcher running but nothing happens | Old briefing without metadata | Re-run `weekly_audit.py --once --force` to generate new briefing with metadata |
| `Cannot import from weekly_audit` | Python path issue | Run watcher from project root: `cd D:\hackathon0-bronze && python scripts/briefing_action_watcher.py` |
| `Claude Code cannot be launched inside another session` | Running watcher from within Claude Code | Run in a standalone terminal, not inside Claude Code |
| Plan file created but message not sent | approval_watcher not running | Start `python scripts/approval_watcher.py` |
| Same action item triggers twice | Processed state corrupted | Check `scripts/processed_briefing_actions.json` |

---

## Resetting State (for re-testing)

```bash
# Reset the dedup guard (allows re-running the audit)
rm scripts/audit_history.json

# Reset action item processing (allows re-triggering checked items)
echo "[]" > scripts/processed_briefing_actions.json

# Reset briefing metadata
rm scripts/briefing_actions.json

# Clean up old briefings
rm Needs_Action/*CEO_Briefing*.md
```
