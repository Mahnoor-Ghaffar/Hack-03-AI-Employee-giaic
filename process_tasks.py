"""
Process all pending tasks in Needs_Action folder
"""
import sys
from datetime import datetime
sys.path.insert(0, 'skills')
from vault_skills import read_task, write_response, move_to_done, get_task_summary, update_dashboard

print("=" * 50)
print("PROCESSING ALL PENDING TASKS")
print("=" * 50)
print()

# Task 1: Email - Client Proposal Review
print("[TASK 1] Processing: email_client_proposal_review.md")
response1 = """## AI Draft Response

Dear John,

Thank you for following up on the project proposal. I've reviewed the document and here's my feedback:

1. **Budget**: The proposed budget appears reasonable for the scope outlined. No major concerns.

2. **Timelines**: The timelines are realistic given the resources available.

3. **Modifications**: I suggest adding a milestone review at the 50% completion point.

Please let me know if you'd like to discuss any details further.

Best regards,
[Your Name]

---
**Note for Human**: This is a draft. Please review and approve before sending."""

write_response('email_client_proposal_review.md', response1, ['Review draft response', 'Approve before sending'])
move_to_done('email_client_proposal_review.md', 'Drafted professional response for client proposal review - awaiting human approval')
print("  [OK] Response written and moved to Done")
print()

# Task 2: FILE_test.md
print("[TASK 2] Processing: FILE_test.md")
response2 = """## File Processing Summary

**Original File:** test.txt
**Size:** 8 bytes
**Type:** File drop for processing

This file was dropped into the drop_zone for processing. No specific content or instructions were provided.

### Recommended Actions
- [ ] Review the original file content
- [ ] Add specific processing instructions if needed
- [ ] Archive or take action based on file purpose"""

write_response('FILE_test.md', response2, ['Review original file', 'Add processing instructions'])
move_to_done('FILE_test.md', 'Processed file drop - added summary and recommendations')
print("  [OK] Response written and moved to Done")
print()

# Task 3: FILE_01-test.md
print("[TASK 3] Processing: FILE_01-test.md")
response3 = """## File Processing Summary

**Original File:** 01-test.txt
**Size:** 0 bytes (empty file)
**Type:** File drop for processing

This appears to be an empty test file dropped into the drop_zone.

### Recommended Actions
- [ ] Verify if this was intentionally empty
- [ ] If test file, can be archived
- [ ] If mistake, request proper file from sender"""

write_response('FILE_01-test.md', response3, ['Verify file purpose', 'Archive if test file'])
move_to_done('FILE_01-test.md', 'Processed empty file drop - flagged for verification')
print("  [OK] Response written and moved to Done")
print()

# Update Dashboard
print("[UPDATING] Dashboard...")
summary = get_task_summary()
update_dashboard('Pending Tasks', summary)
update_dashboard('Recent Activity', f'- **{datetime.now().strftime("%Y-%m-%d")}**: Processed 3 tasks successfully')
print("  [OK] Dashboard updated")
print()

print("=" * 50)
print("ALL TASKS PROCESSED SUCCESSFULLY!")
print("=" * 50)
print()
print("Remaining tasks:", get_task_summary())
