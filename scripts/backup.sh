#!/bin/bash
# =============================================================================
# AI Employee - Backup Script
# =============================================================================
# 
# Automated backup script for AI Employee system
# Run daily via cron
# 
# Usage:
#   ./backup.sh              # Run backup
#   ./backup.sh --restore    # Restore from backup
#   ./backup.sh --list       # List available backups
#
# =============================================================================

set -e

# Configuration
PROJECT_DIR="${PROJECT_DIR:-/opt/ai-employee}"
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/ai-employee}"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create backup directory
mkdir -p "${BACKUP_DIR}"

case "${1:-}" in
    --list)
        log_info "Available backups:"
        ls -lh "${BACKUP_DIR}"
        exit 0
        ;;
    
    --restore)
        echo "Restore functionality - implement based on your needs"
        exit 0
        ;;
esac

log_info "Starting backup..."
log_info "Project: ${PROJECT_DIR}"
log_info "Backup: ${BACKUP_DIR}"

# Backup vault (exclude cache files)
log_info "Backing up vault..."
tar -czf "${BACKUP_DIR}/vault_${DATE}.tar.gz" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='*.log' \
    -C "${PROJECT_DIR}" \
    AI_Employee_Vault

# Backup environment (SECURE THIS!)
log_info "Backing up environment..."
cp "${PROJECT_DIR}/.env" "${BACKUP_DIR}/env_${DATE}.backup"
chmod 600 "${BACKUP_DIR}/env_${DATE}.backup"

# Backup PM2 configuration
log_info "Backing up PM2 configuration..."
if command -v pm2 &> /dev/null; then
    pm2 save "${BACKUP_DIR}/pm2_${DATE}.dump" 2>/dev/null || true
fi

# Backup recent logs (last 7 days)
log_info "Backing up recent logs..."
find "${PROJECT_DIR}/logs" -name "*.log" -mtime -7 -exec cp {} "${BACKUP_DIR}/" \; 2>/dev/null || true

# Delete old backups
log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "*.backup" -mtime +${RETENTION_DAYS} -delete

# Show backup size
BACKUP_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
log_info "Backup complete. Total backup size: ${BACKUP_SIZE}"

echo ""
echo "Backup files created:"
ls -lh "${BACKUP_DIR}"/*"${DATE}"*
