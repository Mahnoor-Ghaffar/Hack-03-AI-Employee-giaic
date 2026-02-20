# Quick Start Guide - AI Employee

## Prerequisites Check

Ensure you have:
- [ ] Python 3.13+ installed
- [ ] Claude Code subscription active
- [ ] Obsidian installed (optional, for viewing vault)

## Setup (One Time)

### 1. Activate Python Environment

```bash
cd "E:\New folder\GIAIC-Q4\sub-hack03\Hack-03-AI-Employee-giaic"
```

### 2. Install Dependencies

```bash
# Create virtual environment (if not already done)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install required packages
pip install watchdog
```

### 3. Verify Setup

```bash
# Test vault skills
python test_vault_skills.py
```

You should see: "All tests completed successfully!"

---

## Daily Workflow

### Option A: File System Watcher (Automated)

**Step 1:** Start the file watcher (keeps running):

```bash
python filesystem_watcher.py
```

This watches the `drop_zone` folder for new files.

**Step 2:** Drop any file into `drop_zone/` folder

The file will be automatically copied to `AI_Employee_Vault/Needs_Action/` with metadata.

**Step 3:** In another terminal, run Claude:

```bash
claude
```

**Step 4:** Prompt Claude:

```
Check the AI_Employee_Vault/Needs_Action folder for pending tasks.
Read each task file, draft responses, and move completed tasks to Done.
Use the vault skills: read_task, write_response, move_to_done.
```

---

### Option B: Manual Processing (Simple)

**Step 1:** Create a task file in `AI_Employee_Vault/Needs_Action/`:

```markdown
---
type: manual_task
priority: normal
---

# Task Description

What needs to be done...

## Suggested Actions
- [ ] Action 1
- [ ] Action 2
```

**Step 2:** Run Claude:

```bash
claude
```

**Step 3:** Process the task using vault skills.

---

## Available Vault Skills

| Skill | Description |
|-------|-------------|
| `list_pending_tasks()` | List all tasks in Needs_Action |
| `read_task("file.md")` | Read a specific task |
| `write_response("file.md", "response")` | Add AI response to task |
| `move_to_done("file.md", "summary")` | Complete a task |
| `get_task_summary()` | Get formatted summary |
| `update_dashboard("Section", "Content")` | Update dashboard |

---

## Example Claude Session

```
You: Check what tasks are pending in the vault.

Claude: I'll use list_pending_tasks() to check...
        Found 2 tasks: email_client_proposal_review.md and FILE_test.md

You: Read the email task and draft a response.

Claude: Reading with read_task("email_client_proposal_review.md")...
        [Reads task and drafts professional response]
        I've added a response to the file.

You: Move it to Done with a summary.

Claude: Moving with move_to_done("email_client_proposal_review.md", "Drafted response...")
        Task completed!
```

---

## Folder Structure

```
Hack-03-AI-Employee-giaic/
├── AI_Employee_Vault/
│   ├── Inbox/           # Raw incoming items
│   ├── Needs_Action/    # Tasks to process
│   ├── Done/            # Completed tasks
│   ├── Dashboard.md     # Status overview
│   └── Company_Handbook.md  # Rules & preferences
├── drop_zone/           # Drop files here for auto-processing
├── filesystem_watcher.py  # Monitors drop_zone
├── skills/
│   ├── vault_skills.py    # Main vault operations
│   └── process_file_skill.py
└── test_vault_skills.py   # Test script
```

---

## Troubleshooting

### "Module not found" error
```bash
# Make sure virtual environment is activated
venv\Scripts\activate

# Install dependencies
pip install watchdog
```

### Claude can't see skills
```bash
# Check .claude/mcp.json exists
# Restart Claude session
```

### File watcher not detecting files
```bash
# Ensure drop_zone folder exists
mkdir drop_zone

# Check filesystem_watcher.py is running
```

---

## Next Steps (Silver Tier)

Once Bronze is working, add:
1. Gmail Watcher for email monitoring
2. MCP servers for sending emails
3. Scheduled tasks (Windows Task Scheduler)
4. Ralph Wiggum loop for autonomous operation

---

## Support

- Check `Personal AI Employee Hackathon 0_....md` for full documentation
- Review `skills/` folder for skill documentation
- Join Wednesday meetings: Zoom link in main document
