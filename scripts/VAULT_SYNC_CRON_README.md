# Vault Git Sync - Cron Activation Guide

## Quick Start

### Activate Cron (Cloud VM)

```bash
cd /path/to/Hack-03-AI-Employee-giaic
bash scripts/setup_cron.sh
```

### Verify Installation

```bash
# List cron jobs
crontab -l

# Should show:
# */2 * * * * cd /path/to/project && ./venv/bin/python git_sync.py pull >> logs/git_sync.log 2>&1
```

### Test Manual Pull

```bash
cd /path/to/Hack-03-AI-Employee-giaic
./venv/bin/python git_sync.py pull
```

### Monitor Logs

```bash
# Watch sync logs in real-time
tail -f logs/git_sync.log

# Check cron execution logs
grep CRON /var/log/syslog | grep git_sync
```

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `bash scripts/setup_cron.sh` | Install/update cron job (idempotent) |
| `crontab -l` | List installed cron jobs |
| `crontab -e` | Edit cron jobs manually |
| `python git_sync.py pull` | Manual vault pull |
| `python git_sync.py status` | Check Git repository status |
| `tail -f logs/git_sync.log` | Watch sync logs |
| `grep CRON /var/log/syslog` | Check cron execution history |

---

## Troubleshooting

### Cron Not Running

```bash
# Check cron service status
systemctl status cron

# Start if needed
sudo systemctl start cron
sudo systemctl enable cron
```

### Permission Denied

```bash
# Make scripts executable
chmod +x scripts/setup_cron.sh
chmod +x git_sync.py
```

### Git Pull Fails

```bash
# Check Git configuration
cd AI_Employee_Vault
git status
git remote -v

# Test pull manually
git pull origin main
```

### Logs Not Appearing

```bash
# Ensure logs directory exists
mkdir -p logs

# Check file permissions
chmod 644 logs/git_sync.log
```

---

## Expected Output

### Successful Setup

```
==============================================
Vault Git Sync - Cron Setup
==============================================

Project Root: /opt/ai-employee
Cron Config:  /opt/ai-employee/scripts/vault_cron.txt

[1/4] Ensuring logs directory exists...
  ✅ Exists: /opt/ai-employee/logs
[2/4] Updating cron configuration...
  ✅ Updated cron file with project path
[3/4] Removing existing vault sync cron jobs...
  ✅ No existing vault sync cron jobs found
[4/4] Installing new cron job...
  ✅ Cron job installed

==============================================
SETUP COMPLETE
==============================================

Installed cron jobs:
*/2 * * * * cd /opt/ai-employee && ./venv/bin/python git_sync.py pull >> logs/git_sync.log 2>&1

Verification commands:
  crontab -l                    # List all cron jobs
  tail -f /opt/ai-employee/logs/git_sync.log  # Watch sync logs

Cron will start syncing within 2 minutes.
```

### Successful Pull

```
============================================================
PLATINUM TIER - VAULT GIT SYNC
============================================================

Mode: Pull Only (Cloud)
Remote: https://github.com/user/ai-employee-vault.git

=== Cloud Vault Pull Mode ===
Pulling changes from remote...
Pull completed: Already up to date.

Pull: ✅ Success

============================================================
```

### Log Output

```
2026-03-19 10:00:01,234 - git_sync - INFO - === Cloud Vault Pull Mode ===
2026-03-19 10:00:01,456 - git_sync - INFO - Pulling changes from remote...
2026-03-19 10:00:02,789 - git_sync - INFO - Pull completed (no changes)
2026-03-19 10:02:01,123 - git_sync - INFO - === Cloud Vault Pull Mode ===
2026-03-19 10:02:01,345 - git_sync - INFO - Pulling changes from remote...
2026-03-19 10:02:02,678 - git_sync - INFO - Pull completed: 1 file changed, 3 insertions(+)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD VM                                  │
│                                                              │
│  ┌──────────────┐                                           │
│  │    Cron      │                                           │
│  │  (*/2 * * * *)│                                          │
│  └──────┬───────┘                                           │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  git_sync.py pull                                     │  │
│  │  - Auto-stash local changes                          │  │
│  │  - Fetch from remote                                 │  │
│  │  - Pull with --autostash                             │  │
│  │  - Log to logs/git_sync.log                          │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AI_Employee_Vault/                                   │  │
│  │  - /Updates/ (Cloud → Local)                         │  │
│  │  - /Signals/ (urgent alerts)                         │  │
│  │  - /Plans/ (task plans)                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Git Remote (GitHub/GitLab)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL MACHINE                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AI_Employee_Vault/                                   │  │
│  │  - Pulls /Updates/ from Cloud                        │  │
│  │  - Merges to Dashboard.md                            │  │
│  │  - Pushes /Approved/, /Done/                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Notes

- ✅ Secrets never sync (.env, tokens, sessions excluded via .gitignore)
- ✅ Auto-stash preserves local changes safely
- ✅ Timeout protection (30s fetch, 60s pull)
- ✅ Rebase abort on failure (prevents stuck state)
- ✅ Idempotent setup (safe to run multiple times)

---

*Platinum Tier - Production Ready*
