"""
Human Approval Agent Skill - Silver Tier

This module implements a blocking human-in-the-loop approval workflow.
It monitors the Needs_Approval folder, blocks execution until human writes
APPROVED or REJECTED in the file, and handles timeouts.

Usage:
    python scripts/request_approval.py --file <path_to_approval_file> [--timeout 3600]

Features:
    - Blocks execution until human responds
    - Configurable timeout (default 1 hour)
    - Renames file to .approved, .rejected, or .timeout based on result
    - Logs all actions to logs/actions.log
"""

import sys
import os
import time
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from typing import Tuple, Optional

# Add project root to sys.path to enable imports from root-level modules
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from log_manager import setup_logging

# Initialize logger (Silver Tier log path)
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="human-approval")


class ApprovalStatus(Enum):
    """Enum representing approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


# Paths
VAULT_PATH = Path("AI_Employee_Vault")
NEEDS_APPROVAL_PATH = VAULT_PATH / "Needs_Approval"
APPROVED_PATH = VAULT_PATH / "Approved"
REJECTED_PATH = VAULT_PATH / "Rejected"
ACTION_LOG_PATH = VAULT_PATH / "Logs" / "actions.log"

# Ensure directories exist
for path in [NEEDS_APPROVAL_PATH, APPROVED_PATH, REJECTED_PATH, ACTION_LOG_PATH.parent]:
    path.mkdir(parents=True, exist_ok=True)


def log_approval_action(message: str, level: str = "INFO"):
    """
    Log approval action to both actions.log and console.
    
    Args:
        message: The message to log
        level: Log level (INFO, WARNING, ERROR)
    """
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] [human-approval] [{level}] {message}\n"
    
    # Append to actions.log
    with open(ACTION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    # Also log via standard logger with prefix
    log_message = f"[human-approval] {message}"
    if level == "ERROR":
        logger.error(log_message)
    elif level == "WARNING":
        logger.warning(log_message)
    else:
        logger.info(log_message)


def read_file(file_path: Path) -> str:
    """
    Read content of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
    """
    return file_path.read_text(encoding="utf-8")


def write_file(file_path: Path, content: str) -> bool:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file
        content: Content to write
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        log_approval_action(f"Error writing file {file_path}: {e}", level="ERROR")
        return False


def move_file(source_path: Path, destination_path: Path) -> bool:
    """
    Move a file from source to destination.
    
    Args:
        source_path: Source file path
        destination_path: Destination directory path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        destination_path.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(destination_path))
        return True
    except Exception as e:
        log_approval_action(f"Error moving file from {source_path} to {destination_path}: {e}", level="ERROR")
        return False


def parse_timeout_from_file(content: str) -> Optional[datetime]:
    """
    Parse timeout timestamp from file content.
    
    Args:
        content: File content
        
    Returns:
        Timeout datetime or None if not found
    """
    # Look for timeout in frontmatter
    for line in content.split('\n'):
        if line.lower().startswith('timeout:'):
            timeout_str = line.split(':', 1)[1].strip()
            try:
                # Try ISO format first
                return datetime.fromisoformat(timeout_str)
            except ValueError:
                # Try other common formats
                for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(timeout_str, fmt)
                    except ValueError:
                        continue
    return None


def parse_timeout_extended(content: str) -> Optional[datetime]:
    """
    Parse timeout extension from file content.
    
    Args:
        content: File content
        
    Returns:
        Extended timeout datetime or None if not found
    """
    for line in content.split('\n'):
        if line.lower().startswith('timeout_extended:'):
            timeout_str = line.split(':', 1)[1].strip()
            try:
                return datetime.fromisoformat(timeout_str)
            except ValueError:
                pass
    return None


def check_approval_status(file_path: Path) -> Tuple[ApprovalStatus, str]:
    """
    Check the approval status of a file.
    
    Args:
        file_path: Path to the approval file
        
    Returns:
        Tuple of (ApprovalStatus, reason/message)
    """
    if not file_path.exists():
        return (ApprovalStatus.REJECTED, "Approval file not found")
    
    try:
        content = read_file(file_path)
    except Exception as e:
        return (ApprovalStatus.REJECTED, f"Error reading file: {e}")
    
    content_lower = content.lower()
    
    # Check for APPROVED status (case-insensitive)
    if 'status: approved' in content_lower:
        # Extract approval reason if present
        reason = "Approved by human reviewer"
        for line in content.split('\n'):
            if line.lower().startswith('approval_reason:') or line.lower().startswith('approved_reason:'):
                reason = line.split(':', 1)[1].strip()
                break
        return (ApprovalStatus.APPROVED, reason)
    
    # Check for REJECTED status (case-insensitive)
    if 'status: rejected' in content_lower:
        # Extract rejection reason if present
        reason = "Rejected by human reviewer"
        for line in content.split('\n'):
            if line.lower().startswith('rejection_reason:') or line.lower().startswith('rejected_reason:'):
                reason = line.split(':', 1)[1].strip()
                break
        return (ApprovalStatus.REJECTED, reason)
    
    # Check for explicit REJECT without 'ed'
    if 'status: reject' in content_lower:
        return (ApprovalStatus.REJECTED, "Rejected by human reviewer")
    
    # Default: pending
    return (ApprovalStatus.PENDING, "Waiting for human response")


def rename_and_move_file(file_path: Path, status: ApprovalStatus) -> bool:
    """
    Rename file based on approval status and move to appropriate folder.
    
    Args:
        file_path: Path to the approval file
        status: Approval status
        
    Returns:
        True if successful, False otherwise
    """
    # Determine destination folder and suffix
    if status == ApprovalStatus.APPROVED:
        destination = APPROVED_PATH
        suffix = ".approved"
    elif status == ApprovalStatus.REJECTED:
        destination = REJECTED_PATH
        suffix = ".rejected"
    elif status == ApprovalStatus.TIMEOUT:
        destination = REJECTED_PATH
        suffix = ".timeout"
    else:
        log_approval_action(f"Unknown status for file movement: {status}", level="ERROR")
        return False
    
    # Create new filename with suffix
    stem = file_path.stem
    # Remove any existing .approved, .rejected, .timeout suffix to avoid duplicates
    for existing_suffix in ['.approved', '.rejected', '.timeout']:
        if stem.endswith(existing_suffix):
            stem = stem[:-len(existing_suffix)]
            break
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"{stem}{suffix}_{timestamp}.md"
    destination_path = destination / new_filename
    
    # Move the file
    return move_file(file_path, destination_path)


def request_approval(
    file_path: str,
    timeout_seconds: int = 3600,
    poll_interval: int = 10
) -> Tuple[ApprovalStatus, str]:
    """
    Request human approval and block until response or timeout.
    
    This is the main entry point for the human-approval skill.
    It blocks execution until a human writes APPROVED or REJECTED
    in the file, or until the timeout is reached.
    
    Args:
        file_path: Path to the approval request file in Needs_Approval
        timeout_seconds: Timeout duration in seconds (default: 3600 = 1 hour)
        poll_interval: Polling interval in seconds (default: 10)
        
    Returns:
        Tuple of (ApprovalStatus, reason/message)
        
    Example:
        >>> status, reason = request_approval(
        ...     "AI_Employee_Vault/Needs_Approval/EMAIL_12345.md",
        ...     timeout_seconds=3600
        ... )
        >>> if status == ApprovalStatus.APPROVED:
        ...     print(f"Approved: {reason}")
    """
    # Convert to Path object
    approval_file = Path(file_path)
    
    # Validate file exists
    if not approval_file.exists():
        error_msg = f"Approval file not found: {file_path}"
        log_approval_action(error_msg, level="ERROR")
        return (ApprovalStatus.REJECTED, error_msg)
    
    # Calculate timeout
    start_time = datetime.now()
    timeout_delta = timedelta(seconds=timeout_seconds)
    timeout_time = start_time + timeout_delta
    
    # Parse any existing timeout from file
    try:
        content = read_file(approval_file)
        file_timeout = parse_timeout_from_file(content)
        if file_timeout:
            # Check for timeout extension
            extended_timeout = parse_timeout_extended(content)
            if extended_timeout and extended_timeout > file_timeout:
                timeout_time = extended_timeout
            else:
                timeout_time = file_timeout
    except Exception as e:
        log_approval_action(f"Error reading initial timeout from file: {e}", level="WARNING")
    
    # Log approval request
    approval_id = approval_file.stem
    log_approval_action(f"Approval request received: {approval_file.name}")
    log_approval_action(f"Timeout set to: {timeout_time.isoformat()} (in {timeout_seconds} seconds)")
    log_approval_action("Blocking execution, waiting for human response...")
    
    # Main polling loop - BLOCKING
    last_status = ApprovalStatus.PENDING
    poll_count = 0
    
    while True:
        current_time = datetime.now()
        
        # Check for timeout
        if current_time >= timeout_time:
            log_approval_action(f"TIMEOUT: No human response after {timeout_seconds} seconds", level="WARNING")
            
            # Rename and move file
            if rename_and_move_file(approval_file, ApprovalStatus.TIMEOUT):
                log_approval_action(f"File renamed and moved to: {REJECTED_PATH}")
            
            timeout_msg = f"Timeout after {timeout_seconds} seconds"
            return (ApprovalStatus.TIMEOUT, timeout_msg)
        
        # Poll for status change
        try:
            status, reason = check_approval_status(approval_file)
            
            if status == ApprovalStatus.APPROVED:
                log_approval_action(f"STATUS_CHANGE: APPROVED detected")
                
                # Rename and move file
                if rename_and_move_file(approval_file, ApprovalStatus.APPROVED):
                    log_approval_action(f"File renamed and moved to: {APPROVED_PATH}")
                
                log_approval_action(f"APPROVAL_COMPLETE: {approval_id} approved by human")
                return (ApprovalStatus.APPROVED, reason)
            
            elif status == ApprovalStatus.REJECTED:
                log_approval_action(f"STATUS_CHANGE: REJECTED detected - {reason}", level="WARNING")
                
                # Rename and move file
                if rename_and_move_file(approval_file, ApprovalStatus.REJECTED):
                    log_approval_action(f"File renamed and moved to: {REJECTED_PATH}")
                
                log_approval_action(f"APPROVAL_REJECTED: {approval_id} rejected by human - {reason}")
                return (ApprovalStatus.REJECTED, reason)
            
            # Status changed from previous poll (e.g., file was modified but not yet approved/rejected)
            if status != last_status:
                log_approval_action(f"File modified, status: {status.value}")
                last_status = status
            
        except Exception as e:
            log_approval_action(f"Error checking approval status: {e}", level="ERROR")
        
        # Log polling activity periodically
        poll_count += 1
        if poll_count % 6 == 0:  # Log every minute (assuming 10-second poll interval)
            elapsed = (current_time - start_time).total_seconds()
            remaining = (timeout_time - current_time).total_seconds()
            log_approval_action(f"Still waiting... Elapsed: {elapsed:.0f}s, Remaining: {remaining:.0f}s")
        
        # Wait before next poll
        time.sleep(poll_interval)


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Human Approval Skill - Block until human approves or rejects"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the approval request file in Needs_Approval"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Timeout in seconds (default: 3600 = 1 hour)"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="Polling interval in seconds (default: 10)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )
    
    args = parser.parse_args()
    
    # Request approval (BLOCKING CALL)
    status, reason = request_approval(
        file_path=args.file,
        timeout_seconds=args.timeout,
        poll_interval=args.poll_interval
    )
    
    # Output result
    if args.json:
        import json
        result = {
            "status": status.value,
            "reason": reason,
            "approval_id": Path(args.file).stem
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"Approval Result: {status.value.upper()}")
        print(f"Reason: {reason}")
        print(f"File: {Path(args.file).name}")
        print(f"{'='*60}")
    
    # Exit with appropriate code
    if status == ApprovalStatus.APPROVED:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
