"""
AI Employee Orchestrator - Silver Tier

This module orchestrates all watchers and skills for the AI Employee system.
It uses Claude Agent SDK 0.1.39 with the T class for task spawning.

File Flow:
    Inbox → Needs_Action → Plan_*.md → Done
    Pending_Approval → Needs_Approval → [Human Approval] → Approved/Rejected

Components:
    - FileSystemWatcher: Monitors Inbox for new .md files
    - GmailWatcher: Checks for new Gmail messages
    - LinkedInWatcher: Monitors Post_Ideas for new content
    - Task Planner Skill: Generates plans for tasks in Needs_Action
    - MCP Executor: Executes approved external actions (Gmail, LinkedIn)
    - Human Approval Skill: Blocks execution until human approves/rejects (Silver Tier)
"""

import json
import time
import threading
from datetime import datetime
from pathlib import Path
from subprocess import run, PIPE

from log_manager import setup_logging
from skills.vault_skills import get_vault
from claude_sdk_wrapper import T
from gmail_watcher import GmailWatcher
from linkedin_watcher import LinkedInWatcher
from filesystem_watcher import FileSystemWatcher
from scripts.request_approval import request_approval, ApprovalStatus

# Setup logger for orchestrator (using Silver Tier log path)
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="orchestrator")

VAULT_PATH = "AI_Employee_Vault"
NEEDS_ACTION_PATH = Path(VAULT_PATH) / "Needs_Action"
APPROVED_PATH = Path(VAULT_PATH) / "Approved"
DONE_PATH = Path(VAULT_PATH) / "Done"
POST_IDEAS_PATH = Path(VAULT_PATH) / "Post_Ideas"
PENDING_APPROVAL_PATH = Path(VAULT_PATH) / "Pending_Approval"
NEEDS_APPROVAL_PATH = Path(VAULT_PATH) / "Needs_Approval"  # Human approval workflow (Silver Tier)

# Get the singleton vault instance
vault = get_vault()


def run_watcher_thread(watcher_instance):
    """Helper function to run a watcher in a separate thread."""
    thread = threading.Thread(target=watcher_instance.run, daemon=True)
    thread.start()
    logger.info(f"Started watcher thread for {watcher_instance.__class__.__name__}")
    return thread


def trigger_task_planner(file_name: str, description: str = None) -> str:
    """
    Trigger the task-planner skill using T class.
    
    Args:
        file_name: Name of the file in Needs_Action to process.
        description: Optional description override.
        
    Returns:
        Task ID or error message.
    """
    try:
        desc = description or f"Process new task file {file_name} with task-planner skill"
        
        plan_prompt = f"""Process the file '{file_name}' located in AI_Employee_Vault/Needs_Action.

Your responsibilities:
1. Read and analyze the task file content
2. Generate a detailed, step-by-step implementation plan
3. Save the plan as 'Plan_{Path(file_name).stem}.md' in the Needs_Action folder

The plan should be actionable with clear steps and checkboxes.
"""
        
        # Use T class to spawn the task-planner subagent
        task = T(
            description=desc,
            prompt=plan_prompt,
            subagent_type='task-planner',
            model='opus',
            run_in_background=True,
            allowed_tools=["Read", "Write", "Glob", "Edit", "Bash", "Skill"],
            system_prompt="""You are a task-planner specialist for the AI Employee system.
Your role is to analyze task files and generate detailed implementation plans.
Always save plans as Plan_*.md files in the Needs_Action folder."""
        )
        
        logger.info(f"Triggered task-planner skill for {file_name}. Task ID: {task.task_id}")
        return task.task_id
        
    except Exception as e:
        logger.error(f"Error triggering task-planner for {file_name}: {e}")
        return f"Error: {e}"




def trigger_mcp_executor(action_type: str, data: dict, approval_id: str) -> str:
    """
    Trigger the mcp-executor skill by running the script directly.

    Args:
        action_type: The type of action (gmail_send, linkedin_post).
        data: Dictionary containing action data.
        approval_id: The ID of the approval document.

    Returns:
        Result message or error message.
    """
    try:
        # Create a temporary data file
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        data_file = temp_dir / f"mcp_data_{approval_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Run mcp_executor.py as a subprocess
        cmd = [
            "python",
            "scripts/mcp_executor.py",
            "--action", action_type,
            "--data", str(data_file),
            "--approval_id", approval_id
        ]
        
        logger.info(f"Executing mcp-executor: {' '.join(cmd)}")
        
        result = run(cmd, capture_output=True, text=True, timeout=120)
        
        # Clean up temp file
        data_file.unlink(missing_ok=True)
        
        # Parse and log result
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                logger.info(f"mcp-executor result for {approval_id}: {output.get('status')}")
                return f"Success: {output.get('message', 'Action completed')}"
            except json.JSONDecodeError:
                logger.info(f"mcp-executor completed for {approval_id}")
                return "Action completed"
        else:
            logger.error(f"mcp-executor error: {result.stderr}")
            return f"Error: {result.stderr or result.stdout}"
            
    except Exception as e:
        logger.error(f"Error triggering mcp-executor for {action_type} (approval: {approval_id}): {e}")
        return f"Error: {e}"


def process_gmail_updates(gmail_watcher: GmailWatcher):
    """Process Gmail updates, create approval requests, and trigger task-planner for each."""
    logger.info("Checking for new Gmail updates (one iteration)...")
    try:
        gmail_updates = gmail_watcher.check_for_updates()
        for update in gmail_updates:
            # Create the action file in Needs_Action as before
            action_file_path = gmail_watcher.create_action_file(update)
            logger.info(f"Created Gmail action file: {action_file_path.name}")

            # Now, create an approval request in Pending_Approval
            approval_id = f"EMAIL_{update['id']}"
            approval_file_path = PENDING_APPROVAL_PATH / f"{approval_id}.md"

            # Extract necessary details for the approval file and later for mcp-executor data
            # Assuming content extraction logic from gmail_watcher.create_action_file
            msg = gmail_watcher.service.users().messages().get(
                userId='me', id=update['id']
            ).execute()
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            email_subject = headers.get('Subject', 'No Subject')
            email_snippet = msg.get('snippet', '')

            approval_content = f"""---
type: email_send_approval
from: {headers.get('From', 'Unknown')}
subject: {email_subject}
approval_id: {approval_id}
status: pending
created: {datetime.now().isoformat()}
---

## Email Send Request

**To:** [Recipient Email Here]
**Subject:** {email_subject}

**Content Preview:**
```
{email_snippet}
```

## Instructions for Approval

To approve this email for sending, edit this file and change `status: pending` to `status: approved`.
Also, update `To:` and provide the full email content if different from the preview.

```yaml
approved: false # CHANGE TO true TO APPROVE
recipient_email: ""
full_email_content: |
  {email_snippet}
```
"""
            approval_file_path.write_text(approval_content)
            logger.info(f"Created Gmail email send approval request: {approval_file_path.name}")

            # Trigger task-planner skill for the original action file in Needs_Action
            trigger_task_planner(
                action_file_path.name,
                f"Plan processing for new Gmail task {action_file_path.name} and await approval for sending email"
            )
            logger.info(f"Triggered task-planner for Gmail task: {action_file_path.name}")
    except Exception as e:
        logger.error(f"Error processing Gmail updates: {e}")


def process_linkedin_ideas(linkedin_watcher: LinkedInWatcher):
    """Process LinkedIn post ideas, create approval requests, and trigger task-planner for each."""
    logger.info("Checking for new LinkedIn post ideas (one iteration)...")
    try:
        linkedin_ideas = linkedin_watcher.check_for_updates()
        for idea in linkedin_ideas:
            # Create the action file in Needs_Action as before
            action_file_path = linkedin_watcher.create_action_file(idea)
            logger.info(f"Created LinkedIn action file from: {action_file_path.name}")

            # Now, create an approval request in Pending_Approval
            approval_id = f"LINKEDIN_POST_{datetime.now().isoformat().replace(':', '-').replace('.', '-')}"
            approval_file_path = PENDING_APPROVAL_PATH / f"{approval_id}.md"

            # Extract content from the original post idea file
            post_content = action_file_path.read_text()

            approval_content = f"""---
type: linkedin_post_approval
approval_id: {approval_id}
status: pending
created: {datetime.now().isoformat()}
source_file: {action_file_path.name}
---

## LinkedIn Post Request

**Content:**
```
{post_content}
```

## Instructions for Approval

To approve this LinkedIn post for publishing, edit this file and change `status: pending` to `status: approved`.

```yaml
approved: false # CHANGE TO true TO APPROVE
final_post_content: |
  {post_content}
```
"""
            approval_file_path.write_text(approval_content)
            logger.info(f"Created LinkedIn post approval request: {approval_file_path.name}")

            # Trigger task-planner skill for the original action file in Needs_Action
            trigger_task_planner(
                action_file_path.name,
                f"Plan processing for new LinkedIn task {action_file_path.name} and await approval for posting"
            )
            logger.info(f"Triggered task-planner for LinkedIn task: {action_file_path.name}")
    except Exception as e:
        logger.error(f"Error processing LinkedIn ideas: {e}")


def process_pending_approvals():
    """
    Process pending approval requests using the human-approval skill.
    
    This function:
    1. Moves approval files from Pending_Approval to Needs_Approval
    2. Uses blocking human-approval skill to wait for human response
    3. Triggers mcp-executor only after approval is granted
    4. Handles timeouts and rejections gracefully
    
    Silver Tier: Human-in-the-loop approval workflow
    """
    logger.info("\n--- Checking Pending_Approval for actions requiring human approval ---")
    
    # First, move any new files from Pending_Approval to Needs_Approval
    for approval_file_path in PENDING_APPROVAL_PATH.glob('*.md'):
        try:
            content = approval_file_path.read_text()
            # Skip files that are already approved (they'll be processed from Needs_Approval)
            if "status: approved" in content.lower() or "status: rejected" in content.lower():
                continue
            
            # Move to Needs_Approval for human-approval processing
            destination = NEEDS_APPROVAL_PATH / approval_file_path.name
            if not destination.exists():
                import shutil
                shutil.move(str(approval_file_path), str(destination))
                logger.info(f"Moved approval request to Needs_Approval: {approval_file_path.name}")
        except Exception as e:
            logger.error(f"Error moving approval file {approval_file_path.name}: {e}")
    
    # Process files in Needs_Approval with blocking human-approval
    logger.info("\n--- Processing Needs_Approval with human-approval skill (BLOCKING) ---")
    
    for approval_file_path in NEEDS_APPROVAL_PATH.glob('*.md'):
        try:
            approval_id = approval_file_path.stem
            logger.info(f"Processing approval request: {approval_file_path.name}")
            
            # Use human-approval skill - THIS BLOCKS until human responds or timeout
            status, reason = request_approval(
                file_path=str(approval_file_path),
                timeout_seconds=3600,  # Default 1 hour timeout
                poll_interval=10       # Check every 10 seconds
            )
            
            if status == ApprovalStatus.APPROVED:
                logger.info(f"Approval GRANTED for {approval_id}: {reason}")
                
                # Extract action type and data for mcp-executor
                content = approval_file_path.read_text() if approval_file_path.exists() else ""
                action_type = ""
                data_for_executor = {}
                
                if "type: email_send_approval" in content:
                    action_type = "gmail_send"
                    recipient_email_line = next((line for line in content.splitlines() if "recipient_email:" in line), None)
                    full_email_content_block = content.split("full_email_content: |")
                    
                    recipient_email = recipient_email_line.split(":")[-1].strip().strip('"') if recipient_email_line else ""
                    full_email_content = full_email_content_block[1].strip() if len(full_email_content_block) > 1 else ""
                    
                    data_for_executor = {
                        "to": recipient_email,
                        "subject": next((line.split(":")[-1].strip() for line in content.splitlines() if "subject:" in line), "No Subject"),
                        "body": full_email_content
                    }
                    
                elif "type: linkedin_post_approval" in content:
                    action_type = "linkedin_post"
                    final_post_content_block = content.split("final_post_content: |")
                    final_post_content = final_post_content_block[1].strip() if len(final_post_content_block) > 1 else ""
                    
                    data_for_executor = {
                        "content": final_post_content
                    }
                
                if action_type:
                    # Trigger mcp-executor only after approval
                    result = trigger_mcp_executor(action_type, data_for_executor, approval_id)
                    
                    if "Error" not in result:
                        logger.info(f"mcp-executor completed successfully for {approval_id}")
                    else:
                        logger.error(f"mcp-executor failed for {approval_id}: {result}")
                else:
                    logger.warning(f"Could not determine action type for {approval_id}")
                    
            elif status == ApprovalStatus.REJECTED:
                logger.warning(f"Approval REJECTED for {approval_id}: {reason}")
                
            elif status == ApprovalStatus.TIMEOUT:
                logger.warning(f"Approval TIMEOUT for {approval_id}: {reason}")
                
        except Exception as e:
            logger.error(f"Error processing approval file {approval_file_path.name}: {e}")




def orchestrate():
    """
    Main orchestration function.
    Starts all watchers and processes pending tasks.
    """
    logger.info("=" * 60)
    logger.info("Starting AI Employee Orchestrator (Silver Tier)...")
    logger.info("=" * 60)

    watcher_threads = []

    # --- Start FileSystemWatcher for Inbox ---
    logger.info("\n--- Starting FileSystemWatcher for Inbox ---")
    fs_watcher = FileSystemWatcher(vault_path=VAULT_PATH)
    watcher_threads.append(run_watcher_thread(fs_watcher))

    # --- Process Gmail Updates ---
    logger.info("\n--- Processing Gmail Updates ---")
    gmail_credentials_path = "gmail_credentials.json"
    if Path(gmail_credentials_path).exists():
        gmail_watcher = GmailWatcher(vault_path=VAULT_PATH, credentials_path=gmail_credentials_path)
        process_gmail_updates(gmail_watcher)
    else:
        logger.warning(f"Gmail credentials not found at {gmail_credentials_path}. Skipping GmailWatcher.")

    # --- Process LinkedIn Post Ideas ---
    logger.info("\n--- Processing LinkedIn Post Ideas ---")
    linkedin_watcher = LinkedInWatcher(vault_path=VAULT_PATH)
    process_linkedin_ideas(linkedin_watcher)

    # --- Process Pending Approvals ---
    logger.info("\n--- Processing Pending Approvals ---")
    process_pending_approvals()

    # --- Summary ---
    logger.info("\n" + "=" * 60)
    logger.info("AI Employee Orchestrator completed one cycle.")
    logger.info(f"Watcher threads running: {len(watcher_threads)}")
    logger.info("FileSystemWatcher continues monitoring Inbox...")
    logger.info("=" * 60)

    # Keep the orchestrator running to maintain watcher threads
    # Note: FileSystemWatcher thread is daemon, so it will stop when main thread exits
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Orchestrator received KeyboardInterrupt. Exiting.")


if __name__ == "__main__":
    # Ensure required directories exist
    Path(VAULT_PATH).mkdir(exist_ok=True)
    NEEDS_ACTION_PATH.mkdir(exist_ok=True)
    APPROVED_PATH.mkdir(exist_ok=True)
    DONE_PATH.mkdir(exist_ok=True)
    POST_IDEAS_PATH.mkdir(exist_ok=True)
    PENDING_APPROVAL_PATH.mkdir(exist_ok=True)
    NEEDS_APPROVAL_PATH.mkdir(exist_ok=True)  # Human approval workflow (Silver Tier)
    (Path(VAULT_PATH) / "Logs").mkdir(exist_ok=True)

    # Create sample LinkedIn post idea for testing if none exists
    sample_idea_path = POST_IDEAS_PATH / "Hackathon_Progress.md"
    if not sample_idea_path.exists():
        sample_idea_content = """We are making great progress on the AI Employee Hackathon!
The Bronze Tier is complete, and we are now moving to the Silver Tier.
Looking forward to demonstrating the new watcher scripts and human-in-the-loop approvals.
#AIEmployee #Hackathon #ClaudeCode #SilverTier"""
        sample_idea_path.write_text(sample_idea_content)
        logger.info(f"Created sample LinkedIn post idea: {sample_idea_path.name}")
    else:
        logger.info(f"Sample LinkedIn post idea exists: {sample_idea_path.name}")

    # Run the orchestrator
    orchestrate()
