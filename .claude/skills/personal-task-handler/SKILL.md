# Personal Task Handler Skill

**Tier:** Gold
**Version:** 1.0.0
**Author:** AI Employee Hackathon Team

---

## Overview

The Personal Task Handler Skill provides personal task management capabilities for the AI Employee system. Tasks are stored in `AI_Employee_Vault/Personal/` with automatic archiving of completed tasks.

---

## Capabilities

- **Task Management**
  - `create_task()` - Create new personal tasks
  - `update_task()` - Update task details
  - `update_task_status()` - Change task status
  - `delete_task()` - Remove tasks
  - `get_task()` - Retrieve task details

- **Task Listing**
  - `list_tasks()` - List tasks with filters
  - `get_summary()` - Get task statistics

- **Organization**
  - Priority levels (urgent, high, medium, low)
  - Tags for categorization
  - Due dates with overdue detection
  - Automatic archiving of completed tasks

- **Logging**
  - All actions logged to `logs/personal_tasks.log`
  - Task history tracking

---

## Installation

### Prerequisites

- Python 3.8+
- No external dependencies required

### Environment Variables

```bash
# Optional
VAULT_PATH=AI_Employee_Vault
LOG_LEVEL=INFO
PERSONAL_LOG_FILE=logs/personal_tasks.log
```

---

## Usage

### Create a Task

```python
from .claude.skills.personal_task_handler import PersonalTaskHandler

personal = PersonalTaskHandler()

# Simple task
result = personal.create_task(
    title="Review quarterly reports"
)

# Task with all options
result = personal.create_task(
    title="Review quarterly reports",
    description="Review Q1 financial reports before board meeting",
    priority="high",
    due_date="2026-03-20",
    tags=["finance", "quarterly", "reports"],
    metadata={
        "related_project": "Q1_Review",
        "estimated_hours": 4
    }
)

print(f"Created task: {result['task_id']}")
```

### Update Task Status

```python
# Start working on a task
result = personal.update_task_status(
    task_id="TASK_ABC123",
    status="in_progress",
    notes="Started reviewing Q1 reports"
)

# Mark as completed
result = personal.update_task_status(
    task_id="TASK_ABC123",
    status="completed",
    notes="All reports reviewed and summarized"
)
```

### Update Task Details

```python
result = personal.update_task(
    task_id="TASK_ABC123",
    title="Review Q1 and Q2 reports",  # New title
    priority="urgent",  # Changed priority
    due_date="2026-03-18"  # Extended deadline
)
```

### Get Task Details

```python
result = personal.get_task(task_id="TASK_ABC123")

if result['status'] == 'success':
    task = result['task']
    print(f"Title: {task['title']}")
    print(f"Status: {task['status']}")
    print(f"Priority: {task['priority']}")
    print(f"Due: {task['due_date']}")
```

### List Tasks

```python
# List all active tasks
result = personal.list_tasks()

# Filter by status
pending = personal.list_tasks(status="pending")
in_progress = personal.list_tasks(status="in_progress")

# Filter by priority
urgent = personal.list_tasks(priority="urgent")

# Filter by tag
finance_tasks = personal.list_tasks(tag="finance")

# Include archived tasks
all_tasks = personal.list_tasks(include_archived=True)
```

### Get Summary

```python
summary = personal.get_summary()

print(f"Total tasks: {summary['summary']['total']}")
print(f"Pending: {summary['summary']['by_status']['pending']}")
print(f"In Progress: {summary['summary']['by_status']['in_progress']}")
print(f"Overdue: {summary['summary']['overdue']}")
```

### Delete a Task

```python
result = personal.delete_task(task_id="TASK_ABC123")
print(f"Deleted: {result['title']}")
```

---

## API Reference

### `create_task()`

Create a new personal task.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `title` | str | Yes | - | Task title |
| `description` | str | No | "" | Task description |
| `priority` | str | No | "medium" | low/medium/high/urgent |
| `due_date` | str | No | None | YYYY-MM-DD format |
| `tags` | List[str] | No | [] | Tags for categorization |
| `metadata` | Dict | No | {} | Additional metadata |

**Returns:**
```python
{
    "status": "success",
    "task_id": "TASK_ABC123",
    "title": "Task title",
    "priority": "high",
    "due_date": "2026-03-20",
    "created_at": "2026-03-17T10:30:00",
    "file_path": "AI_Employee_Vault/Personal/TASK_ABC123.json"
}
```

### `update_task_status()`

Update a task's status.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | str | Yes | Task ID |
| `status` | str | Yes | pending/in_progress/completed/cancelled |
| `notes` | str | No | Status change notes |

**Returns:**
```python
{
    "status": "success",
    "task_id": "TASK_ABC123",
    "old_status": "pending",
    "new_status": "in_progress",
    "updated_at": "2026-03-17T11:00:00"
}
```

### `update_task()`

Update task details.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `task_id` | str | Yes | Task ID |
| `title` | str | No | New title |
| `description` | str | No | New description |
| `priority` | str | No | New priority |
| `due_date` | str | No | New due date |
| `tags` | List[str] | No | New tags |

### `list_tasks()`

List tasks with optional filters.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | str | No | None | Filter by status |
| `priority` | str | No | None | Filter by priority |
| `tag` | str | No | None | Filter by tag |
| `include_archived` | bool | No | False | Include archived |

**Returns:**
```python
{
    "status": "success",
    "count": 5,
    "tasks": [...],
    "filters": {...}
}
```

### `get_summary()`

Get task summary statistics.

**Returns:**
```python
{
    "status": "success",
    "summary": {
        "total": 10,
        "by_status": {
            "pending": 4,
            "in_progress": 3,
            "completed": 2,
            "cancelled": 1
        },
        "by_priority": {
            "urgent": 1,
            "high": 3,
            "medium": 4,
            "low": 2
        },
        "overdue": 2,
        "archived_count": 15
    },
    "timestamp": "2026-03-17T10:30:00"
}
```

---

## Task File Format

Tasks are stored as JSON files in `AI_Employee_Vault/Personal/`:

```json
{
  "task_id": "TASK_ABC123",
  "title": "Review quarterly reports",
  "description": "Review Q1 financial reports",
  "priority": "high",
  "status": "in_progress",
  "created_at": "2026-03-17T10:30:00",
  "updated_at": "2026-03-17T11:00:00",
  "due_date": "2026-03-20",
  "tags": ["finance", "quarterly"],
  "metadata": {
    "estimated_hours": 4
  },
  "history": [
    {
      "action": "created",
      "timestamp": "2026-03-17T10:30:00",
      "status": "pending"
    },
    {
      "action": "status_change",
      "timestamp": "2026-03-17T11:00:00",
      "old_status": "pending",
      "new_status": "in_progress",
      "notes": "Started reviewing"
    }
  ]
}
```

---

## Task Statuses

| Status | Description | Auto-Archive |
|--------|-------------|--------------|
| `pending` | Task not yet started | No |
| `in_progress` | Currently working on | No |
| `completed` | Task finished | Yes |
| `cancelled` | Task cancelled | Yes |

---

## Integration with AI Employee

### With Scheduler

```python
from .claude.skills.personal_task_handler import PersonalTaskHandler

personal = PersonalTaskHandler()

# Daily task summary
def get_daily_summary():
    summary = personal.get_summary()
    overdue = summary['summary']['overdue']
    
    if overdue > 0:
        # Create alert task
        personal.create_task(
            title=f"Address {overdue} overdue tasks",
            priority="urgent",
            due_date=datetime.now().strftime('%Y-%m-%d')
        )
    
    return summary
```

### With Plan Workflow

```python
# Create tasks from plan
from .claude.skills.personal_task_handler import PersonalTaskHandler

personal = PersonalTaskHandler()
plan = read_plan("Plan_Quarterly_Review.md")

for step in plan['steps']:
    personal.create_task(
        title=step['title'],
        description=step['description'],
        priority=step.get('priority', 'medium'),
        due_date=step.get('due_date'),
        tags=['plan', plan['name']]
    )
```

### With CEO Briefing

```python
# Include personal task summary in briefing
from .claude.skills.personal_task_handler import PersonalTaskHandler

personal = PersonalTaskHandler()
summary = personal.get_summary()

briefing_data = {
    'personal_tasks': {
        'total': summary['summary']['total'],
        'pending': summary['summary']['by_status']['pending'],
        'overdue': summary['summary']['overdue']
    }
}
```

---

## Logging

All actions are logged to `logs/personal_tasks.log`:

```
[2026-03-17 10:30:00] [INFO] [personal_task_handler] PersonalTaskHandler initialized at AI_Employee_Vault/Personal
[2026-03-17 10:30:05] [INFO] [personal_task_handler] task_created: {
  "status": "success",
  "task_id": "TASK_ABC123",
  "title": "Review quarterly reports",
  ...
}
[2026-03-17 11:00:00] [INFO] [personal_task_handler] task_status_updated: {
  "status": "success",
  "task_id": "TASK_ABC123",
  "old_status": "pending",
  "new_status": "in_progress",
  ...
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Task not found | Invalid task ID | Check task ID format |
| Invalid status | Status not in valid list | Use: pending/in_progress/completed/cancelled |
| Invalid priority | Priority not in valid list | Use: low/medium/high/urgent |
| Invalid date format | Wrong date format | Use YYYY-MM-DD format |

---

## Best Practices

1. **Use Tags**: Categorize tasks with tags for easy filtering
2. **Set Due Dates**: Always set realistic due dates
3. **Update Status**: Keep status current as you work
4. **Add Notes**: Document status changes with notes
5. **Review Summary**: Check summary regularly for overdue tasks
6. **Archive**: Let completed tasks auto-archive for clean view

---

## Security Considerations

- Tasks are stored as plain JSON files
- Avoid storing sensitive information in task metadata
- Use appropriate file permissions on vault directory
- Consider encryption for sensitive task data

---

## Troubleshooting

### Tasks Not Appearing

```bash
# Check directory exists
ls -la AI_Employee_Vault/Personal/

# Check file format
cat AI_Employee_Vault/Personal/TASK_*.json
```

### Check Logs

```bash
# View recent log entries
tail -f logs/personal_tasks.log
```

### Test Connection

```python
from .claude.skills.personal_task_handler import PersonalTaskHandler

personal = PersonalTaskHandler()
print(personal.get_summary())
```

---

## Related Files

| File | Purpose |
|------|---------|
| `.claude/skills/personal-task-handler/personal_skill.py` | Main implementation |
| `.claude/skills/personal-task-handler/SKILL.md` | This documentation |
| `AI_Employee_Vault/Personal/` | Active tasks directory |
| `AI_Employee_Vault/Personal/Archive/` | Completed tasks directory |
| `logs/personal_tasks.log` | Activity log |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-17 | Initial Gold Tier implementation |
