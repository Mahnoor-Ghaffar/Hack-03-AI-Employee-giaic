# AI Employee - 24/7 Cloud Deployment Summary

**Complete deployment package for running AI Employee on Ubuntu 22.04 LTS**

---

## 📦 Deployment Files Overview

| File | Location | Purpose |
|------|----------|---------|
| `DEPLOYMENT.md` | Root | Complete step-by-step deployment guide |
| `QUICK_DEPLOY.md` | Root | Quick reference commands |
| `ecosystem.config.js` | Root | PM2 process configuration |
| `start.sh` | Root | Start/stop/restart script |
| `requirements.txt` | Root | Python dependencies (updated for production) |
| `scripts/health_check.sh` | scripts/ | Health monitoring script |
| `scripts/backup.sh` | scripts/ | Automated backup script |
| `deploy/setup_vm.sh` | deploy/ | Full VM setup automation |
| `deploy/ai-employee.service` | deploy/ | Systemd service file |

---

## 🚀 Quick Deploy (5 Minutes)

```bash
# 1. SSH to VM
ssh user@your-vm-ip

# 2. Update system
sudo apt update && sudo apt upgrade -y

# 3. Install Node.js & PM2
sudo apt install -y nodejs npm
sudo npm install -g pm2

# 4. Clone project
git clone <YOUR_REPO> /opt/ai-employee
cd /opt/ai-employee

# 5. Setup Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install

# 6. Configure
cp .env.example .env
nano .env  # Edit credentials

# 7. Create directories
mkdir -p AI_Employee_Vault/{Personal/Archive,Plans,Reports,Logs,Needs_Action,Done}
mkdir -p logs temp

# 8. Start with PM2
chmod +x start.sh
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Run the output command

# 9. Verify
pm2 status
pm2 monit
```

---

## 📋 Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Ubuntu 22.04 LTS VM                      │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              PM2 Process Manager                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │Orchestrator  │  │Gmail Watcher │  │LinkedIn     │ │ │
│  │  │(Gold Tier)   │  │              │  │Watcher      │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │Facebook      │  │Twitter       │  │WhatsApp     │ │ │
│  │  │Watcher       │  │Watcher       │  │Watcher      │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │Filesystem    │  │Health        │  │Git Sync     │ │ │
│  │  │Watcher       │  │Monitor       │  │             │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  │  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │MCP Executor  │  │LinkedIn      │                  │ │
│  │  │              │  │Poster        │                  │ │
│  │  └──────────────┘  └──────────────┘                  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Docker Containers                         │ │
│  │  ┌──────────────┐  ┌──────────────┐                   │ │
│  │  │Odoo 19       │  │PostgreSQL    │                   │ │
│  │  │Community     │  │Database      │                   │ │
│  │  └──────────────┘  └──────────────┘                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Storage                                   │ │
│  │  - /opt/ai-employee/AI_Employee_Vault/                │ │
│  │  - /opt/ai-employee/logs/                             │ │
│  │  - /opt/backups/ai-employee/                          │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 PM2 Configuration Summary

**Processes Managed:**

| Process | Script | Max Memory | Restart Delay |
|---------|--------|------------|---------------|
| orchestrator | orchestrator.py | 512MB | 4s |
| orchestrator_gold | orchestrator_gold.py | 768MB | 4s |
| gmail_watcher | gmail_watcher.py | 256MB | 4s |
| linkedin_watcher | linkedin_watcher.py | 256MB | 4s |
| linkedin_poster | linkedin_poster.py | 256MB | 4s |
| facebook_watcher | facebook_watcher.py | 256MB | 4s |
| twitter_watcher | twitter_watcher.py | 256MB | 4s |
| whatsapp_watcher | whatsapp_watcher.py | 512MB | 4s |
| filesystem_watcher | filesystem_watcher.py | 256MB | 4s |
| health_monitor | health_monitor.py | 128MB | 4s |
| git_sync | git_sync.py | 128MB | 4s |
| mcp_executor | mcp_executor.py | 256MB | 4s |

**Features:**
- ✅ Auto-restart on crash
- ✅ Max memory restart limits
- ✅ Log rotation
- ✅ Graceful shutdown (3s timeout)
- ✅ Environment variables per process

---

## 📊 Health Check Features

**Monitored:**
- PM2 process status (online/offline)
- Process restart count
- Process memory usage
- Process CPU usage
- System disk space
- System memory usage
- Log file sizes
- Vault directory integrity
- Odoo container status
- Network connectivity

**Actions:**
- Alerts via email (if configured)
- Auto-restart failed processes (with --fix)
- Log cleanup (old files)
- System journal logging

**Schedule:** Every 5 minutes via cron

---

## 💾 Backup Strategy

**What's Backed Up:**
- AI_Employee_Vault/ (excluding cache)
- .env file (secured with 600 permissions)
- PM2 process list
- Recent logs (last 7 days)

**Retention:** 30 days

**Schedule:** Daily at 2 AM via cron

**Location:** `/opt/backups/ai-employee/`

---

## 🔐 Security Features

| Feature | Implementation |
|---------|----------------|
| Firewall | UFW with SSH, HTTP, HTTPS, Odoo ports |
| SSL/TLS | Let's Encrypt via Certbot |
| Environment | .env with 600 permissions |
| User Isolation | Dedicated `ai-employee` user |
| Process Limits | Memory limits per process |
| Log Rotation | 14 days retention, compressed |
| Auto-Updates | System packages, manual app updates |
| Docker Security | Container isolation for Odoo |

---

## 📈 Resource Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB SSD
- OS: Ubuntu 22.04 LTS

**Recommended:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 40GB SSD
- OS: Ubuntu 22.04 LTS

**Estimated Usage:**
- Base system: ~500MB RAM
- All watchers: ~1.5GB RAM
- Odoo (Docker): ~1GB RAM
- Total: ~3GB RAM average

---

## 🔍 Monitoring Commands

```bash
# Real-time monitoring
pm2 monit

# Process status
pm2 status

# View logs
pm2 logs
pm2 logs orchestrator --lines 100

# System resources
htop
free -h
df -h

# Network
netstat -tulpn

# Docker containers
docker ps
docker-compose ps

# Health check (manual)
./scripts/health_check.sh --verbose
```

---

## 🛠️ Troubleshooting

### Process Won't Start

```bash
# Check logs
pm2 logs orchestrator --err

# Check port conflicts
sudo netstat -tulpn | grep :8069

# Restart process
pm2 restart orchestrator

# Check Python dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### High Memory Usage

```bash
# Check memory
free -h

# Restart all processes
pm2 restart all

# Adjust limits in ecosystem.config.js
```

### Disk Full

```bash
# Check usage
df -h

# Find large files
du -ah /opt/ai-employee | sort -rh | head -20

# Clean old logs
find /opt/ai-employee/logs -name "*.log" -mtime +7 -delete
sudo journalctl --vacuum-time=7d
```

### Odoo Connection Failed

```bash
# Check container
docker-compose ps

# View Odoo logs
docker-compose logs odoo

# Restart Odoo
docker-compose restart odoo
```

---

## 📞 Support & Maintenance

### Daily Tasks (Automated)
- Health checks every 5 minutes
- Backups at 2 AM
- Log rotation daily

### Weekly Tasks
- Review error logs
- Check disk space trends
- Verify backups are working

### Monthly Tasks
- Update system packages
- Review resource usage
- Rotate credentials
- Test backup restoration

### Commands
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update Python packages
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Test backup restoration
./scripts/backup.sh --restore

# View backup status
./scripts/backup.sh --list
```

---

## 🎯 Post-Deployment Checklist

- [ ] All PM2 processes online (`pm2 status`)
- [ ] Health check running (check crontab)
- [ ] Backups configured (check crontab)
- [ ] PM2 saved for auto-start (`pm2 save`)
- [ ] Firewall configured (`ufw status`)
- [ ] SSL enabled (if using domain)
- [ ] Odoo container running
- [ ] Vault directories created
- [ ] .env file configured (not committed!)
- [ ] Monitoring alerts setup

---

**Deployment Complete!** 🎉

Your AI Employee system is now running 24/7 with:
- ✅ Auto-restart on crash
- ✅ Auto-start on boot
- ✅ Health monitoring every 5 minutes
- ✅ Daily automated backups
- ✅ Log rotation
- ✅ Production security hardening

For detailed documentation, see `DEPLOYMENT.md`.
For quick commands, see `QUICK_DEPLOY.md`.
