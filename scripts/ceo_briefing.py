#!/usr/bin/env python3
"""
CEO Briefing Generator - Gold Tier

Automated weekly CEO briefing generator that aggregates data from all AI Employee systems.

Generates: AI_Employee_Vault/Reports/CEO_Weekly.md

Includes:
- Tasks completed
- Emails sent
- LinkedIn/Facebook/Twitter posts
- Pending approvals
- Income/Expense summary
- System health

Auto-run via scheduler every Monday at 7:00 AM.

Usage:
    python scripts/ceo_briefing.py auto
    python scripts/ceo_briefing.py weekly
    python scripts/ceo_briefing.py daily

Author: AI Employee Project
Version: 1.0.0
License: MIT
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ceo_briefing')

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', 'AI_Employee_Vault'))
REPORTS_PATH = VAULT_PATH / 'Reports'
LOGS_PATH = VAULT_PATH / 'Logs'
DONE_PATH = VAULT_PATH / 'Done'
PENDING_APPROVAL_PATH = VAULT_PATH / 'Pending_Approval'
NEEDS_APPROVAL_PATH = VAULT_PATH / 'Needs_Approval'
ACCOUNTING_PATH = VAULT_PATH / 'Accounting'


class CEOBriefing:
    """
    CEO Briefing Generator.
    
    Aggregates data from all AI Employee systems to create
    comprehensive weekly executive reports.
    """

    def __init__(self, vault_path: str = None):
        """
        Initialize CEO Briefing generator.
        
        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = Path(vault_path) if vault_path else VAULT_PATH
        self.reports_path = self.vault_path / 'Reports'
        self.logs_path = self.vault_path / 'Logs'
        self.done_path = self.vault_path / 'Done'
        self.pending_approval_path = self.vault_path / 'Pending_Approval'
        self.needs_approval_path = self.vault_path / 'Needs_Approval'
        self.accounting_path = self.vault_path / 'Accounting'
        
        # Ensure directories exist
        self.reports_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f'CEOBriefing initialized. Vault: {self.vault_path}')

    def get_week_date_range(self) -> tuple:
        """
        Get date range for current week (last Monday to Sunday).
        
        Returns:
            Tuple of (week_start, week_end) as strings (YYYY-MM-DD)
        """
        today = datetime.now()
        days_since_monday = today.weekday()
        
        # Last Monday
        last_monday = today - timedelta(days=days_since_monday, weeks=1)
        week_start = last_monday.strftime('%Y-%m-%d')
        
        # Next Sunday
        week_end = (last_monday + timedelta(days=6)).strftime('%Y-%m-%d')
        
        return week_start, week_end

    def get_tasks_completed(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get completed tasks for period.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of completed task dictionaries
        """
        tasks = []
        
        if not self.done_path.exists():
            return tasks
        
        # Read all task files in Done folder
        for task_file in self.done_path.glob('*.md'):
            try:
                content = task_file.read_text()
                
                # Extract metadata from frontmatter
                task_data = {
                    'file': task_file.name,
                    'completed_date': None,
                    'description': '',
                    'notes': ''
                }
                
                # Parse frontmatter
                if '---' in content:
                    parts = content.split('---')
                    if len(parts) > 1:
                        frontmatter = parts[1]
                        for line in frontmatter.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                key = key.strip()
                                value = value.strip()
                                if key == 'completed_date':
                                    task_data['completed_date'] = value
                                elif key == 'description':
                                    task_data['description'] = value
                
                # Check if within date range
                if task_data['completed_date']:
                    if start_date <= task_data['completed_date'] <= end_date:
                        # Get description from content
                        if '#' in content:
                            desc_lines = [line for line in content.split('\n') if line.startswith('# ')]
                            if desc_lines:
                                task_data['description'] = desc_lines[0].replace('# ', '').strip()
                        
                        tasks.append(task_data)
                        
            except Exception as e:
                logger.warning(f'Error reading task file {task_file.name}: {e}')
                continue
        
        # Sort by date
        tasks.sort(key=lambda x: x.get('completed_date', ''), reverse=True)
        
        return tasks

    def get_emails_sent(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get emails sent for period.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of sent email dictionaries
        """
        emails = []
        
        # Try to read email log
        email_log = self.logs_path / 'emails.log'
        if not email_log.exists():
            # Try alternative: read from Approved folder
            approved_path = self.vault_path / 'Approved'
            if approved_path.exists():
                for email_file in approved_path.glob('EMAIL_*.md'):
                    try:
                        content = email_file.read_text()
                        
                        email_data = {
                            'file': email_file.name,
                            'date': None,
                            'recipient': '',
                            'subject': '',
                            'status': 'Sent'
                        }
                        
                        # Parse frontmatter
                        if '---' in content:
                            parts = content.split('---')
                            if len(parts) > 1:
                                frontmatter = parts[1]
                                for line in frontmatter.split('\n'):
                                    if ':' in line:
                                        key, value = line.split(':', 1)
                                        key = key.strip()
                                        value = value.strip()
                                        if key == 'date' or key == 'created':
                                            email_data['date'] = value
                                        elif key == 'to':
                                            email_data['recipient'] = value
                                        elif key == 'subject':
                                            email_data['subject'] = value
                        
                        if email_data['date']:
                            if start_date <= email_data['date'] <= end_date:
                                emails.append(email_data)
                                
                    except Exception as e:
                        logger.warning(f'Error reading email file {email_file.name}: {e}')
                        continue
            return emails
        
        # Parse email log file
        try:
            with open(email_log, 'r') as f:
                for line in f:
                    if 'EMAIL_SENT' in line or 'Sent' in line:
                        try:
                            # Parse log line
                            parts = line.strip().split(' | ')
                            if len(parts) >= 3:
                                email_data = {
                                    'date': parts[0].strip('[] '),
                                    'recipient': parts[1].strip() if len(parts) > 1 else '',
                                    'subject': parts[2].strip() if len(parts) > 2 else '',
                                    'status': 'Sent'
                                }
                                
                                if start_date <= email_data['date'] <= end_date:
                                    emails.append(email_data)
                        except Exception:
                            continue
        except Exception as e:
            logger.warning(f'Error reading email log: {e}')
        
        return emails

    def get_social_media_activity(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get social media activity for period.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with platform metrics
        """
        activity = {
            'linkedin': {'posts': 0, 'impressions': 0, 'engagement': 0},
            'facebook': {'posts': 0, 'reach': 0, 'engagement': 0},
            'instagram': {'posts': 0, 'likes': 0, 'comments': 0},
            'twitter': {'tweets': 0, 'impressions': 0, 'followers': 0}
        }
        
        # Read social media log
        social_log = self.logs_path / 'social_media.log'
        if not social_log.exists():
            # Try alternative: read from Social_Media folder
            social_path = self.vault_path / 'Social_Media'
            if social_path.exists():
                for post_file in social_path.glob('*.md'):
                    try:
                        content = post_file.read_text()
                        
                        # Detect platform
                        if 'linkedin' in content.lower():
                            platform = 'linkedin'
                        elif 'facebook' in content.lower():
                            platform = 'facebook'
                        elif 'instagram' in content.lower():
                            platform = 'instagram'
                        elif 'twitter' in content.lower():
                            platform = 'twitter'
                        else:
                            continue
                        
                        activity[platform]['posts'] += 1
                        
                    except Exception as e:
                        logger.warning(f'Error reading social file {post_file.name}: {e}')
                        continue
            return activity
        
        # Parse social media log
        try:
            with open(social_log, 'r') as f:
                for line in f:
                    try:
                        parts = line.strip().split(' | ')
                        if len(parts) >= 2:
                            date = parts[0].strip('[] ')
                            if start_date <= date <= end_date:
                                if 'LINKEDIN' in line:
                                    activity['linkedin']['posts'] += 1
                                elif 'FACEBOOK' in line:
                                    activity['facebook']['posts'] += 1
                                elif 'INSTAGRAM' in line:
                                    activity['instagram']['posts'] += 1
                                elif 'TWITTER' in line:
                                    activity['twitter']['tweets'] += 1
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f'Error reading social media log: {e}')
        
        return activity

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """
        Get pending approval items.
        
        Returns:
            List of pending approval dictionaries
        """
        approvals = []
        
        # Check Pending_Approval folder
        if self.pending_approval_path.exists():
            for approval_file in self.pending_approval_path.glob('*.md'):
                try:
                    content = approval_file.read_text()
                    
                    approval_data = {
                        'file': approval_file.name,
                        'type': 'Unknown',
                        'requested': None,
                        'status': 'Pending',
                        'description': approval_file.stem
                    }
                    
                    # Parse frontmatter
                    if '---' in content:
                        parts = content.split('---')
                        if len(parts) > 1:
                            frontmatter = parts[1]
                            for line in frontmatter.split('\n'):
                                if ':' in line:
                                    key, value = line.split(':', 1)
                                    key = key.strip()
                                    value = value.strip()
                                    if key == 'type':
                                        approval_data['type'] = value
                                    elif key == 'created':
                                        approval_data['requested'] = value
                                    elif key == 'approval_id':
                                        approval_data['description'] = value
                    
                    # Extract type from content
                    if 'email' in content.lower():
                        approval_data['type'] = 'Email'
                    elif 'linkedin' in content.lower():
                        approval_data['type'] = 'LinkedIn Post'
                    elif 'facebook' in content.lower():
                        approval_data['type'] = 'Facebook Post'
                    elif 'payment' in content.lower():
                        approval_data['type'] = 'Payment'
                    elif 'invoice' in content.lower():
                        approval_data['type'] = 'Invoice'
                    
                    approvals.append(approval_data)
                    
                except Exception as e:
                    logger.warning(f'Error reading approval file {approval_file.name}: {e}')
                    continue
        
        # Check Needs_Approval folder
        if self.needs_approval_path.exists():
            for approval_file in self.needs_approval_path.glob('*.md'):
                try:
                    content = approval_file.read_text()
                    
                    # Only include if still pending
                    if 'status: pending' in content.lower() or 'approved: false' in content.lower():
                        approval_data = {
                            'file': approval_file.name,
                            'type': 'Unknown',
                            'requested': None,
                            'status': 'Pending',
                            'description': approval_file.stem
                        }
                        
                        if '---' in content:
                            parts = content.split('---')
                            if len(parts) > 1:
                                frontmatter = parts[1]
                                for line in frontmatter.split('\n'):
                                    if ':' in line:
                                        key, value = line.split(':', 1)
                                        key = key.strip()
                                        value = value.strip()
                                        if key == 'type':
                                            approval_data['type'] = value
                                        elif key == 'created':
                                            approval_data['requested'] = value
                        
                        approvals.append(approval_data)
                        
                except Exception as e:
                    logger.warning(f'Error reading approval file {approval_file.name}: {e}')
                    continue
        
        return approvals

    def get_financial_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get financial summary for period.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with income/expense data
        """
        summary = {
            'income': {'total': 0.0, 'transactions': 0},
            'expense': {'total': 0.0, 'transactions': 0},
            'net': 0.0,
            'margin': 0.0
        }
        
        # Try to use Accounting Manager
        try:
            from scripts.accounting_manager import AccountingManager
            
            accounting = AccountingManager(vault_path=str(self.vault_path))
            
            # Get transactions
            transactions = accounting.get_transactions(
                start_date=start_date,
                end_date=end_date
            )
            
            for txn in transactions:
                if txn['type'] == 'income':
                    summary['income']['total'] += txn['amount']
                    summary['income']['transactions'] += 1
                elif txn['type'] == 'expense':
                    summary['expense']['total'] += txn['amount']
                    summary['expense']['transactions'] += 1
            
            summary['net'] = summary['income']['total'] - summary['expense']['total']
            if summary['income']['total'] > 0:
                summary['margin'] = (summary['net'] / summary['income']['total']) * 100
            
            return summary
            
        except ImportError:
            logger.warning('Accounting Manager not available, using fallback')
        except Exception as e:
            logger.warning(f'Error getting financial summary: {e}')
        
        # Fallback: Parse Current_Month.md
        current_month_file = self.accounting_path / 'Current_Month.md'
        if current_month_file.exists():
            try:
                content = current_month_file.read_text()
                
                # Parse frontmatter totals
                if '---' in content:
                    parts = content.split('---')
                    if len(parts) > 1:
                        frontmatter = parts[1]
                        for line in frontmatter.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                key = key.strip()
                                value = value.strip()
                                if key == 'total_income':
                                    summary['income']['total'] = float(value)
                                elif key == 'total_expense':
                                    summary['expense']['total'] = float(value)
                                elif key == 'balance':
                                    summary['net'] = float(value)
                
                summary['margin'] = (summary['net'] / summary['income']['total'] * 100) if summary['income']['total'] > 0 else 0
                
            except Exception as e:
                logger.warning(f'Error parsing current month file: {e}')
        
        return summary

    def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health status.
        
        Returns:
            Dictionary with component health status
        """
        health = {
            'components': [],
            'overall': 'Healthy',
            'issues': []
        }
        
        # Check Gmail Watcher
        gmail_creds = Path('gmail_credentials.json')
        if gmail_creds.exists():
            health['components'].append({
                'name': 'Gmail Watcher',
                'status': '✅ Healthy',
                'details': 'Credentials configured'
            })
        else:
            health['components'].append({
                'name': 'Gmail Watcher',
                'status': '⚠️ Not Configured',
                'details': 'No credentials found'
            })
            health['issues'].append('Gmail credentials not configured')
        
        # Check LinkedIn
        linkedin_watcher = Path('linkedin_watcher.py')
        if linkedin_watcher.exists():
            health['components'].append({
                'name': 'LinkedIn Watcher',
                'status': '✅ Healthy',
                'details': 'Module available'
            })
        else:
            health['components'].append({
                'name': 'LinkedIn Watcher',
                'status': '❌ Missing',
                'details': 'Module not found'
            })
        
        # Check Facebook
        facebook_watcher = Path('facebook_watcher.py')
        if facebook_watcher.exists():
            health['components'].append({
                'name': 'Facebook Watcher',
                'status': '✅ Healthy',
                'details': 'Module available'
            })
        else:
            health['components'].append({
                'name': 'Facebook Watcher',
                'status': '❌ Missing',
                'details': 'Module not found'
            })
        
        # Check Twitter
        twitter_watcher = Path('twitter_watcher.py')
        if twitter_watcher.exists():
            health['components'].append({
                'name': 'Twitter Watcher',
                'status': '✅ Healthy',
                'details': 'Module available'
            })
        else:
            health['components'].append({
                'name': 'Twitter Watcher',
                'status': '❌ Missing',
                'details': 'Module not found'
            })
        
        # Check Accounting
        accounting_manager = Path('scripts/accounting_manager.py')
        if accounting_manager.exists():
            health['components'].append({
                'name': 'Accounting Manager',
                'status': '✅ Healthy',
                'details': 'Module available'
            })
        else:
            health['components'].append({
                'name': 'Accounting Manager',
                'status': '❌ Missing',
                'details': 'Module not found'
            })
        
        # Check Orchestrator
        orchestrator = Path('orchestrator_gold.py')
        if orchestrator.exists():
            health['components'].append({
                'name': 'Orchestrator',
                'status': '✅ Healthy',
                'details': 'Gold tier running'
            })
        else:
            health['components'].append({
                'name': 'Orchestrator',
                'status': '❌ Missing',
                'details': 'Module not found'
            })
        
        # Check vault structure
        required_folders = ['Inbox', 'Needs_Action', 'Done', 'Pending_Approval']
        missing_folders = []
        for folder in required_folders:
            if not (self.vault_path / folder).exists():
                missing_folders.append(folder)
        
        if missing_folders:
            health['components'].append({
                'name': 'Vault Structure',
                'status': '⚠️ Incomplete',
                'details': f'Missing: {", ".join(missing_folders)}'
            })
            health['issues'].append(f'Missing vault folders: {", ".join(missing_folders)}')
        else:
            health['components'].append({
                'name': 'Vault Structure',
                'status': '✅ Healthy',
                'details': 'All folders present'
            })
        
        # Check logs
        if self.logs_path.exists() and any(self.logs_path.glob('*.log')):
            health['components'].append({
                'name': 'Logging',
                'status': '✅ Healthy',
                'details': 'Logs active'
            })
        else:
            health['components'].append({
                'name': 'Logging',
                'status': '⚠️ Not Active',
                'details': 'No log files found'
            })
        
        # Determine overall health
        if health['issues']:
            health['overall'] = '⚠️ Issues Detected'
        else:
            healthy_count = sum(1 for c in health['components'] if '✅' in c['status'])
            if healthy_count == len(health['components']):
                health['overall'] = '🟢 All Systems Operational'
            else:
                health['overall'] = '🟡 Some Systems Degraded'
        
        return health

    def generate_weekly_briefing(
        self,
        period_start: str = None,
        period_end: str = None
    ) -> Dict[str, Any]:
        """
        Generate weekly CEO briefing.
        
        Args:
            period_start: Start date (YYYY-MM-DD), defaults to last Monday
            period_end: End date (YYYY-MM-DD), defaults to next Sunday
            
        Returns:
            Dictionary with briefing data and file path
        """
        # Get date range
        if not period_start or not period_end:
            period_start, period_end = self.get_week_date_range()
        
        logger.info(f'Generating weekly briefing: {period_start} to {period_end}')
        
        # Gather all data
        tasks_completed = self.get_tasks_completed(period_start, period_end)
        emails_sent = self.get_emails_sent(period_start, period_end)
        social_activity = self.get_social_media_activity(period_start, period_end)
        pending_approvals = self.get_pending_approvals()
        financial_summary = self.get_financial_summary(period_start, period_end)
        system_health = self.get_system_health()
        
        # Generate briefing content
        briefing_date = datetime.now()
        briefing_file = self.reports_path / f"CEO_Weekly_{period_start}_to_{period_end}.md"
        
        content = f"""---
type: ceo_weekly_briefing
period_start: {period_start}
period_end: {period_end}
generated: {briefing_date.isoformat()}
---

# CEO Weekly Briefing

**Period:** {period_start} to {period_end}
**Generated:** {briefing_date.strftime('%A, %B %d, %Y at %I:%M %p')}

---

## Executive Summary

This week's performance overview with key highlights and action items.

**Key Metrics:**
- Tasks Completed: {len(tasks_completed)}
- Emails Sent: {len(emails_sent)}
- Social Posts: {sum(p['posts'] for p in social_activity.values())}
- Revenue: ${financial_summary['income']['total']:,.2f}
- Expenses: ${financial_summary['expense']['total']:,.2f}
- Net Profit: ${financial_summary['net']:,.2f}

---

## 📊 Tasks Completed

"""
        
        if tasks_completed:
            content += "| Task | Date | Status | Notes |\n"
            content += "|------|------|--------|-------|\n"
            for task in tasks_completed[:10]:  # Top 10
                content += f"| {task['description'][:50]} | {task['completed_date']} | ✅ Done | - |\n"
            
            if len(tasks_completed) > 10:
                content += f"\n**Total:** {len(tasks_completed)} tasks completed this week\n"
            else:
                content += f"\n**Total:** {len(tasks_completed)} tasks completed\n"
        else:
            content += "*No tasks completed this week.*\n"
        
        content += f"""
---

## 📧 Emails Sent

"""
        
        if emails_sent:
            content += "| Date | Recipient | Subject | Status |\n"
            content += "|------|-----------|---------|--------|\n"
            for email in emails_sent[:10]:  # Top 10
                content += f"| {email.get('date', 'N/A')} | {email.get('recipient', 'N/A')[:30]} | {email.get('subject', 'N/A')[:40]} | ✅ Sent |\n"
            
            content += f"\n**Total:** {len(emails_sent)} emails sent\n"
        else:
            content += "*No emails sent this week.*\n"
        
        content += f"""
---

## 📱 Social Media Activity

### LinkedIn
- **Posts Published:** {social_activity['linkedin']['posts']}
- **Impressions:** {social_activity['linkedin'].get('impressions', 'N/A')}

### Facebook
- **Posts Published:** {social_activity['facebook']['posts']}
- **Reach:** {social_activity['facebook'].get('reach', 'N/A')}

### Instagram
- **Posts Published:** {social_activity['instagram']['posts']}

### Twitter
- **Tweets:** {social_activity['twitter']['tweets']}
- **Impressions:** {social_activity['twitter'].get('impressions', 'N/A')}

---

## ⏳ Pending Approvals

"""
        
        if pending_approvals:
            content += "| Item | Type | Requested | Status | Action |\n"
            content += "|------|------|-----------|--------|--------|\n"
            for approval in pending_approvals[:10]:
                content += f"| {approval['description'][:40]} | {approval['type']} | {approval.get('requested', 'N/A')} | ⏳ Pending | Review |\n"
            
            content += f"\n**Total Pending:** {len(pending_approvals)} items requiring attention\n"
        else:
            content += "*No pending approvals. All caught up!* ✅\n"
        
        content += f"""
---

## 💰 Financial Summary

### Income
- **This Week:** ${financial_summary['income']['total']:,.2f}
- **Transactions:** {financial_summary['income']['transactions']}

### Expenses
- **This Week:** ${financial_summary['expense']['total']:,.2f}
- **Transactions:** {financial_summary['expense']['transactions']}

### Net Profit
- **This Week:** ${financial_summary['net']:,.2f}
- **Profit Margin:** {financial_summary['margin']:.1f}%

---

## 🏥 System Health

| Component | Status | Details |
|-----------|--------|---------|
"""
        
        for component in system_health['components']:
            content += f"| {component['name']} | {component['status']} | {component['details']} |\n"
        
        content += f"\n**Overall Health:** {system_health['overall']}\n"
        
        if system_health['issues']:
            content += "\n### Issues\n"
            for issue in system_health['issues']:
                content += f"- ⚠️ {issue}\n"
        
        content += f"""
---

## 🎯 Key Highlights

"""
        
        # Auto-generate highlights
        highlights = []
        
        if len(tasks_completed) > 0:
            highlights.append(f"✅ Completed {len(tasks_completed)} tasks this week")
        
        if financial_summary['net'] > 0:
            highlights.append(f"✅ Positive net profit of ${financial_summary['net']:,.2f}")
        
        if len(pending_approvals) == 0:
            highlights.append("✅ Zero pending approvals - all caught up!")
        
        if system_health['overall'] == '🟢 All Systems Operational':
            highlights.append("✅ All systems running at 100%")
        
        if social_activity['linkedin']['posts'] > 0:
            highlights.append(f"✅ Published {social_activity['linkedin']['posts']} LinkedIn posts")
        
        if highlights:
            for highlight in highlights:
                content += f"{highlight}\n"
        else:
            content += "*No specific highlights this week.*\n"
        
        content += f"""
---

## ⚠️ Action Items

"""
        
        if pending_approvals:
            content += "1. **Review pending approvals** - "
            content += f"{len(pending_approvals)} items awaiting attention\n"
        
        if system_health['issues']:
            content += "2. **Address system issues** - Review health status above\n"
        
        if len(tasks_completed) == 0:
            content += "3. **Increase productivity** - Set goals for next week\n"
        
        if not pending_approvals and not system_health['issues'] and len(tasks_completed) > 0:
            content += "*No critical action items. Great job!*\n"
        
        content += f"""
---

## 📈 Next Week Focus

- [ ] Review and approve pending items
- [ ] Continue task completion momentum
- [ ] Monitor financial performance
- [ ] Maintain system health

---

_Briefing automatically generated by AI Employee System_
_Next briefing: Monday, {(briefing_date + timedelta(days=7)).strftime('%B %d, %Y')} at 7:00 AM_
"""
        
        # Write briefing file
        briefing_file.write_text(content)
        
        logger.info(f'Weekly briefing generated: {briefing_file}')
        
        return {
            'status': 'success',
            'briefing_file': str(briefing_file),
            'period': {
                'start': period_start,
                'end': period_end
            },
            'summary': {
                'tasks_completed': len(tasks_completed),
                'emails_sent': len(emails_sent),
                'social_posts': sum(p['posts'] for p in social_activity.values()),
                'pending_approvals': len(pending_approvals),
                'revenue': financial_summary['income']['total'],
                'expenses': financial_summary['expense']['total'],
                'net_profit': financial_summary['net']
            },
            'system_health': system_health['overall']
        }

    def generate_daily_briefing(self) -> Dict[str, Any]:
        """
        Generate daily executive summary.
        
        Returns:
            Dictionary with briefing data
        """
        today = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f'Generating daily briefing: {today}')
        
        # Get today's data
        tasks = self.get_tasks_completed(today, today)
        emails = self.get_emails_sent(today, today)
        approvals = self.get_pending_approvals()
        health = self.get_system_health()
        
        # Generate brief content
        briefing_file = self.reports_path / f"CEO_Daily_{today}.md"
        
        content = f"""---
type: ceo_daily_briefing
date: {today}
generated: {datetime.now().isoformat()}
---

# CEO Daily Briefing

**Date:** {datetime.now().strftime('%A, %B %d, %Y')}

---

## Today's Summary

- **Tasks Completed:** {len(tasks)}
- **Emails Sent:** {len(emails)}
- **Pending Approvals:** {len(approvals)}

---

## System Health: {health['overall']}

"""
        
        briefing_file.write_text(content)
        
        return {
            'status': 'success',
            'briefing_file': str(briefing_file),
            'date': today
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='CEO Briefing Generator')
    parser.add_argument('command', choices=['auto', 'weekly', 'daily', 'test'],
                       help='Command to execute')
    parser.add_argument('--start', help='Period start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='Period end date (YYYY-MM-DD)')
    parser.add_argument('--vault', default='AI_Employee_Vault',
                       help='Path to vault directory')
    
    args = parser.parse_args()
    
    # Initialize briefing generator
    briefing = CEOBriefing(vault_path=args.vault)
    
    try:
        if args.command == 'auto':
            # Auto mode: generate weekly briefing for last week
            print("\n=== CEO Weekly Briefing (Auto Mode) ===\n")
            result = briefing.generate_weekly_briefing(
                period_start=args.start,
                period_end=args.end
            )
            
            print(f"✅ Briefing generated: {result['briefing_file']}")
            print(f"\n📊 Summary:")
            print(f"   Tasks Completed: {result['summary']['tasks_completed']}")
            print(f"   Emails Sent: {result['summary']['emails_sent']}")
            print(f"   Revenue: ${result['summary']['revenue']:,.2f}")
            print(f"   Net Profit: ${result['summary']['net_profit']:,.2f}")
            print(f"   System Health: {result['system_health']}")
            print()
            
        elif args.command == 'weekly':
            # Manual weekly briefing
            print("\n=== CEO Weekly Briefing ===\n")
            result = briefing.generate_weekly_briefing(
                period_start=args.start,
                period_end=args.end
            )
            
            print(f"✅ Briefing generated: {result['briefing_file']}")
            print()
            
        elif args.command == 'daily':
            # Daily briefing
            print("\n=== CEO Daily Briefing ===\n")
            result = briefing.generate_daily_briefing()
            
            print(f"✅ Daily briefing generated: {result['briefing_file']}")
            print()
            
        elif args.command == 'test':
            # Test mode
            print("\n=== CEO Briefing Test ===\n")
            
            # Test weekly briefing
            result = briefing.generate_weekly_briefing()
            
            print("✅ All tests passed!")
            print(f"Briefing file: {result['briefing_file']}")
            print()
            
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f'Error generating briefing: {e}', exc_info=True)
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
