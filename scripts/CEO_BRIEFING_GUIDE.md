# CEO Weekly Briefing Guide

## Overview

Automated weekly CEO briefing generated every Sunday morning. The briefing summarizes:
- Revenue from Accounting folder
- Completed tasks from /Done folder
- Pending approvals
- System issues and errors

## Schedule

| Setting | Value |
|---------|-------|
| **Frequency** | Weekly |
| **Day** | Sunday |
| **Time** | 8:00 AM |
| **Period Covered** | Previous Monday to Sunday |

## Output Location

```
AI_Employee_Vault/Briefings/YYYY-MM-DD_CEO_Briefing.md
```

Example: `AI_Employee_Vault/Briefings/2026-03-17_CEO_Briefing.md`

## Installation

### Step 1: Install Cron Job

```bash
# Update the path in the cron file
sed -i 's|/path/to/Hack-03-AI-Employee-giaic|/opt/ai-employee|g' scripts/ceo_briefing_cron.txt

# Install cron job
crontab -l 2>/dev/null | cat - scripts/ceo_briefing_cron.txt | crontab -

# Verify
crontab -l
```

### Step 2: Test Manually

```bash
# Run briefing generator
cd /opt/ai-employee
./venv/bin/python scripts/ceo_briefing.py

# Check output
cat AI_Employee_Vault/Briefings/*CEO_Briefing.md
```

### Step 3: Restart Cron

```bash
systemctl restart cron
```

## Data Sources

### Revenue (Accounting Folder)

Reads from: `AI_Employee_Vault/Accounting/`

**Recognized files:**
- Invoice files: `invoice_*.md`, `inv-*.md`
- Payment files: `payment_*.md`, `receipt_*.md`

**Extracted data:**
- Invoice amounts
- Payment amounts
- Paid/unpaid status

### Completed Tasks (Done Folder)

Reads from: `AI_Employee_Vault/Done/`

**Categories:**
| Pattern | Category |
|---------|----------|
| `email*` | Email |
| `*social*`, `*post*`, `*linkedin*` | Social Media |
| `*invoice*`, `*payment*` | Accounting |
| `*report*` | Reports |
| `*plan*` | Planning |
| `*brief*` | Briefings |

### Pending Approvals

Reads from: `AI_Employee_Vault/Pending_Approval/`

Shows all pending files with:
- Days pending
- Category (email/social/payments)
- Warning for items > 2 days

### Issues & Errors

Reads from:
- `AI_Employee_Vault/Logs/*.log`
- `AI_Employee_Vault/Logs/*.md`
- `AI_Employee_Vault/Rejected/`

Detects patterns:
- ERROR messages
- FAILED operations
- EXCEPTION errors
- CRITICAL issues
- Rejected items

## Usage

### Generate Current Week Briefing

```bash
python scripts/ceo_briefing.py
```

### Generate Specific Week

```bash
# Briefing for week starting March 10, 2026
python scripts/ceo_briefing.py --week-start 2026-03-10
```

### Preview Without Saving

```bash
python scripts/ceo_briefing.py --dry-run
```

### Custom Output Folder

```bash
python scripts/ceo_briefing.py --output /custom/output/path
```

## Briefing Structure

```
# CEO Weekly Briefing
│
├── Executive Summary
│   └── Key Highlights
│
├── Revenue Summary
│   ├── Total Revenue
│   ├── Paid Invoices
│   ├── Pending Invoices
│   └── Invoice/Payment Counts
│
├── Completed Tasks
│   ├── Total Count
│   ├── By Category
│   └── By Day
│
├── Pending Approvals
│   ├── Total Pending
│   └── List with Days Pending
│
├── Issues & Errors
│   └── Top Issues by Frequency
│
└── Recommendations
    └── Action Items
```

## Cron Schedule Options

### Default (Sunday 8 AM)
```cron
0 8 * * 0
```

### Alternative Schedules

| Schedule | Cron | Description |
|----------|------|-------------|
| Sunday 6 AM | `0 6 * * 0` | Earlier briefing |
| Sunday 9 AM | `0 9 * * 0` | Later briefing |
| Monday 7 AM | `0 7 * * 1` | Previous week review |
| Bi-weekly | `0 8 1,15 * *` | 1st and 15th |

## Integration

### Email Delivery

Add email delivery after briefing generation:

```bash
# Add to crontab
30 8 * * 0 cd /opt/ai-employee && ./venv/bin/python scripts/send_briefing_email.py
```

### Slack/Teams Notification

```bash
# Add to crontab
35 8 * * 0 cd /opt/ai-employee && curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"New CEO Briefing available!"}' \
  $SLACK_WEBHOOK_URL
```

### Git Sync

Briefings are automatically synced via Git vault sync:

```
Briefing Generated → Git Sync → Cloud/Local
```

## Troubleshooting

### Briefing Not Generated

**Check cron logs:**
```bash
grep CRON /var/log/syslog | grep ceo_briefing
```

**Check briefing logs:**
```bash
tail -f logs/ceo_briefing.log
```

**Test manually:**
```bash
./venv/bin/python scripts/ceo_briefing.py
```

### No Revenue Data

**Check accounting folder:**
```bash
ls -la AI_Employee_Vault/Accounting/
```

**Verify invoice format:**
```markdown
---
invoice_number: INV-001
amount: $1000.00
status: paid
---
```

### No Tasks Showing

**Check Done folder:**
```bash
ls -la AI_Employee_Vault/Done/
```

**Verify file dates:**
```bash
stat AI_Employee_Vault/Done/some_file.md
```

### Permission Issues

```bash
# Ensure write access to Briefings folder
chmod 755 AI_Employee_Vault/Briefings/
```

## Customization

### Modify Revenue Extraction

Edit `scripts/ceo_briefing.py`:

```python
class RevenueCollector:
    def _extract_amount(self, content: str):
        # Add custom patterns
        patterns = [
            r'\$[\d,]+\.?\d*',
            r'EUR[\d,]+\.?\d*',  # Euro support
            # Add more...
        ]
```

### Add Custom Categories

```python
class TaskCollector:
    def _categorize(self, file_path: Path) -> str:
        name = file_path.name.lower()
        
        # Add custom category
        if 'contract' in name:
            return 'Legal'
        
        # ... existing code
```

### Change Briefing Day

Edit crontab:
```bash
crontab -e
# Change: 0 8 * * 0 → 0 8 * * 1 (Monday)
```

## Best Practices

1. **Review briefings weekly** - Set calendar reminder
2. **Clear pending approvals** - Keep queue manageable
3. **Archive old briefings** - Keep last 12 weeks
4. **Monitor revenue trends** - Track week-over-week
5. **Address recurring issues** - Investigate patterns

## Example Output

See `CEO_BRIEFING_TEMPLATE.md` for sample briefing format.

## Quick Reference

```bash
# Install
crontab -l 2>/dev/null | cat - scripts/ceo_briefing_cron.txt | crontab -

# Test
python scripts/ceo_briefing.py

# View latest
cat AI_Employee_Vault/Briefings/*CEO_Briefing.md | tail -50

# Check logs
tail -f logs/ceo_briefing.log
```
