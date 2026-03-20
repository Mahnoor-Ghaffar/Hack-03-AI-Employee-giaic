#!/bin/bash
# =============================================================================
# Vault Git Sync - Cron Setup Script
# =============================================================================
# Idempotent setup for automated vault synchronization
# Safe to run multiple times - avoids duplicate cron entries
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CRON_FILE="$SCRIPT_DIR/vault_cron.txt"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "=============================================="
echo "Vault Git Sync - Cron Setup"
echo "=============================================="
echo ""
echo "Project Root: $PROJECT_ROOT"
echo "Cron Config:  $CRON_FILE"
echo ""

# Step 1: Create logs directory if missing
echo "[1/4] Ensuring logs directory exists..."
if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
    echo "  ✅ Created: $LOGS_DIR"
else
    echo "  ✅ Exists: $LOGS_DIR"
fi

# Step 2: Update cron file with correct project path
echo "[2/4] Updating cron configuration..."
if [ -f "$CRON_FILE" ]; then
    # Replace placeholder with actual path
    sed -i.bak "s|/path/to/Hack-03-AI-Employee-giaic|$PROJECT_ROOT|g" "$CRON_FILE"
    rm -f "$CRON_FILE.bak"
    echo "  ✅ Updated cron file with project path"
else
    echo "  ❌ Error: Cron file not found: $CRON_FILE"
    exit 1
fi

# Step 3: Remove existing vault sync cron jobs (avoid duplicates)
echo "[3/4] Removing existing vault sync cron jobs..."
EXISTING=$(crontab -l 2>/dev/null | grep -c "git_sync.py" || true)
if [ "$EXISTING" -gt 0 ]; then
    crontab -l 2>/dev/null | grep -v "git_sync.py" | crontab -
    echo "  ✅ Removed $EXISTING existing vault sync cron job(s)"
else
    echo "  ✅ No existing vault sync cron jobs found"
fi

# Step 4: Install new cron job
echo "[4/4] Installing new cron job..."
crontab -l 2>/dev/null | cat - "$CRON_FILE" | crontab -
echo "  ✅ Cron job installed"

# Verification
echo ""
echo "=============================================="
echo "SETUP COMPLETE"
echo "=============================================="
echo ""
echo "Installed cron jobs:"
crontab -l | grep -E "(git_sync|vault)"
echo ""
echo "Verification commands:"
echo "  crontab -l                    # List all cron jobs"
echo "  tail -f $LOGS_DIR/git_sync.log  # Watch sync logs"
echo ""
echo "Cron will start syncing within 2 minutes."
echo ""
