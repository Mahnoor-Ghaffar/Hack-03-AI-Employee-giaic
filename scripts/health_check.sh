#!/bin/bash
# =============================================================================
# AI Employee - Health Check Script
# =============================================================================
# 
# This script performs health checks on all AI Employee processes and services
# Run every 5 minutes via cron
# 
# Usage:
#   ./health_check.sh              # Run health check
#   ./health_check.sh --verbose    # Verbose output
#   ./health_check.sh --fix        # Auto-fix issues
#
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
VENV_DIR="${PROJECT_DIR}/venv"
LOG_DIR="${PROJECT_DIR}/logs"
VAULT_DIR="${PROJECT_DIR}/AI_Employee_Vault"
HEALTH_LOG="${LOG_DIR}/health_check.log"
ALERT_EMAIL="${ALERT_EMAIL:-admin@example.com}"
MAX_LOG_SIZE_MB=50
MAX_MEMORY_PERCENT=90
MIN_DISK_PERCENT=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Health status
HEALTH_STATUS=0
ISSUES_FOUND=0

# =============================================================================
# Helper Functions
# =============================================================================

log_health() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "${timestamp} [${level}] ${message}" >> "${HEALTH_LOG}"
    
    if [ "${VERBOSE:-false}" = "true" ]; then
        case "$level" in
            ERROR)   echo -e "${RED}[ERROR]${NC} ${message}" ;;
            WARNING) echo -e "${YELLOW}[WARNING]${NC} ${message}" ;;
            INFO)    echo -e "${GREEN}[INFO]${NC} ${message}" ;;
        esac
    fi
}

send_alert() {
    local subject="$1"
    local message="$2"
    
    log_health "ERROR" "ALERT: ${subject}"
    
    # Send email alert (if mail is configured)
    if command -v mail &> /dev/null; then
        echo "${message}" | mail -s "[AI Employee Alert] ${subject}" "${ALERT_EMAIL}"
    fi
    
    # Log to system journal
    if command -v journalctl &> /dev/null; then
        journalctl -t ai-employee-health --priority=err --message="${subject}: ${message}"
    fi
}

# =============================================================================
# Health Check Functions
# =============================================================================

check_pm2_processes() {
    log_health "INFO" "Checking PM2 processes..."
    
    # Get PM2 status
    local pm2_status=$(pm2 list --json 2>/dev/null)
    
    if [ -z "${pm2_status}" ]; then
        log_health "ERROR" "PM2 is not running or no processes found"
        send_alert "PM2 Not Running" "PM2 process manager is not running or has no processes"
        HEALTH_STATUS=1
        ((ISSUES_FOUND++))
        return
    fi
    
    # Check each process
    local processes=$(echo "${pm2_status}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for proc in data:
    name = proc.get('name', 'unknown')
    status = proc.get('pm2_env', {}).get('status', 'unknown')
    restart_count = proc.get('pm2_env', {}).get('restart_time', 0)
    memory = proc.get('pm2_env', {}).get('monit', {}).get('memory', 0)
    cpu = proc.get('pm2_env', {}).get('monit', {}).get('cpu', 0)
    print(f'{name}|{status}|{restart_count}|{memory}|{cpu}')
" 2>/dev/null)
    
    while IFS='|' read -r name status restart_count memory cpu; do
        if [ -z "${name}" ]; then continue; fi
        
        # Check status
        if [ "${status}" != "online" ]; then
            log_health "ERROR" "Process '${name}' is ${status} (not online)"
            send_alert "Process Down" "Process '${name}' is ${status}"
            HEALTH_STATUS=1
            ((ISSUES_FOUND++))
            
            # Auto-fix if requested
            if [ "${FIX:-false}" = "true" ]; then
                log_health "INFO" "Attempting to restart '${name}'..."
                pm2 restart "${name}"
            fi
        fi
        
        # Check restart count
        if [ "${restart_count}" -gt 10 ]; then
            log_health "WARNING" "Process '${name}' has restarted ${restart_count} times"
            ((ISSUES_FOUND++))
        fi
        
        # Check memory (in MB)
        local memory_mb=$((memory / 1024 / 1024))
        if [ "${memory_mb}" -gt 500 ]; then
            log_health "WARNING" "Process '${name}' using ${memory_mb}MB memory"
            ((ISSUES_FOUND++))
        fi
        
        # Check CPU
        local cpu_int=${cpu%.*}
        if [ "${cpu_int}" -gt 80 ]; then
            log_health "WARNING" "Process '${name}' using ${cpu}% CPU"
            ((ISSUES_FOUND++))
        fi
        
        if [ "${VERBOSE:-false}" = "true" ]; then
            log_health "INFO" "Process '${name}': status=${status}, restarts=${restart_count}, memory=${memory_mb}MB, cpu=${cpu}%"
        fi
    done <<< "${processes}"
    
    log_health "INFO" "PM2 processes check complete"
}

check_disk_space() {
    log_health "INFO" "Checking disk space..."
    
    local disk_usage=$(df -h "${PROJECT_DIR}" | tail -1 | awk '{print $5}' | sed 's/%//')
    local disk_available=$(df -h "${PROJECT_DIR}" | tail -1 | awk '{print $4}')
    
    if [ "${disk_usage}" -gt 90 ]; then
        log_health "ERROR" "Disk usage critical: ${disk_usage}% (only ${disk_available} available)"
        send_alert "Disk Space Critical" "Disk usage is ${disk_usage}%, only ${disk_available} available"
        HEALTH_STATUS=1
        ((ISSUES_FOUND++))
    elif [ "${disk_usage}" -gt 80 ]; then
        log_health "WARNING" "Disk usage high: ${disk_usage}% (${disk_available} available)"
        ((ISSUES_FOUND++))
    else
        log_health "INFO" "Disk usage OK: ${disk_usage}% (${disk_available} available)"
    fi
}

check_memory() {
    log_health "INFO" "Checking system memory..."
    
    local memory_usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    
    if [ "${memory_usage}" -gt "${MAX_MEMORY_PERCENT}" ]; then
        log_health "ERROR" "System memory critical: ${memory_usage}%"
        send_alert "Memory Critical" "System memory usage is ${memory_usage}%"
        HEALTH_STATUS=1
        ((ISSUES_FOUND++))
    elif [ "${memory_usage}" -gt 80 ]; then
        log_health "WARNING" "System memory high: ${memory_usage}%"
        ((ISSUES_FOUND++))
    else
        log_health "INFO" "System memory OK: ${memory_usage}%"
    fi
}

check_log_files() {
    log_health "INFO" "Checking log files..."
    
    # Check log directory size
    local log_size=$(du -sm "${LOG_DIR}" 2>/dev/null | cut -f1)
    
    if [ "${log_size}" -gt "${MAX_LOG_SIZE_MB}" ]; then
        log_health "WARNING" "Log directory size: ${log_size}MB (max: ${MAX_LOG_SIZE_MB}MB)"
        ((ISSUES_FOUND++))
        
        # Auto-cleanup if requested
        if [ "${FIX:-false}" = "true" ]; then
            log_health "INFO" "Cleaning up old logs..."
            find "${LOG_DIR}" -name "*.log" -mtime +7 -delete
        fi
    else
        log_health "INFO" "Log directory size OK: ${log_size}MB"
    fi
    
    # Check for error patterns in recent logs
    local error_count=$(grep -c "ERROR" "${LOG_DIR}/ai_employee.log" 2>/dev/null || echo "0")
    if [ "${error_count}" -gt 100 ]; then
        log_health "WARNING" "High error count in logs: ${error_count} errors"
        ((ISSUES_FOUND++))
    fi
}

check_vault_directory() {
    log_health "INFO" "Checking vault directory..."
    
    if [ ! -d "${VAULT_DIR}" ]; then
        log_health "ERROR" "Vault directory not found: ${VAULT_DIR}"
        send_alert "Vault Missing" "Vault directory is missing"
        HEALTH_STATUS=1
        ((ISSUES_FOUND++))
        return
    fi
    
    # Check vault subdirectories
    local required_dirs=("Personal/Archive" "Plans" "Reports" "Logs" "Needs_Action" "Done")
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "${VAULT_DIR}/${dir}" ]; then
            log_health "WARNING" "Vault subdirectory missing: ${dir}"
            ((ISSUES_FOUND++))
        fi
    done
    
    # Check vault disk usage
    local vault_size=$(du -sm "${VAULT_DIR}" 2>/dev/null | cut -f1)
    log_health "INFO" "Vault directory size: ${vault_size}MB"
}

check_odoo_container() {
    log_health "INFO" "Checking Odoo container..."
    
    if command -v docker &> /dev/null; then
        local odoo_status=$(docker ps --filter "name=odoo" --format "{{.Status}}" 2>/dev/null)
        
        if [ -z "${odoo_status}" ]; then
            log_health "WARNING" "Odoo container not running"
            ((ISSUES_FOUND++))
        else
            log_health "INFO" "Odoo container: ${odoo_status}"
        fi
    else
        log_health "INFO" "Docker not installed, skipping Odoo check"
    fi
}

check_network() {
    log_health "INFO" "Checking network connectivity..."
    
    # Check if we can reach common endpoints
    local endpoints=("google.com" "github.com" "pypi.org")
    
    for endpoint in "${endpoints[@]}"; do
        if ping -c 1 -W 2 "${endpoint}" &> /dev/null; then
            if [ "${VERBOSE:-false}" = "true" ]; then
                log_health "INFO" "Network OK: ${endpoint}"
            fi
        else
            log_health "WARNING" "Network unreachable: ${endpoint}"
            ((ISSUES_FOUND++))
        fi
    done
}

check_python_environment() {
    log_health "INFO" "Checking Python environment..."
    
    if [ ! -d "${VENV_DIR}" ]; then
        log_health "ERROR" "Virtual environment not found: ${VENV_DIR}"
        HEALTH_STATUS=1
        ((ISSUES_FOUND++))
        return
    fi
    
    # Check if venv is active
    if [ ! -f "${VENV_DIR}/bin/activate" ]; then
        log_health "ERROR" "Virtual environment broken: ${VENV_DIR}"
        HEALTH_STATUS=1
        ((ISSUES_FOUND++))
    fi
    
    log_health "INFO" "Python environment OK"
}

# =============================================================================
# Report Functions
# =============================================================================

generate_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo ""
    echo "============================================================"
    echo "  AI Employee Health Check Report"
    echo "  Generated: ${timestamp}"
    echo "============================================================"
    echo ""
    
    if [ ${HEALTH_STATUS} -eq 0 ] && [ ${ISSUES_FOUND} -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed${NC}"
        echo ""
        echo "System Status: HEALTHY"
    else
        echo -e "${RED}✗ ${ISSUES_FOUND} issue(s) found${NC}"
        echo ""
        echo "System Status: NEEDS ATTENTION"
    fi
    
    echo ""
    echo "Summary:"
    echo "  - PM2 Processes: Checked"
    echo "  - Disk Space: Checked"
    echo "  - Memory: Checked"
    echo "  - Log Files: Checked"
    echo "  - Vault Directory: Checked"
    echo ""
    echo "Log file: ${HEALTH_LOG}"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

# Parse arguments
VERBOSE=false
FIX=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --fix|-f)
            FIX=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--verbose] [--fix]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v    Show detailed output"
            echo "  --fix, -f        Auto-fix issues when possible"
            echo "  --help, -h       Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Run health checks
log_health "INFO" "Starting health check..."

check_pm2_processes
check_disk_space
check_memory
check_log_files
check_vault_directory
check_odoo_container
check_network
check_python_environment

# Generate report
generate_report

# Exit with appropriate status
exit ${HEALTH_STATUS}
