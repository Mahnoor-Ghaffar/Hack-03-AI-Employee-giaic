"""
Error Recovery Skill Package

Provides automatic error handling for AI Employee tasks:
- Error logging to logs/errors.log
- File quarantine to AI_Employee_Vault/Errors/
- Automatic retry after 5 minutes
"""

from .error_recovery import (
    log_error,
    move_to_errors_vault,
    schedule_retry,
    handle_task_failure,
    get_retry_status,
    cleanup_old_errors,
    error_recovery_skill,
    error_logger,
    ERRORS_LOG_PATH,
    ERRORS_VAULT_PATH,
    RETRY_DELAY_MINUTES,
    MAX_RETRIES
)

__all__ = [
    "log_error",
    "move_to_errors_vault",
    "schedule_retry",
    "handle_task_failure",
    "get_retry_status",
    "cleanup_old_errors",
    "error_recovery_skill",
    "error_logger",
    "ERRORS_LOG_PATH",
    "ERRORS_VAULT_PATH",
    "RETRY_DELAY_MINUTES",
    "MAX_RETRIES"
]

__version__ = "1.0.0"
