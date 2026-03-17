"""
Error Recovery Skill - AI Employee

Handles task failures by:
1. Logging errors to logs/errors.log
2. Moving failed files to AI_Employee_Vault/Errors/
3. Retrying failed tasks once after 5 minutes
"""

import os
import shutil
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import threading


# Configuration
ERRORS_LOG_PATH = Path("logs/errors.log")
ERRORS_VAULT_PATH = Path("AI_Employee_Vault/Errors")
RETRY_DELAY_MINUTES = 5
MAX_RETRIES = 1

# Ensure directories exist
ERRORS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
ERRORS_VAULT_PATH.mkdir(parents=True, exist_ok=True)

# Setup error-specific logger
def setup_error_logger():
    """Setup dedicated error logging with rotation."""
    logger = logging.getLogger("error_recovery")
    logger.setLevel(logging.ERROR)
    
    if not logger.handlers:
        # File handler for error logs
        file_handler = logging.FileHandler(ERRORS_LOG_PATH, encoding="utf-8")
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(task_name)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler for immediate visibility
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - ERROR - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(console_handler)
    
    return logger


error_logger = setup_error_logger()

# Retry queue for tracking pending retries
retry_queue: Dict[str, Dict[str, Any]] = {}
retry_lock = threading.Lock()


def log_error(
    error_message: str,
    task_name: str = "unknown_task",
    file_path: Optional[str] = None,
    exception: Optional[Exception] = None,
    extra_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Log an error to the errors.log file.
    
    Args:
        error_message: Description of the error
        task_name: Name of the task that failed
        file_path: Path to the file that caused the error (if applicable)
        exception: The exception object (if applicable)
        extra_context: Additional context information
    
    Returns:
        Log entry ID (timestamp-based)
    """
    timestamp = datetime.now().isoformat()
    log_entry_id = timestamp.replace(":", "-").replace(".", "-")
    
    error_details = {
        "timestamp": timestamp,
        "log_id": log_entry_id,
        "task_name": task_name,
        "error_message": error_message,
        "file_path": file_path,
        "exception_type": type(exception).__name__ if exception else None,
        "exception_str": str(exception) if exception else None,
        "extra_context": extra_context
    }
    
    # Log with structured context
    extra = {"task_name": task_name}
    log_msg = f"{error_message}"
    if file_path:
        log_msg += f" | File: {file_path}"
    if exception:
        log_msg += f" | Exception: {type(exception).__name__}: {exception}"
    
    error_logger.error(log_msg, extra=extra)
    
    # Also write JSON entry for programmatic access
    json_log_path = Path("logs/errors.jsonl")
    json_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(error_details) + "\n")
    
    return log_entry_id


def move_to_errors_vault(
    file_path: str,
    reason: str = "Task failure",
    preserve_original: bool = True
) -> Optional[str]:
    """
    Move a failed file to the Errors vault.
    
    Args:
        file_path: Path to the file to move
        reason: Reason for moving to errors vault
        preserve_original: If True, keep original filename with timestamp prefix
    
    Returns:
        New path in errors vault, or None if move failed
    """
    src_path = Path(file_path)
    
    if not src_path.exists():
        error_logger.error(
            f"Cannot move file to errors vault - file does not exist: {file_path}",
            extra={"task_name": "error_recovery"}
        )
        return None
    
    # Create timestamped filename to preserve history
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if preserve_original:
        new_filename = f"{timestamp}_{src_path.name}"
    else:
        new_filename = src_path.name
    
    dest_path = ERRORS_VAULT_PATH / new_filename
    
    try:
        # Add metadata file alongside the error file
        metadata = {
            "original_path": str(src_path.absolute()),
            "moved_at": datetime.now().isoformat(),
            "reason": reason,
            "timestamp": timestamp
        }
        metadata_path = dest_path.with_suffix(dest_path.suffix + ".error_meta.json")
        
        # Move the file
        shutil.move(str(src_path), str(dest_path))
        
        # Write metadata
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        error_logger.info(
            f"Moved file to errors vault: {dest_path}",
            extra={"task_name": "error_recovery"}
        )
        
        return str(dest_path)
    
    except Exception as e:
        error_logger.error(
            f"Failed to move file to errors vault: {e}",
            extra={"task_name": "error_recovery"}
        )
        return None


def schedule_retry(
    task_func: callable,
    task_name: str,
    file_path: Optional[str] = None,
    args: tuple = (),
    kwargs: Optional[Dict[str, Any]] = None
) -> str:
    """
    Schedule a task for retry after 5 minutes.
    
    Args:
        task_func: The function to retry
        task_name: Name of the task
        file_path: Path to the file being processed
        args: Positional arguments for the task function
        kwargs: Keyword arguments for the task function
    
    Returns:
        Retry ID for tracking
    """
    retry_id = f"{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    retry_time = datetime.now() + timedelta(minutes=RETRY_DELAY_MINUTES)
    
    with retry_lock:
        retry_queue[retry_id] = {
            "task_func": task_func,
            "task_name": task_name,
            "file_path": file_path,
            "args": args,
            "kwargs": kwargs or {},
            "scheduled_time": retry_time,
            "attempt": 1,
            "status": "pending"
        }
    
    error_logger.warning(
        f"Task scheduled for retry in {RETRY_DELAY_MINUTES} minutes",
        extra={"task_name": task_name}
    )
    
    # Start background thread to handle retry
    retry_thread = threading.Thread(
        target=_execute_retry,
        args=(retry_id,),
        daemon=True
    )
    retry_thread.start()
    
    return retry_id


def _execute_retry(retry_id: str):
    """Execute a scheduled retry after the delay."""
    with retry_lock:
        if retry_id not in retry_queue:
            return
        retry_info = retry_queue[retry_id]
    
    retry_time = retry_info["scheduled_time"]
    wait_seconds = (retry_time - datetime.now()).total_seconds()
    
    if wait_seconds > 0:
        error_logger.info(
            f"Waiting {wait_seconds:.0f} seconds before retry",
            extra={"task_name": retry_info["task_name"]}
        )
        time.sleep(wait_seconds)
    
    with retry_lock:
        if retry_id not in retry_queue:
            return
        retry_info = retry_queue[retry_id]
        retry_info["status"] = "running"
    
    task_func = retry_info["task_func"]
    task_name = retry_info["task_name"]
    args = retry_info["args"]
    kwargs = retry_info["kwargs"]
    file_path = retry_info["file_path"]
    
    try:
        error_logger.info(
            f"Executing retry for task: {task_name}",
            extra={"task_name": task_name}
        )
        result = task_func(*args, **kwargs)
        
        with retry_lock:
            retry_info["status"] = "success"
        
        error_logger.info(
            f"Retry successful for task: {task_name}",
            extra={"task_name": task_name}
        )
        
        # If file was moved to errors, move it back to original location
        if file_path:
            _restore_file_from_errors(file_path)
        
        return result
    
    except Exception as e:
        with retry_lock:
            retry_info["status"] = "failed"
            retry_info["error"] = str(e)
        
        error_logger.error(
            f"Retry failed for task: {task_name} - {e}",
            extra={"task_name": task_name}
        )
        
        # Log final failure
        log_error(
            error_message=f"Final failure after retry: {e}",
            task_name=task_name,
            file_path=file_path,
            exception=e
        )
        
        raise


def _restore_file_from_errors(original_path: str) -> Optional[str]:
    """
    Restore a file from the Errors vault back to its original location.
    
    Args:
        original_path: The original path where the file should be restored
    
    Returns:
        Restored path, or None if restoration failed
    """
    src_path = Path(original_path)
    
    # Find the file in errors vault (may have timestamp prefix)
    matching_files = list(ERRORS_VAULT_PATH.glob(f"*{src_path.name}"))
    
    if not matching_files:
        error_logger.warning(
            f"Cannot restore file - not found in errors vault: {original_path}",
            extra={"task_name": "error_recovery"}
        )
        return None
    
    # Get the most recent matching file
    src_path = max(matching_files, key=lambda p: p.stat().st_mtime)
    
    try:
        # Ensure destination directory exists
        dest_path = Path(original_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move back from errors vault
        shutil.move(str(src_path), str(dest_path))
        
        # Remove metadata file if it exists
        meta_path = src_path.with_suffix(src_path.suffix + ".error_meta.json")
        if meta_path.exists():
            meta_path.unlink()
        
        error_logger.info(
            f"Restored file from errors vault: {dest_path}",
            extra={"task_name": "error_recovery"}
        )
        
        return str(dest_path)
    
    except Exception as e:
        error_logger.error(
            f"Failed to restore file from errors vault: {e}",
            extra={"task_name": "error_recovery"}
        )
        return None


def handle_task_failure(
    task_func: callable,
    task_name: str,
    file_path: Optional[str] = None,
    error_message: str = "Task execution failed",
    exception: Optional[Exception] = None,
    args: tuple = (),
    kwargs: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Complete error handling workflow for a failed task.
    
    This is the main entry point that:
    1. Logs the error
    2. Moves the file to errors vault
    3. Schedules a retry
    
    Args:
        task_func: The task function to retry
        task_name: Name of the failed task
        file_path: Path to the file that failed
        error_message: Description of the error
        exception: The exception that was raised
        args: Arguments to pass to retry
        kwargs: Keyword arguments to pass to retry
    
    Returns:
        Dictionary with error handling status and retry information
    """
    # Step 1: Log the error
    log_id = log_error(
        error_message=error_message,
        task_name=task_name,
        file_path=file_path,
        exception=exception
    )
    
    # Step 2: Move file to errors vault
    errors_vault_path = None
    if file_path and Path(file_path).exists():
        errors_vault_path = move_to_errors_vault(
            file_path=file_path,
            reason=error_message
        )
    
    # Step 3: Schedule retry
    retry_id = schedule_retry(
        task_func=task_func,
        task_name=task_name,
        file_path=file_path,
        args=args,
        kwargs=kwargs
    )
    
    return {
        "status": "error_handled",
        "log_id": log_id,
        "errors_vault_path": errors_vault_path,
        "retry_id": retry_id,
        "retry_scheduled_in_minutes": RETRY_DELAY_MINUTES,
        "task_name": task_name
    }


def get_retry_status(retry_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a scheduled retry.
    
    Args:
        retry_id: The retry ID returned from schedule_retry
    
    Returns:
        Status dictionary or None if retry_id not found
    """
    with retry_lock:
        if retry_id not in retry_queue:
            return None
        
        info = retry_queue[retry_id]
        return {
            "retry_id": retry_id,
            "task_name": info["task_name"],
            "status": info["status"],
            "scheduled_time": info["scheduled_time"].isoformat(),
            "attempt": info["attempt"],
            "error": info.get("error")
        }


def cleanup_old_errors(days: int = 30) -> int:
    """
    Clean up old error files from the Errors vault.
    
    Args:
        days: Remove error files older than this many days
    
    Returns:
        Number of files cleaned up
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    cleaned_count = 0
    
    for error_file in ERRORS_VAULT_PATH.glob("*"):
        if error_file.is_file():
            file_mtime = datetime.fromtimestamp(error_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                try:
                    error_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    error_logger.error(
                        f"Failed to delete old error file {error_file}: {e}",
                        extra={"task_name": "error_recovery"}
                    )
    
    return cleaned_count


# Skill interface for Claude
def error_recovery_skill(
    action: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Main skill interface for error recovery operations.
    
    Actions:
    - "log": Log an error
    - "move_to_vault": Move a file to errors vault
    - "schedule_retry": Schedule a task retry
    - "handle_failure": Complete error handling workflow
    - "get_status": Get retry status
    - "cleanup": Clean up old errors
    
    Args:
        action: The action to perform
        **kwargs: Action-specific arguments
    
    Returns:
        Result dictionary with status and data
    """
    actions = {
        "log": lambda: {
            "log_id": log_error(
                error_message=kwargs.get("error_message", "Unknown error"),
                task_name=kwargs.get("task_name", "unknown"),
                file_path=kwargs.get("file_path"),
                exception=kwargs.get("exception")
            )
        },
        "move_to_vault": lambda: {
            "path": move_to_errors_vault(
                file_path=kwargs.get("file_path"),
                reason=kwargs.get("reason", "Manual move")
            )
        },
        "handle_failure": lambda: handle_task_failure(
            task_func=kwargs.get("task_func"),
            task_name=kwargs.get("task_name", "unknown"),
            file_path=kwargs.get("file_path"),
            error_message=kwargs.get("error_message", "Task failed"),
            exception=kwargs.get("exception"),
            args=kwargs.get("args", ()),
            kwargs=kwargs.get("kwargs", {})
        ),
        "get_status": lambda: {
            "status": get_retry_status(kwargs.get("retry_id", ""))
        },
        "cleanup": lambda: {
            "cleaned_count": cleanup_old_errors(kwargs.get("days", 30))
        }
    }
    
    if action not in actions:
        return {
            "status": "error",
            "message": f"Unknown action: {action}. Valid actions: {list(actions.keys())}"
        }
    
    try:
        result = actions[action]()
        result["status"] = "success"
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == "__main__":
    # Test the error recovery system
    print("Testing Error Recovery System...")
    
    # Test logging
    log_id = log_error(
        error_message="Test error for validation",
        task_name="test_task",
        file_path="test/file.txt"
    )
    print(f"Logged error with ID: {log_id}")
    
    # Test error vault status
    print(f"Errors vault path: {ERRORS_VAULT_PATH.absolute()}")
    print(f"Errors log path: {ERRORS_LOG_PATH.absolute()}")
    
    print("\nError Recovery System initialized successfully!")
