#!/bin/bash
# Platinum Tier - Cloud VM Setup Script
# For Oracle Cloud Free Tier / AWS EC2
#
# This script sets up a production-ready AI Employee Cloud Agent:
# - Docker + Docker Compose
# - Odoo 19 Community Edition
# - Monitoring stack (Prometheus + Grafana)
# - PM2 for process management
# - Nginx with HTTPS (Let's Encrypt)
# - Git and Python dependencies
#
# Usage:
#   curl -o cloud_vm_setup.sh <script_url>
#   chmod +x cloud_vm_setup.sh
#   ./cloud_vm_setup.sh your-domain.com your-email@example.com
#
# Requirements:
# - Fresh Oracle Cloud Free Tier VM (Ubuntu/Oracle Linux)
# - Domain name pointing to VM IP
# - Root or sudo access

set -e

echo "============================================================"
echo "PLATINUM TIER - CLOUD VM SETUP"
echo "============================================================"
echo ""

# Check for required arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <domain-name> <email-address>"
    echo "Example: $0 ai-employee.example.com admin@example.com"
    exit 1
fi

DOMAIN_NAME="$1"
EMAIL_ADDRESS="$2"

echo "Domain: $DOMAIN_NAME"
echo "Email: $EMAIL_ADDRESS"
echo ""

# Detect OS
if [ -f /etc/oracle-release ]; then
    OS="oracle"
    echo "Detected: Oracle Linux"
elif [ -f /etc/ubuntu-release ]; then
    OS="ubuntu"
    echo "Detected: Ubuntu"
else
    OS="unknown"
    echo "Detected: Unknown Linux (assuming Ubuntu-compatible)"
fi

echo ""
echo "=== Step 1: System Update ==="

# Update system
if [ "$OS" = "oracle" ]; then
    sudo dnf update -y
    sudo dnf install -y dnf-utils
else
    sudo apt update -y
    sudo apt upgrade -y
fi

echo ""
echo "=== Step 2: Install Docker ==="

# Install Docker
if [ "$OS" = "oracle" ]; then
    sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo dnf install -y docker-ce docker-ce-cli containerd.io
    sudo systemctl enable docker
    sudo systemctl start docker
else
    sudo apt install -y ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update -y
    sudo apt install -y docker-ce docker-ce-cli containerd.io
fi

# Add user to docker group
sudo usermod -aG docker $USER

echo "Docker installed successfully"

echo ""
echo "=== Step 3: Install Docker Compose ==="

# Install Docker Compose
DOCKER_COMPOSE_VERSION="v2.24.0"
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "Docker Compose installed: $(docker-compose --version)"

echo ""
echo "=== Step 4: Install Node.js ==="

# Install Node.js 20.x
if [ "$OS" = "oracle" ]; then
    curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
    sudo dnf install -y nodejs
else
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
fi

echo "Node.js installed: $(node --version)"
echo "npm installed: $(npm --version)"

echo ""
echo "=== Step 5: Install Python 3.13 ==="

# Install Python 3.13
if [ "$OS" = "oracle" ]; then
    sudo dnf install -y python3.13 python3.13-pip
else
    sudo apt install -y python3.13 python3.13-pip python3.13-venv
fi

echo "Python installed: $(python3 --version)"

echo ""
echo "=== Step 6: Install Git ==="

# Install Git
if [ "$OS" = "oracle" ]; then
    sudo dnf install -y git
else
    sudo apt install -y git
fi

echo "Git installed: $(git --version)"

echo ""
echo "=== Step 7: Install PM2 ==="

# Install PM2 globally
sudo npm install -g pm2

echo "PM2 installed: $(pm2 --version)"

echo ""
echo "=== Step 8: Install Nginx ==="

# Install Nginx
if [ "$OS" = "oracle" ]; then
    sudo dnf install -y nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx
else
    sudo apt install -y nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx
fi

echo "Nginx installed"

echo ""
echo "=== Step 9: Install Certbot (Let's Encrypt) ==="

# Install Certbot
if [ "$OS" = "oracle" ]; then
    sudo dnf install -y certbot python3-certbot-nginx
else
    sudo apt install -y certbot python3-certbot-nginx
fi

echo "Certbot installed: $(certbot --version)"

echo ""
echo "=== Step 10: Clone Repository ==="

# Clone repository (adjust URL as needed)
cd /home/$USER
if [ ! -d "Hack-03-AI-Employee-giaic" ]; then
    echo "Repository not found. Please clone manually:"
    echo "  git clone <your-repo-url> Hack-03-AI-Employee-giaic"
    echo ""
    # For now, create directory structure
    mkdir -p Hack-03-AI-Employee-giaic
    cd Hack-03-AI-Employee-giaic
else
    cd Hack-03-AI-Employee-giaic
    echo "Repository already exists"
fi

echo ""
echo "=== Step 11: Setup Python Dependencies ==="

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "Python dependencies installed"
else
    echo "requirements.txt not found"
fi

echo ""
echo "=== Step 12: Setup Odoo Docker ==="

# Setup Odoo environment
cd docker
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || touch .env
fi

# Generate secure passwords if not set
if ! grep -q "ODOO_DB_PASSWORD" .env || [ -z "$(grep ODOO_DB_PASSWORD .env | cut -d'=' -f2)" ]; then
    echo "ODOO_DB_PASSWORD=$(openssl rand -base64 32)" >> .env
    echo "ODOO_ADMIN_PASSWORD=$(openssl rand -base64 32)" >> .env
    echo "PGADMIN_EMAIL=$EMAIL_ADDRESS" >> .env
    echo "PGADMIN_PASSWORD=$(openssl rand -base64 16)" >> .env
    echo "GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16)" >> .env
    echo "Secure passwords generated and saved to .env"
fi

cd ..

echo ""
echo "=== Step 13: Start Odoo Production ==="

# Start Odoo
cd docker
docker-compose -f docker-compose.prod.yml up -d

echo "Waiting for Odoo to start (60 seconds)..."
sleep 60

# Check Odoo status
docker-compose -f docker-compose.prod.yml ps

cd ..

echo ""
echo "=== Step 14: Setup Nginx Reverse Proxy ==="

# Create Nginx configuration
sudo tee /etc/nginx/conf.d/odoo.conf > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Odoo proxy
    location / {
        proxy_pass http://127.0.0.1:8069;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Server \$host;
        proxy_buffering off;
    }

    # WebSocket support for Odoo
    location /longpolling {
        proxy_pass http://127.0.0.1:8072;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=odoo_limit:10m rate=10r/s;
    limit_req zone=odoo_limit burst=20 nodelay;
}
EOF

echo "Nginx configuration created"

echo ""
echo "=== Step 15: Setup Let's Encrypt SSL ==="

# Create certbot directory
sudo mkdir -p /var/www/certbot

# Get SSL certificate
sudo certbot --nginx -d $DOMAIN_NAME --email $EMAIL_ADDRESS --agree-tos --non-interactive

echo "SSL certificate installed"

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

echo "Nginx reloaded"

echo ""
echo "=== Step 16: Start Monitoring Stack ==="

cd docker

# Start monitoring
if [ -f "docker-compose.monitoring.yml" ]; then
    docker-compose -f docker-compose.monitoring.yml up -d
    echo "Monitoring stack started"
    echo "  Prometheus: http://$DOMAIN_NAME:9090"
    echo "  Grafana: http://$DOMAIN_NAME:3000"
else
    echo "docker-compose.monitoring.yml not found"
fi

cd ..

echo ""
echo "=== Step 17: Setup PM2 for Cloud Agent ==="

# Setup PM2 for Cloud Agent processes
source venv/bin/activate

if [ -f "orchestrator_cloud.py" ]; then
    pm2 start orchestrator_cloud.py --name cloud_agent --interpreter python3
    echo "Cloud Agent started"
else
    echo "orchestrator_cloud.py not found"
fi

if [ -f "gmail_watcher.py" ]; then
    pm2 start gmail_watcher.py --name gmail_watcher --interpreter python3
    echo "Gmail Watcher started"
fi

if [ -f "facebook_watcher.py" ]; then
    pm2 start facebook_watcher.py --name facebook_watcher --interpreter python3
    echo "Facebook Watcher started"
fi

if [ -f "twitter_watcher.py" ]; then
    pm2 start twitter_watcher.py --name twitter_watcher --interpreter python3
    echo "Twitter Watcher started"
fi

if [ -f "git_sync.py" ]; then
    pm2 start git_sync.py --name git_sync --interpreter python3 -- --agent=cloud_agent
    echo "Git Sync started"
fi

if [ -f "health_monitor.py" ]; then
    pm2 start health_monitor.py --name health_monitor --interpreter python3 -- --agent=cloud
    echo "Health Monitor started"
fi

# Save PM2 configuration
pm2 save

# Setup PM2 startup
pm2 startup | tail -1 | sudo bash

echo "PM2 processes configured"

echo ""
echo "=== Step 18: Setup Firewall ==="

# Configure firewall
if command -v ufw &> /dev/null; then
    sudo ufw allow 22/tcp    # SSH
    sudo ufw allow 80/tcp    # HTTP
    sudo ufw allow 443/tcp   # HTTPS
    sudo ufw allow 3000/tcp  # Grafana
    sudo ufw allow 9090/tcp  # Prometheus
    sudo ufw --force enable
    echo "UFW firewall configured"
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-service=ssh
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --permanent --add-port=3000/tcp
    sudo firewall-cmd --permanent --add-port=9090/tcp
    sudo firewall-cmd --reload
    echo "FirewallD configured"
fi

echo ""
echo "=== Step 19: Display Access Information ==="

echo ""
echo "============================================================"
echo "SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Cloud VM Access:"
echo "  Odoo ERP: https://$DOMAIN_NAME"
echo "  Grafana: http://$DOMAIN_NAME:3000"
echo "  Prometheus: http://$DOMAIN_NAME:9090"
echo ""
echo "PM2 Commands:"
echo "  pm2 status          - Check process status"
echo "  pm2 logs            - View logs"
echo "  pm2 restart all     - Restart all processes"
echo "  pm2 monit           - Real-time monitoring"
echo ""
echo "Docker Commands:"
echo "  docker-compose -f docker-compose.prod.yml ps"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "Important Files:"
echo "  .env file: docker/.env (contains secure passwords)"
echo "  Nginx config: /etc/nginx/conf.d/odoo.conf"
echo "  PM2 config: ~/.pm2/"
echo ""
echo "Next Steps:"
echo "  1. Login to Odoo and configure your database"
echo "  2. Login to Grafana (admin/PGADMIN_PASSWORD from .env)"
echo "  3. Configure Git remote for vault sync"
echo "  4. Start Local Agent on your machine"
echo ""
echo "============================================================"
echo ""
