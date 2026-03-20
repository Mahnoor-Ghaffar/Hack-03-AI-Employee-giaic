# Work-Zone Quick Reference

## Folder Structure

```
AI_Employee_Vault/
├── Needs_Action/
│   ├── email/          # Incoming emails to triage
│   └── social/         # Social media requests
├── Pending_Approval/
│   ├── email/          # Draft replies awaiting approval
│   └── social/         # Draft posts awaiting approval
├── Approved/           # Approved, ready for execution
├── In_Progress/
│   ├── cloud/          # Cloud VM working area
│   └── local/          # Local machine working area
├── Done/               # Completed actions
└── Rejected/           # Rejected items
```

## Responsibilities

| Cloud VM | Local Machine |
|----------|---------------|
| Email triage | Final send actions |
| Draft replies | Post to social media |
| Draft social posts | WhatsApp messages |
| Write approval files | Payments |
| | Approvals (human) |

## Quick Commands

### Cloud VM
```bash
# Process incoming emails
python scripts/workzone_processor.py process email

# Process social media requests
python scripts/workzone_processor.py process social

# Check status
python scripts/workzone_processor.py status
```

### Local Machine
```bash
# Approve a draft
python scripts/workzone_processor.py approve filename.md yes

# Reject a draft
python scripts/workzone_processor.py approve filename.md no

# Send approved email
python scripts/workzone_processor.py execute filename.md send_email

# Post to social media
python scripts/workzone_processor.py execute filename.md post_social
```

## Rules

1. **Claim-by-Move**: Moving a file to your zone = claiming ownership
2. **Single-Writer Dashboard**: Only one zone writes to Dashboard.md at a time
3. **Cloud writes drafts, Local executes**: Cloud never sends/posts directly

## Workflow

```
Needs_Action → In_Progress/{zone} → Pending_Approval → Approved → Done
                    ↑                    ↓
              (claim-by-move)      (human approval)
```
