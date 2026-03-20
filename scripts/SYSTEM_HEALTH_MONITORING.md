# System Health Monitoring Guide

## Overview

The System Watchdog monitors all AI Employee processes (orchestrator and watchers), automatically restarts failed processes, and logs health status every 5 minutes.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SYSTEM WATCHDOG                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐ │
│  │  Process Monitor │────▶│   Health Check   │────▶│ Auto-Restart │ │
│  │  (PM2 status)    │     │   (Every 1 min)  │     │   (if down)  │ │
│  └──────────────────┘     └──────────────────┘     └──────────────┘ │
│                                    │                                  │
│                                    ▼                                  │
│                            ┌──────────────────┐                      │
│                            │  Health Logger   │                      │
│                            │  (Every 5 min)   │                      │
│                            └──────────────────┘                      │
│                                    │                                  │
│                                    ▼                                  │
│                    /vault/Logs/system_health.md                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Monitored Processes

### Critical Processes (Must be running)
| Process | Description |
|---------|-------------|
| `orchestrator` | Main orchestrator - coordinates all watchers |
| `orchestrator_gold` | Enhanced orchestrator with social/Odoo |

### Watcher Processes
| Process | Description |
|---------|-------------|
| `gmail_watcher` | Monitors Gmail for new emails |
| `linkedin_watcher` | Monitors LinkedIn notifications |
| `linkedin_poster` | Auto-posts LinkedIn content |
| `facebook_watcher` | Monitors Facebook/Instagram |
| `twitter_watcher` | Monitors Twitter/X |
| `whatsapp_watcher` | Monitors WhatsApp messages |
| `filesystem_watcher` | Monitors file system changes |

### Support Processes
| Process | Description |
|---------|-------------|
| `health_monitor` | Built-in health monitoring |
| `git_sync` | Vault Git synchronization |
| `mcp_executor` | MCP server actions |

## Installation

### Option 1: PM2 (Recommended)

**1. Add watchdog to PM2 ecosystem:**

```bash
# Copy watchdog config to ecosystem
cat scripts/watchdog.pm2.config.js >> ecosystem.config.js

# Or add manually to ecosystem.config.js apps array

# Start watchdog
pm2 start ecosystem.config.js --only system_watchdog

# Verify
pm2 status
```

**2. Auto-start on boot:**

```bash
pm2 startup
pm2 save
```

### Option 2: Cron Job

**1. Install cron job:**

```bash
# Update path in watchdog_cron.txt first
sed -i 's|/path/to/Hack-03-AI-Employee-giaic|/opt/ai-employee|g' scripts/watchdog_cron.txt

# Install cron
crontab -l 2>/dev/null | cat - scripts/watchdog_cron.txt | crontab -

# Verify
crontab -l
```

**2. Restart cron service:**

```bash
systemctl restart cron
```

### Option 3: Systemd Service

**1. Install service:**

```bash
# Update paths in service file
sed -i 's|/opt/ai-employee|/path/to/your/project|g' scripts/watchdog.service

# Copy to systemd
sudo cp scripts/watchdog.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable watchdog
sudo systemctl start watchdog

# Check status
sudo systemctl status watchdog
```

## Usage

### Commands

```bash
# Single health check (check and restart if needed)
python scripts/watchdog.py check

# Show current status and write health report
python scripts/watchdog.py status

# Run continuously (foreground)
python scripts/watchdog.py run

# Restart specific process
python scripts/watchdog.py restart --process orchestrator
```

### PM2 Commands

```bash
# Start watchdog
pm2 start system_watchdog

# Stop watchdog
pm2 stop system_watchdog

# Restart watchdog
pm2 restart system_watchdog

# View logs
pm2 logs system_watchdog

# Monitor
pm2 monit
```

## Health Report

### Location
```
/vault/Logs/system_health.md
AI_Employee_Vault/Logs/system_health.md
```

### Format

```markdown
# System Health Report

**Generated:** 2026-03-19 10:30:00
**Overall Status:** 🟢 HEALTHY

## Summary

| Metric | Value |
|--------|-------|
| Total Processes | 12 |
| Running | 12 ✅ |
| Stopped | 0 ⏹️ |
| Errored | 0 ❌ |

## Process Status

### Critical Processes
| Process | Status | PID | Memory | CPU | Uptime |
|---------|--------|-----|--------|-----|--------|
| orchestrator | ✅ online | 1234 | 256.5MB | 2.3% | 2d |
| orchestrator_gold | ✅ online | 1235 | 312.1MB | 1.8% | 2d |

...
```

### Status Indicators

| Icon | Status | Meaning |
|------|--------|---------|
| 🟢 | HEALTHY | All critical processes running |
| 🟡 | DEGRADED | Some non-critical processes down |
| 🔴 | CRITICAL | Critical processes down |

## Auto-Restart Behavior

### Restart Rules

1. **Cooldown Period**: 30 seconds between restarts of same process
2. **Max Attempts**: 3 restart attempts before giving up
3. **Counter Reset**: Reset when process stays healthy

### Restart Flow

```
Process Down
     │
     ▼
Check Cooldown ────▶ Wait ────▶ Retry
     │
     ▼ (OK)
Restart Process
     │
     ▼
Check Status ────▶ Failed ────▶ Increment Counter
     │
     ▼ (OK)
Reset Counter
```

## Troubleshooting

### Watchdog Not Starting Processes

**Check PM2 is installed:**
```bash
pm2 --version
```

**Check permissions:**
```bash
pm2 list
```

**Check watchdog logs:**
```bash
tail -f logs/watchdog_cron.log
# or
pm2 logs system_watchdog
```

### Processes Keep Crashing

**Check process logs:**
```bash
pm2 logs orchestrator --lines 50
```

**Check memory limits:**
```bash
pm2 monit
```

**Check error logs:**
```bash
cat logs/pm2_orchestrator_error.log
```

### Health Report Not Updating

**Check log location:**
```bash
ls -la AI_Employee_Vault/Logs/
```

**Check permissions:**
```bash
chmod 755 AI_Employee_Vault/Logs/
```

**Manually trigger:**
```bash
python scripts/watchdog.py status
```

### Cron Not Running

**Check cron status:**
```bash
systemctl status cron
```

**Check cron logs:**
```bash
grep CRON /var/log/syslog | grep watchdog
```

**Test manually:**
```bash
./venv/bin/python scripts/watchdog.py check
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VAULT_PATH` | `./AI_Employee_Vault` | Path to vault directory |
| `HEALTH_LOG_INTERVAL` | `300` | Seconds between health logs |
| `STATUS_CHECK_INTERVAL` | `60` | Seconds between status checks |
| `MAX_RESTART_ATTEMPTS` | `3` | Max restart attempts per process |
| `RESTART_COOLDOWN_SECONDS` | `30` | Cooldown between restarts |

### Customizing Monitored Processes

Edit `scripts/watchdog.py`:

```python
CRITICAL_PROCESSES = [
    "orchestrator",
    "orchestrator_gold",
    # Add more...
]

WATCHER_PROCESSES = [
    "gmail_watcher",
    # Add more...
]
```

## Integration

### With Git Sync

Watchdog logs to vault, which syncs via Git:

```
Watchdog → system_health.md → Git Sync → Cloud/Local
```

### With Health Monitor

Built-in `health_monitor` process provides additional monitoring:

```bash
pm2 logs health_monitor
```

### With Notification System

Add email/WhatsApp alerts for critical failures:

```python
# In watchdog.py check_and_heal()
if proc.name in CRITICAL_PROCESSES and proc.status == "errored":
    send_alert(f"Critical process {proc.name} failed!")
```

## Best Practices

1. **Use PM2** for production (better process management)
2. **Monitor watchdog itself** (add to external monitoring)
3. **Rotate logs** regularly (cron job included)
4. **Set up alerts** for critical failures
5. **Review health reports** daily
6. **Tune thresholds** based on your usage

## Quick Reference

```bash
# Install (PM2)
pm2 start ecosystem.config.js --only system_watchdog
pm2 save

# Install (Cron)
crontab -l 2>/dev/null | cat - scripts/watchdog_cron.txt | crontab -

# Check status
python scripts/watchdog.py status

# View health report
cat AI_Employee_Vault/Logs/system_health.md

# View logs
pm2 logs system_watchdog
```
