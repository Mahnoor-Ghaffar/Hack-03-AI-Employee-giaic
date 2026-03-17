"""
Platinum Tier Local Orchestrator
Approval + Final Execution

This orchestrator runs ONLY on the Local machine and performs:
- Merges Cloud updates into Dashboard.md (Single-Writer)
- Processes pending approvals
- Executes approved actions via MCP
- Monitors WhatsApp (Local-only session)
- Checks urgent signals from Cloud

SECURITY: This agent has exclusive access to:
- WhatsApp session files
- Email send credentials
- Social media posting credentials
- Banking/payment credentials

Usage:
    python orchestrator_local.py
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from log_manager import setup_logging
from skills.vault_skills import get_vault

# Setup logging
logger = setup_logging(
    log_file="logs/local_agent.log",
    logger_name="local_orchestrator"
)

# Import Local-only watchers
try:
    from whatsapp_watcher import WhatsAppWatcher
    WHATSAPP_AVAILABLE = True
except ImportError:
    WHATSAPP_AVAILABLE = False
    logger.warning("WhatsAppWatcher not available - WhatsApp monitoring disabled")

try:
    from filesystem_watcher import FileSystemWatcher
    FILE_WATCHER_AVAILABLE = True
except ImportError:
    FILE_WATCHER_AVAILABLE = False
    logger.warning("FileSystemWatcher not available - file monitoring disabled")

# Import MCP Executor
try:
    from mcp_executor import MCPExecutor
    MCP_EXECUTOR_AVAILABLE = True
except ImportError:
    MCP_EXECUTOR_AVAILABLE = False
    logger.warning("MCPExecutor not available - action execution disabled")


class LocalOrchestrator:
    """
    Platinum Tier Local Orchestrator
    
    Runs on local machine with full credentials access.
    Merges Cloud updates, processes approvals, executes actions.
    """

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        """
        Initialize Local Orchestrator.
        
        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = Path(vault_path)
        self.vault = get_vault()
        
        # Platinum Tier folders
        self.updates_dir = self.vault_path / "Updates"
        self.signals_dir = self.vault_path / "Signals"
        self.pending_approval_dir = self.vault_path / "Pending_Approval"
        self.approved_dir = self.vault_path / "Approved"
        self.rejected_dir = self.vault_path / "Rejected"
        self.in_progress_dir = self.vault_path / "In_Progress" / "local_agent"
        self.needs_action_dir = self.vault_path / "Needs_Action"
        
        # Ensure directories exist
        for dir_path in [
            self.updates_dir, self.signals_dir, self.pending_approval_dir,
            self.approved_dir, self.rejected_dir, self.in_progress_dir,
            self.needs_action_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Local-only watchers
        self.whatsapp_watcher = None
        self.file_watcher = None
        self.mcp_executor = None
        
        self._initialize_components()
        
        # Statistics
        self.stats = {
            'updates_merged': 0,
            'approvals_processed': 0,
            'approvals_approved': 0,
            'approvals_rejected': 0,
            'actions_executed': 0,
            'whatsapp_messages': 0,
            'signals_received': 0,
            'start_time': datetime.now().isoformat(),
            'errors': 0
        }
        
        logger.info("Local Orchestrator initialized (Approval + Execution Mode)")

    def _initialize_components(self):
        """Initialize Local-only components"""
        
        # WhatsApp Watcher (Local-only session)
        if WHATSAPP_AVAILABLE:
            try:
                session_path = Path.home() / ".qwen" / "whatsapp_session"
                self.whatsapp_watcher = WhatsAppWatcher(
                    vault_path=str(self.vault_path),
                    session_path=str(session_path),
                    check_interval=30
                )
                logger.info("WhatsAppWatcher initialized (Local-only)")
            except Exception as e:
                logger.error(f"Failed to initialize WhatsAppWatcher: {e}")
        
        # File System Watcher
        if FILE_WATCHER_AVAILABLE:
            try:
                self.file_watcher = FileSystemWatcher(
                    vault_path=str(self.vault_path),
                    watch_folders=["drop_zone", "Inbox"]
                )
                logger.info("FileSystemWatcher initialized")
            except Exception as e:
                logger.error(f"Failed to initialize FileSystemWatcher: {e}")
        
        # MCP Executor
        if MCP_EXECUTOR_AVAILABLE:
            try:
                self.mcp_executor = MCPExecutor()
                logger.info("MCPExecutor initialized (Local-only)")
            except Exception as e:
                logger.error(f"Failed to initialize MCPExecutor: {e}")

    def merge_updates_to_dashboard(self) -> int:
        """
        Merge Cloud updates into Dashboard.md (Single-Writer rule).
        
        Only the Local agent can write to Dashboard.md.
        Cloud writes to /Updates/, Local merges into Dashboard.
        
        Returns:
            Number of updates merged
        """
        logger.info("Merging updates to Dashboard...")
        
        updates_merged = 0
        dashboard_sections = {
            'email_triage': [],
            'social_drafts': [],
            'odoo_reports': [],
            'signals': []
        }
        
        # Collect all updates
        try:
            # Email triage updates
            email_updates = list((self.updates_dir / "email_triage").glob("*.md"))
            dashboard_sections['email_triage'] = email_updates[-5:]  # Last 5
            
            # Social media drafts
            social_updates = list((self.updates_dir / "social_drafts").glob("*.md"))
            dashboard_sections['social_drafts'] = social_updates[-5:]  # Last 5
            
            # Odoo reports
            odoo_updates = list((self.updates_dir / "odoo_reports").glob("*.md"))
            dashboard_sections['odoo_reports'] = odoo_updates[-3:]  # Last 3
            
            # Urgent signals
            signals = list((self.signals_dir / "urgent").glob("*.md"))
            dashboard_sections['signals'] = signals[-5:]  # Last 5
            
        except Exception as e:
            logger.error(f"Error collecting updates: {e}")
            self.stats['errors'] += 1
            return 0
        
        # Build dashboard content
        dashboard_content = f"""# AI Employee Dashboard

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode:** Platinum Tier (Cloud + Local)
**Status:** {'🟢 Online' if self.stats['errors'] < 3 else '🟡 Degraded'}

---

## Quick Stats
- Updates Merged: {self.stats['updates_merged']}
- Approvals Processed: {self.stats['approvals_processed']}
- Actions Executed: {self.stats['actions_executed']}
- Errors: {self.stats['errors']}

---

## 📧 Email Triage (Cloud)

"""
        
        # Add email updates
        for update_file in dashboard_sections['email_triage']:
            try:
                content = update_file.read_text()
                metadata = self._parse_frontmatter(content)
                
                from_email = metadata.get('from', 'Unknown')
                subject = metadata.get('subject', 'No Subject')
                priority = metadata.get('priority', 'normal')
                
                priority_emoji = {'urgent': '🔴', 'high': '🟠', 'normal': '🟢'}.get(priority.lower(), '🟢')
                
                dashboard_content += f"""### {priority_emoji} {subject}
**From:** {from_email}
**Status:** {metadata.get('status', 'draft_ready')}
**File:** `{update_file.name}`

"""
                updates_merged += 1
                
            except Exception as e:
                logger.error(f"Error reading email update {update_file}: {e}")
        
        if not dashboard_sections['email_triage']:
            dashboard_content += "*No new email triage updates.*\n\n"
        
        dashboard_content += """---

## 📱 Social Media Drafts (Cloud)

"""
        
        # Add social drafts
        for update_file in dashboard_sections['social_drafts']:
            try:
                content = update_file.read_text()
                metadata = self._parse_frontmatter(content)
                
                platform = metadata.get('platform', 'unknown').capitalize()
                
                dashboard_content += f"""### {platform} Post Draft
**Status:** {metadata.get('status', 'draft_ready')}
**File:** `{update_file.name}`
**Action:** Move to /Pending_Approval/social_posts/ to approve

"""
                updates_merged += 1
                
            except Exception as e:
                logger.error(f"Error reading social update {update_file}: {e}")
        
        if not dashboard_sections['social_drafts']:
            dashboard_content += "*No new social media drafts.*\n\n"
        
        dashboard_content += """---

## 💰 Financial Reports (Cloud)

"""
        
        # Add Odoo reports
        for update_file in dashboard_sections['odoo_reports']:
            try:
                content = update_file.read_text()
                metadata = self._parse_frontmatter(content)
                
                dashboard_content += f"""### Financial Report - {metadata.get('report_date', 'Unknown')[:10]}
**Status:** {metadata.get('status', 'ready')}
**File:** `{update_file.name}`

"""
                updates_merged += 1
                
            except Exception as e:
                logger.error(f"Error reading Odoo update {update_file}: {e}")
        
        if not dashboard_sections['odoo_reports']:
            dashboard_content += "*No new financial reports.*\n\n"
        
        dashboard_content += """---

## ⚠️ Urgent Signals (Cloud)

"""
        
        # Add signals
        for signal_file in dashboard_sections['signals']:
            try:
                content = signal_file.read_text()
                metadata = self._parse_frontmatter(content)
                
                severity = metadata.get('severity', 'high')
                severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(severity.lower(), '🟠')
                
                dashboard_content += f"""### {severity_emoji} {signal_file.name}
**Severity:** {severity}
**File:** `{signal_file.name}`

"""
                updates_merged += 1
                
            except Exception as e:
                logger.error(f"Error reading signal {signal_file}: {e}")
        
        if not dashboard_sections['signals']:
            dashboard_content += "*No urgent signals.*\n\n"
        
        dashboard_content += f"""
---

## ⏳ Pending Your Approval

Check `/Pending_Approval/` for items requiring your review.

**Current Pending:** {len(list(self.pending_approval_dir.glob('**/*.md')))}

---

## 🚀 Quick Actions

- Review email drafts → Move to /Pending_Approval/email_drafts/
- Approve social posts → Move to /Pending_Approval/social_posts/
- Process payments → Check /Pending_Approval/payments/

---

*Generated by Platinum Tier Local Orchestrator*
"""
        
        # Write Dashboard.md (Single-Writer: Local only)
        try:
            dashboard_file = self.vault_path / "Dashboard.md"
            dashboard_file.write_text(dashboard_content)
            self.stats['updates_merged'] += updates_merged
            logger.info(f"Dashboard updated with {updates_merged} updates")
        except Exception as e:
            logger.error(f"Failed to write Dashboard.md: {e}")
            self.stats['errors'] += 1
        
        return updates_merged

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from markdown content"""
        import re
        
        match = re.search(r'^---\s*\n(.*?)\n---\s*$', content, re.DOTALL)
        if not match:
            return {}
        
        frontmatter = match.group(1)
        metadata = {}
        
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.startswith('[') and value.endswith(']'):
                    value = [v.strip() for v in value[1:-1].split(',')]
                
                metadata[key] = value
        
        return metadata

    def process_pending_approvals(self) -> int:
        """
        Process items in /Pending_Approval/
        
        Checks for approved/rejected items and executes actions.
        
        Returns:
            Number of approvals processed
        """
        logger.info("Processing pending approvals...")
        
        approvals_processed = 0
        approval_files = list(self.pending_approval_dir.glob("**/*.md"))
        
        for approval_file in approval_files:
            try:
                content = approval_file.read_text()
                metadata = self._parse_frontmatter(content)
                
                # Check if approved
                is_approved = (
                    metadata.get('approved') == True or
                    metadata.get('status', '').lower() == 'approved' or
                    'approved: true' in content.lower()
                )
                
                is_rejected = (
                    metadata.get('approved') == False or
                    metadata.get('status', '').lower() == 'rejected' or
                    'rejected: true' in content.lower()
                )
                
                if is_approved:
                    logger.info(f"Executing approved action: {approval_file.name}")
                    
                    # Execute via MCP
                    if self.mcp_executor:
                        result = self.mcp_executor.execute_from_file(approval_file)
                        
                        if result.get('success'):
                            # Move to Approved/
                            approved_dir = self.vault_path / "Approved"
                            approved_dir.mkdir(parents=True, exist_ok=True)
                            approval_file.rename(approved_dir / approval_file.name)
                            logger.info(f"Action executed successfully: {approval_file.name}")
                            self.stats['approvals_approved'] += 1
                            self.stats['actions_executed'] += 1
                        else:
                            logger.error(f"Action failed: {result.get('error')}")
                            self.stats['errors'] += 1
                    else:
                        logger.error("MCP Executor not available")
                        self.stats['errors'] += 1
                
                elif is_rejected:
                    # Move to Rejected/
                    rejected_dir = self.vault_path / "Rejected"
                    rejected_dir.mkdir(parents=True, exist_ok=True)
                    approval_file.rename(rejected_dir / approval_file.name)
                    logger.info(f"Action rejected: {approval_file.name}")
                    self.stats['approvals_rejected'] += 1
                
                approvals_processed += 1
                
            except Exception as e:
                logger.error(f"Failed to process approval {approval_file}: {e}")
                self.stats['errors'] += 1
        
        self.stats['approvals_processed'] += approvals_processed
        return approvals_processed

    def process_whatsapp_messages(self) -> int:
        """
        Process WhatsApp messages (Local-only).
        
        Returns:
            Number of messages processed
        """
        logger.info("Processing WhatsApp messages...")
        
        if not self.whatsapp_watcher:
            logger.debug("WhatsAppWatcher not available")
            return 0
        
        try:
            messages = self.whatsapp_watcher.check_for_updates()
            
            for message in messages:
                # Create action file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                action_file = self.needs_action_dir / f"WHATSAPP_{message.get('id', timestamp)}.md"
                
                content = f"""---
type: whatsapp_message
from: {message.get('from', 'Unknown')}
timestamp: {message.get('timestamp', datetime.now().isoformat())}
status: pending
---

# WhatsApp Message

**From:** {message.get('from', 'Unknown')}
**Time:** {message.get('timestamp', 'Unknown')}

**Message:**
```
{message.get('text', 'No content')}
```

## Suggested Actions
- [ ] Reply via WhatsApp
- [ ] Create task
- [ ] Forward to email
"""
                
                action_file.write_text(content)
                self.stats['whatsapp_messages'] += 1
                logger.info(f"Created WhatsApp action file: {action_file.name}")
            
            return len(messages)
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp messages: {e}")
            self.stats['errors'] += 1
            return 0

    def check_urgent_signals(self) -> int:
        """
        Check for urgent signals from Cloud.
        
        Returns:
            Number of signals processed
        """
        logger.info("Checking urgent signals...")
        
        signal_files = list((self.signals_dir / "urgent").glob("*.md"))
        signals_processed = 0
        
        for signal_file in signal_files:
            try:
                content = signal_file.read_text()
                metadata = self._parse_frontmatter(content)
                
                severity = metadata.get('severity', 'high')
                
                # Alert user immediately
                print(f"\n{'🔴' if severity == 'critical' else '🟠'} URGENT SIGNAL: {signal_file.name}")
                print(f"Severity: {severity}")
                print(f"Content preview: {content[:200]}...")
                print()
                
                self.stats['signals_received'] += 1
                signals_processed += 1
                
            except Exception as e:
                logger.error(f"Error reading signal {signal_file}: {e}")
                self.stats['errors'] += 1
        
        return signals_processed

    def write_health_status(self):
        """Write current health status to logs"""
        try:
            health_file = self.logs_dir / "health_status.md"
            
            uptime_seconds = (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds()
            uptime_hours = uptime_seconds / 3600
            
            health_content = f"""---
last_check: {datetime.now().isoformat()}
status: {'healthy' if self.stats['errors'] < 5 else 'degraded'}
uptime_hours: {uptime_hours:.2f}
---

# Local Agent Health Status

## Statistics
- Updates Merged: {self.stats['updates_merged']}
- Approvals Processed: {self.stats['approvals_processed']}
  - Approved: {self.stats['approvals_approved']}
  - Rejected: {self.stats['approvals_rejected']}
- Actions Executed: {self.stats['actions_executed']}
- WhatsApp Messages: {self.stats['whatsapp_messages']}
- Signals Received: {self.stats['signals_received']}
- Errors: {self.stats['errors']}

## Status
{'✅ All systems operational.' if self.stats['errors'] < 5 else '⚠️ Elevated error rate. Check logs.'}
"""
            
            health_file.write_text(health_content)
            
        except Exception as e:
            logger.error(f"Failed to write health status: {e}")

    def run(self):
        """Main Local Agent loop"""
        logger.info("Local Orchestrator started (Approval + Execution Mode)")
        logger.info(f"Monitoring folders: Updates/, Signals/, Pending_Approval/")
        logger.info("Security: Full credentials access (Local only)")
        
        cycle_count = 0
        
        while True:
            cycle_count += 1
            logger.info(f"=== Cycle {cycle_count} ===")
            
            try:
                # Merge cloud updates to dashboard (every cycle)
                updates_merged = self.merge_updates_to_dashboard()
                logger.info(f"Merged {updates_merged} updates")
                
                # Process pending approvals (every cycle)
                approvals_processed = self.process_pending_approvals()
                logger.info(f"Processed {approvals_processed} approvals")
                
                # Process WhatsApp messages (every 30 seconds)
                if cycle_count % 2 == 0:
                    whatsapp_messages = self.process_whatsapp_messages()
                    logger.info(f"Processed {whatsapp_messages} WhatsApp messages")
                
                # Check urgent signals (every cycle)
                signals_received = self.check_urgent_signals()
                logger.info(f"Received {signals_received} signals")
                
                # Write health status (every 5 cycles)
                if cycle_count % 5 == 0:
                    self.write_health_status()
                
                # Wait before next cycle (15 seconds)
                logger.info(f"Cycle {cycle_count} complete. Sleeping for 15 seconds...")
                time.sleep(15)
                
            except KeyboardInterrupt:
                logger.info("Local Orchestrator shutting down (user interrupt)")
                self.write_health_status()
                break
            except Exception as e:
                logger.error(f"Local orchestrator error: {e}")
                self.stats['errors'] += 1
                time.sleep(30)


def main():
    """Entry point for Local Orchestrator"""
    print("=" * 60)
    print("PLATINUM TIER - LOCAL ORCHESTRATOR")
    print("=" * 60)
    print()
    print("🤖 Starting Local Agent (Approval + Execution Mode)")
    print()
    print("Capabilities:")
    print("  ✅ Merge Cloud updates to Dashboard.md")
    print("  ✅ Process pending approvals")
    print("  ✅ Execute actions via MCP")
    print("  ✅ WhatsApp messaging (Local-only)")
    print("  ✅ Check urgent signals")
    print()
    print("Security:")
    print("  🔒 Exclusive access to:")
    print("    - WhatsApp session")
    print("    - Email send credentials")
    print("    - Social media posting credentials")
    print("    - Banking/payment credentials")
    print()
    print("=" * 60)
    print()
    
    orchestrator = LocalOrchestrator()
    orchestrator.run()


if __name__ == "__main__":
    main()
