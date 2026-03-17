# Error Recovery Skill

**Module:** `.claude.skills.error-recovery.error_recovery`

## Description

This skill provides automatic error handling and recovery for the AI Employee system. When any task fails, it:

1. **Logs the error** to `logs/errors.log` with full context
2. **Moves failed files** to `AI_Employee_Vault/Errors/` for investigation
3. **Retries once** after 5 minutes automatically

## Features

| Feature | Description |
|---------|-------------|
| Error Logging | Structured logging to `logs/errors.log` and `logs/errors.jsonl` |
| File Quarantine | Moves failed files to `AI_Employee_Vault/Errors/` with metadata |
| Automatic Retry | Schedules one retry after 5 minutes |
| File Restoration | Restores files from Errors vault on successful retry |
| Cleanup | Removes error files older than 30 days (configurable) |

## Usage

### Quick Start - Handle Task Failure

```python
from .claude.skills.error-recovery.error_recovery import handle_task_failure

# Wrap your task execution in error handling
try:
    result = my_task_function(file_path="path/to/file.txt")
except Exception as e:
    error_info = handle_task_failure(
        task_func=my_task_function,
        task_name="my_task",
        file_path="path/to/file.txt",
        error_message="Failed to process file",
        exception=e,
        args=(),
        kwargs={"file_path": "path/to/file.txt"}
    )
    print(f"Error handled: {error_info}")
```

### Individual Operations

#### Log an Error

```python
from .claude.skills.error-recovery.error_recovery import log_error

log_id = log_error(
    error_message="Connection timeout",
    task_name="gmail_watcher",
    file_path="emails/inbox.msg",
    exception=timeout_exception
)
```

#### Move File to Errors Vault

```python
from .claude.skills.error-recovery.error_recovery import move_to_errors_vault

vault_path = move_to_errors_vault(
    file_path="AI_Employee_Vault/Needs_Action/corrupted_file.md",
    reason="File format invalid"
)
```

#### Schedule a Retry

```python
from .claude.skills.error-recovery.error_recovery import schedule_retry

retry_id = schedule_retry(
    task_func=process_file,
    task_name="file_processor",
    file_path="documents/report.pdf"
)
```

#### Get Retry Status

```python
from .claude.skills.error-recovery.error_recovery import get_retry_status

status = get_retry_status("file_processor_20260314_143022")
print(status)
# {'status': 'success', 'task_name': 'file_processor', ...}
```

#### Cleanup Old Errors

```python
from .claude.skills.error-recovery.error_recovery import cleanup_old_errors

removed_count = cleanup_old_errors(days=30)
print(f"Cleaned up {removed_count} old error files")
```

### Skill Interface (for Claude)

```python
from .claude.skills.error-recovery.error_recovery import error_recovery_skill

# Log an error via skill interface
result = error_recovery_skill(
    action="log",
    error_message="API rate limit exceeded",
    task_name="twitter_poster"
)

# Handle complete failure workflow
result = error_recovery_skill(
    action="handle_failure",
    task_func=my_task,
    task_name="document_processor",
    file_path="docs/input.pdf",
    error_message="PDF parsing failed"
)
```

## Function Reference

### `log_error()`

Logs an error to the errors.log file.

```python
log_error(
    error_message: str,
    task_name: str = "unknown_task",
    file_path: Optional[str] = None,
    exception: Optional[Exception] = None,
    extra_context: Optional[Dict[str, Any]] = None
) -> str  # Returns log entry ID
```

### `move_to_errors_vault()`

Moves a failed file to the Errors vault.

```python
move_to_errors_vault(
    file_path: str,
    reason: str = "Task failure",
    preserve_original: bool = True
) -> Optional[str]  # Returns new path in vault
```

### `schedule_retry()`

Schedules a task for retry after 5 minutes.

```python
schedule_retry(
    task_func: callable,
    task_name: str,
    file_path: Optional[str] = None,
    args: tuple = (),
    kwargs: Optional[Dict[str, Any]] = None
) -> str  # Returns retry ID
```

### `handle_task_failure()`

Complete error handling workflow (recommended).

```python
handle_task_failure(
    task_func: callable,
    task_name: str,
    file_path: Optional[str] = None,
    error_message: str = "Task execution failed",
    exception: Optional[Exception] = None,
    args: tuple = (),
    kwargs: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

Returns:
```json
{
  "status": "error_handled",
  "log_id": "2026-03-14T14-30-22",
  "errors_vault_path": "AI_Employee_Vault/Errors/20260314_143022_file.md",
  "retry_id": "my_task_20260314_143022",
  "retry_scheduled_in_minutes": 5,
  "task_name": "my_task"
}
```

### `get_retry_status()`

Get the status of a scheduled retry.

```python
get_retry_status(retry_id: str) -> Optional[Dict[str, Any]]
```

### `cleanup_old_errors()`

Clean up old error files from the Errors vault.

```python
cleanup_old_errors(days: int = 30) -> int
```

## File Structure

```
AI_Employee_Vault/
├── Errors/
│   ├── 20260314_143022_failed_file.md
│   ├── 20260314_143022_failed_file.md.error_meta.json
│   └── ...
└── ...

logs/
├── errors.log        # Human-readable error log
└── errors.jsonl      # Machine-readable JSON lines
```

## Error Metadata Format

When a file is moved to the Errors vault, a metadata file is created:

```json
{
  "original_path": "E:\\project\\AI_Employee_Vault\\Needs_Action\\task.md",
  "moved_at": "2026-03-14T14:30:22.123456",
  "reason": "Task failure: Invalid format",
  "timestamp": "20260314_143022"
}
```

## Integration Example

### With File Watcher

```python
from filesystem_watcher import FileSystemWatcher
from .claude.skills.error-recovery.error_recovery import handle_task_failure

def process_file_safe(file_path):
    """Process a file with error handling."""
    def task():
        # Your actual processing logic
        return process_file(file_path)
    
    try:
        return task()
    except Exception as e:
        return handle_task_failure(
            task_func=task,
            task_name="file_processor",
            file_path=file_path,
            error_message=f"File processing failed: {e}",
            exception=e,
            kwargs={"file_path": file_path}
        )

watcher = FileSystemWatcher(callback=process_file_safe)
watcher.start()
```

### With Orchestrator

```python
from orchestrator_gold import TaskOrchestrator
from .claude.skills.error-recovery.error_recovery import error_recovery_skill

orchestrator = TaskOrchestrator()

@orchestrator.task("process_document")
def process_document_task(file_path):
    try:
        return process_document(file_path)
    except Exception as e:
        return error_recovery_skill(
            action="handle_failure",
            task_func=process_document,
            task_name="process_document",
            file_path=file_path,
            error_message=str(e),
            exception=e
        )
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ERRORS_LOG_PATH` | `logs/errors.log` | Path to error log file |
| `ERRORS_VAULT_PATH` | `AI_Employee_Vault/Errors/` | Path to errors vault |
| `RETRY_DELAY_MINUTES` | `5` | Minutes before retry |
| `MAX_RETRIES` | `1` | Maximum retry attempts |

## Error Log Format

### Human-readable (errors.log)

```
2026-03-14 14:30:22 - ERROR - [gmail_watcher] - Failed to fetch emails | File: inbox.msg | Exception: TimeoutError: Connection timed out
```

### Machine-readable (errors.jsonl)

```json
{"timestamp": "2026-03-14T14:30:22.123456", "log_id": "2026-03-14T14-30-22", "task_name": "gmail_watcher", "error_message": "Failed to fetch emails", "file_path": "inbox.msg", "exception_type": "TimeoutError", "exception_str": "Connection timed out"}
```

## Best Practices

1. **Always catch exceptions** at task boundaries and use `handle_task_failure()`
2. **Provide meaningful error messages** that help with debugging
3. **Include the original exception** for full stack trace preservation
4. **Use task names** consistently for easier log filtering
5. **Check retry status** if you need to know if a retry succeeded

## Related Files

- `log_manager.py` - Base logging configuration
- `orchestrator_gold.py` - Task orchestration with error handling
- `AI_Employee_Vault/Errors/` - Quarantine folder for failed files
- `logs/errors.log` - Error log file
