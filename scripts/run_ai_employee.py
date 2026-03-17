#!/usr/bin/env python3
"""
Silver Scheduler - AI Employee Orchestrator Script

This script runs the vault-watcher and task-planner in a scheduled loop.
It supports multiple execution modes and prevents duplicate instances.

Silver Tier Requirements:
- Run vault-watcher and task-planner in a loop
- Default interval: 5 minutes
- CLI modes: --daemon, --once, --status
- Log to logs/ai_employee.log
- Log rotation at 5MB
- Lock file system to prevent duplicates

Usage:
    python scripts/run_ai_employee.py --daemon     # Run continuously (5 min interval)
    python scripts/run_ai_employee.py --once       # Single execution
    python scripts/run_ai_employee.py --status     # Show status
    python scripts/run_ai_employee.py --help       # Show help
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from log_manager import setup_logging, MAX_FILE_SIZE, BACKUP_COUNT

# Constants
LOCK_FILE = Path("logs/.scheduler.lock")
LOG_FILE = Path("logs/ai_employee.log")
DEFAULT_INTERVAL_MINUTES = 5
VAULT_PATH = Path("AI_Employee_Vault")

# Scheduler state
_scheduler_running = False
_current_pid: Optional[int] = None


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        global _scheduler_running
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        _scheduler_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def get_pid() -> int:
    """Get current process ID."""
    return os.getpid()


def check_lock() -> bool:
    """
    Check if a lock file exists and if the scheduler is still running.
    
    Returns:
        bool: True if lock is active (another instance is running), False otherwise
    """
    if not LOCK_FILE.exists():
        return False
    
    try:
        with open(LOCK_FILE, 'r') as f:
            lock_data = json.load(f)
        
        pid = lock_data.get('pid')
        created = lock_data.get('created', '')
        
        # Check if the process is still running
        if pid:
            try:
                os.kill(pid, 0)  # Signal 0 checks if process exists without killing it
                logger.warning(f"Scheduler already running with PID {pid} since {created}")
                return True
            except OSError:
                # Process not running, stale lock file
                logger.info("Found stale lock file, removing...")
                LOCK_FILE.unlink()
                return False
        
        return False
    
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error reading lock file: {e}, removing...")
        try:
            LOCK_FILE.unlink()
        except:
            pass
        return False


def acquire_lock() -> bool:
    """
    Create a lock file to prevent duplicate instances.
    
    Returns:
        bool: True if lock acquired successfully, False otherwise
    """
    if check_lock():
        return False
    
    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        lock_data = {
            'pid': get_pid(),
            'created': datetime.now().isoformat(),
            'mode': 'daemon' if _scheduler_running else 'once'
        }
        
        with open(LOCK_FILE, 'w') as f:
            json.dump(lock_data, f, indent=2)
        
        logger.info(f"Lock file created: {LOCK_FILE} (PID: {get_pid()})")
        return True
    
    except IOError as e:
        logger.error(f"Failed to create lock file: {e}")
        return False


def release_lock():
    """Remove the lock file."""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
            logger.info(f"Lock file removed: {LOCK_FILE}")
    except IOError as e:
        logger.warning(f"Failed to remove lock file: {e}")


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        VAULT_PATH,
        VAULT_PATH / "Inbox",
        VAULT_PATH / "Needs_Action",
        VAULT_PATH / "Done",
        VAULT_PATH / "Approved",
        VAULT_PATH / "Pending_Approval",
        VAULT_PATH / "Needs_Approval",
        VAULT_PATH / "Logs",
        LOG_FILE.parent
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_vault_status() -> Dict:
    """
    Get current vault status including file counts.
    
    Returns:
        dict: Status information
    """
    status = {
        'inbox_count': 0,
        'needs_action_count': 0,
        'pending_approval_count': 0,
        'active_tasks': [],
        'last_run': None,
        'lock_active': check_lock()
    }
    
    # Count files in each directory
    if (VAULT_PATH / "Inbox").exists():
        status['inbox_count'] = len(list((VAULT_PATH / "Inbox").glob("*.md")))
    
    if (VAULT_PATH / "Needs_Action").exists():
        needs_action_files = list((VAULT_PATH / "Needs_Action").glob("*.md"))
        status['needs_action_count'] = len(needs_action_files)
        status['active_tasks'] = [f.name for f in needs_action_files]
    
    if (VAULT_PATH / "Pending_Approval").exists():
        status['pending_approval_count'] = len(list((VAULT_PATH / "Pending_Approval").glob("*.md")))
    
    if (VAULT_PATH / "Needs_Approval").exists():
        status['pending_approval_count'] += len(list((VAULT_PATH / "Needs_Approval").glob("*.md")))
    
    # Check for last run info from lock file
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, 'r') as f:
                lock_data = json.load(f)
                status['last_run'] = lock_data.get('created', 'Unknown')
        except:
            pass
    
    return status


def run_vault_watcher_cycle():
    """
    Run a single cycle of the vault-watcher.
    Processes files in Inbox and moves them to Needs_Action.
    """
    logger.info("--- Starting vault-watcher cycle ---")
    
    try:
        from filesystem_watcher import FileSystemWatcher
        
        inbox_path = VAULT_PATH / "Inbox"
        if not inbox_path.exists():
            logger.debug("Inbox directory does not exist, skipping vault-watcher")
            return
        
        md_files = list(inbox_path.glob("*.md"))
        logger.info(f"Found {len(md_files)} file(s) in Inbox")
        
        for file_path in md_files:
            logger.info(f"Processing file: {file_path.name}")
            
            # Move file to Needs_Action
            from skills.vault_skills import get_vault
            vault = get_vault()
            result = vault.move_to_needs_action(file_path.name)
            logger.info(f"Move result: {result}")
            
            if "Error" not in result:
                # Trigger task-planner for this file
                run_task_planner(file_path.name)
            else:
                logger.error(f"Failed to move {file_path.name}: {result}")
        
        logger.info("--- vault-watcher cycle completed ---")
    
    except Exception as e:
        logger.error(f"Error in vault-watcher cycle: {e}")


def run_task_planner(file_name: str) -> bool:
    """
    Run the task-planner skill for a specific file.
    
    Args:
        file_name: Name of the file in Needs_Action to process
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"--- Starting task-planner for: {file_name} ---")
    
    try:
        from claude_sdk_wrapper import T
        
        plan_prompt = f"""Process the task file '{file_name}' located in AI_Employee_Vault/Needs_Action.

Your responsibilities:
1. Read and analyze the content of the task file
2. Generate a detailed, step-by-step implementation plan
3. Return the plan in markdown format with clear sections and checkboxes for action items.

File to process: {file_name}
"""
        
        # Use T class to spawn the task-planner subagent
        task = T(
            description=f"Process task file: {file_name}",
            prompt=plan_prompt,
            subagent_type='task-planner',
            model='opus',
            run_in_background=False,
            allowed_tools=["Read", "Write", "Glob", "Edit", "Bash", "Skill"],
            system_prompt="""You are a task-planner specialist for the AI Employee system.
Your role is to analyze task files in Needs_Action and generate detailed implementation plans.
Always save plans as Plan_*.md files in the Needs_Action folder."""
        )
        
        logger.info(f"Task-planner completed for {file_name}. Task ID: {task.task_id}")
        
        if task.output:
            # Save the plan
            from skills.vault_skills import get_vault
            vault = get_vault()
            plan_result = vault.write_plan(file_name, task.output)
            logger.info(f"Plan saved: {plan_result}")
            logger.info(f"--- task-planner completed for: {file_name} ---")
            return True
        else:
            logger.warning(f"No plan content generated for {file_name}")
            return False
    
    except Exception as e:
        logger.error(f"Error in task-planner for {file_name}: {e}")
        return False


def run_orchestrator_cycle():
    """
    Run a single cycle of the full orchestrator.
    Processes Gmail, LinkedIn, and pending approvals.
    """
    logger.info("--- Starting orchestrator cycle ---")
    
    try:
        from orchestrator import process_gmail_updates, process_linkedin_ideas, process_pending_approvals
        from gmail_watcher import GmailWatcher
        from linkedin_watcher import LinkedInWatcher
        
        # Process Gmail updates
        gmail_credentials_path = "gmail_credentials.json"
        if Path(gmail_credentials_path).exists():
            logger.info("Processing Gmail updates...")
            gmail_watcher = GmailWatcher(vault_path=str(VAULT_PATH), credentials_path=gmail_credentials_path)
            process_gmail_updates(gmail_watcher)
        else:
            logger.debug("Gmail credentials not found, skipping Gmail processing")
        
        # Process LinkedIn post ideas
        logger.info("Processing LinkedIn post ideas...")
        linkedin_watcher = LinkedInWatcher(vault_path=str(VAULT_PATH))
        process_linkedin_ideas(linkedin_watcher)
        
        # Process pending approvals
        logger.info("Processing pending approvals...")
        process_pending_approvals()
        
        logger.info("--- Orchestrator cycle completed ---")
    
    except Exception as e:
        logger.error(f"Error in orchestrator cycle: {e}")


def run_cycle(cycle_number: int):
    """
    Run a complete execution cycle.
    
    Args:
        cycle_number: Current cycle number for logging
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting execution cycle {cycle_number}")
    logger.info(f"{'='*60}")
    
    start_time = datetime.now()
    
    try:
        # Step 1: Run vault-watcher
        run_vault_watcher_cycle()
        
        # Step 2: Run orchestrator cycle (Gmail, LinkedIn, Approvals)
        run_orchestrator_cycle()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Cycle {cycle_number} completed in {elapsed:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Cycle {cycle_number} failed: {e}")
    
    logger.info(f"{'='*60}\n")


def run_daemon(interval_minutes: int = DEFAULT_INTERVAL_MINUTES):
    """
    Run the scheduler in daemon mode (continuous loop).
    
    Args:
        interval_minutes: Minutes between execution cycles
    """
    global _scheduler_running
    
    _scheduler_running = True
    setup_signal_handlers()
    
    if not acquire_lock():
        logger.error("Failed to acquire lock. Another instance may be running.")
        print(f"Error: Scheduler already running. Use '--status' to check.")
        return False
    
    logger.info(f"Scheduler started in daemon mode (interval: {interval_minutes} minutes)")
    logger.info(f"Press Ctrl+C to stop")
    
    cycle_number = 0
    
    try:
        while _scheduler_running:
            cycle_number += 1
            run_cycle(cycle_number)
            
            if not _scheduler_running:
                logger.info("Shutdown signal received, stopping after this cycle...")
                break
            
            # Sleep for the interval (in seconds)
            sleep_seconds = interval_minutes * 60
            logger.info(f"Sleeping for {interval_minutes} minutes...")
            
            # Sleep in small increments to allow signal handling
            for _ in range(sleep_seconds):
                if not _scheduler_running:
                    break
                time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
    
    finally:
        release_lock()
        logger.info("Scheduler stopped")
    
    return True


def run_once():
    """
    Run a single execution cycle.
    """
    if check_lock():
        logger.warning("Another scheduler instance may be running, but proceeding with --once mode")
    
    logger.info("Scheduler started in once mode (single execution)")
    run_cycle(1)
    logger.info("Single execution completed")
    return True


def show_status():
    """
    Display current scheduler and vault status.
    """
    status = get_vault_status()
    
    print("\n" + "=" * 60)
    print("AI Employee Scheduler Status")
    print("=" * 60)
    print(f"\nLock Active: {'Yes' if status['lock_active'] else 'No'}")
    print(f"Last Run: {status['last_run'] or 'Never'}")
    print(f"\nVault Statistics:")
    print(f"  - Inbox: {status['inbox_count']} file(s)")
    print(f"  - Needs Action: {status['needs_action_count']} task(s)")
    print(f"  - Pending Approval: {status['pending_approval_count']} item(s)")
    
    if status['active_tasks']:
        print(f"\nActive Tasks:")
        for task in status['active_tasks']:
            print(f"  - {task}")
    else:
        print(f"\nNo active tasks")
    
    print(f"\nLog File: {LOG_FILE}")
    if LOG_FILE.exists():
        log_size = LOG_FILE.stat().st_size
        print(f"Log Size: {log_size / 1024:.2f} KB")
        print(f"Max Log Size: {MAX_FILE_SIZE / (1024 * 1024):.0f} MB (rotation threshold)")
    
    print("=" * 60 + "\n")
    
    return status


def run_scheduler(mode: str = 'once', interval_minutes: int = DEFAULT_INTERVAL_MINUTES, 
                  log_file: str = str(LOG_FILE)) -> Dict:
    """
    Main scheduler function - entry point for skill usage.
    
    Args:
        mode: Execution mode - 'daemon', 'once', or 'status'
        interval_minutes: Minutes between cycles (daemon mode)
        log_file: Path to log file
        
    Returns:
        dict: Status dictionary with execution results
    """
    global logger
    
    # Setup logging
    logger = setup_logging(log_file=log_file, logger_name="silver-scheduler")
    
    # Ensure directories exist
    ensure_directories()
    
    logger.info(f"Scheduler initialized with mode: {mode}")
    
    if mode == 'status':
        status = show_status()
        return {'status': 'success', 'data': status}
    
    elif mode == 'once':
        success = run_once()
        return {'status': 'success' if success else 'failed', 'mode': 'once'}
    
    elif mode == 'daemon':
        success = run_daemon(interval_minutes)
        return {'status': 'success' if success else 'failed', 'mode': 'daemon'}
    
    else:
        logger.error(f"Unknown mode: {mode}")
        return {'status': 'error', 'message': f'Unknown mode: {mode}'}


def check_status() -> Dict:
    """
    Check current scheduler status - wrapper for skill usage.
    
    Returns:
        dict: Status information
    """
    return get_vault_status()


def stop_scheduler() -> bool:
    """
    Stop a running scheduler by removing the lock file.
    
    Returns:
        bool: True if scheduler was stopped, False if not running
    """
    if not check_lock():
        logger.info("Scheduler is not running")
        return False
    
    try:
        release_lock()
        logger.info("Scheduler stopped")
        return True
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        return False


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description='AI Employee Scheduler - Silver Tier',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --daemon              Run continuously (5 min interval)
  %(prog)s --daemon --interval 10  Run continuously (10 min interval)
  %(prog)s --once                Run single execution cycle
  %(prog)s --status              Show current status
        """
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run continuously in daemon mode (default interval: 5 minutes)'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run a single execution cycle and exit'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status (active tasks & inbox count)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=DEFAULT_INTERVAL_MINUTES,
        help=f'Interval in minutes between cycles (default: {DEFAULT_INTERVAL_MINUTES})'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default=str(LOG_FILE),
        help=f'Log file path (default: {LOG_FILE})'
    )
    
    args = parser.parse_args()
    
    # Determine mode
    if args.status:
        mode = 'status'
    elif args.daemon:
        mode = 'daemon'
    elif args.once:
        mode = 'once'
    else:
        # Default to --once if no mode specified
        mode = 'once'
        print("No mode specified, defaulting to --once mode. Use --daemon, --once, or --status.")
    
    # Setup logging
    global logger
    logger = setup_logging(log_file=args.log_file, logger_name="silver-scheduler")
    
    # Ensure directories exist
    ensure_directories()
    
    # Run scheduler
    if mode == 'status':
        show_status()
    elif mode == 'daemon':
        run_daemon(args.interval)
    elif mode == 'once':
        run_once()


if __name__ == '__main__':
    main()
