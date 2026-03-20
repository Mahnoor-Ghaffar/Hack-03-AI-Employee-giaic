#!/bin/bash
# =============================================================================
# AI Employee - Start Script
# =============================================================================
# 
# This script starts all AI Employee processes for 24/7 operation
# 
# Usage:
#   ./start.sh              # Start all processes
#   ./start.sh --status     # Check status
#   ./start.sh --stop       # Stop all processes
#   ./start.sh --restart    # Restart all processes
#   ./start.sh --logs       # View logs
#   ./start.sh --monitor    # Open PM2 monitor
#
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}"
VENV_DIR="${PROJECT_DIR}/venv"
LOG_DIR="${PROJECT_DIR}/logs"
VAULT_DIR="${PROJECT_DIR}/AI_Employee_Vault"
PM2_CONFIG="${PROJECT_DIR}/ecosystem.config.js"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================

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
    echo "  AI Employee - $1"
    echo "============================================================"
    echo ""
}

# =============================================================================
# Check Functions
# =============================================================================

check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is not installed. Please install Python 3.10+"
        exit 1
    fi
    log_info "Python version: $(python3 --version)"
}

check_venv() {
    if [ ! -d "${VENV_DIR}" ]; then
        log_error "Virtual environment not found at ${VENV_DIR}"
        log_info "Creating virtual environment..."
        python3 -m venv "${VENV_DIR}"
        source "${VENV_DIR}/bin/activate"
        pip install --upgrade pip
        pip install -r "${PROJECT_DIR}/requirements.txt"
    else
        log_info "Virtual environment found"
    fi
}

check_pm2() {
    if ! command -v pm2 &> /dev/null; then
        log_error "PM2 is not installed. Installing..."
        npm install -g pm2
    fi
    log_info "PM2 version: $(pm2 --version | grep -oP '(?<=version ).*')"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if [ ! -f "${PROJECT_DIR}/requirements.txt" ]; then
        log_error "requirements.txt not found"
        exit 1
    fi
    
    source "${VENV_DIR}/bin/activate"
    
    # Check critical packages
    python -c "import watchdog" 2>/dev/null || log_warning "watchdog not installed"
    python -c "import tweepy" 2>/dev/null || log_warning "tweepy not installed"
    python -c "import requests" 2>/dev/null || log_warning "requests not installed"
    
    log_success "Dependencies check complete"
}

check_directories() {
    log_info "Checking directories..."
    
    # Create required directories
    mkdir -p "${LOG_DIR}"
    mkdir -p "${VAULT_DIR}/Personal/Archive"
    mkdir -p "${VAULT_DIR}/Plans"
    mkdir -p "${VAULT_DIR}/Reports"
    mkdir -p "${VAULT_DIR}/Logs"
    mkdir -p "${VAULT_DIR}/Needs_Action"
    mkdir -p "${VAULT_DIR}/Done"
    mkdir -p "${VAULT_DIR}/Pending_Approval"
    mkdir -p "${PROJECT_DIR}/temp"
    
    # Set permissions
    chmod -R 755 "${LOG_DIR}" "${VAULT_DIR}" "${PROJECT_DIR}/temp"
    
    log_success "Directories ready"
}

check_env() {
    if [ ! -f "${PROJECT_DIR}/.env" ]; then
        log_warning ".env file not found. Copying from .env.example..."
        cp "${PROJECT_DIR}/.env.example" "${PROJECT_DIR}/.env"
        log_warning "Please edit .env file with your credentials"
    else
        log_info ".env file found"
    fi
}

# =============================================================================
# Action Functions
# =============================================================================

start_all() {
    print_header "Starting AI Employee System"
    
    check_python
    check_venv
    check_pm2
    check_directories
    check_env
    check_dependencies
    
    cd "${PROJECT_DIR}"
    
    log_info "Starting processes with PM2..."
    
    # Start all processes from ecosystem config
    pm2 start "${PM2_CONFIG}"
    
    # Wait for processes to start
    sleep 5
    
    # Show status
    pm2 status
    
    log_success "All processes started!"
    log_info "Use 'pm2 monit' to monitor processes"
    log_info "Use 'pm2 logs' to view logs"
    log_info "Use 'pm2 status' to check status"
}

stop_all() {
    print_header "Stopping AI Employee System"
    
    cd "${PROJECT_DIR}"
    
    log_info "Stopping all PM2 processes..."
    pm2 stop all
    
    log_success "All processes stopped"
}

restart_all() {
    print_header "Restarting AI Employee System"
    
    cd "${PROJECT_DIR}"
    
    log_info "Restarting all PM2 processes..."
    pm2 restart all
    
    sleep 3
    pm2 status
    
    log_success "All processes restarted"
}

reload_all() {
    print_header "Reloading AI Employee System (Zero Downtime)"
    
    cd "${PROJECT_DIR}"
    
    log_info "Reloading all PM2 processes..."
    pm2 reload all
    
    sleep 3
    pm2 status
    
    log_success "All processes reloaded"
}

show_status() {
    print_header "AI Employee System Status"
    
    cd "${PROJECT_DIR}"
    
    echo ""
    log_info "PM2 Process Status:"
    pm2 status
    
    echo ""
    log_info "System Resources:"
    echo "  Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
    echo "  Disk: $(df -h "${PROJECT_DIR}" | tail -1 | awk '{print $3 "/" $2}')"
    
    echo ""
    log_info "Recent Logs (last 10 lines):"
    pm2 logs --lines 10 --nostream
}

view_logs() {
    print_header "AI Employee Logs"
    
    cd "${PROJECT_DIR}"
    
    log_info "Streaming logs (Ctrl+C to exit)..."
    pm2 logs --lines 50
}

open_monitor() {
    print_header "AI Employee Monitor"
    
    cd "${PROJECT_DIR}"
    
    log_info "Opening PM2 monitor (Ctrl+C to exit)..."
    pm2 monit
}

save_pm2() {
    print_header "Saving PM2 Configuration"
    
    cd "${PROJECT_DIR}"
    
    pm2 save
    pm2 startup
    
    log_success "PM2 configuration saved"
    log_info "Processes will auto-start on system reboot"
}

cleanup() {
    print_header "Cleaning Up"
    
    cd "${PROJECT_DIR}"
    
    log_info "Deleting stopped processes..."
    pm2 delete stopped
    
    log_info "Clearing logs older than 7 days..."
    find "${LOG_DIR}" -name "*.log" -mtime +7 -delete
    
    log_success "Cleanup complete"
}

show_help() {
    print_header "AI Employee Start Script"
    
    echo "Usage: ./start.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  (no args)     Start all processes"
    echo "  --status      Show process status"
    echo "  --stop        Stop all processes"
    echo "  --restart     Restart all processes"
    echo "  --reload      Reload all processes (zero downtime)"
    echo "  --logs        View logs"
    echo "  --monitor     Open PM2 monitor"
    echo "  --save        Save PM2 configuration for auto-start"
    echo "  --cleanup     Clean up stopped processes and old logs"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start.sh              # Start all processes"
    echo "  ./start.sh --status     # Check status"
    echo "  ./start.sh --logs       # View logs"
    echo "  ./start.sh --monitor    # Open interactive monitor"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

case "${1:-}" in
    --status)
        show_status
        ;;
    --stop)
        stop_all
        ;;
    --restart)
        restart_all
        ;;
    --reload)
        reload_all
        ;;
    --logs)
        view_logs
        ;;
    --monitor)
        open_monitor
        ;;
    --save)
        save_pm2
        ;;
    --cleanup)
        cleanup
        ;;
    --help|-h)
        show_help
        ;;
    "")
        start_all
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
