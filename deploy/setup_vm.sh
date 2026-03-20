#!/bin/bash
# =============================================================================
# AI Employee - Cloud VM Setup Script
# =============================================================================
# 
# Automated setup script for Ubuntu 22.04 LTS cloud VM
# This script installs all dependencies and configures the system
# 
# Usage:
#   curl -o setup.sh <URL-to-this-script>
#   chmod +x setup.sh
#   sudo ./setup.sh
#
# =============================================================================

set -e

# Configuration
PROJECT_DIR="${PROJECT_DIR:-/opt/ai-employee}"
APP_USER="${APP_USER:-ai-employee}"
PYTHON_VERSION="${PYTHON_VERSION:-3.10}"
NODE_VERSION="${NODE_VERSION:-18}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
    echo ""
}

# =============================================================================
# System Setup
# =============================================================================

setup_system() {
    print_header "Updating System Packages"
    
    apt update
    apt upgrade -y
    
    log_success "System packages updated"
}

install_dependencies() {
    print_header "Installing Dependencies"
    
    # Install essential packages
    apt install -y \
        git \
        curl \
        wget \
        build-essential \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        python${PYTHON_VERSION}-dev \
        python3-pip \
        libpq-dev \
        gcc \
        nodejs \
        npm \
        nginx \
        htop \
        net-tools \
        ufw \
        fail2ban \
        software-properties-common \
        certbot \
        python3-certbot-nginx
    
    log_success "Dependencies installed"
}

install_docker() {
    print_header "Installing Docker"
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Add user to docker group
    usermod -aG docker "${APP_USER}" || true
    
    log_success "Docker installed"
}

install_nodejs() {
    print_header "Installing Node.js ${NODE_VERSION}.x"
    
    # Install Node.js
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
    apt install -y nodejs
    
    # Install PM2
    npm install -g pm2
    
    log_success "Node.js ${NODE_VERSION} and PM2 installed"
}

create_user() {
    print_header "Creating Application User"
    
    if ! id -u "${APP_USER}" > /dev/null 2>&1; then
        useradd -m -s /bin/bash "${APP_USER}"
        log_info "Created user: ${APP_USER}"
    else
        log_info "User ${APP_USER} already exists"
    fi
    
    log_success "Application user ready"
}

setup_project() {
    print_header "Setting Up Project Directory"
    
    # Create project directory
    mkdir -p "${PROJECT_DIR}"
    chown "${APP_USER}:${APP_USER}" "${PROJECT_DIR}"
    
    # Create vault directories
    mkdir -p "${PROJECT_DIR}/AI_Employee_Vault"/{Personal/Archive,Plans,Reports,Logs,Needs_Action,Done,Pending_Approval,Social_Media,Accounting,Briefings}
    mkdir -p "${PROJECT_DIR}/logs"
    mkdir -p "${PROJECT_DIR}/temp"
    mkdir -p "/opt/backups/ai-employee"
    
    # Set permissions
    chmod -R 755 "${PROJECT_DIR}"
    chown -R "${APP_USER}:${APP_USER}" "${PROJECT_DIR}"
    
    log_success "Project directory setup complete"
}

setup_python_environment() {
    print_header "Setting Up Python Environment"
    
    cd "${PROJECT_DIR}"
    
    # Create virtual environment
    sudo -u "${APP_USER}" python${PYTHON_VERSION} -m venv venv
    
    # Activate and upgrade pip
    sudo -u "${APP_USER}" bash -c "
        source venv/bin/activate
        pip install --upgrade pip
    "
    
    log_success "Python environment created"
}

install_python_dependencies() {
    print_header "Installing Python Dependencies"
    
    cd "${PROJECT_DIR}"
    
    if [ -f "requirements.txt" ]; then
        sudo -u "${APP_USER}" bash -c "
            source venv/bin/activate
            pip install -r requirements.txt
            pip install gunicorn psycopg2-binary
        "
        log_success "Python dependencies installed"
    else
        log_warning "requirements.txt not found"
    fi
}

setup_environment() {
    print_header "Setting Up Environment"
    
    cd "${PROJECT_DIR}"
    
    # Copy environment file
    if [ -f ".env.example" ] && [ ! -f ".env" ]; then
        cp .env.example .env
        chown "${APP_USER}:${APP_USER}" .env
        chmod 600 .env
        log_info "Created .env file from template"
        log_warning "Please edit .env with your credentials"
    fi
    
    log_success "Environment setup complete"
}

setup_firewall() {
    print_header "Configuring Firewall"
    
    # Enable UFW
    ufw --force enable
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP/HTTPS
    ufw allow http
    ufw allow https
    
    # Allow Odoo port
    ufw allow 8069/tcp
    
    # Show status
    ufw status verbose
    
    log_success "Firewall configured"
}

setup_pm2_startup() {
    print_header "Configuring PM2 Auto-Start"
    
    sudo -u "${APP_USER}" bash -c "
        pm2 startup
    " || true
    
    log_success "PM2 auto-start configured"
}

setup_cron() {
    print_header "Configuring Cron Jobs"
    
    # Create cron jobs for app user
    CRON_JOBS="
# AI Employee Health Check (every 5 minutes)
*/5 * * * * ${PROJECT_DIR}/scripts/health_check.sh >> ${PROJECT_DIR}/logs/health_check.log 2>&1

# AI Employee Backup (daily at 2 AM)
0 2 * * * ${PROJECT_DIR}/scripts/backup.sh >> ${PROJECT_DIR}/logs/backup.log 2>&1

# Log rotation cleanup (weekly on Sunday at 3 AM)
0 3 * * 0 find ${PROJECT_DIR}/logs -name '*.log' -mtime +14 -delete
"
    
    echo "${CRON_JOBS}" | crontab -u "${APP_USER}" -
    
    log_success "Cron jobs configured"
}

setup_logrotate() {
    print_header "Configuring Log Rotation"
    
    cat > /etc/logrotate.d/ai-employee << EOF
${PROJECT_DIR}/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 ${APP_USER} ${APP_USER}
    sharedscripts
    postrotate
        su - ${APP_USER} -c 'cd ${PROJECT_DIR} && pm2 reload all > /dev/null 2>&1 || true'
    endscript
}
EOF
    
    log_success "Log rotation configured"
}

install_systemd_service() {
    print_header "Installing Systemd Service"
    
    if [ -f "${PROJECT_DIR}/deploy/ai-employee.service" ]; then
        cp "${PROJECT_DIR}/deploy/ai-employee.service" /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable ai-employee.service
        log_success "Systemd service installed"
    else
        log_warning "Systemd service file not found"
    fi
}

show_next_steps() {
    print_header "Setup Complete!"
    
    echo ""
    echo "Next Steps:"
    echo ""
    echo "1. Configure environment variables:"
    echo "   sudo nano ${PROJECT_DIR}/.env"
    echo ""
    echo "2. Start the AI Employee system:"
    echo "   sudo -u ${APP_USER} bash -c 'cd ${PROJECT_DIR} && ./start.sh'"
    echo ""
    echo "3. Check status:"
    echo "   sudo -u ${APP_USER} pm2 status"
    echo ""
    echo "4. View logs:"
    echo "   sudo -u ${APP_USER} pm2 logs"
    echo ""
    echo "5. Monitor processes:"
    echo "   sudo -u ${APP_USER} pm2 monit"
    echo ""
    echo "6. Setup SSL (if you have a domain):"
    echo "   sudo certbot --nginx -d your-domain.com"
    echo ""
    echo "============================================================"
    echo ""
    echo "Important Files:"
    echo "  - Project Directory: ${PROJECT_DIR}"
    echo "  - Environment File:  ${PROJECT_DIR}/.env"
    echo "  - Logs Directory:    ${PROJECT_DIR}/logs"
    echo "  - Vault Directory:   ${PROJECT_DIR}/AI_Employee_Vault"
    echo "  - Backup Directory:  /opt/backups/ai-employee"
    echo ""
    echo "Useful Commands:"
    echo "  - Start:    cd ${PROJECT_DIR} && ./start.sh"
    echo "  - Stop:     cd ${PROJECT_DIR} && ./start.sh --stop"
    echo "  - Status:   pm2 status"
    echo "  - Logs:     pm2 logs"
    echo "  - Monitor:  pm2 monit"
    echo "  - Restart:  pm2 restart all"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

main() {
    print_header "AI Employee Cloud VM Setup"
    
    echo "This script will set up the AI Employee system on your Ubuntu VM."
    echo ""
    echo "Target Directory: ${PROJECT_DIR}"
    echo "Application User: ${APP_USER}"
    echo "Python Version:   ${PYTHON_VERSION}"
    echo "Node.js Version:  ${NODE_VERSION}"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Setup cancelled"
        exit 1
    fi
    
    # Run setup steps
    setup_system
    install_dependencies
    create_user
    setup_project
    install_docker
    install_nodejs
    setup_python_environment
    install_python_dependencies
    setup_environment
    setup_firewall
    setup_pm2_startup
    setup_cron
    setup_logrotate
    install_systemd_service
    
    show_next_steps
}

# Run main function
main "$@"
