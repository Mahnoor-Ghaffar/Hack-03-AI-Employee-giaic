# Plan Workflow Skill

**Tier:** Platinum
**Version:** 1.0.0
**Author:** AI Employee Hackathon Team

---

## Overview

The Plan Workflow Skill provides structured task planning and execution capabilities for the AI Employee system. It reads plan files from `AI_Employee_Vault/Plans/` and coordinates execution across all Gold Tier integrations (Odoo, Twitter, Facebook/Instagram, Personal Tasks).

---

## Capabilities

- **Plan Management**
  - `create_plan()` - Create new plan files
  - `read_plan()` - Read and parse plan files
  - `update_plan()` - Update plan status
  - `list_plans()` - List plans by status

- **Plan Execution**
  - `execute_plan()` - Execute all actions in a plan
  - `execute_step()` - Execute a single plan step
  - `validate_plan()` - Validate plan structure

- **Integration**
  - Odoo invoice creation
  - Twitter posting
  - Facebook/Instagram posting
  - Personal task creation
  - Human approval workflow

---

## Plan File Structure

Plans are stored as Markdown files in `AI_Employee_Vault/Plans/`:

```markdown
# Plan: Q1 Social Media Campaign

**Status:** pending
**Priority:** high
**Created:** 2026-03-17
**Due:** 2026-03-31
**Tags:** marketing, social-media, q1

## Overview

Launch a comprehensive social media campaign for Q1 2026 product release.

## Steps

### Step 1: Create Invoice
- **Action:** odoo.create_invoice
- **Customer:** Acme Corp
- **Items:**
  - name: Social Media Management
  - quantity: 1
  - price: 5000.00
- **Auto-validate:** false

### Step 2: Post Twitter Announcement
- **Action:** twitter.post_tweet
- **Content:** 🚀 Exciting news! Our Q1 product launch is here! #Innovation #AI

### Step 3: Facebook Post
- **Action:** social.post_facebook
- **Content:** We're thrilled to announce our Q1 product release!
- **Image:** images/q1_launch.jpg

### Step 4: Instagram Post
- **Action:** social.post_instagram
- **Content:** Q1 Launch Day! 🎉 #NewProduct #Innovation
- **Image:** images/q1_launch_ig.jpg

### Step 5: Create Follow-up Tasks
- **Action:** personal.create_tasks
- **Tasks:**
  - title: Monitor campaign metrics
    priority: high
    due_date: 2026-04-07
  - title: Prepare performance report
    priority: medium
    due_date: 2026-04-14

## Approval

- **Requires Approval:** true
- **Approved By:** 
- **Approved At:** 
```

---

## Usage

### Create a Plan

```python
from .claude.skills.plan_workflow import PlanWorkflow

plan = PlanWorkflow()

# Create plan from template
result = plan.create_plan(
    name="Q1_Social_Media_Campaign",
    title="Q1 Social Media Campaign",
    priority="high",
    due_date="2026-03-31",
    steps=[
        {
            "action": "twitter.post_tweet",
            "content": "🚀 Launch announcement!"
        },
        {
            "action": "social.post_facebook",
            "content": "Facebook launch post",
            "image": "images/launch.jpg"
        }
    ]
)
```

### Read a Plan

```python
# Read plan file
plan_data = plan.read_plan("Q1_Social_Media_Campaign.md")

print(f"Plan: {plan_data['title']}")
print(f"Status: {plan_data['status']}")
print(f"Steps: {len(plan_data['steps'])}")
```

### Execute a Plan

```python
# Execute entire plan
result = plan.execute_plan(
    plan_file="Q1_Social_Media_Campaign.md",
    require_approval=True
)

# Execute single step
result = plan.execute_step(
    plan_file="Q1_Social_Media_Campaign.md",
    step_index=0
)
```

### List Plans

```python
# List all plans
plans = plan.list_plans()

# List pending plans only
pending = plan.list_plans(status="pending")

# List by priority
urgent = plan.list_plans(priority="urgent")
```

---

## API Reference

### `create_plan()`

Create a new plan file.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | str | Yes | Plan file name (without .md) |
| `title` | str | Yes | Plan title |
| `priority` | str | No | low/medium/high/urgent |
| `due_date` | str | No | YYYY-MM-DD |
| `steps` | List[Dict] | Yes | Plan steps |
| `tags` | List[str] | No | Plan tags |
| `requires_approval` | bool | No | Require human approval |

### `read_plan()`

Read and parse a plan file.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `plan_file` | str | Yes | Plan file name |

**Returns:**
```python
{
    "status": "success",
    "plan": {
        "name": "Q1_Social_Media_Campaign",
        "title": "Q1 Social Media Campaign",
        "status": "pending",
        "priority": "high",
        "created": "2026-03-17",
        "due": "2026-03-31",
        "tags": ["marketing", "social-media"],
        "steps": [...],
        "requires_approval": true
    }
}
```

### `execute_plan()`

Execute all steps in a plan.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `plan_file` | str | Yes | Plan file name |
| `require_approval` | bool | No | Require approval before execution |
| `dry_run` | bool | No | Validate without executing |

**Returns:**
```python
{
    "status": "success",
    "plan_file": "Q1_Social_Media_Campaign.md",
    "total_steps": 5,
    "executed": 5,
    "failed": 0,
    "skipped": 0,
    "results": [...]
}
```

### `execute_step()`

Execute a single plan step.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `plan_file` | str | Yes | Plan file name |
| `step_index` | int | Yes | Step index (0-based) |

### `list_plans()`

List plans with optional filters.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | str | No | None | Filter by status |
| `priority` | str | No | None | Filter by priority |
| `tag` | str | No | None | Filter by tag |

---

## Supported Actions

| Action | Module | Description |
|--------|--------|-------------|
| `odoo.create_invoice` | mcp.odoo_mcp | Create invoice |
| `odoo.record_payment` | mcp.odoo_mcp | Record payment |
| `twitter.post_tweet` | .claude.skills.twitter-post | Post tweet |
| `twitter.post_thread` | .claude.skills.twitter-post | Post thread |
| `social.post_facebook` | .claude.skills.social-meta | Facebook post |
| `social.post_instagram` | .claude.skills.social-meta | Instagram post |
| `social.post_to_both` | .claude.skills.social-meta | Cross-post |
| `personal.create_task` | .claude.skills.personal-task-handler | Create task |
| `personal.sync_tasks` | .claude.skills.personal-task-handler | Sync multiple tasks |

---

## Integration with Scheduler

```python
from .claude.skills.plan_workflow import PlanWorkflow
from scripts.scheduler import run_scheduled_task

plan = PlanWorkflow()

# Execute pending plans daily
def execute_pending_plans():
    pending_plans = plan.list_plans(status="pending")
    
    for plan_file in pending_plans['plans']:
        if plan_file['due_date'] <= today:
            plan.execute_plan(plan_file['name'])
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Plan not found | Invalid file name | Check plan file exists in Plans/ |
| Invalid plan format | Malformed markdown | Use plan template |
| Action not supported | Unknown action type | Use supported actions only |
| Missing credentials | Env vars not set | Configure environment variables |

---

## Related Files

| File | Purpose |
|------|---------|
| `.claude/skills/plan-workflow/plan_workflow.py` | Main implementation |
| `.claude/skills/plan-workflow/SKILL.md` | This documentation |
| `AI_Employee_Vault/Plans/` | Plan files directory |
| `gold_tier_integration.py` | Gold Tier integration |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-18 | Initial Platinum Tier implementation |
