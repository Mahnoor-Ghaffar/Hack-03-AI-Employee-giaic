import os
import sys
import time
import uuid

APPROVAL_VAULT_PATH = "AI_Employee_Vault/Needs_Approval/"

def request_approval(action_details):
    os.makedirs(APPROVAL_VAULT_PATH, exist_ok=True)

    approval_id = uuid.uuid4()
    approval_file = os.path.join(APPROVAL_VAULT_PATH, f"approval_{approval_id}.md")

    try:
        with open(approval_file, "w") as f:
            f.write(f"ACTION REQUIRED: Please review the following action:\n\n")
            f.write(f"{action_details}\n\n")
            f.write(f"Update this file with 'APPROVED' or 'REJECTED' to proceed.")
        print(f"Approval request created: {approval_file}")

        status = "PENDING"
        while status == "PENDING":
            if not os.path.exists(approval_file):
                print("Error: Approval file was deleted unexpectedly.")
                sys.exit(1)
            with open(approval_file, "r") as f:
                content = f.read().strip().upper()

            if "APPROVED" in content:
                status = "APPROVED"
            elif "REJECTED" in content:
                status = "REJECTED"
            else:
                time.sleep(5)  # Wait 5 seconds before checking again

        print(f"Approval status: {status}")
        return status

    except Exception as e:
        print(f"Error with human approval process: {e}")
        sys.exit(1)
    finally:
        if os.path.exists(approval_file):
            os.remove(approval_file)
            print(f"Cleaned up approval file: {approval_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python request_approval.py \"<action_details>\"")
        sys.exit(1)

    action_details = sys.argv[1]
    request_approval(action_details)
