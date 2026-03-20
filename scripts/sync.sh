#!/bin/bash
# =============================================================================
# Vault Git Sync Script
# =============================================================================
# Synchronizes vault data between local machine and cloud via Git
# 
# Usage:
#   ./sync.sh pull    - Pull latest changes from cloud (Cloud VM)
#   ./sync.sh push    - Push local changes to cloud (Local Machine)
#   ./sync.sh status  - Show sync status
#   ./sync.sh setup   - Initialize vault sync repository
# =============================================================================

set -e

# Configuration
VAULT_DIR="AI_Employee_Vault"
SYNC_REPO="${VAULT_SYNC_REPO:-git@github.com:user/vault-sync.git}"
SYNC_BRANCH="${VAULT_SYNC_BRANCH:-main}"
GIT_USER_NAME="${GIT_USER_NAME:-Vault Sync}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-vault@local}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Helper Functions
# =============================================================================

check_vault_dir() {
    if [ ! -d "$VAULT_DIR" ]; then
        log_error "Vault directory '$VAULT_DIR' not found!"
        exit 1
    fi
}

check_git_repo() {
    if [ ! -d "$VAULT_DIR/.git" ]; then
        log_error "Vault directory is not a Git repository. Run './sync.sh setup' first."
        exit 1
    fi
}

# =============================================================================
# Setup: Initialize vault sync repository
# =============================================================================

setup() {
    log_info "Setting up vault sync repository..."
    
    check_vault_dir
    
    cd "$VAULT_DIR"
    
    # Initialize git repo if not exists
    if [ ! -d ".git" ]; then
        git init
        log_info "Initialized Git repository in $VAULT_DIR"
    fi
    
    # Configure git user
    git config user.name "$GIT_USER_NAME"
    git config user.email "$GIT_USER_EMAIL"
    
    # Copy .gitignore.vault to .gitignore if exists
    if [ -f "../.gitignore.vault" ] && [ ! -f ".gitignore" ]; then
        cp "../.gitignore.vault" ".gitignore"
        log_info "Created .gitignore from template"
    fi
    
    # Add remote if not exists
    if ! git remote get-url origin &>/dev/null; then
        git remote add origin "$SYNC_REPO"
        log_info "Added remote origin: $SYNC_REPO"
    fi
    
    # Initial commit if there are uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        git add .
        git commit -m "Initial vault sync setup"
        log_info "Created initial commit"
    fi
    
    # Pull from remote if exists
    if git ls-remote origin &>/dev/null; then
        git pull origin "$SYNC_BRANCH" --allow-unrelated-histories || true
        log_info "Pulled from remote repository"
    fi
    
    cd ..
    log_success "Vault sync setup complete!"
}

# =============================================================================
# Pull: Fetch and merge changes from cloud (for Cloud VM)
# =============================================================================

pull() {
    log_info "Pulling latest changes from cloud..."
    
    check_vault_dir
    check_git_repo
    
    cd "$VAULT_DIR"
    
    # Stash any local changes
    git stash push -m "Local changes before pull" --include-untracked
    
    # Fetch and merge
    git fetch origin
    
    # Check if there are changes to pull
    if [ "$(git rev-parse HEAD)" != "$(git rev-parse @{u} 2>/dev/null)" ]; then
        git merge origin/"$SYNC_BRANCH" --no-edit || handle_merge_conflict
        log_success "Pulled latest changes from cloud"
    else
        log_info "Already up to date"
    fi
    
    # Restore stashed changes if any
    if git stash list | grep -q "Local changes before pull"; then
        git stash pop || log_warn "Could not restore stashed changes"
    fi
    
    cd ..
    log_success "Pull complete!"
}

# =============================================================================
# Push: Commit and push local changes (for Local Machine)
# =============================================================================

push() {
    log_info "Pushing local changes to cloud..."
    
    check_vault_dir
    check_git_repo
    
    cd "$VAULT_DIR"
    
    # Check for changes
    if [ -z "$(git status --porcelain)" ]; then
        log_info "No changes to push"
        cd ..
        return 0
    fi
    
    # Stage all changes
    git add -A
    
    # Commit with timestamp
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    git commit -m "Vault sync: $TIMESTAMP"
    
    # Push to remote
    git push origin "$SYNC_BRANCH" || handle_push_error
    
    cd ..
    log_success "Push complete! Changes synced to cloud."
}

# =============================================================================
# Status: Show current sync status
# =============================================================================

status() {
    check_vault_dir
    check_git_repo
    
    cd "$VAULT_DIR"
    
    echo ""
    echo "=== Vault Sync Status ==="
    echo ""
    git status
    echo ""
    
    # Show last sync time
    if git log -1 --format="%ci" &>/dev/null; then
        echo "Last commit: $(git log -1 --format="%ci")"
    fi
    
    # Show remote status
    if git rev-parse --abbrev-ref @{u} &>/dev/null; then
        echo ""
        echo "Remote tracking: $(git rev-parse --abbrev-ref @{u})"
        git log --oneline --left-right --graph HEAD...@{u}
    fi
    
    cd ..
}

# =============================================================================
# Conflict Handling
# =============================================================================

handle_merge_conflict() {
    log_error "Merge conflict detected!"
    echo ""
    echo "=== MERGE CONFLICT HANDLING ==="
    echo ""
    log_info "Conflicting files:"
    git diff --name-only --diff-filter=U
    echo ""
    
    # List conflicted files
    CONFLICTED_FILES=$(git diff --name-only --diff-filter=U)
    
    for file in $CONFLICTED_FILES; do
        echo "----------------------------------------"
        log_warn "Conflict in: $file"
        
        # Check if it's a markdown file (safe to auto-merge)
        if [[ "$file" == *.md ]]; then
            log_info "Auto-resolving markdown conflict by keeping both versions..."
            # For markdown files, we can try to keep both versions
            git checkout --ours "$file"
            OURS_CONTENT=$(cat "$file")
            git checkout --theirs "$file"
            THEIRS_CONTENT=$(cat "$file")
            
            # Combine both (ours first, then theirs)
            echo "$OURS_CONTENT" > "$file"
            echo "" >> "$file"
            echo "--- Remote changes below ---" >> "$file"
            echo "$THEIRS_CONTENT" >> "$file"
            
            git add "$file"
            log_info "Auto-resolved: $file"
        else
            log_error "Manual resolution required: $file"
            echo "  Run: git checkout --ours/--theirs <file>"
            echo "  Then: git add <file>"
        fi
    done
    
    echo ""
    log_info "To complete the merge:"
    echo "  1. Review and manually resolve any conflicts marked above"
    echo "  2. git add <resolved_files>"
    echo "  3. git commit -m 'Resolved merge conflicts'"
    echo ""
    
    exit 1
}

handle_push_error() {
    log_error "Push failed! This usually means remote has changes."
    echo ""
    log_info "Solution: Pull first, then push again"
    echo "  ./sync.sh pull"
    echo "  ./sync.sh push"
    echo ""
    exit 1
}

# =============================================================================
# Cron Mode: Silent pull for automated cloud sync
# =============================================================================

cron_pull() {
    # Silent mode for cron (no colors, minimal output)
    cd "$VAULT_DIR" 2>/dev/null || exit 1
    
    # Stash local changes
    git stash push -q -m "Cron stash" --include-untracked 2>/dev/null
    
    # Fetch and merge
    git fetch -q origin 2>/dev/null
    git merge -q origin/"$SYNC_BRANCH" --no-edit 2>/dev/null || true
    
    # Restore stashed changes
    git stash pop -q 2>/dev/null || true
    
    cd ..
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Vault sync completed" >> logs/vault_sync.log 2>/dev/null || true
}

# =============================================================================
# Main Entry Point
# =============================================================================

case "${1:-}" in
    setup)
        setup
        ;;
    pull)
        pull
        ;;
    push)
        push
        ;;
    status)
        status
        ;;
    cron)
        cron_pull
        ;;
    *)
        echo "Vault Git Sync Script"
        echo ""
        echo "Usage: $0 {setup|pull|push|status|cron}"
        echo ""
        echo "Commands:"
        echo "  setup   - Initialize vault sync repository"
        echo "  pull    - Pull latest changes from cloud (Cloud VM)"
        echo "  push    - Push local changes to cloud (Local Machine)"
        echo "  status  - Show current sync status"
        echo "  cron    - Silent pull for automated cron jobs"
        echo ""
        echo "Examples:"
        echo "  Local:  ./sync.sh push    # Push changes to cloud"
        echo "  Cloud:  ./sync.sh pull    # Pull changes from local"
        echo "  Cloud:  ./sync.sh cron    # Silent pull for cron"
        exit 1
        ;;
esac
