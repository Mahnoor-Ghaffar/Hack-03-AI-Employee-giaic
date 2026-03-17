# Error Recovery Skill - Usage Examples

## Quick Start

```python
# Import the error recovery system
from .claude.skills.error-recovery import handle_task_failure, log_error, move_to_errors_vault
```

## Pattern 1: Wrap Task Execution

```python
def process_file_safe(file_path):
    """Process a file with automatic error handling."""
    
    def task():
        # Your actual processing logic here
        return process_file(file_path)
    
    try:
        return task()
    except Exception as e:
        # This will:
        # 1. Log error to logs/errors.log
        # 2. Move file to AI_Employee_Vault/Errors/
        # 3. Retry once after 5 minutes
        return handle_task_failure(
            task_func=task,
            task_name="file_processor",
            file_path=file_path,
            error_message=f"Failed to process: {e}",
            exception=e,
            kwargs={"file_path": file_path}
        )
```

## Pattern 2: Decorator for Error Handling

```python
from functools import wraps

def with_error_recovery(task_name):
    """Decorator to add error recovery to any function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return handle_task_failure(
                    task_func=func,
                    task_name=task_name,
                    file_path=kwargs.get("file_path") or args[0] if args else None,
                    error_message=str(e),
                    exception=e,
                    args=args,
                    kwargs=kwargs
                )
        return wrapper
    return decorator

# Usage
@with_error_recovery("document_processor")
def process_document(file_path):
    # Your processing logic
    pass
```

## Pattern 3: Integration with Existing Watchers

```python
# In your watcher files (e.g., file_watcher.py, gmail_watcher.py)

from .claude.skills.error-recovery import error_recovery_skill

class MyWatcher:
    def handle_event(self, event):
        file_path = event.src_path
        
        try:
            self.process_file(file_path)
        except Exception as e:
            result = error_recovery_skill(
                action="handle_failure",
                task_func=self.process_file,
                task_name=self.__class__.__name__,
                file_path=file_path,
                error_message=str(e),
                exception=e
            )
            print(f"Error handled: {result}")
```

## Pattern 4: Check Retry Status

```python
from .claude.skills.error-recovery import get_retry_status

# After scheduling a retry, check its status
status = get_retry_status("my_task_20260314_143022")

if status:
    print(f"Retry status: {status['status']}")
    print(f"Task name: {status['task_name']}")
    if status.get('error'):
        print(f"Error: {status['error']}")
```

## Pattern 5: Manual Error Logging

```python
from .claude.skills.error-recovery import log_error

# Log without moving files or retrying
log_id = log_error(
    error_message="External API unavailable",
    task_name="twitter_poster",
    exception=connection_error
)
```

## Pattern 6: Cleanup Old Errors

```python
from .claude.skills.error-recovery import cleanup_old_errors

# Remove error files older than 30 days
removed = cleanup_old_errors(days=30)
print(f"Cleaned up {removed} old error files")
```

## Output Locations

- **Error Log**: `logs/errors.log` (human-readable)
- **Error JSON**: `logs/errors.jsonl` (machine-readable)
- **Error Files**: `AI_Employee_Vault/Errors/` (quarantined failed files)

## Error Log Format

```
2026-03-14 18:47:06 - ERROR - [task_name] - Error message | File: path/to/file | Exception: ErrorType: message
```

## Retry Behavior

- **Delay**: 5 minutes before retry
- **Attempts**: 1 retry (2 total attempts)
- **On Success**: File restored from Errors vault
- **On Failure**: Final error logged, file remains in Errors vault
