# AI Employee - Quick Deploy Reference

**24/7 Cloud VM Deployment Guide - Ubuntu 22.04 LTS**

---

## 🚀 Quick Start (Copy-Paste Commands)

### Step 1: Connect to VM & Update System

```bash
# SSH into your VM
ssh user@your-vm-ip

# Update system
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Dependencies

```bash
# Install required packages
sudo apt install -y git curl wget build-essential python3 python3-pip python3-venv nodejs npm

# Install PM2
sudo npm install -g pm2
```

### Step 3: Clone Project

```bash
# Create project directory
sudo mkdir -p /opt/ai-employee
sudo chown $USER:$USER /opt/ai-employee
cd /opt/ai-employee

# Clone or copy your project
git clone <YOUR_REPO_URL> .
# OR copy files manually
```

### Step 4: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

### Step 6: Create Required Directories

```bash
# Create vault and logs directories
mkdir -p AI_Employee_Vault/{Personal/Archive,Plans,Reports,Logs,Needs_Action,Done}
mkdir -p logs temp
chmod -R 755 AI_Employee_Vault logs temp
```

### Step 7: Start with PM2

```bash
# Make start script executable
chmod +x start.sh

# Start all processes
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Run the command it outputs
```

### Step 8: Verify Deployment

```bash
# Check all processes
pm2 status

# View logs
pm2 logs

# Monitor in real-time
pm2 monit
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `ecosystem.config.js` | PM2 process configuration |
| `start.sh` | Start/stop/restart script |
| `scripts/health_check.sh` | Health monitoring (run every 5 min) |
| `scripts/backup.sh` | Automated backups (run daily) |
| `deploy/setup_vm.sh` | Full VM setup automation |
| `deploy/ai-employee.service` | Systemd service file |
| `DEPLOYMENT.md` | Detailed deployment guide |

---

## 🔧 PM2 Commands Reference

```bash
# Start all processes
pm2 start ecosystem.config.js

# Stop all
pm2 stop all

# Restart all
pm2 restart all

# Reload (zero downtime)
pm2 reload all

# Check status
pm2 status

# Monitor
pm2 monit

# View logs
pm2 logs
pm2 logs orchestrator --lines 100

# Scale processes
pm2 scale orchestrator 2

# Delete stopped
pm2 delete stopped

# Save configuration
pm2 save

# Resurrect saved
pm2 resurrect
```

---

## 📊 Health Check Commands

```bash
# Run health check
./scripts/health_check.sh

# Verbose output
./scripts/health_check.sh --verbose

# Auto-fix issues
./scripts/health_check.sh --fix

# Add to crontab (every 5 minutes)
crontab -e
*/5 * * * * /opt/ai-employee/scripts/health_check.sh >> /opt/ai-employee/logs/health_check.log 2>&1
```

---

## 💾 Backup Commands

```bash
# Run backup
./scripts/backup.sh

# List backups
./scripts/backup.sh --list

# Add to crontab (daily at 2 AM)
crontab -e
0 2 * * * /opt/ai-employee/scripts/backup.sh >> /opt/ai-employee/logs/backup.log 2>&1
```

---

## 🔍 Monitoring & Troubleshooting

### Check Process Status

```bash
# PM2 status
pm2 status

# System resources
htop
free -h
df -h

# Network connections
netstat -tulpn
```

### View Logs

```bash
# All logs
pm2 logs

# Specific process
pm2 logs orchestrator

# Error logs only
pm2 logs --err

# Raw log files
tail -f logs/ai_employee.log
tail -f logs/social.log
```

### Common Issues

**Process won't start:**
```bash
pm2 logs orchestrator --err
sudo netstat -tulpn | grep :8069
```

**High memory usage:**
```bash
pm2 restart all
# Adjust max_memory_restart in ecosystem.config.js
```

**Disk full:**
```bash
df -h
du -ah /opt/ai-employee | sort -rh | head -20
sudo journalctl --vacuum-time=7d
```

---

## 🔐 Security Checklist

- [ ] Configure firewall (UFW)
- [ ] Enable SSL/HTTPS
- [ ] Set strong passwords in .env
- [ ] Never commit .env file
- [ ] Setup regular backups
- [ ] Configure log rotation
- [ ] Enable fail2ban
- [ ] Restrict sudo access

```bash
# Enable firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw status

# Setup log rotation
sudo nano /etc/logrotate.d/ai-employee
```

---

## 📈 Production Optimization

### Adjust PM2 Settings

Edit `ecosystem.config.js`:

```javascript
{
  instances: 2,              // Scale horizontally
  exec_mode: 'cluster',      // Cluster mode for scaling
  max_memory_restart: '1G',  // Auto-restart at 1GB
}
```

### Enable Docker for Odoo

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Start Odoo
cd docker
docker-compose up -d
```

### Setup SSL Certificate

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renew
sudo certbot renew --dry-run
```

---

## 🎯 Post-Deployment Checklist

- [ ] All PM2 processes online (`pm2 status`)
- [ ] Logs flowing (`pm2 logs`)
- [ ] Health check running (check cron)
- [ ] Backups configured (check cron)
- [ ] PM2 saved for auto-start (`pm2 save`)
- [ ] Firewall configured (`ufw status`)
- [ ] SSL enabled (if using domain)
- [ ] Monitoring alerts setup
- [ ] Documentation updated

---

## 📞 Support Commands

```bash
# Generate status report
pm2 status && pm2 logs --lines 50 --nostream

# Export PM2 logs
pm2 logs --json > pm2_logs.json

# System info
uname -a
python3 --version
node --version
pm2 --version
docker --version
```

---

**Deployment Complete!** 🎉

Your AI Employee system is now running 24/7 with:
- ✅ Auto-restart on crash
- ✅ Auto-start on boot
- ✅ Health monitoring
- ✅ Automated backups
- ✅ Log rotation

For detailed documentation, see `DEPLOYMENT.md`.
