"""
Vault Git Sync for Platinum Tier
Syncs vault state between Cloud and Local via Git

This script runs on both Cloud and Local machines:
- Cloud: Pushes /Updates/, /Signals/, /Plans/ to remote
- Local: Pulls updates, merges to Dashboard.md, pushes /Approved/, /Done/

SECURITY: .gitignore ensures secrets NEVER sync:
- .env files
- *.session files
- credentials.json
- tokens/
- secrets/

Usage:
    python git_sync.py
"""

import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

from log_manager import setup_logging

# Setup logging
logger = setup_logging(
    log_file="logs/git_sync.log",
    logger_name="git_sync"
)


class VaultGitSync:
    """
    Platinum Tier Vault Git Sync
    
    Manages Git synchronization between Cloud and Local.
    Implements claim-by-move rule and single-writer constraints.
    """

    def __init__(
        self,
        vault_path: str = "AI_Employee_Vault",
        remote_url: str = None,
        agent_name: str = "unknown"
    ):
        """
        Initialize Git Sync.
        
        Args:
            vault_path: Path to AI Employee vault
            remote_url: Git remote URL (e.g., GitHub repo)
            agent_name: 'cloud_agent' or 'local_agent'
        """
        self.vault_path = Path(vault_path)
        self.remote_url = remote_url
        self.agent_name = agent_name
        self.git_dir = self.vault_path / ".git"
        
        # Folders this agent can sync
        if agent_name == "cloud_agent":
            self.sync_folders = [
                "Updates",
                "Signals",
                "Plans",
                "In_Progress/cloud_agent",
                "Logs/cloud_agent.log"
            ]
        elif agent_name == "local_agent":
            self.sync_folders = [
                "Approved",
                "Done",
                "Rejected",
                "In_Progress/local_agent",
                "Logs/local_agent.log"
            ]
        else:
            self.sync_folders = []
        
        logger.info(f"Git Sync initialized for {agent_name}")

    def initialize_repo(self) -> bool:
        """
        Initialize Git repository if not exists.
        Also sets up default git identity if not configured.

        Returns:
            True if successful
        """
        try:
            # Set default git identity if not configured
            self._setup_git_identity()
            
            if not self.git_dir.exists():
                logger.info("Initializing Git repository...")

                result = subprocess.run(
                    ['git', 'init'],
                    cwd=self.vault_path,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    logger.info("Git repository initialized")

                    # Add remote if URL provided
                    if self.remote_url:
                        result = subprocess.run(
                            ['git', 'remote', 'add', 'origin', self.remote_url],
                            cwd=self.vault_path,
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            logger.info(f"Remote 'origin' added: {self.remote_url}")
                        else:
                            logger.warning(f"Could not add remote: {result.stderr}")
                    else:
                        logger.info("No remote URL configured - running in local-only mode")

                    return True
                else:
                    logger.error(f"Git init failed: {result.stderr}")
                    return False
            else:
                logger.debug("Git repository already exists")
                
                # Ensure remote is configured if URL was provided
                if self.remote_url:
                    result = subprocess.run(
                        ['git', 'remote', 'get-url', 'origin'],
                        cwd=self.vault_path,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        # No remote configured, add it
                        subprocess.run(
                            ['git', 'remote', 'add', 'origin', self.remote_url],
                            cwd=self.vault_path,
                            capture_output=True,
                            text=True
                        )
                        logger.info(f"Added remote 'origin': {self.remote_url}")
                
                return True

        except Exception as e:
            logger.error(f"Error initializing Git repo: {e}")
            return False

    def _setup_git_identity(self) -> bool:
        """
        Set up default git user name and email if not configured.
        
        Returns:
            True if successful or already configured
        """
        try:
            # Check if user.name is configured
            result = subprocess.run(
                ['git', 'config', '--global', 'user.name'],
                capture_output=True,
                text=True
            )
            if not result.stdout.strip():
                # Not configured, set default
                subprocess.run(
                    ['git', 'config', '--global', 'user.name', 'Mahnoor'],
                    capture_output=True,
                    text=True
                )
                logger.info("Set default git user.name: 'Mahnoor'")
            
            # Check if user.email is configured
            result = subprocess.run(
                ['git', 'config', '--global', 'user.email'],
                capture_output=True,
                text=True
            )
            if not result.stdout.strip():
                # Not configured, set default
                subprocess.run(
                    ['git', 'config', '--global', 'user.email', 'mahnoor@example.com'],
                    capture_output=True,
                    text=True
                )
                logger.info("Set default git user.email: 'mahnoor@example.com'")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up git identity: {e}")
            return False

    def check_git_installed(self) -> bool:
        """Check if Git is installed"""
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.debug(f"Git version: {result.stdout.strip()}")
                return True
            else:
                logger.error("Git not installed or not in PATH")
                return False
        except FileNotFoundError:
            logger.error("Git not found. Please install Git.")
            return False

    def pull_changes(self, force: bool = False) -> bool:
        """
        Pull latest changes from remote with conflict avoidance.
        If no remote is configured, logs a warning and returns True (graceful degradation).

        Args:
            force: If True, reset to remote state (discard local changes)

        Returns:
            True if successful or no remote configured (graceful degradation)
        """
        try:
            if not self.git_dir.exists():
                logger.warning("Git repo not initialized, skipping pull")
                return False

            # Check if remote is configured
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.vault_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0 or not result.stdout.strip():
                logger.warning("No remote configured - skipping pull (local-only mode)")
                return True  # Graceful degradation

            logger.info("Pulling changes from remote...")

            # Stash any local changes first (preserves them safely)
            result = subprocess.run(
                ['git', 'stash', 'push', '-m', 'Auto-stash before pull'],
                cwd=self.vault_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                logger.debug(f"Stashed local changes: {result.stdout.strip()}")

            # Fetch first
            result = subprocess.run(
                ['git', 'fetch', 'origin'],
                cwd=self.vault_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"Git fetch failed: {result.stderr}")
                return False

            # Check if we have a tracking branch
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'],
                cwd=self.vault_path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Has tracking branch, pull with rebase
                result = subprocess.run(
                    ['git', 'pull', '--rebase', '--autostash'],
                    cwd=self.vault_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            else:
                # No tracking branch, try to pull from origin/main
                result = subprocess.run(
                    ['git', 'pull', 'origin', 'main', '--allow-unrelated-histories', '--autostash'],
                    cwd=self.vault_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

            if result.returncode == 0:
                if result.stdout.strip():
                    logger.info(f"Pull completed: {result.stdout.strip()}")
                else:
                    logger.info("Pull completed (no changes)")
                return True
            else:
                logger.error(f"Pull failed: {result.stderr}")
                # Try to abort rebase if it failed mid-way
                subprocess.run(
                    ['git', 'rebase', '--abort'],
                    cwd=self.vault_path,
                    capture_output=True,
                    timeout=10
                )
                return False

        except subprocess.TimeoutExpired:
            logger.error("Git pull timed out")
            return False
        except Exception as e:
            logger.error(f"Error pulling changes: {e}")
            return False

    def pull_only(self) -> bool:
        """
        Pull-only mode for Cloud VM (no push).
        Safe pull with conflict avoidance and auto-stash.

        Returns:
            True if successful
        """
        logger.info("=== Cloud Vault Pull Mode ===")
        
        # Check Git is installed
        if not self.check_git_installed():
            return False

        # Initialize repo if needed
        if not self.initialize_repo():
            return False

        # Pull changes
        return self.pull_changes()

    def push_changes(self) -> bool:
        """
        Push local changes to remote.
        If no remote is configured, logs a warning and returns True (graceful degradation).

        Returns:
            True if successful or no remote configured (graceful degradation)
        """
        try:
            if not self.git_dir.exists():
                logger.warning("Git repo not initialized, skipping push")
                return False

            # Check if remote is configured
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.vault_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0 or not result.stdout.strip():
                logger.warning("No remote configured - skipping push (local-only mode)")
                return True  # Graceful degradation

            # Stage changes in sync folders
            logger.info("Staging changes...")

            for folder in self.sync_folders:
                folder_path = self.vault_path / folder
                if folder_path.exists():
                    result = subprocess.run(
                        ['git', 'add', str(folder_path.relative_to(self.vault_path))],
                        cwd=self.vault_path,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        logger.debug(f"Staged: {folder}")
                    else:
                        logger.debug(f"Could not stage {folder}: {result.stderr}")

            # Check if there are changes to commit
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.vault_path,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                # Commit changes
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                commit_message = f"Auto-sync ({self.agent_name}): {timestamp}"

                result = subprocess.run(
                    ['git', 'commit', '-m', commit_message],
                    cwd=self.vault_path,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    logger.info(f"Committed: {commit_message}")
                else:
                    logger.error(f"Commit failed: {result.stderr}")
                    return False
                
                # Push changes
                logger.info("Pushing changes to remote...")
                
                # Check if we have a tracking branch
                result = subprocess.run(
                    ['git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'],
                    cwd=self.vault_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    # Has tracking branch, push
                    result = subprocess.run(
                        ['git', 'push'],
                        cwd=self.vault_path,
                        capture_output=True,
                        text=True
                    )
                else:
                    # No tracking branch, push to origin/main
                    result = subprocess.run(
                        ['git', 'push', '-u', 'origin', 'main'],
                        cwd=self.vault_path,
                        capture_output=True,
                        text=True
                    )
                
                if result.returncode == 0:
                    if result.stdout.strip():
                        logger.info(f"Push completed: {result.stdout.strip()}")
                    else:
                        logger.info("Push completed successfully")
                    return True
                else:
                    logger.error(f"Push failed: {result.stderr}")
                    return False
            else:
                logger.info("No changes to push")
                return True
                
        except Exception as e:
            logger.error(f"Error pushing changes: {e}")
            return False

    def run_sync(self) -> Tuple[bool, bool]:
        """
        Run full sync cycle (pull, then push).
        
        Returns:
            Tuple of (pull_success, push_success)
        """
        # Check Git is installed
        if not self.check_git_installed():
            return (False, False)
        
        # Initialize repo if needed
        self.initialize_repo()
        
        # Pull first
        pull_success = self.pull_changes()
        
        # Then push
        push_success = self.push_changes()
        
        return (pull_success, push_success)

    def get_status(self) -> dict:
        """Get Git repository status"""
        try:
            if not self.git_dir.exists():
                return {'initialized': False, 'status': 'Not initialized'}
            
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.vault_path,
                capture_output=True,
                text=True
            )
            
            changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            return {
                'initialized': True,
                'changes_count': len(changes),
                'changes': changes[:10],  # First 10 changes
                'status': 'Clean' if not changes else 'Has changes'
            }
            
        except Exception as e:
            return {'error': str(e)}


def main():
    """Entry point for Git Sync with CLI commands"""
    import os
    import sys
    import time

    # Parse command
    command = sys.argv[1] if len(sys.argv) > 1 else "sync"

    print("=" * 60)
    print("PLATINUM TIER - VAULT GIT SYNC")
    print("=" * 60)
    print()

    # Determine agent name from environment or default
    agent_name = os.getenv('PLATINUM_AGENT', 'local_agent')
    remote_url = os.getenv('VAULT_GIT_REMOTE', '')

    sync = VaultGitSync(
        vault_path="AI_Employee_Vault",
        remote_url=remote_url if remote_url else None,
        agent_name=agent_name
    )

    if command == "pull":
        # Pull-only mode (Cloud VM)
        print(f"Mode: Pull Only (Cloud)")
        print(f"Remote: {remote_url or 'Not configured'}")
        print()

        success = sync.pull_only()

        print(f"Pull: {'✅ Success' if success else '❌ Failed'}")
        print()
        print("=" * 60)

        sys.exit(0 if success else 1)

    elif command == "push":
        # Push-only mode (Local)
        print(f"Mode: Push Only (Local)")
        print(f"Agent: {agent_name}")
        print()

        # Check Git is installed
        if not sync.check_git_installed():
            sys.exit(1)

        sync.initialize_repo()
        success = sync.push_changes()

        print(f"Push: {'✅ Success' if success else '❌ Failed'}")
        print()
        print("=" * 60)

        sys.exit(0 if success else 1)

    elif command == "sync":
        # Full sync (pull + push)
        print(f"Agent: {agent_name}")
        print(f"Remote: {remote_url or 'Not configured'}")
        print()

        # Run initial sync
        print("Running initial sync...")
        pull_success, push_success = sync.run_sync()

        print(f"Pull: {'✅ Success' if pull_success else '❌ Failed'}")
        print(f"Push: {'✅ Success' if push_success else '❌ Failed'}")
        print()

        # Show status
        status = sync.get_status()
        print(f"Repository Status: {status.get('status', 'Unknown')}")
        if status.get('changes'):
            print(f"Changes ({status.get('changes_count', 0)}):")
            for change in status['changes'][:5]:
                print(f"  {change}")

        print()
        print("=" * 60)
        print()

        # Continue syncing every 5 minutes
        if remote_url:
            print("Starting continuous sync (every 5 minutes)...")
            print("Press Ctrl+C to stop")
            print()

            cycle_count = 0

            while True:
                try:
                    cycle_count += 1
                    logger.info(f"=== Sync Cycle {cycle_count} ===")

                    pull_success, push_success = sync.run_sync()

                    if pull_success and push_success:
                        logger.info(f"Cycle {cycle_count} completed successfully")
                    else:
                        logger.warning(f"Cycle {cycle_count} had errors")

                    time.sleep(300)  # 5 minutes

                except KeyboardInterrupt:
                    logger.info("Git Sync shutting down (user interrupt)")
                    break
                except Exception as e:
                    logger.error(f"Sync error: {e}")
                    time.sleep(60)
        else:
            print("Note: No remote URL configured. Run once mode only.")
            print("Set VAULT_GIT_REMOTE environment variable for continuous sync.")

    elif command == "status":
        # Show repository status
        print(f"Agent: {agent_name}")
        print()

        status = sync.get_status()
        print(f"Initialized: {status.get('initialized', False)}")
        print(f"Status: {status.get('status', 'Unknown')}")
        if status.get('changes'):
            print(f"Changes ({status.get('changes_count', 0)}):")
            for change in status['changes']:
                print(f"  {change}")

        print()
        print("=" * 60)

    elif command == "init":
        # Initialize repository
        print(f"Initializing repository for {agent_name}...")
        print()

        if sync.check_git_installed():
            success = sync.initialize_repo()
            if success:
                print("✅ Repository initialized")
            else:
                print("❌ Initialization failed")
                sys.exit(1)
        else:
            print("❌ Git not installed")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print()
        print("Usage: python git_sync.py <command>")
        print()
        print("Commands:")
        print("  pull   - Pull changes from remote (Cloud VM)")
        print("  push   - Push changes to remote (Local)")
        print("  sync   - Full sync cycle (pull + push)")
        print("  status - Show repository status")
        print("  init   - Initialize Git repository")
        sys.exit(1)


if __name__ == "__main__":
    main()
