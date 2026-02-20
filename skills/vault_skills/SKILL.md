# Vault Skills

**Module:** `skills.vault_skills`

## Description

Comprehensive skills for interacting with the AI Employee Obsidian vault. These skills enable Claude Code to read tasks, write responses, move files between workflow stages, and update the dashboard.

## Available Functions

### `read_task(file_name: str) -> dict`

Read a task file from the Needs_Action folder.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `file_name` | str | Name of the file (e.g., 'task_001.md') |

**Returns:**
```python
{
    "file_name": "task_001.md",
    "metadata": {"type": "email", "priority": "high"},
    "body": "Task content here...",
    "full_content": "Full file content..."
}
```

**Example:**
```python
from skills.vault_skills import read_task
task = read_task("client_email_001.md")
print(task["body"])
```

---

### `write_response(file_name: str, response: str, action_items: list = None) -> str`

Write an AI response to a task file.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `file_name` | str | Name of the task file |
| `response` | str | The AI's response content |
| `action_items` | list | Optional list of action items (checkboxes) |

**Returns:** Status message

**Example:**
```python
from skills.vault_skills import write_response
write_response(
    "client_email_001.md",
    "I've drafted a response to the client.",
    ["Review draft", "Send email"]
)
```

---

### `move_to_done(file_name: str, summary: str = None) -> str`

Move a completed task to the Done folder.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `file_name` | str | Name of the file to move |
| `summary` | str | Optional completion summary |

**Returns:** Status message

**Example:**
```python
from skills.vault_skills import move_to_done
move_to_done("client_email_001.md", "Drafted and sent response to client.")
```

---

### `move_to_needs_action(file_name: str) -> str`

Move a file from Inbox to Needs_Action folder.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `file_name` | str | Name of the file to move |

**Returns:** Status message

---

### `update_dashboard(section: str, content: str) -> str`

Update a section of the Dashboard.md file.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `section` | str | Section name to update |
| `content` | str | New content for the section |

**Returns:** Status message

**Example:**
```python
from skills.vault_skills import update_dashboard
update_dashboard("Pending Tasks", "- Task 1\n- Task 2")
```

---

### `list_pending_tasks() -> list`

List all pending tasks in Needs_Action folder.

**Returns:** List of task file names

**Example:**
```python
from skills.vault_skills import list_pending_tasks
tasks = list_pending_tasks()
print(f"Pending: {len(tasks)} tasks")
```

---

### `get_task_summary() -> str`

Get a formatted summary of all pending tasks.

**Returns:** Formatted summary string

**Example:**
```python
from skills.vault_skills import get_task_summary
print(get_task_summary())
```

---

## Vault Class (Advanced Usage)

For more control, use the `VaultSkills` class directly:

```python
from skills.vault_skills import VaultSkills

vault = VaultSkills("AI_Employee_Vault")

# Read a task
task = vault.read_task("task_001.md")

# Write response
vault.write_response("task_001.md", "Processing...")

# Move to done
vault.move_to_done("task_001.md", "Completed successfully")
```

---

## Folder Structure

```
AI_Employee_Vault/
├── Inbox/           # Raw incoming items
├── Needs_Action/    # Tasks requiring attention
├── Done/            # Completed tasks
└── Dashboard.md     # Status summary
```

---

## Workflow

1. **Incoming:** Files land in `Inbox/` or `Needs_Action/`
2. **Processing:** Claude reads from `Needs_Action/`
3. **Response:** AI writes response in the same file
4. **Completion:** Move file to `Done/` with summary

---

## Error Handling

All functions return error messages as strings if operations fail:
- File not found
- Permission errors
- Invalid paths

Check return values for "Error:" prefix to detect failures.
