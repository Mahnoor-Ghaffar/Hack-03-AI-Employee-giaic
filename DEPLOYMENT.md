# AI Employee - 24/7 Cloud VM Deployment Guide

**Version:** 1.0.0  
**Target:** Ubuntu 22.04 LTS  
**Status:** Production Ready

---

## Overview

This guide provides step-by-step instructions for deploying the AI Employee system on a Linux cloud VM for 24/7 operation with:

- ✅ PM2 process management
- ✅ Auto-restart on crash
- ✅ Auto-start on system reboot
- ✅ Health monitoring
- ✅ Log rotation
- ✅ Resource limits

---

## Prerequisites

- Ubuntu 22.04 LTS VM (minimum 2GB RAM, 2 CPU cores)
- Root or sudo access
- Domain name (optional, for HTTPS)
- Git installed

---

## Step 1: System Update & Package Installation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    git \
    curl \
    wget \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libpq-dev \
    gcc \
    nodejs \
    npm \
    nginx \
    certbot \
    python3-certbot-nginx \
    htop \
    net-tools \
    ufw \
    fail2ban
```

---

## Step 2: Install Python 3.10+ (if needed)

```bash
# Add deadsnakes PPA for latest Python
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.10
sudo apt install -y python3.10 python3.10-venv python3.10-dev

# Verify Python version
python3.10 --version
```

---

## Step 3: Install Node.js 18+ (for PM2)

```bash
# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify Node.js and npm versions
node --version
npm --version
```

---

## Step 4: Install PM2 Process Manager

```bash
# Install PM2 globally
sudo npm install -g pm2

# Setup PM2 to start on boot
pm2 startup
# Run the command it outputs (e.g., sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u youruser --hp /home/youruser)
```

---

## Step 5: Clone Project Repository

```bash
# Create application directory
sudo mkdir -p /opt/ai-employee
sudo chown $USER:$USER /opt/ai-employee

# Clone repository (replace with your repo URL)
cd /opt/ai-employee
git clone <YOUR_REPOSITORY_URL> .

# Or copy existing project
# rsync -avz /local/path/to/project/ user@vm:/opt/ai-employee/
```

---

## Step 6: Setup Python Virtual Environment

```bash
cd /opt/ai-employee

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn psycopg2-binary
```

---

## Step 7: Configure Environment Variables

```bash
cd /opt/ai-employee

# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

**Required Environment Variables:**

```bash
# =============================================================================
# ODOO ERP CONFIGURATION
# =============================================================================
ODOO_URL=http://localhost:8069
ODOO_DB=odoo_db
ODOO_USERNAME=admin
ODOO_PASSWORD=YourSecureOdooPassword123!

# =============================================================================
# SOCIAL MEDIA CONFIGURATION
# =============================================================================
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
TWITTER_ACCESS_TOKEN=your-twitter-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-twitter-access-token-secret
TWITTER_BEARER_TOKEN=your-twitter-bearer-token

FACEBOOK_PAGE_ID=your-page-id
FACEBOOK_ACCESS_TOKEN=your-facebook-access-token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your-ig-account-id
INSTAGRAM_ACCESS_TOKEN=your-instagram-access-token

# =============================================================================
# GMAIL CONFIGURATION
# =============================================================================
GMAIL_CLIENT_ID=your-gmail-client-id
GMAIL_CLIENT_SECRET=your-gmail-client-secret
GMAIL_REDIRECT_URI=http://localhost:8080
GMAIL_TOKEN_FILE=gmail_token.json
GMAIL_SENDER_EMAIL=your-email@gmail.com

# =============================================================================
# LINKEDIN CONFIGURATION
# =============================================================================
LINKEDIN_EMAIL=your-linkedin-email@example.com
LINKEDIN_PASSWORD=YourLinkedInPassword123!

# =============================================================================
# SYSTEM CONFIGURATION
# =============================================================================
VAULT_PATH=/opt/ai-employee/AI_Employee_Vault
LOG_LEVEL=INFO
LOG_FILE=/opt/ai-employee/logs/ai_employee.log
DEBUG_MODE=false

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
SOCIAL_AUTO_APPROVE_LIMIT=0
INVOICE_AUTO_APPROVE_LIMIT=0
PAYMENT_AUTO_APPROVE_LIMIT=0
```

---

## Step 8: Create Required Directories

```bash
cd /opt/ai-employee

# Create vault directories
mkdir -p AI_Employee_Vault/{Personal/Archive,Plans,Reports,Logs,Needs_Action,Done,Pending_Approval,Social_Media,Accounting,Briefings}

# Create logs directory
mkdir -p logs

# Create temp directory
mkdir -p temp

# Set proper permissions
chmod -R 755 AI_Employee_Vault logs temp
chown -R $USER:$USER AI_Employee_Vault logs temp
```

---

## Step 9: Configure Firewall

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow ssh

# Allow HTTP/HTTPS (if running web services)
sudo ufw allow http
sudo ufw allow https

# Allow Odoo port (if running locally)
sudo ufw allow 8069/tcp

# Check firewall status
sudo ufw status verbose
```

---

## Step 10: Setup SSL/HTTPS (Optional but Recommended)

```bash
# If you have a domain name pointing to your VM

# Install SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renew SSL
sudo certbot renew --dry-run
```

---

## Step 11: Deploy Odoo ERP (Docker)

```bash
cd /opt/ai-employee

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Start Odoo containers
cd docker
docker-compose up -d

# Check container status
docker-compose ps
```

---

## Step 12: Deploy AI Employee with PM2

```bash
cd /opt/ai-employee

# Make start script executable
chmod +x start.sh

# Start all processes with PM2
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Monitor processes
pm2 monit

# View logs
pm2 logs

# Check process status
pm2 status
```

---

## Step 13: Verify Deployment

```bash
# Check all processes are running
pm2 status

# View real-time logs
pm2 logs --lines 100

# Check system resources
htop

# Check disk space
df -h

# Test Odoo connection
curl http://localhost:8069

# Check vault directories
ls -la AI_Employee_Vault/
```

---

## Step 14: Setup Health Monitoring

```bash
# Make health check script executable
chmod +x scripts/health_check.sh

# Add to crontab (run every 5 minutes)
crontab -e

# Add this line:
*/5 * * * * /opt/ai-employee/scripts/health_check.sh >> /opt/ai-employee/logs/health_check.log 2>&1
```

---

## Step 15: Setup Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/ai-employee
```

**Add this content:**

```
/opt/ai-employee/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 youruser youruser
    sharedscripts
    postrotate
        pm2 reload all > /dev/null 2>&1 || true
    endscript
}
```

**Test logrotate:**

```bash
sudo logrotate -f /etc/logrotate.d/ai-employee
```

---

## Step 16: Setup Backup System

```bash
# Create backup script
sudo nano /opt/ai-employee/scripts/backup.sh
```

**Add this content:**

```bash
#!/bin/bash
# AI Employee Backup Script

BACKUP_DIR="/opt/backups/ai-employee"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/opt/ai-employee"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup vault
tar -czf $BACKUP_DIR/vault_$DATE.tar.gz \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    $PROJECT_DIR/AI_Employee_Vault

# Backup .env (IMPORTANT: Secure this!)
cp $PROJECT_DIR/.env $BACKUP_DIR/env_$DATE.backup

# Backup logs (last 7 days)
find $PROJECT_DIR/logs -name "*.log" -mtime -7 -exec cp {} $BACKUP_DIR/ \;

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Add to crontab (daily at 2 AM):**

```bash
crontab -e
0 2 * * * /opt/ai-employee/scripts/backup.sh
```

---

## Common Commands Reference

### PM2 Commands

```bash
# Start all processes
pm2 start ecosystem.config.js

# Stop all processes
pm2 stop all

# Restart all processes
pm2 restart all

# Reload all processes (zero downtime)
pm2 reload all

# Delete all processes
pm2 delete all

# View status
pm2 status

# Monitor in real-time
pm2 monit

# View logs
pm2 logs
pm2 logs orchestrator --lines 100

# Scale processes
pm2 scale orchestrator 2

# Save process list
pm2 save

# Resurrect saved processes
pm2 resurrect
```

### Log Commands

```bash
# View all logs
tail -f logs/ai_employee.log

# View specific logs
tail -f logs/social.log
tail -f logs/personal_tasks.log

# Search logs
grep "ERROR" logs/ai_employee.log | tail -50
grep "invoice" logs/ai_employee.log | grep "success"
```

### System Commands

```bash
# Check system resources
htop
free -h
df -h

# Check running processes
ps aux | grep python
ps aux | grep node

# Check network connections
netstat -tulpn
ss -tulpn

# Check Docker containers
docker ps
docker-compose ps

# Restart a service
sudo systemctl restart nginx
sudo systemctl restart docker
```

---

## Troubleshooting

### Process Won't Start

```bash
# Check PM2 logs
pm2 logs orchestrator --err

# Check if port is in use
sudo netstat -tulpn | grep :8069

# Check Python dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### Odoo Connection Failed

```bash
# Check Odoo container
docker-compose ps

# View Odoo logs
docker-compose logs odoo

# Restart Odoo
docker-compose restart odoo
```

### High Memory Usage

```bash
# Check memory
free -h

# Restart processes
pm2 restart all

# Adjust max_memory in ecosystem.config.js
```

### Disk Space Full

```bash
# Check disk usage
df -h

# Find large files
du -ah /opt/ai-employee | sort -rh | head -20

# Clear old logs
sudo journalctl --vacuum-time=7d
```

---

## Security Best Practices

1. **Never commit .env file** - Always keep credentials secure
2. **Use firewall** - Only allow necessary ports
3. **Regular updates** - Keep system packages updated
4. **Monitor logs** - Set up alerts for errors
5. **Backup regularly** - Automated daily backups
6. **Use SSL** - Always enable HTTPS
7. **Limit sudo access** - Use dedicated user account
8. **Rotate credentials** - Change passwords regularly

---

## Next Steps

1. Setup monitoring alerts (email/SMS)
2. Configure log aggregation (ELK stack)
3. Setup load balancing (if scaling)
4. Implement CI/CD pipeline
5. Add performance monitoring (Prometheus/Grafana)

---

**Deployment Complete!** 🎉

Your AI Employee system is now running 24/7 with automatic restart and monitoring.
