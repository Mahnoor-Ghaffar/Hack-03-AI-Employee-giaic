# mcp-executor Skill

**Tier:** Silver  
**Version:** 1.0.0  
**Author:** AI Employee Hackathon Team  

---

## Overview

The `mcp-executor` skill is responsible for executing external actions (sending Gmail emails, posting LinkedIn messages) after verifying human-in-the-loop approvals. It ensures all actions are logged, handles errors gracefully with automatic retries, and maintains audit trails by moving approval files to appropriate folders.

---

## Goals

- ✅ Accept requests from AI workflow (watchers, orchestrator, or scheduler)
- ✅ Execute external actions:
  1. **gmail_send** - Send emails via Gmail API
  2. **linkedin_post** - Post messages to LinkedIn
- ✅ Ensure human-in-the-loop approvals are respected (checks `AI_Employee_Vault/Pending_Approval`)
- ✅ Log all actions in `AI_Employee_Vault/Logs/actions.log`
- ✅ Handle errors gracefully with configurable retry mechanism
- ✅ Move approval files to `Approved/` or `Rejected/` based on execution result

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Orchestrator  │────▶│  mcp-executor    │────▶│  Gmail/LinkedIn │
│   (Silver Tier) │     │  (This Skill)    │     │  API            │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │ Pending_Approval │
                        │ Approved/Rejected│
                        │ actions.log      │
                        └──────────────────┘
```

---

## Usage

### Command Line Interface

```bash
python scripts/mcp_executor.py \
    --action <gmail_send|linkedin_post> \
    --data <path_to_json_file> \
    --approval_id <approval_document_id> \
    [--max-retries 3] \
    [--retry-delay 5]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--action` | Yes | Type of action: `gmail_send` or `linkedin_post` |
| `--data` | Yes | Path to JSON file containing action data |
| `--approval_id` | Yes | Approval document ID (filename without `.md`) |
| `--max-retries` | No | Maximum retry attempts (default: 3) |
| `--retry-delay` | No | Delay between retries in seconds (default: 5) |

---

## Data Formats

### Gmail Send Action Data

```json
{
    "to": "recipient@example.com",
    "subject": "Email Subject",
    "body": "Email body content here..."
}
```

### LinkedIn Post Action Data

```json
{
    "content": "Your LinkedIn post content here... #hashtags"
}
```

---

## Approval Workflow

### 1. Approval File Location
Approval files must exist in `AI_Employee_Vault/Pending_Approval/` with format:
```
{approval_id}.md
```

### 2. Approval File Format

```markdown
---
type: email_send_approval
approval_id: EMAIL_12345
status: pending
created: 2026-02-24T10:30:00
---

## Email Send Request

**To:** recipient@example.com
**Subject:** Email Subject

## Approval Status

```yaml
approved: true  # Change to 'true' to approve
```
```

### 3. Approval Detection
The skill checks for approval using these indicators:
- `approved: true` in YAML frontmatter
- `status: approved` in frontmatter

### 4. Post-Execution File Movement

| Result | Destination |
|--------|-------------|
| Success | `AI_Employee_Vault/Approved/` |
| Failure | `AI_Employee_Vault/Rejected/` |
| Not Approved | Stays in `Pending_Approval/` |

---

## Logging

All actions are logged to `AI_Employee_Vault/Logs/actions.log`:

```
[2026-02-24T10:30:00] [INFO] === MCP Executor Request ===
[2026-02-24T10:30:00] [INFO] Action Type: gmail_send
[2026-02-24T10:30:00] [INFO] Approval ID: EMAIL_12345
[2026-02-24T10:30:01] [INFO] Approval confirmed for: EMAIL_12345
[2026-02-24T10:30:01] [INFO] Sending Gmail email to: recipient@example.com
[2026-02-24T10:30:02] [INFO] Gmail email sent successfully
[2026-02-24T10:30:02] [INFO] ACTION_SUCCESS: gmail_send completed for approval EMAIL_12345
[2026-02-24T10:30:02] [INFO] Moved approval file to: Approved
```

---

## Response Format

### Success Response
```json
{
    "status": "success",
    "message": "Gmail email sent successfully",
    "action_type": "gmail_send",
    "approval_id": "EMAIL_12345"
}
```

### Pending Approval Response
```json
{
    "status": "pending_approval",
    "message": "Action awaiting human approval",
    "approval_id": "EMAIL_12345"
}
```

### Error Response
```json
{
    "status": "error",
    "message": "Action failed after 4 attempts",
    "action_type": "gmail_send",
    "approval_id": "EMAIL_12345"
}
```

---

## Integration Points

### With Orchestrator
The orchestrator calls this skill via the `trigger_mcp_executor()` function using Claude's T class.

### With Watchers
- **GmailWatcher**: Creates action files that eventually trigger email sends
- **LinkedInWatcher**: Creates post ideas that eventually trigger LinkedIn posts

### With Approval Workflow
Reads approval status from `Pending_Approval/` folder and moves files upon completion.

### With Logging System
Uses `log_manager.setup_logging()` for console output and maintains separate `actions.log` for audit trail.

---

## Error Handling

| Error Type | Behavior |
|------------|----------|
| Approval not found | Returns `pending_approval` status, file stays in `Pending_Approval/` |
| Approval not granted | Returns `pending_approval` status, file stays in `Pending_Approval/` |
| Action execution failure | Retries up to `max_retries` times, then moves to `Rejected/` |
| Unknown action type | Returns error immediately, logs error |
| Invalid data file | Returns error immediately, logs error |

---

## Extension Points

To add new action types:

1. Add new action handler function:
```python
def new_action_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    log_action("Executing new action...")
    # Implementation here
    return {"status": "success", "message": "Action completed"}
```

2. Register in `execute_action()`:
```python
if action_type == "new_action":
    result = new_action_handler(data)
```

3. Update argument parser choices:
```python
choices=["gmail_send", "linkedin_post", "new_action"]
```

---

## Testing

### Manual Test

```bash
# Create test data file
echo '{"to": "test@example.com", "subject": "Test", "body": "Test body"}' > test_data.json

# Run with test approval (create approval file first)
python scripts/mcp_executor.py --action gmail_send --data test_data.json --approval_id TEST_001
```

### Unit Test Structure

```python
def test_check_approval():
    # Test approval detection
    pass

def test_execute_action_success():
    # Test successful execution
    pass

def test_execute_action_retry():
    # Test retry mechanism
    pass
```

---

## Security Considerations

- Approval files must be in the correct folder before execution
- All actions are logged for audit purposes
- Sensitive data (emails, posts) should be handled securely
- API credentials are managed by respective watcher modules

---

## Related Files

| File | Purpose |
|------|---------|
| `scripts/mcp_executor.py` | Main implementation |
| `.claude/skills/mcp-executor/SKILL.md` | This documentation |
| `orchestrator.py` | Integration point |
| `gmail_watcher.py` | Gmail integration |
| `linkedin_watcher.py` | LinkedIn integration |
| `log_manager.py` | Logging utilities |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-24 | Initial Silver Tier implementation |
