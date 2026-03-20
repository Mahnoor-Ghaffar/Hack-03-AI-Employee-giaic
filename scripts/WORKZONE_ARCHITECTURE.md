# Cloud vs Local Work-Zone Architecture

## Overview

This architecture separates responsibilities between Cloud VM and Local Machine to ensure security and prevent conflicts.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VAULT STRUCTURE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  /Needs_Action/           ← New items arrive here                        │
│  ├── email/               ← Incoming emails to triage                    │
│  └── social/              ← Social media requests                        │
│                                                                          │
│  /Pending_Approval/       ← Awaiting human approval                      │
│  ├── email/               ← Draft replies ready to send                  │
│  └── social/              ← Draft posts ready to post                    │
│                                                                          │
│  /Approved/               ← Approved, awaiting execution                 │
│                                                                          │
│  /In_Progress/            ← Currently being worked on                    │
│  ├── cloud/               ← Cloud VM working area                        │
│  └── local/               ← Local machine working area                   │
│                                                                          │
│  /Done/                   ← Completed actions                            │
│  /Rejected/               ← Rejected items                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Responsibilities

### Cloud VM (Automated Worker)

| Task | Description | Output Location |
|------|-------------|-----------------|
| **Email Triage** | Read incoming emails, categorize | `/Needs_Action/email/` |
| **Draft Replies** | Write email responses | `/Pending_Approval/email/` |
| **Draft Social Posts** | Create social media content | `/Pending_Approval/social/` |
| **Write Approval Files** | Create `.approval.json` markers | Alongside drafts |

**Cloud CANNOT:**
- Send actual emails (no SMTP credentials)
- Post to social media (no API tokens)
- Access WhatsApp (no session)
- Process payments (no payment credentials)
- Make final approval decisions

### Local Machine (Human + Final Actions)

| Task | Description | Requires |
|------|-------------|----------|
| **Final Send** | Actually send emails | SMTP credentials |
| **Post Actions** | Publish to social media | API tokens |
| **WhatsApp** | Send WhatsApp messages | Session files |
| **Payments** | Process payments | Payment credentials |
| **Approvals** | Review and approve/reject drafts | Human decision |

**Local ONLY:**
- Has access to `.env`, `tokens/`, `sessions/`
- Makes final approval decisions
- Executes real-world actions

## Core Rules

### 1. Claim-by-Move Rule

**Rule:** Moving a file into a zone folder claims ownership.

```
/Needs_Action/email/incoming_001.md
         ↓ (Cloud moves to its zone)
/In_Progress/cloud/incoming_001.md
         ↑ Cloud now owns this file
```

**Implementation:**
```python
# Cloud claims email task
processor.process_needs_action("email")
# Files automatically moved to /In_Progress/cloud/
```

**Benefits:**
- No file locking needed
- Visual ownership (see folder = see owner)
- Prevents duplicate work
- Git sync friendly

### 2. Single-Writer Rule for Dashboard.md

**Rule:** Only one zone can write to `Dashboard.md` at a time.

**Lock Mechanism:**
```
1. Zone acquires lock (.dashboard.lock file)
2. Zone writes Dashboard.md
3. Zone releases lock
4. Other zone can now acquire lock
```

**Lock File Format:**
```json
{
  "locked_by": "cloud",
  "locked_at": "2026-03-19T10:30:00",
  "expires_at": "2026-03-19T10:35:00"
}
```

**Timeout:** 5 minutes (prevents deadlocks)

**Usage:**
```python
# Cloud updates dashboard
processor.update_dashboard(Zone.CLOUD, {
    "email_drafts": 3,
    "social_drafts": 2
})

# Local updates dashboard
processor.update_dashboard(Zone.LOCAL, {
    "pending_approvals": 5,
    "actions_completed": 12
})
```

## Processing Logic

### Email Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│ EMAIL PROCESSING FLOW                                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. Gmail Watcher (Cloud)                                             │
│     └─→ Creates /Needs_Action/email/{email_id}.md                    │
│                                                                       │
│  2. Work-Zone Processor (Cloud, every 2 min)                          │
│     └─→ Moves to /In_Progress/cloud/ (claim-by-move)                 │
│     └─→ Drafts reply                                                  │
│     └─→ Moves to /Pending_Approval/email/                            │
│     └─→ Creates {email_id}.approval.json                              │
│                                                                       │
│  3. Human Review (Local)                                              │
│     └─→ Reviews draft                                                 │
│     └─→ python workzone_processor.py approve {email_id} yes          │
│     └─→ Moves to /Approved/                                           │
│                                                                       │
│  4. Final Send (Local)                                                │
│     └─→ python workzone_processor.py execute {email_id} send_email   │
│     └─→ Actually sends email via SMTP                                 │
│     └─→ Moves to /Done/                                               │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Social Media Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│ SOCIAL MEDIA PROCESSING FLOW                                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. Social Watcher (Cloud)                                            │
│     └─→ Creates /Needs_Action/social/{topic}.md                      │
│                                                                       │
│  2. Work-Zone Processor (Cloud, every 2 min)                          │
│     └─→ Moves to /In_Progress/cloud/ (claim-by-move)                 │
│     └─→ Drafts post content                                           │
│     └─→ Moves to /Pending_Approval/social/                           │
│     └─→ Creates {topic}.approval.json                                 │
│                                                                       │
│  3. Human Review (Local)                                              │
│     └─→ Reviews draft                                                 │
│     └─→ python workzone_processor.py approve {topic} yes             │
│     └─→ Moves to /Approved/                                           │
│                                                                       │
│  4. Final Post (Local)                                                │
│     └─→ python workzone_processor.py execute {topic} post_social     │
│     └─→ Actually posts via LinkedIn/Twitter API                       │
│     └─→ Moves to /Done/                                               │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

## Example Workflow

### Scenario: Process Incoming Email

**Step 1: Email arrives (Cloud)**
```bash
# Gmail watcher creates file
cat > AI_Employee_Vault/Needs_Action/email/email_20260319_001.md << EOF
---
from: client@example.com
subject: Project Update Request
received: 2026-03-19T10:00:00
---

Hi, can you send me the latest project status?
EOF
```

**Step 2: Cloud processes (every 2 min)**
```bash
cd scripts
python workzone_processor.py process email

# Output: [cloud] Claimed: email_20260319_001.md -> cloud
```

**Step 3: Cloud drafts reply**
```bash
# Cloud AI writes reply in /In_Progress/cloud/
# Then moves to pending approval
python workzone_processor.py move_to_pending email_20260319_001.md email

# Output: [cloud] Moved to approval: email_20260319_001.md
```

**Step 4: Human approves (Local)**
```bash
# Review the draft
cat AI_Employee_Vault/Pending_Approval/email/email_20260319_001.md

# Approve it
python workzone_processor.py approve email_20260319_001.md yes

# Output: [local] Approved: email_20260319_001.md
```

**Step 5: Local sends email**
```bash
python workzone_processor.py execute email_20260319_001.md send_email

# Output: [local] Sending email: email_20260319_001.md
# Output: [local] Completed: email_20260319_001.md
```

### Scenario: Social Media Post

**Step 1: Create social media request**
```bash
cat > AI_Employee_Vault/Needs_Action/social/product_launch.md << EOF
---
platform: linkedin
topic: Product Launch
priority: high
---

Announce our new AI Employee feature launching next week.
Include: key features, benefits, call-to-action
EOF
```

**Step 2-5: Same flow as email**
```bash
# Cloud drafts
python workzone_processor.py process social

# Human approves
python workzone_processor.py approve product_launch.md yes

# Local posts
python workzone_processor.py execute product_launch.md post_social
```

## Commands Reference

### Process Needs_Action
```bash
# Cloud: Process email tasks
python workzone_processor.py process email

# Cloud: Process social tasks
python workzone_processor.py process social
```

### Approve/Reject
```bash
# Local: Approve a file
python workzone_processor.py approve filename.md yes

# Local: Reject a file
python workzone_processor.py approve filename.md no
```

### Execute Final Actions
```bash
# Local: Send email
python workzone_processor.py execute filename.md send_email

# Local: Post to social
python workzone_processor.py execute filename.md post_social

# Local: Send WhatsApp
python workzone_processor.py execute filename.md whatsapp

# Local: Process payment
python workzone_processor.py execute filename.md payments
```

### Status
```bash
# Check work-zone status
python workzone_processor.py status
```

### Dashboard
```bash
# Update dashboard (cloud or local)
python workzone_processor.py dashboard cloud
python workzone_processor.py dashboard local
```

## Integration with Git Sync

```
┌──────────────────────────────────────────────────────────────────────┐
│ GIT SYNC + WORK-ZONE INTEGRATION                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Cloud VM:                                                            │
│  ├── Cron pulls every 2 min (sync.sh cron)                           │
│  ├── Work-zone processor runs every 2 min                            │
│  ├── Claims files by moving to /In_Progress/cloud/                   │
│  └── Writes drafts to /Pending_Approval/                             │
│                                                                       │
│  Git Push:                                                            │
│  └─→ Drafts synced to Local                                          │
│                                                                       │
│  Local Machine:                                                       │
│  ├── Human reviews drafts in /Pending_Approval/                      │
│  ├── Approves (moves to /Approved/)                                  │
│  ├── Executes final actions                                          │
│  └─→ Manual push when ready (sync.sh push)                           │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

## Security Boundaries

| Resource | Cloud | Local | Reason |
|----------|-------|-------|--------|
| `.env` | ❌ | ✅ | Contains secrets |
| `tokens/` | ❌ | ✅ | API authentication |
| `sessions/` | ❌ | ✅ | WhatsApp/session data |
| SMTP credentials | ❌ | ✅ | Email sending |
| Social API tokens | ❌ | ✅ | Social posting |
| Payment credentials | ❌ | ✅ | Financial security |

## File Naming Conventions

```
Needs_Action:
  email_YYYYMMDD_NNN.md      # Email tasks
  social_topic.md            # Social media tasks

Pending_Approval:
  email_YYYYMMDD_NNN.md      # Draft replies
  email_YYYYMMDD_NNN.approval.json
  social_topic.md            # Draft posts
  social_topic.approval.json

Approved:
  <original_name>.md         # Ready for execution

Done:
  <original_name>.md         # Completed
```
