# human-approval Skill

**Purpose:** Implement human-in-the-loop for sensitive actions, awaiting explicit human approval or rejection.

**Usage:**
This skill creates an approval request file with action details and waits for a human to review and update the file with "APPROVED" or "REJECTED".

**Arguments:**
*   `action_details`: A description of the action requiring approval.

**Process:**
1.  A new file is created in `AI_Employee_Vault/Needs_Approval/` with the provided action details.
2.  The skill monitors this file.
3.  Execution pauses until the file content is updated to either "APPROVED" or "REJECTED".
4.  The final status is returned.

**Example Invocation:**
```bash
python scripts/request_approval.py "Deploy changes to production database."
```
