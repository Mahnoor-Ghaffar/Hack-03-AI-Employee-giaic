# Silver Scheduler Agent Skill

**Tier:** Silver  
**Version:** 1.0.0  
**Date:** 2026-02-25  

---

## Overview

The Silver Scheduler is the central orchestration skill that runs the AI Employee system on a scheduled basis. It executes the vault-watcher and task-planner workflow in a continuous loop with configurable intervals.

---

## Purpose

- Run vault-watcher and task-planner in a scheduled loop
- Default interval: 5 minutes between cycles
- Support multiple execution modes (daemon, once, status)
- Prevent duplicate instances using lock files
- Log all actions to `logs/ai_employee.log`
- Rotate logs when file size exceeds 5MB

---

## Installation

The skill is registered in `.claude/mcp.json`:

```json
{
  "name": "silver-scheduler",
  "module": "scripts.run_ai_employee",
  "functions": [
    "run_scheduler",
    "check_status",
    "stop_scheduler"
  ]
}
```

---

## Usage

### Command Line Interface

```bash
# Run continuously (daemon mode) - default 5 minute interval
python scripts/run_ai_employee.py --daemon

# Run continuously with custom interval (in minutes)
python scripts/run_ai_employee.py --daemon --interval 10

# Run a single execution cycle
python scripts/run_ai_employee.py --once

# Show current status (active tasks & inbox count)
python scripts/run_ai_employee.py --status

# Show help
python scripts/run_ai_employee.py --help
```

### CLI Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--daemon` | Run continuously in background loop | False |
| `--once` | Run single execution cycle and exit | False |
| `--status` | Show active tasks and inbox count | False |
| `--interval` | Interval in minutes between cycles (daemon mode) | 5 |
| `--log-file` | Custom log file path | logs/ai_employee.log |
| `--help` | Show help message | - |

---

## Functions

### `run_scheduler(mode='once', interval_minutes=5, log_file='logs/ai_employee.log')`

Main scheduler function that executes the AI Employee workflow.

**Args:**
- `mode` (str): Execution mode - 'daemon', 'once', or 'status'
- `interval_minutes` (int): Minutes between cycles in daemon mode
- `log_file` (str): Path to log file

**Returns:**
- dict: Status dictionary with execution results

### `check_status()`

Returns current system status including active tasks and inbox count.

**Returns:**
- dict: Status information
  - `inbox_count`: Number of files in Inbox
  - `needs_action_count`: Number of pending tasks
  - `pending_approval_count`: Number of items awaiting human approval
  - `active_tasks`: List of active task names
  - `last_run`: Timestamp of last scheduler run
  - `lock_active`: Boolean indicating if lock file exists

### `stop_scheduler()`

Stops a running daemon scheduler by removing the lock file.

**Returns:**
- bool: True if scheduler was stopped, False if not running

---

## Architecture

### Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SILVER SCHEDULER                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Check Lock     │
                    │  (Prevent       │
                    │   Duplicates)   │
                    └─────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │   --once   │  │  --daemon  │  │  --status  │
       │  (single)  │  │   (loop)   │  │   (info)   │
       └────────────┘  └────────────┘  └────────────┘
              │               │               │
              │               │               ▼
              │               │      ┌────────────────┐
              │               │      │ Show:          │
              │               │      │ - Inbox count  │
              │               │      │ - Active tasks │
              │               │      │ - Last run     │
              │               │      └────────────────┘
              ▼               ▼
       ┌─────────────────────────────┐
       │    Execute Workflow:        │
       │  1. vault-watcher           │
       │  2. task-planner            │
       │  3. orchestrator cycle      │
       └─────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Log to:        │
                    │  logs/ai_       │
                    │  employee.log   │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Release Lock   │
                    │  (or keep for   │
                    │   daemon mode)  │
                    └─────────────────┘
```

### Lock File System

- **Lock File Location:** `logs/.scheduler.lock`
- **Purpose:** Prevents multiple scheduler instances from running simultaneously
- **Behavior:**
  - On startup: Check for existing lock file
  - If lock exists: Exit with error (duplicate instance detected)
  - If no lock: Create lock file with PID and timestamp
  - On normal exit: Remove lock file
  - On crash: Lock file may remain (manual cleanup required)

---

## Logging

### Log File: `logs/ai_employee.log`

**Rotation Settings:**
- Maximum file size: 5MB
- Backup count: 5 files
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

**Sample Log Entries:**
```
2026-02-25 10:00:00,000 - silver-scheduler - INFO - Scheduler started in daemon mode
2026-02-25 10:00:00,001 - silver-scheduler - INFO - Lock file created: logs/.scheduler.lock
2026-02-25 10:00:00,002 - silver-scheduler - INFO - Starting execution cycle 1
2026-02-25 10:00:00,003 - vault-watcher - INFO - Checking Inbox for new files...
2026-02-25 10:00:00,004 - vault-watcher - INFO - Found 2 new files in Inbox
2026-02-25 10:00:00,005 - task-planner - INFO - Processing task: new_task.md
2026-02-25 10:00:05,000 - task-planner - INFO - Plan created: Plan_new_task.md
2026-02-25 10:00:05,001 - silver-scheduler - INFO - Cycle 1 completed successfully
2026-02-25 10:05:00,000 - silver-scheduler - INFO - Starting execution cycle 2
```

---

## Integration Points

### vault-watcher

The scheduler triggers the vault-watcher to:
- Monitor Inbox folder for new `.md` files
- Move files to Needs_Action
- Trigger task-planner for each new file

**Integration:** Uses `FileSystemWatcher` from `filesystem_watcher.py`

### task-planner

The scheduler triggers the task-planner skill to:
- Read task files from Needs_Action
- Generate step-by-step implementation plans
- Save plans as `Plan_*.md` in Needs_Action

**Integration:** Uses `TaskPlannerSkill` from `skills.task_planner_skill`

### orchestrator

The scheduler can optionally trigger the full orchestrator cycle:
- Process Gmail updates
- Process LinkedIn post ideas
- Process pending approvals

**Integration:** Uses `orchestrate()` from `orchestrator.py`

---

## Error Handling

| Error Type | Behavior |
|------------|----------|
| Lock file exists | Exit with error message, suggest `--status` to check |
| Log directory missing | Create directory automatically |
| Vault directories missing | Create directories automatically |
| vault-watcher error | Log error, continue to next cycle |
| task-planner error | Log error, continue to next cycle |
| KeyboardInterrupt | Graceful shutdown, release lock |

---

## Silver Tier Compliance

This skill satisfies the Silver Tier scheduling requirement:

| Requirement | Implementation |
|-------------|----------------|
| Scheduled execution | 5-minute default interval loop |
| CLI modes | --daemon, --once, --status |
| Logging | logs/ai_employee.log with 5MB rotation |
| Duplicate prevention | Lock file system |
| vault-watcher integration | FileSystemWatcher integration |
| task-planner integration | TaskPlannerSkill integration |

---

## Troubleshooting

### Scheduler won't start - "Lock file exists"

```bash
# Check if scheduler is running
python scripts/run_ai_employee.py --status

# If not running, manually remove lock file
rm logs/.scheduler.lock
```

### Logs not appearing

```bash
# Check log directory exists
ls -la logs/

# Check file permissions
# Ensure user has write access to logs/ directory
```

### High memory usage in daemon mode

- Reduce interval between cycles
- Check for memory leaks in vault-watcher or task-planner
- Restart scheduler periodically

---

## Related Files

| File | Purpose |
|------|---------|
| `scripts/run_ai_employee.py` | Main scheduler implementation |
| `.claude/skills/silver-scheduler/SKILL.md` | This documentation |
| `logs/ai_employee.log` | Scheduler log file |
| `logs/.scheduler.lock` | Lock file for duplicate prevention |
| `orchestrator.py` | Full orchestration workflow |
| `filesystem_watcher.py` | Vault-watcher implementation |
| `skills/task_planner_skill.py` | Task-planner skill |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-25 | Initial implementation |
