# Ralph Wiggum Autonomous Loop Skill

**Module:** `.claude.skills.ralph-wiggum`

## Description

Implements the Ralph Wiggum persistence pattern for autonomous multi-step task completion. When a task appears, the system:

1. **Analyzes** the task
2. **Creates** Plan.md
3. **Executes** first step
4. **Checks** result
5. **Continues** to next step
6. **Repeats** until completed
7. **Moves** task to Done

## Safety Features

| Feature | Default | Description |
|---------|---------|-------------|
| Max Iterations | 5 | Prevents infinite loops |
| Human Approval | Required for risky actions | High-risk actions require approval |
| Risk Assessment | Automatic | Analyzes actions for risk level |
| Timeout Protection | Configurable | Prevents hung tasks |

## Quick Start

```python
from .claude.skills.ralph-wiggum import ralph_wiggum_skill

# Process all pending tasks
result = ralph_wiggum_skill(action="process_all")

# Process a single task
result = ralph_wiggum_skill(
    action="process_task",
    task_path="AI_Employee_Vault/Needs_Action/my_task.md"
)
```

## Usage

### Process All Pending Tasks

```python
from .claude.skills.ralph-wiggum import process_all_pending_tasks

results = process_all_pending_tasks(
    vault_path="AI_Employee_Vault",
    max_iterations=5
)

print(f"Completed: {results['completed']}/{results['processed']}")
```

### Process Single Task

```python
from .claude.skills.ralph-wiggum import RalphWiggumAutonomousLoop

loop = RalphWiggumAutonomousLoop(max_iterations=5)
status, reason = loop.process_task_file(
    Path("AI_Employee_Vault/Needs_Action/task.md")
)

print(f"Status: {status.value}, Reason: {reason}")
```

### Analyze Task (Without Execution)

```python
from .claude.skills.ralph-wiggum import ralph_wiggum_skill

result = ralph_wiggum_skill(
    action="analyze",
    task_path="AI_Employee_Vault/Needs_Action/task.md"
)

print(f"Complexity: {result['analysis']['estimated_complexity']}")
print(f"Risk Level: {result['analysis']['risk_level']}")
```

### Create Plan Only

```python
result = ralph_wiggum_skill(
    action="create_plan",
    task_path="AI_Employee_Vault/Needs_Action/task.md"
)

print(f"Plan saved to: {result['plan_path']}")
```

## Integration with Scheduler

### FileSystemWatcher Integration

```python
from .claude.skills.ralph-wiggum.scheduler_integration import (
    setup_filesystem_watcher_callback
)

# Create callback for FileSystemWatcher
ralph_callback = setup_filesystem_watcher_callback(
    vault_path="AI_Employee_Vault",
    auto_process=True
)

# Register with FileSystemWatcher
watcher = FileSystemWatcher(
    vault_path="AI_Employee_Vault",
    callback=ralph_callback
)
```

### Orchestrator Integration

```python
from .claude.skills.ralph-wiggum.scheduler_integration import (
    integrate_with_orchestrator,
    on_task_appears
)

# Get integration hooks
ralph_hooks = integrate_with_orchestrator()

# In your orchestrator, when a task appears:
def process_new_task(file_path):
    result = on_task_appears(
        task_file=Path(file_path),
        auto_process=True
    )
    return result
```

### Scheduled Processing

```python
from .claude.skills.ralph-wiggum.scheduler_integration import (
    scheduled_ralph_processing
)

# Call periodically (e.g., every 5 minutes via cron)
def scheduled_task():
    result = scheduled_ralph_processing()
    print(f"Processed: {result['total']} tasks")
    print(f"Completed: {result['completed']}, Failed: {result['failed']}")
```

## Function Reference

### `ralph_wiggum_skill()`

Main skill interface.

```python
ralph_wiggum_skill(
    action: str,
    **kwargs
) -> Dict[str, Any]
```

**Actions:**
- `process_task` - Process a single task file
- `process_all` - Process all pending tasks
- `analyze` - Analyze task without executing
- `create_plan` - Create plan for a task
- `get_status` - Get task status

### `process_all_pending_tasks()`

Process all tasks in Needs_Action folder.

```python
process_all_pending_tasks(
    vault_path: Path = "AI_Employee_Vault",
    max_iterations: int = 5
) -> Dict[str, Any]
```

Returns:
```json
{
  "processed": 3,
  "completed": 2,
  "failed": 1,
  "tasks": [
    {"file": "task1.md", "status": "completed", "reason": "..."},
    {"file": "task2.md", "status": "failed", "reason": "..."}
  ]
}
```

### `RalphWiggumAutonomousLoop.process_task_file()`

Process a single task through the full loop.

```python
loop = RalphWiggumAutonomousLoop(max_iterations=5)
status, reason = loop.process_task_file(task_file)
```

Returns:
- `TaskStatus.COMPLETED` - Task finished successfully
- `TaskStatus.FAILED` - Task failed
- `TaskStatus.MAX_ITERATIONS` - Hit iteration limit
- `TaskStatus.TIMEOUT` - Approval timeout

### `assess_risk()`

Assess risk level of an action.

```python
risk = assess_risk("Send email to client with invoice")
print(risk)  # RiskLevel.MEDIUM
```

Risk levels:
- `RiskLevel.LOW` - Auto-approve
- `RiskLevel.MEDIUM` - Log and notify
- `RiskLevel.HIGH` - Require human approval

### `request_human_approval()`

Request human approval for risky actions.

```python
approved, reason = request_human_approval(
    task_name="send_invoice",
    step_description="Send $5000 invoice to client",
    plan_path=Path("Plans/Plan_invoice.md"),
    timeout_seconds=3600
)
```

## Risk Assessment

### Automatic Risk Detection

The system automatically flags these as **high risk**:

| Category | Keywords |
|----------|----------|
| Financial | payment, invoice, transfer, money, $amount |
| Data Modification | delete, remove, destroy, erase, format |
| External Publishing | post, publish, tweet, facebook, linkedin |
| System Changes | install, deploy, restart, shutdown |
| Urgency | urgent, immediate, asap |
| Sensitivity | confidential, secret, private |

### Risk Thresholds

- **Score ≥ 5**: HIGH (requires approval)
- **Score 2-4**: MEDIUM (log and notify)
- **Score 0-1**: LOW (auto-approve)

## Plan Format

Generated plans follow this structure:

```markdown
---
type: execution_plan
task_name: my_task
created: 2026-03-14T18:00:00
complexity: moderate
risk_level: medium
max_iterations: 5
status: pending
---

# Execution Plan: my_task

## Task Analysis
- **Complexity:** moderate
- **Risk Level:** medium
- **Required Actions:** email_communication, file_processing

## Execution Steps

### Step 1: Analyze Task Requirements
- [ ] Review task content thoroughly
- [ ] Identify all required actions
...

### Step N: Complete Task
- [ ] Verify all steps completed
- [ ] Move task file to Done folder
- [ ] Mark TASK_COMPLETE
```

## Task Status Values

| Status | Description |
|--------|-------------|
| `pending` | Task waiting to be processed |
| `analyzing` | Task analysis in progress |
| `planning` | Plan generation in progress |
| `executing` | Step execution in progress |
| `waiting_approval` | Waiting for human approval |
| `completed` | Task completed successfully |
| `failed` | Task failed |
| `max_iterations` | Hit iteration limit |
| `timeout` | Approval timeout |

## File Structure

```
AI_Employee_Vault/
├── Needs_Action/
│   ├── task_file.md          # Input task
│   └── ...
├── Plans/
│   ├── Plan_task_file.md     # Generated plan
│   └── ...
├── Pending_Approval/
│   └── RALPH_*_approval.md   # Approval requests
├── Needs_Approval/
│   └── RALPH_*_approval.md   # Active approvals
└── Done/
    ├── task_file.md          # Completed task
    ├── Plan_task_file.md     # Completed plan
    └── RALPH_*_approved.md   # Approval records
```

## Completion Detection

A task is considered complete when:

1. All checklist steps are marked done
2. Task file is moved to `Done/` folder
3. `TASK_COMPLETE` marker is present in output
4. Completion summary is logged

## Error Handling

### Max Iterations Reached

When max iterations (5) is reached:
- Task processing stops
- Current state is logged
- Task remains in Needs_Action for manual review
- Status: `max_iterations`

### Human Approval Timeout

When approval times out (default 1 hour):
- Task processing stops
- Timeout is logged
- Task remains in Needs_Action
- Status: `timeout`

### Step Execution Failure

When a step fails:
- Step is marked as failed
- Retry on next iteration
- After max iterations: task fails
- Status: `failed`

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_ITERATIONS` | 5 | Maximum loop iterations |
| `DEFAULT_ITERATION_DELAY` | 2s | Delay between iterations |
| `RISKY_ACTION_THRESHOLD` | 0.7 | Confidence for approval |
| `APPROVAL_TIMEOUT` | 3600s | Approval timeout (1 hour) |

## Examples

### Example 1: Email Processing Task

Task file (`Needs_Action/send_followup.md`):
```markdown
---
type: email_task
priority: normal
---

Send follow-up email to John about the project proposal.
Include:
- Project timeline update
- Budget revision
- Next steps
```

Processing:
```python
result = ralph_wiggum_skill(
    action="process_task",
    task_path="AI_Employee_Vault/Needs_Action/send_followup.md"
)
```

### Example 2: Social Media Post

Task file (`Needs_Action/linkedin_update.md`):
```markdown
Post to LinkedIn about our hackathon progress.
Mention: AI Employee, Gold Tier, autonomous tasks.
Hashtags: #AI #Automation #Hackathon
```

This will be flagged as MEDIUM risk (external publishing) and may require approval.

### Example 3: Batch Processing

```python
from .claude.skills.ralph-wiggum import process_all_pending_tasks

# Process all pending tasks with custom settings
results = process_all_pending_tasks(
    max_iterations=5
)

print(f"Summary:")
print(f"  Total: {results['total']}")
print(f"  Completed: {results['completed']}")
print(f"  Failed: {results['failed']}")

for task in results['tasks']:
    print(f"  - {task['file']}: {task['status']}")
```

## Best Practices

1. **Set appropriate max_iterations**: Complex tasks may need more iterations
2. **Monitor approval queue**: Check Pending_Approval regularly
3. **Review failed tasks**: Check logs for failure reasons
4. **Use risk assessment**: Understand why actions are flagged
5. **Test with simple tasks first**: Validate before complex workflows

## Related Files

- `orchestrator_gold.py` - Gold Tier orchestrator
- `scripts/ralph_wiggum_loop.py` - Original Ralph Wiggum implementation
- `.claude/skills/error-recovery/` - Error handling system
- `AI_Employee_Vault/Plans/` - Generated plans
- `logs/ai_employee.log` - Execution logs
