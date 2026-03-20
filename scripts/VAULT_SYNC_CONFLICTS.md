# Vault Git Sync - Conflict Handling Guide

## Overview

This guide explains how to prevent and resolve merge conflicts in the vault synchronization system.

## Architecture

```
┌─────────────────┐         Git Repo         ┌─────────────────┐
│   Local Machine │ ◄──────────────────────► │     Cloud VM    │
│                 │      (GitHub/GitLab)     │                 │
│   Manual Push   │                          │  Cron Pull      │
│   ./sync.sh push│                          │  */2 * * * *    │
└─────────────────┘                          └─────────────────┘
```

## Conflict Prevention

### 1. Workflow Rules

| Machine | Operation | Frequency |
|---------|-----------|-----------|
| **Local** | `push` | Manual (when you have changes) |
| **Cloud** | `pull` | Automatic (every 2 min via cron) |

### 2. Golden Rules

- **NEVER edit the same file on both machines simultaneously**
- **Always pull before push** if you haven't synced in a while
- **Cloud VM only pulls** - never push from cloud
- **Local machine only pushes** - never pull on local (unless resolving conflicts)

### 3. Pre-Push Checklist

```bash
# Before pushing from local:
./scripts/sync.sh status    # Check what changed
./scripts/sync.sh pull      # Get latest from cloud
./scripts/sync.sh push      # Now push your changes
```

## Conflict Resolution

### Automatic Resolution (Markdown Files)

The `sync.sh` script automatically resolves conflicts for `.md` files by keeping both versions:

```
Local content
--- Remote changes below ---
Remote content
```

### Manual Resolution Required

For non-markdown files, manual resolution is needed:

```bash
# 1. Check which files have conflicts
git status

# 2. View conflicts in each file
cat AI_Employee_Vault/SomeFile.txt

# 3. Choose resolution strategy:

# Option A: Keep local version (ours)
git checkout --ours <file>

# Option B: Keep remote version (theirs)
git checkout --theirs <file>

# Option C: Manual edit
# Edit the file to resolve <<<HEAD >>> markers
# Then stage the file
git add <file>

# 4. Complete the merge
git commit -m "Resolved merge conflicts"
```

### Emergency Reset

If conflicts become unmanageable:

```bash
# WARNING: This discards local changes!
cd AI_Employee_Vault

# Reset to match remote exactly
git fetch origin
git reset --hard origin/main

# Verify
./scripts/sync.sh status
```

## Troubleshooting

### Problem: "Push rejected - remote has changes"

```bash
# Solution: Pull first, then push
./scripts/sync.sh pull
./scripts/sync.sh push
```

### Problem: "Merge conflict in progress"

```bash
# Check status
git status

# Abort if needed
git merge --abort

# Or resolve conflicts and complete
git add <resolved_files>
git commit -m "Resolved conflicts"
```

### Problem: "Cron not pulling"

```bash
# Check cron is running
systemctl status cron

# Check cron logs
grep CRON /var/log/syslog

# Test manually
./scripts/sync.sh cron

# Check sync log
cat logs/vault_sync.log
```

### Problem: ".gitignore not working"

```bash
# Files already tracked won't be ignored
# Remove from git cache, then add to .gitignore
cd AI_Employee_Vault
git rm --cached <file>
git commit -m "Stop tracking <file>"
```

## Setup Instructions

### Initial Setup (One-time)

```bash
# 1. Create a new Git repository (GitHub/GitLab)
# 2. Clone it into AI_Employee_Vault
cd AI_Employee_Vault
git init
git remote add origin git@github.com:user/vault-sync.git

# 3. Copy .gitignore
cp ../.gitignore.vault .gitignore

# 4. Initial commit
git add .
git commit -m "Initial vault sync"
git push -u origin main

# 5. Setup on cloud VM (pull only)
./scripts/sync.sh setup
```

### Install Cron on Cloud VM

```bash
# Edit crontab
crontab -e

# Add this line (update path):
*/2 * * * * cd /path/to/Hack-03-AI-Employee-giaic && ./scripts/sync.sh cron

# Or use the provided file:
crontab -l 2>/dev/null | cat - scripts/vault_cron.txt | crontab -
```

## Best Practices

1. **Commit frequently** on local machine with meaningful messages
2. **Test sync** after setup: push from local, wait 2 min, verify on cloud
3. **Monitor logs**: `cat logs/vault_sync.log`
4. **Backup vault** before major changes
5. **Use branches** for experimental features

## Security Notes

- `.gitignore.vault` prevents `.env`, `tokens/`, `sessions/` from being committed
- Never commit credentials or secrets
- Use separate repos for sensitive data
- Enable 2FA on Git hosting service
