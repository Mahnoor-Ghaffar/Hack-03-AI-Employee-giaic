"""
Platinum Tier Cloud Orchestrator
Draft-only operations, 24/7 monitoring

This orchestrator runs on a Cloud VM and performs:
- Email triage (read-only, creates drafts)
- Social media monitoring (read-only, generates post drafts)
- Odoo financial reports (read-only, creates reports)
- Writes all outputs to /Updates/ folder for Git sync to Local

SECURITY: This agent NEVER:
- Sends emails
- Posts to social media
- Accesses WhatsApp
- Executes payments
- Accesses banking credentials
- Modifies Dashboard.md

Usage:
    python orchestrator_cloud.py
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import os

from log_manager import setup_logging
from skills.vault_skills import get_vault

# Setup logging
logger = setup_logging(
    log_file="logs/cloud_agent.log",
    logger_name="cloud_orchestrator"
)

# Import watchers (read-only mode for cloud)
try:
    from gmail_watcher import GmailWatcher
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    logger.warning("GmailWatcher not available - email triage disabled")

try:
    from facebook_watcher import FacebookWatcher
    FACEBOOK_AVAILABLE = True
except ImportError:
    FACEBOOK_AVAILABLE = False
    logger.warning("FacebookWatcher not available - Facebook monitoring disabled")

try:
    from twitter_watcher import TwitterWatcher
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False
    logger.warning("TwitterWatcher not available - Twitter monitoring disabled")

try:
    from scripts.odoo_mcp_server import OdooMCPServer
    ODOO_AVAILABLE = True
except ImportError:
    ODOO_AVAILABLE = False
    logger.warning("OdooMCPServer not available - Odoo reports disabled")


class CloudOrchestrator:
    """
    Platinum Tier Cloud Orchestrator
    
    Runs 24/7 on cloud VM, performing draft-only operations.
    All outputs written to /Updates/ for Git sync to Local agent.
    """

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        """
        Initialize Cloud Orchestrator.
        
        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = Path(vault_path)
        self.vault = get_vault()
        
        # Platinum Tier folders
        self.updates_dir = self.vault_path / "Updates"
        self.signals_dir = self.vault_path / "Signals"
        self.in_progress_dir = self.vault_path / "In_Progress" / "cloud_agent"
        self.logs_dir = self.vault_path / "Logs"
        
        # Ensure directories exist
        for dir_path in [self.updates_dir, self.signals_dir, self.in_progress_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize watchers (read-only credentials for cloud)
        self.gmail_watcher = None
        self.facebook_watcher = None
        self.twitter_watcher = None
        self.odoo_client = None
        
        self._initialize_watchers()
        
        # Statistics
        self.stats = {
            'emails_processed': 0,
            'drafts_created': 0,
            'reports_generated': 0,
            'signals_sent': 0,
            'start_time': datetime.now().isoformat(),
            'errors': 0
        }
        
        logger.info("Cloud Orchestrator initialized (Draft-Only Mode)")

    def _initialize_watchers(self):
        """Initialize watchers with read-only credentials"""
        
        # Gmail Watcher (read-only token for cloud)
        if GMAIL_AVAILABLE:
            try:
                # Cloud uses read-only Gmail token
                credentials_path = os.getenv('GMAIL_READ_CREDENTIALS', 'credentials/gmail_read.json')
                if Path(credentials_path).exists():
                    self.gmail_watcher = GmailWatcher(
                        vault_path=str(self.vault_path),
                        credentials_path=credentials_path
                    )
                    logger.info("GmailWatcher initialized (read-only)")
                else:
                    logger.warning(f"Gmail credentials not found at {credentials_path}")
            except Exception as e:
                logger.error(f"Failed to initialize GmailWatcher: {e}")
        
        # Facebook Watcher
        if FACEBOOK_AVAILABLE:
            try:
                facebook_pages = os.getenv('FACEBOOK_PAGES', '[]').split(',')
                instagram_accounts = os.getenv('INSTAGRAM_ACCOUNTS', '[]').split(',')
                
                self.facebook_watcher = FacebookWatcher(
                    vault_path=str(self.vault_path),
                    facebook_pages=[p.strip() for p in facebook_pages if p.strip()],
                    instagram_accounts=[a.strip() for a in instagram_accounts if a.strip()],
                    check_interval=600
                )
                logger.info("FacebookWatcher initialized (read-only)")
            except Exception as e:
                logger.error(f"Failed to initialize FacebookWatcher: {e}")
        
        # Twitter Watcher
        if TWITTER_AVAILABLE:
            try:
                username = os.getenv('TWITTER_USERNAME')
                hashtags = os.getenv('TWITTER_HASHTAGS', 'AI,Automation').split(',')
                
                self.twitter_watcher = TwitterWatcher(
                    vault_path=str(self.vault_path),
                    username=username,
                    hashtags=[h.strip() for h in hashtags if h.strip()],
                    check_interval=300
                )
                logger.info("TwitterWatcher initialized (read-only)")
            except Exception as e:
                logger.error(f"Failed to initialize TwitterWatcher: {e}")
        
        # Odoo Client (read-only + draft create for cloud)
        if ODOO_AVAILABLE:
            try:
                self.odoo_client = OdooMCPServer(
                    url=os.getenv('ODOO_URL', 'http://localhost:8069'),
                    db=os.getenv('ODOO_DB', 'odoo_db'),
                    username=os.getenv('ODOO_USERNAME', 'ai_employee'),
                    password=os.getenv('ODOO_PASSWORD', '')
                )
                logger.info("OdooMCPServer initialized (read-only + draft)")
            except Exception as e:
                logger.error(f"Failed to initialize OdooMCPServer: {e}")

    def process_email_triage(self) -> int:
        """
        Read Gmail, analyze emails, create triage drafts in /Updates/email_triage/
        
        Returns:
            Number of emails processed
        """
        logger.info("Processing email triage...")
        
        if not self.gmail_watcher:
            logger.debug("GmailWatcher not available, skipping email triage")
            return 0
        
        try:
            # Get new emails (read-only)
            new_emails = self.gmail_watcher.check_for_updates()
            
            for email in new_emails:
                try:
                    # Get full email details
                    msg = self.gmail_watcher.service.users().messages().get(
                        userId='me', id=email['id']
                    ).execute()
                    
                    # Extract headers
                    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                    
                    # Create email triage draft
                    draft_file = self.updates_dir / "email_triage" / f"email_{email['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    
                    # Generate AI-style draft reply (simplified - Claude would do this in production)
                    subject = headers.get('Subject', 'No Subject')
                    from_email = headers.get('From', 'Unknown')
                    snippet = msg.get('snippet', 'No content available')
                    
                    draft_content = f"""---
type: email_triage
email_id: {email['id']}
from: {from_email}
subject: {subject}
received: {datetime.now().isoformat()}
priority: {self._detect_priority(subject, snippet)}
draft_created: {datetime.now().isoformat()}
status: draft_ready
---

# Email Triage Summary

**From:** {from_email}
**Subject:** {subject}
**Priority:** {self._detect_priority(subject, snippet)}

## Summary
{snippet}

## Suggested Action
{self._suggest_action(subject, snippet)}

## Draft Reply
```
Dear Sender,

Thank you for your email regarding "{subject}".

[AI-generated response based on email content - requires Claude analysis]

Best regards,
AI Employee
```

## To Approve
1. Review draft reply
2. Move to /Pending_Approval/email_drafts/
3. Local agent will send after human approval
"""
                    
                    draft_file.write_text(draft_content)
                    self.stats['emails_processed'] += 1
                    self.stats['drafts_created'] += 1
                    logger.info(f"Created email triage draft: {draft_file.name}")
                    
                except Exception as e:
                    logger.error(f"Error processing email {email['id']}: {e}")
                    self.stats['errors'] += 1
            
            return len(new_emails)
            
        except Exception as e:
            logger.error(f"Error in email triage: {e}")
            self.stats['errors'] += 1
            return 0

    def _detect_priority(self, subject: str, snippet: str) -> str:
        """Detect email priority from content"""
        subject_lower = subject.lower()
        snippet_lower = snippet.lower()
        
        urgent_keywords = ['urgent', 'asap', 'emergency', 'immediate', 'important']
        high_keywords = ['invoice', 'payment', 'deadline', 'review', 'approval']
        
        for keyword in urgent_keywords:
            if keyword in subject_lower or keyword in snippet_lower:
                return 'urgent'
        
        for keyword in high_keywords:
            if keyword in subject_lower or keyword in snippet_lower:
                return 'high'
        
        return 'normal'

    def _suggest_action(self, subject: str, snippet: str) -> str:
        """Suggest action based on email content"""
        subject_lower = subject.lower()
        snippet_lower = snippet.lower()
        
        if 'invoice' in subject_lower or 'payment' in snippet_lower:
            return "Review for accounting processing. May require Odoo invoice creation."
        elif 'meeting' in subject_lower or 'schedule' in subject_lower:
            return "Check calendar availability and draft scheduling response."
        elif 'question' in subject_lower or 'help' in snippet_lower:
            return "Provide helpful response or escalate to human."
        elif 'feedback' in subject_lower or 'review' in subject_lower:
            return "Acknowledge feedback and consider for service improvement."
        else:
            return "Review content and determine appropriate response."

    def generate_social_drafts(self) -> int:
        """
        Monitor social media, generate post drafts in /Updates/social_drafts/
        
        Returns:
            Number of drafts created
        """
        logger.info("Generating social media drafts...")
        
        drafts_created = 0
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate Facebook draft
        if self.facebook_watcher:
            try:
                fb_draft_file = self.updates_dir / "social_drafts" / f"facebook_draft_{timestamp}.md"
                
                fb_draft = f"""---
type: social_post_draft
platform: facebook
draft_created: {datetime.now().isoformat()}
status: draft_ready
---

# Facebook Post Draft

**Suggested Content:**
```
🚀 Exciting updates from our team! 

We're continuously working to improve our AI-powered automation solutions. Stay tuned for more innovations!

#AI #Automation #Innovation #Technology
```

**Suggested Hashtags:**
#AI #Automation #Business #Technology #Innovation

**Best Time to Post:**
Based on engagement patterns: Weekdays 1-3 PM or 7-8 PM

## To Approve
1. Review and edit content
2. Move to /Pending_Approval/social_posts/
3. Local agent will post after human approval
"""
                
                fb_draft_file.write_text(fb_draft)
                drafts_created += 1
                logger.info(f"Created Facebook draft: {fb_draft_file.name}")
                
            except Exception as e:
                logger.error(f"Error creating Facebook draft: {e}")
                self.stats['errors'] += 1
        
        # Generate Twitter draft
        if self.twitter_watcher:
            try:
                twitter_draft_file = self.updates_dir / "social_drafts" / f"twitter_draft_{timestamp}.md"
                
                twitter_draft = f"""---
type: social_post_draft
platform: twitter
draft_created: {datetime.now().isoformat()}
status: draft_ready
---

# Twitter Post Draft

**Suggested Tweet:**
```
Just completed another successful automation task with our AI Employee! 🤖✨

Productivity is up 85% this week. #AI #Automation #Productivity
```

**Thread Option:**
1/3 Building an AI Employee isn't just about automation—it's about reclaiming time for creative work.

2/3 Our Platinum Tier system now handles email triage, social media drafting, and financial reporting 24/7.

3/3 The future of work is here, and it's collaborative. Human + AI > AI alone.

## To Approve
1. Review and edit content
2. Move to /Pending_Approval/social_posts/
3. Local agent will post after human approval
"""
                
                twitter_draft_file.write_text(twitter_draft)
                drafts_created += 1
                logger.info(f"Created Twitter draft: {twitter_draft_file.name}")
                
            except Exception as e:
                logger.error(f"Error creating Twitter draft: {e}")
                self.stats['errors'] += 1
        
        self.stats['drafts_created'] += drafts_created
        return drafts_created

    def sync_odoo_reports(self) -> int:
        """
        Generate Odoo financial reports in /Updates/odoo_reports/
        
        Returns:
            Number of reports generated
        """
        logger.info("Syncing Odoo reports...")
        
        if not self.odoo_client:
            logger.debug("Odoo client not available, skipping reports")
            return 0
        
        try:
            # Get financial data (read-only)
            report_file = self.updates_dir / "odoo_reports" / f"financial_{datetime.now().strftime('%Y%m%d')}.md"
            
            # Try to get financial report
            try:
                financial_report = self.odoo_client.get_financial_report(report_type='profit_loss')
                report_content = f"""---
type: odoo_financial_report
report_date: {datetime.now().isoformat()}
period: current_month
status: ready
---

# Financial Report

## Profit & Loss Summary

{financial_report.get('summary', 'No data available')}

## Key Metrics
- Revenue: ${financial_report.get('revenue', 0):,.2f}
- Expenses: ${financial_report.get('expenses', 0):,.2f}
- Net Profit: ${financial_report.get('net_profit', 0):,.2f}

## Alerts
{self._analyze_financials(financial_report)}
"""
            except Exception as e:
                logger.warning(f"Could not fetch Odoo report: {e}")
                report_content = f"""---
type: odoo_financial_report
report_date: {datetime.now().isoformat()}
period: current_month
status: error
---

# Financial Report

**Status:** Could not connect to Odoo ERP

Please check Odoo service status and credentials.
"""
            
            report_file.write_text(report_content)
            self.stats['reports_generated'] += 1
            logger.info(f"Created Odoo financial report: {report_file.name}")
            
            return 1
            
        except Exception as e:
            logger.error(f"Error syncing Odoo reports: {e}")
            self.stats['errors'] += 1
            return 0

    def _analyze_financials(self, report: Dict[str, Any]) -> str:
        """Analyze financial report for alerts"""
        alerts = []
        
        revenue = report.get('revenue', 0)
        expenses = report.get('expenses', 0)
        net_profit = report.get('net_profit', 0)
        
        if expenses > revenue:
            alerts.append("⚠️ Expenses exceed revenue this period.")
        
        if net_profit < 0:
            alerts.append("⚠️ Net loss detected. Review expenses.")
        
        if not alerts:
            return "✅ Financials appear healthy."
        
        return "\n".join(alerts)

    def send_urgent_signal(self, message: str, severity: str = "high") -> bool:
        """
        Send urgent signal to Local agent via /Signals/urgent/
        
        Args:
            message: Signal message
            severity: Severity level (low, medium, high, critical)
        
        Returns:
            True if signal sent successfully
        """
        try:
            signal_file = self.signals_dir / "urgent" / f"SIGNAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            signal_file.parent.mkdir(parents=True, exist_ok=True)
            
            signal_content = f"""---
type: urgent_signal
severity: {severity}
timestamp: {datetime.now().isoformat()}
---

# Urgent Signal

{message}

**Action Required:** Please review immediately.
"""
            
            signal_file.write_text(signal_content)
            self.stats['signals_sent'] += 1
            logger.warning(f"Sent urgent signal: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send urgent signal: {e}")
            self.stats['errors'] += 1
            return False

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

# Cloud Agent Health Status

## Statistics
- Emails Processed: {self.stats['emails_processed']}
- Drafts Created: {self.stats['drafts_created']}
- Reports Generated: {self.stats['reports_generated']}
- Signals Sent: {self.stats['signals_sent']}
- Errors: {self.stats['errors']}

## Status
{'✅ All systems operational.' if self.stats['errors'] < 5 else '⚠️ Elevated error rate. Check logs.'}
"""
            
            health_file.write_text(health_content)
            
        except Exception as e:
            logger.error(f"Failed to write health status: {e}")

    def run(self):
        """Main Cloud Agent loop"""
        logger.info("Cloud Orchestrator started (Draft-Only Mode)")
        logger.info(f"Monitoring folders: Updates/, Signals/")
        logger.info("Security: Draft-only operations, no send/post capabilities")
        
        # Send startup signal
        self.send_urgent_signal(
            "Cloud Agent started successfully. Beginning 24/7 monitoring.",
            severity="low"
        )
        
        cycle_count = 0
        
        while True:
            cycle_count += 1
            logger.info(f"=== Cycle {cycle_count} ===")
            
            try:
                # Email triage (every 5 minutes)
                emails_processed = self.process_email_triage()
                logger.info(f"Processed {emails_processed} emails")
                
                # Social media drafts (every 15 minutes)
                if cycle_count % 3 == 0:
                    drafts_created = self.generate_social_drafts()
                    logger.info(f"Created {drafts_created} social drafts")
                
                # Odoo reports (every hour)
                if cycle_count % 12 == 0:
                    reports_generated = self.sync_odoo_reports()
                    logger.info(f"Generated {reports_generated} reports")
                
                # Write health status
                self.write_health_status()
                
                # Wait before next cycle (5 minutes)
                logger.info(f"Cycle {cycle_count} complete. Sleeping for 5 minutes...")
                time.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("Cloud Orchestrator shutting down (user interrupt)")
                self.send_urgent_signal(
                    "Cloud Agent shutting down. Manual restart required.",
                    severity="high"
                )
                break
            except Exception as e:
                logger.error(f"Cloud orchestrator error: {e}")
                self.stats['errors'] += 1
                self.send_urgent_signal(f"Cloud Agent error: {e}")
                time.sleep(60)


def main():
    """Entry point for Cloud Orchestrator"""
    print("=" * 60)
    print("PLATINUM TIER - CLOUD ORCHESTRATOR")
    print("=" * 60)
    print()
    print("🤖 Starting Cloud Agent (Draft-Only Mode)")
    print()
    print("Capabilities:")
    print("  ✅ Email triage and draft replies")
    print("  ✅ Social media post drafts")
    print("  ✅ Odoo financial reports")
    print("  ✅ Urgent signal alerts")
    print()
    print("Security:")
    print("  ❌ NO email sending")
    print("  ❌ NO social media posting")
    print("  ❌ NO WhatsApp access")
    print("  ❌ NO payment execution")
    print("  ❌ NO Dashboard.md modification")
    print()
    print("=" * 60)
    print()
    
    orchestrator = CloudOrchestrator()
    orchestrator.run()


if __name__ == "__main__":
    main()
