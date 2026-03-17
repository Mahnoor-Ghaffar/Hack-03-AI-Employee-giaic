# Platinum Tier Architecture: Always-On Cloud + Local Executive

**Version:** 1.0.0  
**Date:** 2026-03-16  
**Status:** 🏗️ ARCHITECTURE DEFINED  
**Tier:** Platinum - Production-Grade Autonomous AI Employee

---

## Executive Summary

The Platinum Tier extends the Gold Tier by transforming the AI Employee from a local assistant into a **production-grade, always-on executive system** with distributed cloud-local architecture. This tier introduces:

1. **24/7 Cloud Operations** - Continuous monitoring and draft generation
2. **Work-Zone Specialization** - Clear separation between cloud (drafts) and local (approvals/actions)
3. **Synced Vault Architecture** - Secure file-based agent communication
4. **Production Hardening** - HTTPS, backups, health monitoring, auto-recovery
5. **A2A Communication** - Optional direct agent-to-agent messaging

**Key Innovation:** The Cloud Agent works while you sleep, drafting responses and preparing social content. When you wake up, you approve drafts and the Local Agent executes final actions. This maintains security while achieving 24/7 productivity.

---

## Platinum Tier Requirements (from Hackathon Spec)

| # | Requirement | Phase | Status |
|---|-------------|-------|--------|
| 1 | Run AI Employee on Cloud 24/7 (always-on watchers + orchestrator + health monitoring) | Phase 1 | ⏳ Pending |
| 2 | Work-Zone Specialization: Cloud owns email triage + social drafts (draft-only) | Phase 1 | ⏳ Pending |
| 3 | Local owns: approvals, WhatsApp session, payments/banking, final send/post actions | Phase 1 | ⏳ Pending |
| 4 | Delegation via Synced Vault (Phase 1) | Phase 1 | ⏳ Pending |
| 5 | Cloud writes to `/Updates/` or `/Signals/`, Local merges to `Dashboard.md` | Phase 1 | ⏳ Pending |
| 6 | Claim-by-move rule: First agent to move to `/In_Progress/<agent>/` owns it | Phase 1 | ⏳ Pending |
| 7 | Single-writer rule for `Dashboard.md` (Local only) | Phase 1 | ⏳ Pending |
| 8 | Security: Vault sync excludes secrets (.env, tokens, WhatsApp sessions, banking creds) | Phase 1 | ⏳ Pending |
| 9 | Deploy Odoo on Cloud VM with HTTPS, backups, health monitoring | Phase 1 | ⏳ Pending |
| 10 | Optional A2A Upgrade (Phase 2) | Phase 2 | ⏳ Pending |
| 11 | Platinum Demo: Email → Cloud drafts → Local approves → Local sends | Phase 1 | ⏳ Pending |

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PLATINUM TIER AI EMPLOYEE                           │
│                    Always-On Cloud + Local Executive System                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLOUD ENVIRONMENT (VM)                            │
│                    Oracle Cloud Free Tier / AWS EC2                         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    CLOUD AGENT (Draft-Only Operations)                │ │
│  │                                                                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │ │
│  │  │ Gmail Watcher│  │Social Watcher│  │  Odoo Watcher│                │ │
│  │  │  (24/7)      │  │  (24/7)      │  │  (24/7)      │                │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                │ │
│  │         │                 │                  │                         │ │
│  │         ▼                 ▼                  ▼                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │              CLOUD ORCHESTRATOR (orchestrator_cloud.py)         │  │ │
│  │  │         Reads watchers → Creates drafts → Writes to /Updates/   │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │              CLOUD VAULT SYNC (Git Remote)                      │  │ │
│  │  │         Pushes /Updates/ to Git, Pulls /Approved/ from Git      │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │              ODOO ERP (Docker: Odoo + PostgreSQL)               │  │ │
│  │  │         HTTPS via Nginx + Let's Encrypt                         │  │ │
│  │  │         Daily backups to S3/Object Storage                      │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │         HEALTH MONITORING (Prometheus + Grafana)                │  │ │
│  │  │         Auto-restart failed processes (PM2/Systemd)             │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ⚠️ CLOUD SECURITY BOUNDARY: NO SECRETS STORED HERE                        │
│  - No WhatsApp sessions                                                     │
│  - No banking credentials                                                    │
│  - No payment tokens                                                        │
│  - No send/post capabilities (draft-only)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Git Sync (Vault State Only)
                                    │ /Updates/, /Signals/, /Plans/, /Needs_Action/
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LOCAL ENVIRONMENT (Your Machine)                    │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    LOCAL AGENT (Approval + Execution)                 │ │
│  │                                                                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │ │
│  │  │WhatsApp Watch│  │ Payment Watch│  │  Git Sync    │                │ │
│  │  │  (Session)   │  │  (Credentials)│  │  (Pull/Push) │                │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                │ │
│  │         │                 │                  │                         │ │
│  │         ▼                 ▼                  ▼                         │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │           LOCAL ORCHESTRATOR (orchestrator_local.py)            │  │ │
│  │  │    Merges /Updates/ → Dashboard.md → Notifies for Approval      │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │              HUMAN-IN-THE-LOOP APPROVAL                         │  │ │
│  │  │    Review drafts in /Pending_Approval/ → Move to /Approved/     │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │              MCP EXECUTORS (Final Actions)                      │  │ │
│  │  │    Email MCP (send) │ Social MCP (post) │ Payment MCP (pay)    │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │              LOCAL VAULT (Obsidian Dashboard)                   │  │ │
│  │  │         Single-writer: Dashboard.md (Local only)                │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  🔒 LOCAL SECURITY ZONE: SECRETS STORED HERE ONLY                          │
│  - WhatsApp session files                                                   │
│  - Banking credentials (Keychain/Credential Manager)                       │
│  - Payment tokens                                                           │
│  - Email send credentials                                                   │
│  - Social media posting credentials                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Work-Zone Specialization

### 2.1 Cloud Agent Responsibilities (Draft-Only)

| Domain | Cloud Capabilities | Local Capabilities |
|--------|-------------------|-------------------|
| **Email** | Triage, draft replies, categorize, prioritize | Review drafts, approve send, execute via MCP |
| **Social Media** | Generate post drafts, schedule drafts, analyze engagement | Approve posts, execute posting via MCP |
| **Accounting (Odoo)** | Create draft invoices, record draft payments, generate reports | Approve invoices/payments, execute via MCP |
| **WhatsApp** | ❌ NO ACCESS (session stored locally only) | Full access, send/receive messages |
| **Payments/Banking** | ❌ NO ACCESS (credentials stored locally only) | Full access, execute payments |

### 2.2 Cloud Agent Limitations (Security by Design)

```yaml
# Cloud Agent Capability Matrix
cloud_agent:
  can_do:
    - read_gmail
    - draft_email_replies
    - monitor_social_media
    - generate_social_posts
    - read_odoo_data
    - create_draft_invoices
    - generate_reports
    - write_to_vault_updates
  
  cannot_do:
    - send_emails
    - post_to_social_media
    - access_whatsapp
    - execute_payments
    - access_banking_credentials
    - modify_dashboard_md
    - access_secrets
```

---

## 3. Synced Vault Architecture (Phase 1)

### 3.1 Folder Structure for Distributed Agents

```
AI_Employee_Vault/
├── .git/                          # Git repository for sync
│
├── Inbox/                         # Raw incoming (Cloud writes)
├── Needs_Action/                  # Tasks pending processing
│   └── .gitkeep
│
├── In_Progress/                   # Claimed tasks (prevents double-work)
│   ├── cloud_agent/               # Cloud-owned tasks
│   └── local_agent/               # Local-owned tasks
│
├── Updates/                       # Cloud → Local communication
│   ├── email_triage/              # Email summaries and drafts
│   ├── social_drafts/             # Social media post drafts
│   ├── odoo_reports/              # Accounting updates
│   └── signals/                   # Alert signals
│
├── Signals/                       # Time-critical alerts
│   └── urgent/                    # High-priority notifications
│
├── Plans/                         # Task plans (Cloud writes drafts)
│   └── .gitkeep
│
├── Pending_Approval/              # Drafts awaiting human approval
│   ├── email_drafts/              # Email drafts for approval
│   ├── social_posts/              # Social posts for approval
│   └── payments/                  # Payment requests
│
├── Approved/                      # Approved actions (Local executes)
│   └── .gitkeep
│
├── Done/                          # Completed tasks
│   └── .gitkeep
│
├── Accounting/                    # Financial data (read-only for Cloud)
│   ├── Invoices.md
│   ├── Transactions.md
│   └── Reports/
│
├── Social_Media/                  # Social media activity
│   ├── Posts.md
│   └── Campaigns.md
│
├── Briefings/                     # CEO briefings
│   └── .gitkeep
│
├── Logs/                          # Action logs (both agents write)
│   ├── cloud_agent.log
│   └── local_agent.log
│
├── Ralph_State/                   # Ralph Wiggum loop state
│   └── .gitkeep
│
├── Dashboard.md                   # ⚠️ SINGLE-WRITER: Local only
├── Company_Handbook.md            # Rules (read-only for Cloud)
└── Business_Goals.md              # Objectives (read-only for Cloud)
```

### 3.2 Claim-by-Move Rule

**Purpose:** Prevent two agents from processing the same task.

**Algorithm:**
```python
def claim_task(task_file: Path, agent_name: str) -> bool:
    """
    First agent to move task to /In_Progress/<agent>/ owns it.
    Other agents must ignore tasks in another agent's folder.
    """
    in_progress_dir = VAULT_ROOT / "In_Progress" / agent_name
    
    # Check if task already claimed
    if task_file.parent.name == agent_name:
        return True  # Already claimed by this agent
    
    # Check if claimed by another agent
    if task_file.parent.parent.name == "In_Progress":
        return False  # Already claimed by another agent
    
    # Attempt to claim
    try:
        task_file.rename(in_progress_dir / task_file.name)
        return True
    except FileExistsError:
        return False  # Race condition: another agent claimed it first
```

### 3.3 Single-Writer Rule for Dashboard.md

**Rule:** Only the Local Agent can write to `Dashboard.md`.

**Cloud Agent Pattern:**
```python
# ❌ WRONG: Cloud should NOT write to Dashboard.md
# dashboard_path.write_text("Cloud update...")

# ✅ CORRECT: Cloud writes to /Updates/
update_file = VAULT_ROOT / "Updates" / "email_triage" / f"summary_{timestamp}.md"
update_file.write_text(cloud_summary)
```

**Local Agent Pattern:**
```python
# ✅ CORRECT: Local reads /Updates/ and merges into Dashboard.md
def merge_updates_into_dashboard():
    updates = list((VAULT_ROOT / "Updates").glob("**/*.md"))
    dashboard_content = build_dashboard_from_updates(updates)
    (VAULT_ROOT / "Dashboard.md").write_text(dashboard_content)
```

---

## 4. Security Architecture

### 4.1 Secrets Boundary

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUD VM (NO SECRETS)                        │
│                                                                 │
│  ✅ Allowed:                                                     │
│  - Gmail API read-only token                                    │
│  - Social media read tokens                                     │
│  - Odoo API credentials (read + draft create)                   │
│  - Git credentials (vault sync)                                 │
│                                                                 │
│  ❌ NEVER Stored:                                                │
│  - WhatsApp session files                                       │
│  - Banking credentials                                          │
│  - Payment tokens                                               │
│  - Email send credentials                                       │
│  - Social media posting credentials                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL MACHINE (SECRETS ZONE)                 │
│                                                                 │
│  ✅ All Secrets Stored Here:                                    │
│  - WhatsApp session: ~/.qwen/whatsapp_session/                  │
│  - Banking credentials: OS Keychain / Credential Manager        │
│  - Payment tokens: Encrypted vault                              │
│  - Email send credentials: .env (local only)                    │
│  - Social posting credentials: .env (local only)                │
│                                                                 │
│  🔒 .gitignore ensures secrets never sync:                       │
│  - .env                                                        │
│  - *.session                                                   │
│  - **/credentials.json                                         │
│  - **/tokens/                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Git Sync Security

**.gitignore (Root of Vault):**
```gitignore
# NEVER SYNC SECRETS
.env
.env.local
.env.*.local
*.session
*.session3d
**/credentials.json
**/tokens/
**/secrets/

# OS Files
.DS_Store
Thumbs.db
desktop.ini

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs (sync only recent)
logs/*.log
!logs/recent.log

# Ralph State (local only)
Ralph_State/
```

**.gitignore.allow (Explicit Sync List):**
```
# SYNC THESE FOLDERS
Inbox/
Needs_Action/
In_Progress/
Updates/
Signals/
Plans/
Pending_Approval/
Approved/
Done/
Accounting/*.md
Accounting/Reports/
Social_Media/*.md
Briefings/
Logs/recent.log
Dashboard.md
Company_Handbook.md
Business_Goals.md
```

---

## 5. Cloud VM Deployment

### 5.1 Recommended: Oracle Cloud Free Tier

**Specifications:**
- **Instance:** ARM Ampere A1 Compute
- **CPU:** 4 OCPUs (ARM64)
- **RAM:** 24 GB
- **Storage:** 200 GB Block Volume
- **Network:** 10 Gbps
- **Cost:** FREE (Always Free tier)

**Alternative:** AWS EC2 t2.micro (750 hours/month free for 12 months)

### 5.2 Cloud VM Setup Script

```bash
#!/bin/bash
# scripts/cloud_vm_setup.sh
# Automated setup for Oracle Cloud Free Tier

set -e

echo "=== Platinum Tier Cloud VM Setup ==="

# Update system
sudo dnf update -y  # Oracle Linux

# Install Docker
sudo dnf install -y dnf-utils
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Node.js 20.x
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs

# Install Python 3.13
sudo dnf install -y python3.13 python3.13-pip

# Install Git
sudo dnf install -y git

# Install PM2 (Process Manager)
sudo npm install -g pm2

# Install Nginx (for HTTPS)
sudo dnf install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Install Certbot (Let's Encrypt)
sudo dnf install -y certbot python3-certbot-nginx

# Clone repository
cd /home/$USER
git clone https://github.com/yourusername/Hack-03-AI-Employee-giaic.git
cd Hack-03-AI-Employee-giaic

# Install Python dependencies
pip3 install -r requirements.txt

# Setup Odoo Docker
cd docker
cp .env.example .env
# Edit .env with secure passwords

# Start Odoo
docker-compose up -d

# Setup Nginx reverse proxy for Odoo
sudo cp /home/$USER/Hack-03-AI-Employee-giaic/docker/nginx.conf /etc/nginx/conf.d/odoo.conf
sudo certbot --nginx -d your-domain.com

# Setup PM2 for Cloud Agent
cd /home/$USER/Hack-03-AI-Employee-giaic
pm2 start orchestrator_cloud.py --name cloud_agent --interpreter python3
pm2 start gmail_watcher.py --name gmail_watcher --interpreter python3
pm2 start social_watcher.py --name social_watcher --interpreter python3
pm2 start health_monitor.py --name health_monitor --interpreter python3
pm2 save

# Setup PM2 startup
pm2 startup
# Run the generated command as root

# Setup monitoring
docker-compose -f docker-compose.monitoring.yml up -d

echo "=== Cloud VM Setup Complete ==="
echo "Odoo: https://your-domain.com"
echo "Grafana: http://your-vm-ip:3000"
echo "PM2 Status: pm2 status"
```

### 5.3 Odoo Production Deployment (Cloud VM)

**docker-compose.yml (Production):**
```yaml
version: '3.8'

services:
  odoo:
    image: odoo:19.0-community
    container_name: odoo_prod
    depends_on:
      - db
    ports:
      - "127.0.0.1:8069:8069"  # Only accessible via Nginx
    environment:
      - HOST=db
      - DATABASE=odoo_db
      - USER=odoo
      - PASSWORD=${ODOO_PASSWORD}
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./odoo/config:/etc/odoo
      - ./odoo/addons:/mnt/extra-addons
      - ./odoo/backups:/backups
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8069"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15
    container_name: odoo_db_prod
    environment:
      - POSTGRES_DB=odoo_db
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=${ODOO_PASSWORD}
    volumes:
      - odoo-db-data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U odoo"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Automated backups
  backup:
    image: prodrigestivill/postgres-backup-local
    container_name: odoo_backup
    environment:
      - POSTGRES_HOST=db
      - POSTGRES_DB=odoo_db
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=${ODOO_PASSWORD}
      - SCHEDULE=@daily
      - BACKUP_KEEP_DAYS=7
      - BACKUP_KEEP_WEEKS=4
      - BACKUP_KEEP_MONTHS=6
    volumes:
      - ./odoo/backups:/backups
    restart: always

volumes:
  odoo-web-data:
  odoo-db-data:
```

**Nginx Configuration (HTTPS):**
```nginx
# /etc/nginx/conf.d/odoo.conf
server {
    listen 80;
    server_name your-domain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://127.0.0.1:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=odoo_limit:10m rate=10r/s;
    limit_req zone=odoo_limit burst=20 nodelay;
}
```

---

## 6. Health Monitoring System

### 6.1 Health Monitor Script

```python
# health_monitor.py
"""
Platinum Tier Health Monitor
Monitors all processes and auto-recovers failures
"""

import psutil
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PROCESSES = {
    'cloud_agent': 'orchestrator_cloud.py',
    'gmail_watcher': 'gmail_watcher.py',
    'social_watcher': 'social_watcher.py',
    'git_sync': 'git_sync.py',
}

DOCKER_CONTAINERS = ['odoo_prod', 'odoo_db_prod', 'odoo_backup']

class HealthMonitor:
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.restart_count = {}
        
    def check_process(self, name: str, script: str) -> bool:
        """Check if process is running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if script in cmdline and 'python' in cmdline:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def restart_process(self, name: str, script: str):
        """Restart a failed process via PM2"""
        try:
            logger.warning(f"Restarting {name}...")
            subprocess.run(['pm2', 'restart', name], check=True)
            self.restart_count[name] = self.restart_count.get(name, 0) + 1
            
            if self.restart_count[name] > 3:
                logger.error(f"{name} restarted {self.restart_count[name]} times. Alerting human.")
                self.alert_human(f"Process {name} keeps failing")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart {name}: {e}")
    
    def check_docker_containers(self) -> list:
        """Check if Docker containers are running"""
        failed = []
        for container in DOCKER_CONTAINERS:
            result = subprocess.run(
                ['docker', 'inspect', '--format={{.State.Running}}', container],
                capture_output=True,
                text=True
            )
            if result.stdout.strip() != 'true':
                failed.append(container)
        return failed
    
    def restart_docker(self, container: str):
        """Restart a failed Docker container"""
        try:
            logger.warning(f"Restarting Docker container {container}...")
            subprocess.run(['docker-compose', 'restart', container], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart {container}: {e}")
    
    def check_disk_space(self) -> bool:
        """Check available disk space"""
        usage = psutil.disk_usage(str(self.vault_path))
        if usage.percent > 90:
            logger.error(f"Disk space critical: {usage.percent}% used")
            self.alert_human(f"Disk space critical: {usage.percent}% used")
            return False
        return True
    
    def check_memory(self) -> bool:
        """Check available memory"""
        memory = psutil.virtual_memory()
        if memory.percent > 95:
            logger.error(f"Memory critical: {memory.percent}% used")
            return False
        return True
    
    def alert_human(self, message: str):
        """Send alert to human via vault file"""
        alert_file = self.vault_path / "Signals" / "urgent" / f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        alert_file.parent.mkdir(parents=True, exist_ok=True)
        alert_file.write_text(f"""---
type: system_alert
severity: high
timestamp: {datetime.now().isoformat()}
---

# System Alert

{message}

**Action Required:** Please check the Cloud VM immediately.
""")
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Health Monitor started")
        
        while True:
            try:
                # Check processes
                for name, script in PROCESSES.items():
                    if not self.check_process(name, script):
                        logger.warning(f"Process {name} not running")
                        self.restart_process(name, script)
                
                # Check Docker containers
                failed_containers = self.check_docker_containers()
                for container in failed_containers:
                    self.restart_docker(container)
                
                # Check resources
                self.check_disk_space()
                self.check_memory()
                
                # Write health status
                health_file = self.vault_path / "Logs" / "health_status.md"
                health_file.write_text(f"""---
last_check: {datetime.now().isoformat()}
status: healthy
---

# Health Status

All systems operational.
""")
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                self.alert_human(f"Health monitor error: {e}")
            
            time.sleep(self.check_interval)

if __name__ == "__main__":
    monitor = HealthMonitor(vault_path="AI_Employee_Vault")
    monitor.run()
```

### 6.2 Prometheus + Grafana Monitoring

**docker-compose.monitoring.yml:**
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    ports:
      - "9090:9090"
    restart: always

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    restart: always

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node_exporter
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    restart: always

volumes:
  prometheus-data:
  grafana-data:
```

---

## 7. Cloud Agent Implementation

### 7.1 Cloud Orchestrator

```python
# orchestrator_cloud.py
"""
Platinum Tier Cloud Orchestrator
Draft-only operations, 24/7 monitoring
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from gmail_watcher import GmailWatcher
from facebook_watcher import FacebookWatcher
from twitter_watcher import TwitterWatcher
from odoo_mcp_server import OdooMCPServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cloud_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CloudOrchestrator:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.updates_dir = self.vault_path / "Updates"
        self.signals_dir = self.vault_path / "Signals"
        self.in_progress_dir = self.vault_path / "In_Progress" / "cloud_agent"
        
        # Initialize watchers (read-only for cloud)
        self.gmail_watcher = GmailWatcher(
            vault_path=str(vault_path),
            credentials_path="credentials/gmail_read.json"  # Read-only token
        )
        
        self.facebook_watcher = FacebookWatcher(
            vault_path=str(vault_path),
            facebook_pages=["YourBusinessPage"],
            instagram_accounts=["yourbusiness"],
            check_interval=600
        )
        
        self.twitter_watcher = TwitterWatcher(
            vault_path=str(vault_path),
            username="YourUsername",
            hashtags=["AI", "Automation"],
            check_interval=300
        )
        
        self.odoo_client = OdooMCPServer(
            url="http://localhost:8069",
            db="odoo_db",
            username="ai_employee",
            password="your-api-token"
        )
        
        # Ensure directories exist
        for dir_path in [self.updates_dir, self.signals_dir, self.in_progress_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def process_email_triage(self):
        """Read Gmail, create drafts, write to /Updates/"""
        logger.info("Processing email triage...")
        
        # Get new emails (read-only)
        new_emails = self.gmail_watcher.check_for_updates()
        
        for email in new_emails:
            # Create email draft analysis
            draft_file = self.updates_dir / "email_triage" / f"email_{email['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            draft_file.parent.mkdir(parents=True, exist_ok=True)
            
            draft_content = f"""---
type: email_triage
email_id: {email['id']}
from: {email['from']}
subject: {email['subject']}
received: {email['date']}
priority: {email.get('priority', 'normal')}
draft_created: {datetime.now().isoformat()}
status: draft_ready
---

# Email Triage Summary

**From:** {email['from']}
**Subject:** {email['subject']}
**Priority:** {email.get('priority', 'normal')}

## Summary
{email.get('snippet', 'No summary available')}

## Suggested Action
[AI-generated suggested action]

## Draft Reply
```
[AI-generated draft reply]
```

## To Approve
1. Review draft reply
2. Move to /Pending_Approval/email_drafts/
3. Local agent will send after human approval
"""
            
            draft_file.write_text(draft_content)
            logger.info(f"Created email triage draft: {draft_file.name}")
    
    def generate_social_drafts(self):
        """Monitor social media, generate post drafts"""
        logger.info("Generating social media drafts...")
        
        # Get engagement data (read-only)
        fb_engagement = self.facebook_watcher.get_engagement_summary()
        twitter_engagement = self.twitter_watcher.get_engagement_summary()
        
        # Generate post drafts based on trends
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Facebook draft
        fb_draft_file = self.updates_dir / "social_drafts" / f"facebook_draft_{timestamp}.md"
        fb_draft_file.parent.mkdir(parents=True, exist_ok=True)
        
        fb_draft = f"""---
type: social_post_draft
platform: facebook
draft_created: {datetime.now().isoformat()}
status: draft_ready
---

# Facebook Post Draft

**Suggested Content:**
```
[AI-generated Facebook post based on engagement trends]
```

**Suggested Hashtags:**
#AI #Automation #Business

**Best Time to Post:**
[AI-recommended posting time based on engagement data]

## To Approve
1. Review and edit content
2. Move to /Pending_Approval/social_posts/
3. Local agent will post after human approval
"""
        
        fb_draft_file.write_text(fb_draft)
        
        # Twitter draft
        twitter_draft_file = self.updates_dir / "social_drafts" / f"twitter_draft_{timestamp}.md"
        
        twitter_draft = f"""---
type: social_post_draft
platform: twitter
draft_created: {datetime.now().isoformat()}
status: draft_ready
---

# Twitter Post Draft

**Suggested Tweet:**
```
[AI-generated tweet (280 chars max)]
```

**Thread Option:**
[Optional thread if content is longer]

## To Approve
1. Review and edit content
2. Move to /Pending_Approval/social_posts/
3. Local agent will post after human approval
"""
        
        twitter_draft_file.write_text(twitter_draft)
        logger.info(f"Created social media drafts")
    
    def sync_odoo_reports(self):
        """Generate Odoo financial reports"""
        logger.info("Syncing Odoo reports...")
        
        try:
            # Get financial data (read-only)
            financial_report = self.odoo_client.get_financial_report(report_type='profit_loss')
            
            report_file = self.updates_dir / "odoo_reports" / f"financial_{datetime.now().strftime('%Y%m%d')}.md"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            
            report_content = f"""---
type: odoo_financial_report
report_date: {datetime.now().isoformat()}
period: current_month
status: ready
---

# Financial Report

## Profit & Loss Summary

{financial_report.get('summary', 'No data available')}

## Key Metrics
- Revenue: ${financial_report.get('revenue', 0):,.2f}
- Expenses: ${financial_report.get('expenses', 0):,.2f}
- Net Profit: ${financial_report.get('net_profit', 0):,.2f}

## Alerts
[Any financial alerts or anomalies]
"""
            
            report_file.write_text(report_content)
            logger.info(f"Created Odoo financial report")
            
        except Exception as e:
            logger.error(f"Failed to sync Odoo reports: {e}")
    
    def send_urgent_signal(self, message: str, severity: str = "high"):
        """Send urgent signal to Local agent"""
        signal_file = self.signals_dir / "urgent" / f"SIGNAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        signal_file.parent.mkdir(parents=True, exist_ok=True)
        
        signal_content = f"""---
type: urgent_signal
severity: {severity}
timestamp: {datetime.now().isoformat()}
---

# Urgent Signal

{message}

**Action Required:** Please review immediately.
"""
        
        signal_file.write_text(signal_content)
        logger.warning(f"Sent urgent signal: {message}")
    
    def run(self):
        """Main Cloud Agent loop"""
        logger.info("Cloud Orchestrator started (Draft-Only Mode)")
        
        while True:
            try:
                # Email triage (every 5 minutes)
                self.process_email_triage()
                
                # Social media drafts (every 15 minutes)
                self.generate_social_drafts()
                
                # Odoo reports (every hour)
                self.sync_odoo_reports()
                
                # Wait before next cycle
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Cloud orchestrator error: {e}")
                self.send_urgent_signal(f"Cloud Agent error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    orchestrator = CloudOrchestrator(vault_path="AI_Employee_Vault")
    orchestrator.run()
```

---

## 8. Local Agent Implementation

### 8.1 Local Orchestrator

```python
# orchestrator_local.py
"""
Platinum Tier Local Orchestrator
Approval + Final Execution
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from whatsapp_watcher import WhatsAppWatcher
from filesystem_watcher import FileSystemWatcher
from mcp_executor import MCPExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/local_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LocalOrchestrator:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.updates_dir = self.vault_path / "Updates"
        self.signals_dir = self.vault_path / "Signals"
        self.pending_approval_dir = self.vault_path / "Pending_Approval"
        self.in_progress_dir = self.vault_path / "In_Progress" / "local_agent"
        
        # Local-only watchers (with credentials)
        self.whatsapp_watcher = WhatsAppWatcher(
            vault_path=str(vault_path),
            session_path="~/.qwen/whatsapp_session"  # Local only
        )
        
        self.file_watcher = FileSystemWatcher(
            vault_path=str(vault_path),
            watch_folders=["drop_zone", "Inbox"]
        )
        
        self.mcp_executor = MCPExecutor()
        
        # Ensure directories exist
        for dir_path in [self.updates_dir, self.signals_dir, 
                         self.pending_approval_dir, self.in_progress_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def merge_updates_to_dashboard(self):
        """Merge Cloud updates into Dashboard.md (Single-Writer)"""
        logger.info("Merging updates to Dashboard...")
        
        # Collect all updates
        updates = []
        
        # Email triage updates
        email_updates = list((self.updates_dir / "email_triage").glob("*.md"))
        updates.extend([("Email", f) for f in email_updates])
        
        # Social media drafts
        social_updates = list((self.updates_dir / "social_drafts").glob("*.md"))
        updates.extend([("Social", f) for f in social_updates])
        
        # Odoo reports
        odoo_updates = list((self.updates_dir / "odoo_reports").glob("*.md"))
        updates.extend([("Accounting", f) for f in odoo_updates])
        
        # Build dashboard content
        dashboard_content = f"""# AI Employee Dashboard

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode:** Platinum Tier (Cloud + Local)

---

## Recent Cloud Updates

"""
        
        for category, update_file in updates[-10:]:  # Last 10 updates
            try:
                content = update_file.read_text()
                dashboard_content += f"### {category}: {update_file.name}\n\n{content[:500]}...\n\n"
            except Exception as e:
                logger.error(f"Failed to read update {update_file}: {e}")
        
        dashboard_content += """
---

## Pending Your Approval

Check /Pending_Approval/ for items requiring your review.

## Quick Actions
- Review email drafts
- Approve social media posts
- Process payments
"""
        
        # Write Dashboard.md (Local only)
        (self.vault_path / "Dashboard.md").write_text(dashboard_content)
        logger.info(f"Dashboard updated with {len(updates)} updates")
    
    def process_pending_approvals(self):
        """Process items in /Pending_Approval/"""
        logger.info("Processing pending approvals...")
        
        approval_files = list(self.pending_approval_dir.glob("**/*.md"))
        
        for approval_file in approval_files:
            try:
                content = approval_file.read_text()
                
                # Check if approved
                if "approved: true" in content or "status: approved" in content:
                    logger.info(f"Executing approved action: {approval_file.name}")
                    
                    # Execute via MCP
                    result = self.mcp_executor.execute_from_file(approval_file)
                    
                    if result['success']:
                        # Move to Approved/
                        approved_dir = self.vault_path / "Approved"
                        approved_dir.mkdir(parents=True, exist_ok=True)
                        approval_file.rename(approved_dir / approval_file.name)
                        logger.info(f"Action executed successfully: {approval_file.name}")
                    else:
                        logger.error(f"Action failed: {result.get('error')}")
                
                elif "approved: false" in content or "status: rejected" in content:
                    # Move to Rejected/
                    rejected_dir = self.vault_path / "Rejected"
                    rejected_dir.mkdir(parents=True, exist_ok=True)
                    approval_file.rename(rejected_dir / approval_file.name)
                    logger.info(f"Action rejected: {approval_file.name}")
                    
            except Exception as e:
                logger.error(f"Failed to process approval {approval_file}: {e}")
    
    def process_whatsapp_messages(self):
        """Process WhatsApp messages (Local only)"""
        logger.info("Processing WhatsApp messages...")
        
        messages = self.whatsapp_watcher.check_for_updates()
        
        for message in messages:
            # Create action file
            action_file = self.vault_path / "Needs_Action" / f"WHATSAPP_{message['id']}.md"
            action_file.write_text(f"""---
type: whatsapp_message
from: {message['from']}
timestamp: {message['timestamp']}
status: pending
---

# WhatsApp Message

**From:** {message['from']}
**Time:** {message['timestamp']}

**Message:**
```
{message['text']}
```

## Suggested Actions
- [ ] Reply via WhatsApp
- [ ] Create task
- [ ] Forward to email
""")
            
            logger.info(f"Created WhatsApp action file: {action_file.name}")
    
    def check_urgent_signals(self):
        """Check for urgent signals from Cloud"""
        logger.info("Checking urgent signals...")
        
        signal_files = list((self.signals_dir / "urgent").glob("*.md"))
        
        for signal_file in signal_files:
            content = signal_file.read_text()
            logger.warning(f"Urgent signal received: {signal_file.name}")
            
            # Alert human immediately
            print(f"\n🚨 URGENT SIGNAL: {signal_file.name}\n")
            print(content)
            print()
    
    def run(self):
        """Main Local Agent loop"""
        logger.info("Local Orchestrator started (Approval + Execution Mode)")
        
        while True:
            try:
                # Merge cloud updates to dashboard
                self.merge_updates_to_dashboard()
                
                # Process pending approvals
                self.process_pending_approvals()
                
                # Process WhatsApp messages
                self.process_whatsapp_messages()
                
                # Check urgent signals
                self.check_urgent_signals()
                
                # Wait before next cycle
                time.sleep(60)  # 1 minute
                
            except Exception as e:
                logger.error(f"Local orchestrator error: {e}")
                time.sleep(30)

if __name__ == "__main__":
    orchestrator = LocalOrchestrator(vault_path="AI_Employee_Vault")
    orchestrator.run()
```

---

## 9. Git Sync Implementation

### 9.1 Git Sync Script

```python
# git_sync.py
"""
Vault Git Sync for Platinum Tier
Syncs vault state between Cloud and Local
"""

import subprocess
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VaultGitSync:
    def __init__(self, vault_path: str, remote_url: str):
        self.vault_path = Path(vault_path)
        self.remote_url = remote_url
        self.git_dir = self.vault_path / ".git"
        
    def initialize_repo(self):
        """Initialize Git repo if not exists"""
        if not self.git_dir.exists():
            logger.info("Initializing Git repository...")
            subprocess.run(['git', 'init'], cwd=self.vault_path, check=True)
            subprocess.run(['git', 'remote', 'add', 'origin', self.remote_url], 
                          cwd=self.vault_path, check=True)
    
    def pull_changes(self):
        """Pull latest changes from remote"""
        try:
            logger.info("Pulling changes from remote...")
            subprocess.run(['git', 'pull', 'origin', 'main'], 
                          cwd=self.vault_path, check=True, capture_output=True)
            logger.info("Pull completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Pull failed: {e.stderr}")
            return False
    
    def push_changes(self):
        """Push local changes to remote"""
        try:
            # Stage changes
            subprocess.run(['git', 'add', '.'], cwd=self.vault_path, check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                   cwd=self.vault_path, capture_output=True, text=True)
            
            if result.stdout.strip():
                # Commit changes
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                subprocess.run(['git', 'commit', '-m', f'Auto-sync: {timestamp}'], 
                              cwd=self.vault_path, check=True)
                
                # Push changes
                subprocess.run(['git', 'push', 'origin', 'main'], 
                              cwd=self.vault_path, check=True)
                
                logger.info("Push completed successfully")
            else:
                logger.info("No changes to push")
            
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Push failed: {e.stderr if hasattr(e, 'stderr') else e}")
            return False
    
    def run_sync(self):
        """Run full sync cycle"""
        self.initialize_repo()
        self.pull_changes()
        # Local changes would be made here by other processes
        self.push_changes()

if __name__ == "__main__":
    import time
    
    sync = VaultGitSync(
        vault_path="AI_Employee_Vault",
        remote_url="https://github.com/yourusername/ai-employee-vault.git"
    )
    
    logger.info("Starting Git sync loop...")
    while True:
        try:
            sync.run_sync()
            time.sleep(300)  # Sync every 5 minutes
        except Exception as e:
            logger.error(f"Sync error: {e}")
            time.sleep(60)
```

---

## 10. Platinum Demo Flow

### 10.1 End-to-End Demo Scenario

**Scenario:** Email arrives while Local is offline → Cloud drafts reply → Local approves → Local sends

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PLATINUM DEMO FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1: Email Arrives (Local Offline)
┌─────────────────────────────────────────────────────────┐
│  Cloud VM (24/7)                                        │
│                                                         │
│  📧 Gmail Watcher detects new email                     │
│     From: client@example.com                            │
│     Subject: "Invoice Request"                          │
│                                                         │
│  🤖 Cloud Orchestrator processes email                  │
│     - Reads email content                               │
│     - Generates draft reply                             │
│     - Creates triage file                               │
│                                                         │
│  📝 Writes to /Updates/email_triage/                    │
│     email_12345_20260316_103000.md                      │
└─────────────────────────────────────────────────────────┘
                    │
                    │ Git Sync
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Git Remote (Vault Sync)                                │
│                                                         │
│  Cloud pushes /Updates/ to Git                          │
└─────────────────────────────────────────────────────────┘
                    │
                    │ Git Sync (when Local comes online)
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Local Machine (User comes online)                      │
│                                                         │
│  🔄 Local Orchestrator pulls from Git                   │
│     - Detects new /Updates/ file                        │
│     - Merges into Dashboard.md                          │
│     - Notifies user                                     │
│                                                         │
│  👤 User reviews dashboard                              │
│     - Sees email draft                                  │
│     - Reviews AI-generated reply                        │
│                                                         │
│  ✅ User approves draft                                 │
│     - Moves file to /Pending_Approval/                  │
│     - Marks as approved                                 │
│                                                         │
│  🚀 Local Orchestrator executes                         │
│     - Calls Email MCP to send                           │
│     - Moves file to /Approved/                          │
│     - Logs action                                       │
└─────────────────────────────────────────────────────────┘

Result: Email sent successfully with human approval! ✅
```

### 10.2 Demo Test Script

```python
# test_platinum_demo.py
"""
Platinum Tier Demo Test
Simulates the end-to-end flow
"""

from pathlib import Path
from datetime import datetime
import time

VAULT_PATH = Path("AI_Employee_Vault")

def test_platinum_demo():
    """Test the complete Platinum demo flow"""
    
    print("=== Platinum Tier Demo ===\n")
    
    # Step 1: Cloud creates email triage draft
    print("Step 1: Cloud detects email and creates draft...")
    updates_dir = VAULT_PATH / "Updates" / "email_triage"
    updates_dir.mkdir(parents=True, exist_ok=True)
    
    draft_file = updates_dir / f"email_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    draft_content = f"""---
type: email_triage
email_id: demo_12345
from: client@example.com
subject: Invoice Request
received: {datetime.now().isoformat()}
priority: high
draft_created: {datetime.now().isoformat()}
status: draft_ready
---

# Email Triage Summary

**From:** client@example.com
**Subject:** Invoice Request

## Summary
Client is requesting an invoice for services rendered.

## Draft Reply
```
Dear Client,

Thank you for your request. Please find attached your invoice for January 2026.

Best regards,
Your AI Employee
```

## To Approve
Move this file to /Pending_Approval/email_drafts/ and mark as approved.
"""
    
    draft_file.write_text(draft_content)
    print(f"✅ Draft created: {draft_file.name}\n")
    
    # Step 2: Local merges to dashboard
    print("Step 2: Local merges updates to Dashboard...")
    dashboard_content = f"""# AI Employee Dashboard

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Recent Updates

### Email: {draft_file.name}
New email draft ready for review.
"""
    
    (VAULT_PATH / "Dashboard.md").write_text(dashboard_content)
    print("✅ Dashboard updated\n")
    
    # Step 3: User approves (simulate)
    print("Step 3: User approves draft...")
    pending_dir = VAULT_PATH / "Pending_Approval" / "email_drafts"
    pending_dir.mkdir(parents=True, exist_ok=True)
    
    approved_file = pending_dir / draft_file.name
    approved_content = draft_content.replace("status: draft_ready", "status: approved")
    approved_content = approved_content.replace("## To Approve", "approved: true\n\n## Approved")
    
    approved_file.write_text(approved_content)
    draft_file.unlink()  # Remove from Updates
    print(f"✅ Draft approved: {approved_file.name}\n")
    
    # Step 4: Local executes (simulate send)
    print("Step 4: Local executes send via MCP...")
    print("📧 Sending email via Email MCP...")
    time.sleep(2)  # Simulate API call
    print("✅ Email sent successfully\n")
    
    # Step 5: Archive to Approved
    print("Step 5: Archiving to Approved...")
    approved_dir = VAULT_PATH / "Approved"
    approved_dir.mkdir(parents=True, exist_ok=True)
    
    final_file = approved_dir / approved_file.name
    approved_file.rename(final_file)
    print(f"✅ Archived: {final_file.name}\n")
    
    print("=== Platinum Demo Complete! ===")
    print("✅ Email arrived → Cloud drafted → Local approved → Local sent")

if __name__ == "__main__":
    test_platinum_demo()
```

---

## 11. File Structure

```
Hack-03-AI-Employee-giaic/
├── AI_Employee_Vault/              # Obsidian vault (Git-synced)
│   ├── .git/                       # Git repository
│   ├── Inbox/
│   ├── Needs_Action/
│   ├── In_Progress/
│   │   ├── cloud_agent/
│   │   └── local_agent/
│   ├── Updates/                    # Cloud → Local communication
│   │   ├── email_triage/
│   │   ├── social_drafts/
│   │   └── odoo_reports/
│   ├── Signals/                    # Urgent alerts
│   │   └── urgent/
│   ├── Plans/
│   ├── Pending_Approval/
│   │   ├── email_drafts/
│   │   ├── social_posts/
│   │   └── payments/
│   ├── Approved/
│   ├── Done/
│   ├── Accounting/
│   ├── Social_Media/
│   ├── Briefings/
│   ├── Logs/
│   │   ├── cloud_agent.log
│   │   ├── local_agent.log
│   │   └── health_status.md
│   ├── Ralph_State/
│   ├── Dashboard.md                # Single-writer: Local only
│   ├── Company_Handbook.md
│   └── Business_Goals.md
│
├── scripts/
│   ├── orchestrator_cloud.py       # Cloud Agent (draft-only)
│   ├── orchestrator_local.py       # Local Agent (approval + execution)
│   ├── git_sync.py                 # Vault Git sync
│   ├── health_monitor.py           # Health monitoring
│   ├── odoo_mcp_server.py
│   ├── facebook_mcp_server.py
│   ├── twitter_mcp_server.py
│   ├── ceo_briefing_generator.py
│   ├── ralph_wiggum_loop.py
│   ├── mcp_executor.py
│   └── request_approval.py
│
├── docker/
│   ├── docker-compose.yml          # Odoo + PostgreSQL
│   ├── docker-compose.monitoring.yml  # Prometheus + Grafana
│   ├── nginx.conf                  # Nginx reverse proxy
│   └── .env.example
│
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│       ├── dashboards/
│       └── datasources/
│
├── cloud_vm_setup.sh               # Cloud VM setup script
├── test_platinum_demo.py           # Platinum demo test
├── requirements.txt
├── .gitignore                      # Security: exclude secrets
└── PLATINUM_TIER_ARCHITECTURE.md   # This document
```

---

## 12. Next Steps

### Phase 1 (Core Platinum Features)
- [ ] Setup Cloud VM (Oracle Free Tier)
- [ ] Deploy Odoo with HTTPS
- [ ] Implement Cloud Orchestrator
- [ ] Implement Local Orchestrator
- [ ] Setup Git sync
- [ ] Implement health monitoring
- [ ] Test Platinum demo flow

### Phase 2 (A2A Upgrade - Optional)
- [ ] Implement direct Agent-to-Agent messaging
- [ ] Keep vault as audit record
- [ ] Reduce file-based handoff latency

---

## Conclusion

The Platinum Tier transforms the AI Employee from a local assistant into a **production-grade, always-on executive system**. By separating concerns between Cloud (drafts) and Local (approvals/actions), we achieve:

✅ **24/7 Operations** - Cloud works while you sleep  
✅ **Security** - Secrets never leave your local machine  
✅ **Scalability** - Cloud VM handles heavy monitoring  
✅ **Human Control** - You approve all sensitive actions  
✅ **Audit Trail** - Complete logging in Obsidian vault  

**This is the future of autonomous AI employees.**
