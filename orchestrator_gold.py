"""
AI Employee Orchestrator - Gold Tier

This module orchestrates all watchers and skills for the AI Employee system with Gold Tier features:
- Full cross-domain integration (Personal + Business)
- Odoo ERP integration for accounting
- Facebook/Instagram integration
- Twitter (X) integration via MCP server
- Weekly Business Audit & CEO Briefing
- Ralph Wiggum persistence loop for autonomous task completion

File Flow:
    Inbox → Needs_Action → Plan_*.md → Done
    Pending_Approval → Needs_Approval → [Human Approval] → Approved/Rejected

Gold Tier Components:
    - All Silver Tier components PLUS:
    - FacebookWatcher: Monitors Facebook Pages and Instagram
    - TwitterWatcher: Monitors Twitter/X mentions and hashtags
    - OdooMCPServer: ERP integration for invoices, payments, reports
    - FacebookMCPServer: Posts to Facebook and Instagram
    - TwitterMCPServer: Posts tweets, threads, and generates analytics summaries
    - CEOBriefingGenerator: Weekly business audit and CEO briefing
    - RalphWiggumLoop: Autonomous multi-step task completion
"""

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from subprocess import run, PIPE
from typing import Tuple

from log_manager import setup_logging
from skills.vault_skills import get_vault
from claude_sdk_wrapper import T
from gmail_watcher import GmailWatcher
from linkedin_watcher import LinkedInWatcher
from filesystem_watcher import FileSystemWatcher
from facebook_watcher import FacebookWatcher
from twitter_watcher import TwitterWatcher
from scripts.request_approval import request_approval, ApprovalStatus
from scripts.odoo_mcp_server import OdooMCPServer
from scripts.facebook_mcp_server import FacebookMCPServer
from scripts.twitter_mcp_server import TwitterMCPServer
from scripts.ceo_briefing_generator import CEOBriefingGenerator
from scripts.ralph_wiggum_loop import RalphWiggumLoop, TaskStatus

# Setup logger for orchestrator (using Gold Tier log path)
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="orchestrator_gold")

# Vault Paths
VAULT_PATH = "AI_Employee_Vault"
NEEDS_ACTION_PATH = Path(VAULT_PATH) / "Needs_Action"
APPROVED_PATH = Path(VAULT_PATH) / "Approved"
DONE_PATH = Path(VAULT_PATH) / "Done"
POST_IDEAS_PATH = Path(VAULT_PATH) / "Post_Ideas"
PENDING_APPROVAL_PATH = Path(VAULT_PATH) / "Pending_Approval"
NEEDS_APPROVAL_PATH = Path(VAULT_PATH) / "Needs_Approval"
SOCIAL_MEDIA_PATH = Path(VAULT_PATH) / "Social_Media"
BRIEFINGS_PATH = Path(VAULT_PATH) / "Briefings"
ACCOUNTING_PATH = Path(VAULT_PATH) / "Accounting"

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
        action_type: The type of action (gmail_send, linkedin_post, facebook_post, twitter_post, odoo_invoice).
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


def trigger_ralph_loop(prompt: str, task_id: str = None, max_iterations: int = 10) -> Tuple[TaskStatus, str, int]:
    """
    Trigger the Ralph Wiggum persistence loop for autonomous task completion.

    Args:
        prompt: Task prompt to process
        task_id: Optional task ID
        max_iterations: Maximum number of iterations

    Returns:
        Tuple of (status, reason, iterations)
    """
    try:
        loop = RalphWiggumLoop(
            vault_path=VAULT_PATH,
            max_iterations=max_iterations,
            max_duration_minutes=60
        )

        logger.info(f"Starting Ralph Wiggum loop for task: {task_id or 'auto-generated'}")
        
        status, reason, iterations = loop.run(
            prompt=prompt,
            task_id=task_id
        )

        logger.info(f"Ralph Wiggum loop completed: {status.value} after {iterations} iterations")
        return (status, reason, iterations)

    except Exception as e:
        logger.error(f"Error in Ralph Wiggum loop: {e}")
        return (TaskStatus.FAILED, str(e), 0)


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


def process_facebook_activity(facebook_watcher: FacebookWatcher):
    """Process Facebook/Instagram activity and create action files."""
    logger.info("Checking for new Facebook/Instagram activity (one iteration)...")
    try:
        updates = facebook_watcher.check_for_updates()
        for update in updates:
            action_file_path = facebook_watcher.create_action_file(update)
            logger.info(f"Created Facebook/Instagram action file: {action_file_path.name}")
            
            # Trigger task-planner for engagement response
            trigger_task_planner(
                action_file_path.name,
                f"Plan engagement response for social media activity in {action_file_path.name}"
            )
    except Exception as e:
        logger.error(f"Error processing Facebook activity: {e}")


def process_twitter_activity(twitter_watcher: TwitterWatcher):
    """Process Twitter/X activity and create action files."""
    logger.info("Checking for new Twitter/X activity (one iteration)...")
    try:
        updates = twitter_watcher.check_for_updates()
        for update in updates:
            action_file_path = twitter_watcher.create_action_file(update)
            logger.info(f"Created Twitter action file: {action_file_path.name}")
            
            # Trigger task-planner for engagement response
            trigger_task_planner(
                action_file_path.name,
                f"Plan engagement response for Twitter activity in {action_file_path.name}"
            )
    except Exception as e:
        logger.error(f"Error processing Twitter activity: {e}")


def sync_odoo_accounting():
    """Sync accounting data from Odoo and create financial reports."""
    logger.info("Syncing Odoo accounting data...")
    try:
        odoo = OdooMCPServer()
        
        # Test connection
        conn_result = odoo.test_connection()
        if conn_result.get("connected"):
            logger.info(f"Odoo connected: {conn_result.get('odoo_version', 'unknown')}")
            
            # Get invoices
            invoices_result = odoo.get_invoices(status="all", limit=50)
            if invoices_result.get("status") == "success":
                # Save to Accounting folder
                invoices_file = ACCOUNTING_PATH / f"Invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                content = f"""---
type: odoo_invoices_export
generated: {datetime.now().isoformat()}
count: {invoices_result.get('count', 0)}
---

# Odoo Invoices Export

{json.dumps(invoices_result, indent=2)}
"""
                invoices_file.write_text(content)
                logger.info(f"Exported {invoices_result.get('count', 0)} invoices to {invoices_file.name}")
            
            # Get financial report
            report_result = odoo.get_financial_report(report_type="profit_loss")
            if report_result.get("status") == "success":
                report_file = ACCOUNTING_PATH / f"Financial_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                content = f"""---
type: odoo_financial_report
generated: {datetime.now().isoformat()}
report_type: profit_loss
---

# Odoo Financial Report

{json.dumps(report_result, indent=2)}
"""
                report_file.write_text(content)
                logger.info(f"Exported financial report to {report_file.name}")
        else:
            logger.warning(f"Odoo not connected: {conn_result.get('message')}")
            
    except Exception as e:
        logger.error(f"Error syncing Odoo accounting: {e}")


def generate_weekly_ceo_briefing():
    """Generate weekly CEO briefing with business audit."""
    logger.info("Generating weekly CEO briefing...")
    try:
        generator = CEOBriefingGenerator(vault_path=VAULT_PATH)
        result = generator.generate_weekly_briefing()
        
        if result.get("status") == "success":
            logger.info(f"CEO briefing generated: {result['briefing_file']}")
        else:
            logger.error(f"CEO briefing generation failed: {result}")
            
    except Exception as e:
        logger.error(f"Error generating CEO briefing: {e}")


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
    logger.info("\n" + "=" * 60)
    logger.info("=== HITL APPROVAL WORKFLOW ===")
    logger.info("=" * 60)
    
    # Ensure Pending_Approval folder exists
    PENDING_APPROVAL_PATH.mkdir(parents=True, exist_ok=True)
    NEEDS_APPROVAL_PATH.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Checking Pending_Approval folder: {PENDING_APPROVAL_PATH}")
    logger.info(f"Needs_Approval folder: {NEEDS_APPROVAL_PATH}")

    # First, move any new files from Pending_Approval to Needs_Approval
    files_moved = 0
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
                files_moved += 1
        except Exception as e:
            logger.error(f"Error moving approval file {approval_file_path.name}: {e}")
    
    if files_moved > 0:
        logger.info(f"Moved {files_moved} file(s) from Pending_Approval to Needs_Approval")

    # Process files in Needs_Approval with blocking human-approval
    logger.info("\n--- Processing Needs_Approval with human-approval skill (BLOCKING) ---")

    for approval_file_path in NEEDS_APPROVAL_PATH.glob('*.md'):
        try:
            approval_id = approval_file_path.stem
            logger.info(f"\n{'='*60}")
            logger.info(f"Waiting for approval: {approval_file_path.name}")
            logger.info(f"{'='*60}")

            # Use human-approval skill - THIS BLOCKS until human responds or timeout
            status, reason = request_approval(
                file_path=str(approval_file_path),
                timeout_seconds=3600,  # Default 1 hour timeout
                poll_interval=10       # Check every 10 seconds
            )

            if status == ApprovalStatus.APPROVED:
                logger.info(f"\n{'✓'} APPROVED → Executing: {approval_id}")
                logger.info(f"Approval reason: {reason}")

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
                    logger.info(f"Triggering mcp-executor for action: {action_type}")
                    result = trigger_mcp_executor(action_type, data_for_executor, approval_id)

                    if "Error" not in result:
                        logger.info(f"✓ EXECUTION COMPLETE: {approval_id} - Success")
                    else:
                        logger.error(f"✗ EXECUTION FAILED: {approval_id} - {result}")
                else:
                    logger.warning(f"Could not determine action type for {approval_id}")

            elif status == ApprovalStatus.REJECTED:
                logger.info(f"\n{'✗'} REJECTED → Skipping: {approval_id}")
                logger.info(f"Rejection reason: {reason}")

            elif status == ApprovalStatus.TIMEOUT:
                logger.info(f"\n{'⏱'} TIMEOUT → Skipping: {approval_id}")
                logger.info(f"Timeout reason: {reason}")

        except Exception as e:
            logger.error(f"Error processing approval file {approval_file_path.name}: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("=== HITL APPROVAL WORKFLOW COMPLETE ===")
    logger.info("=" * 60)


def orchestrate():
    """
    Main orchestration function - Gold Tier.
    Starts all watchers and processes pending tasks with full cross-domain integration.
    """
    logger.info("=" * 60)
    logger.info("Starting AI Employee Orchestrator (Gold Tier)...")
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

    # --- Process Facebook/Instagram Activity ---
    logger.info("\n--- Processing Facebook/Instagram Activity ---")
    facebook_watcher = FacebookWatcher(
        vault_path=VAULT_PATH,
        facebook_pages=["YourBusinessPage"],  # Configure your pages
        instagram_accounts=["yourbusiness"],   # Configure your accounts
        check_interval=600
    )
    process_facebook_activity(facebook_watcher)

    # --- Process Twitter/X Activity ---
    logger.info("\n--- Processing Twitter/X Activity ---")
    twitter_watcher = TwitterWatcher(
        vault_path=VAULT_PATH,
        username="YourUsername",      # Configure your username
        hashtags=["AI", "Automation"], # Configure your hashtags
        check_interval=300
    )
    process_twitter_activity(twitter_watcher)

    # --- Sync Odoo Accounting ---
    logger.info("\n--- Syncing Odoo Accounting Data ---")
    sync_odoo_accounting()

    # --- Process Pending Approvals ---
    logger.info("\n--- Processing Pending Approvals ---")
    process_pending_approvals()

    # --- Check for Weekly CEO Briefing ---
    # Generate briefing if it's Monday morning
    today = datetime.now()
    if today.weekday() == 0 and today.hour < 12:  # Monday before noon
        logger.info("\n--- Generating Weekly CEO Briefing ---")
        generate_weekly_ceo_briefing()

    # --- Summary ---
    logger.info("\n" + "=" * 60)
    logger.info("AI Employee Orchestrator (Gold Tier) completed one cycle.")
    logger.info(f"Watcher threads running: {len(watcher_threads)}")
    logger.info("FileSystemWatcher continues monitoring Inbox...")
    logger.info("Gold Tier Features: Facebook, Instagram, Twitter, Odoo ERP, CEO Briefing")
    logger.info("=" * 60)

    # Keep the orchestrator running to maintain watcher threads
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
    NEEDS_APPROVAL_PATH.mkdir(exist_ok=True)
    SOCIAL_MEDIA_PATH.mkdir(exist_ok=True)
    BRIEFINGS_PATH.mkdir(exist_ok=True)
    ACCOUNTING_PATH.mkdir(exist_ok=True)
    (Path(VAULT_PATH) / "Logs").mkdir(exist_ok=True)

    # Run the orchestrator
    orchestrate()
