# CEO Briefing Skill - README

## Overview

Automated weekly CEO briefing generator for the AI Employee system. Aggregates data from all subsystems to create comprehensive executive reports.

**Output:** `AI_Employee_Vault/Reports/CEO_Weekly.md`

---

## Quick Start

### Generate Weekly Briefing

```bash
# Auto mode (last week)
python scripts/ceo_briefing.py auto

# Manual date range
python scripts/ceo_briefing.py weekly --start 2026-03-10 --end 2026-03-16

# Test mode
python scripts/ceo_briefing.py test
```

### Python Import

```python
from scripts.ceo_briefing import CEOBriefing

briefing = CEOBriefing(vault_path="AI_Employee_Vault")
result = briefing.generate_weekly_briefing()

print(f"Briefing: {result['briefing_file']}")
```

---

## Auto-Run Scheduler

### Windows Task Scheduler

1. Open **Task Scheduler**
2. **Create Basic Task**
3. Name: "CEO Weekly Briefing"
4. Trigger: **Weekly**
5. Day: **Monday**
6. Time: **7:00 AM**
7. Action: **Start a program**
8. Program: `python`
9. Arguments: `scripts/ceo_briefing.py auto`
10. Start in: `E:\New folder\GIAIC-Q4\sub-hack03\Hack-03-AI-Employee-giaic`

### Linux/Mac Cron

```bash
# Edit crontab
crontab -e

# Add: Every Monday at 7:00 AM
0 7 * * 1 cd /path/to/project && python scripts/ceo_briefing.py auto
```

---

## Briefing Sections

1. **Executive Summary** - Key metrics overview
2. **Tasks Completed** - All tasks from Done folder
3. **Emails Sent** - Email activity from logs
4. **Social Media Activity** - LinkedIn, Facebook, Twitter, Instagram
5. **Pending Approvals** - Items requiring attention
6. **Financial Summary** - Income/Expense from Accounting Manager
7. **System Health** - Status of all watchers and components
8. **Key Highlights** - Auto-generated achievements
9. **Action Items** - Pending items requiring attention

---

## Configuration

### Environment Variables

```env
VAULT_PATH=AI_Employee_Vault
BRIEFING_OUTPUT_PATH=AI_Employee_Vault/Reports
BRIEFING_SCHEDULE=0 7 * * 1  # Monday 7:00 AM
```

---

## Testing

```bash
python scripts/test_ceo_briefing.py
```

---

## Integration

### Accounting Manager

Automatically integrates with `accounting_manager.py` for financial data.

### Task System

Reads completed tasks from `AI_Employee_Vault/Done/`.

### Logs

Parses logs from `AI_Employee_Vault/Logs/`.

---

## Output Example

See `SKILL.md` for complete briefing structure example.

---

## Troubleshooting

1. **No data in briefing** - Ensure watchers are logging activity
2. **Financial summary empty** - Check Accounting Manager is configured
3. **System health warnings** - Review component status in briefing

---

**CEO Briefing Skill** - Automated executive reporting ✅
