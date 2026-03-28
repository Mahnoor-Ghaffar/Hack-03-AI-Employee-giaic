"""
AI Employee Dashboard - Platinum Tier
Web-based dashboard for monitoring and managing the AI Employee system.

Features:
- Real-time vault status monitoring
- Task management (Needs_Action, Pending_Approval, Done)
- Email triage and drafts
- Social media drafts and scheduling
- Financial reports (Odoo integration)
- System health monitoring
- Human-in-the-loop approval interface
- CEO Briefing generation

Usage:
    python dashboard/app.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.vault_skills import (
    get_vault, 
    list_pending_tasks, 
    get_task_summary,
    read_task,
    move_to_done,
    update_dashboard
)
from log_manager import setup_logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Setup logging
logger = setup_logging(
    log_file="logs/dashboard.log",
    logger_name="dashboard"
)

# Configuration
VAULT_PATH = Path(__file__).parent.parent / "AI_Employee_Vault"
LOGS_PATH = Path(__file__).parent.parent / "logs"

# Ensure directories exist
VAULT_PATH.mkdir(parents=True, exist_ok=True)
LOGS_PATH.mkdir(parents=True, exist_ok=True)

# Initialize vault skills
vault = get_vault()


# =============================================================================
# Web Routes
# =============================================================================

@app.route('/')
def index():
    """Dashboard home page"""
    return render_template('index.html')


@app.route('/tasks')
def tasks():
    """Task management page"""
    return render_template('tasks.html')


@app.route('/approvals')
def approvals():
    """Approval management page"""
    return render_template('approvals.html')


@app.route('/email')
def email():
    """Email triage page"""
    return render_template('email.html')


@app.route('/social')
def social():
    """Social media management page"""
    return render_template('social.html')


@app.route('/accounting')
def accounting():
    """Accounting and financial reports page"""
    return render_template('accounting.html')


@app.route('/health')
def health():
    """System health monitoring page"""
    return render_template('health.html')


@app.route('/briefings')
def briefings():
    """CEO Briefings page"""
    return render_template('briefings.html')


@app.route('/settings')
def settings():
    """System settings page"""
    return render_template('settings.html')


# =============================================================================
# API Routes - Vault Operations
# =============================================================================

@app.route('/api/vault/status')
def api_vault_status():
    """Get overall vault status"""
    try:
        stats = {
            'inbox': len(list((VAULT_PATH / "Inbox").glob("*.md"))) if (VAULT_PATH / "Inbox").exists() else 0,
            'needs_action': len(list((VAULT_PATH / "Needs_Action").glob("*.md"))) if (VAULT_PATH / "Needs_Action").exists() else 0,
            'pending_approval': len(list((VAULT_PATH / "Pending_Approval").glob("*.md"))) if (VAULT_PATH / "Pending_Approval").exists() else 0,
            'needs_approval': len(list((VAULT_PATH / "Needs_Approval").glob("*.md"))) if (VAULT_PATH / "Needs_Approval").exists() else 0,
            'approved': len(list((VAULT_PATH / "Approved").glob("*.md"))) if (VAULT_PATH / "Approved").exists() else 0,
            'done': len(list((VAULT_PATH / "Done").glob("*.md"))) if (VAULT_PATH / "Done").exists() else 0,
            'in_progress': len(list((VAULT_PATH / "In_Progress").glob("**/*.md"))) if (VAULT_PATH / "In_Progress").exists() else 0,
            'updates': len(list((VAULT_PATH / "Updates").glob("**/*.md"))) if (VAULT_PATH / "Updates").exists() else 0,
            'signals': len(list((VAULT_PATH / "Signals/urgent").glob("*.md"))) if (VAULT_PATH / "Signals/urgent").exists() else 0,
        }
        
        # Read dashboard status
        dashboard_path = VAULT_PATH / "Dashboard.md"
        dashboard_status = "offline"
        last_updated = None
        
        if dashboard_path.exists():
            content = dashboard_path.read_text()
            dashboard_status = "online"
            # Extract last updated time
            for line in content.split('\n'):
                if 'Last Updated:' in line:
                    last_updated = line.split(':', 1)[1].strip()
                    break
        
        stats['dashboard_status'] = dashboard_status
        stats['last_updated'] = last_updated
        stats['timestamp'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting vault status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tasks/list')
def api_tasks_list():
    """List all pending tasks"""
    try:
        tasks = list_pending_tasks()
        task_details = []
        
        for task_name in tasks:
            task_data = read_task(task_name)
            if 'error' not in task_data:
                task_details.append({
                    'name': task_name,
                    'type': task_data['metadata'].get('type', 'unknown'),
                    'priority': task_data['metadata'].get('priority', 'normal'),
                    'status': task_data['metadata'].get('status', 'pending'),
                    'created': task_data['metadata'].get('created', ''),
                    'body_preview': task_data['body'][:200] + '...' if len(task_data['body']) > 200 else task_data['body']
                })
        
        return jsonify({
            'success': True,
            'data': {
                'total': len(task_details),
                'tasks': task_details
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tasks/<path:task_name>')
def api_task_detail(task_name):
    """Get detailed task information"""
    try:
        task_data = read_task(task_name)
        
        if 'error' in task_data:
            return jsonify({
                'success': False,
                'error': task_data['error']
            }), 404
        
        return jsonify({
            'success': True,
            'data': task_data
        })
        
    except Exception as e:
        logger.error(f"Error getting task detail: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tasks/<path:task_name>/complete', methods=['POST'])
def api_task_complete(task_name):
    """Mark a task as complete"""
    try:
        data = request.get_json()
        summary = data.get('summary', 'Task completed')
        
        result = move_to_done(task_name, summary)
        
        if 'Error' in result:
            return jsonify({
                'success': False,
                'error': result
            }), 400
        
        return jsonify({
            'success': True,
            'message': result
        })
        
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# API Routes - Approvals
# =============================================================================

@app.route('/api/approvals/list')
def api_approvals_list():
    """List all pending approvals"""
    try:
        approvals = []
        
        # Check Pending_Approval folder
        pending_path = VAULT_PATH / "Pending_Approval"
        if pending_path.exists():
            for file in pending_path.glob("*.md"):
                content = file.read_text()
                approval_data = parse_approval_file(content, file.name)
                approvals.append(approval_data)
        
        # Check Needs_Approval folder
        needs_approval_path = VAULT_PATH / "Needs_Approval"
        if needs_approval_path.exists():
            for file in needs_approval_path.glob("*.md"):
                content = file.read_text()
                approval_data = parse_approval_file(content, file.name)
                approval_data['location'] = 'needs_approval'
                approvals.append(approval_data)
        
        return jsonify({
            'success': True,
            'data': {
                'total': len(approvals),
                'approvals': approvals
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing approvals: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def parse_approval_file(content: str, filename: str) -> dict:
    """Parse approval file content"""
    approval_data = {
        'filename': filename,
        'location': 'pending_approval',
        'type': 'unknown',
        'status': 'pending',
        'created': '',
        'summary': ''
    }
    
    # Extract metadata from frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if key in ['type', 'status', 'created', 'approval_id']:
                        approval_data[key] = value
    
    # Extract summary from content
    if "## Email Send Request" in content:
        approval_data['summary'] = "Email send request"
        # Extract recipient
        for line in content.split('\n'):
            if 'recipient_email:' in line:
                approval_data['recipient'] = line.split(':')[-1].strip().strip('"')
            if 'subject:' in line.lower():
                approval_data['subject'] = line.split(':', 1)[1].strip()
    elif "## LinkedIn Post Request" in content:
        approval_data['summary'] = "LinkedIn post request"
        approval_data['content_preview'] = content.split("```")[1][:100] + '...' if "```" in content else ''
    elif "Payment" in content:
        approval_data['summary'] = "Payment approval request"
    
    return approval_data


@app.route('/api/approvals/<path:approval_name>/approve', methods=['POST'])
def api_approval_approve(approval_name):
    """Approve a pending action"""
    try:
        # Determine file path
        file_path = VAULT_PATH / "Pending_Approval" / f"{approval_name}"
        if not file_path.exists():
            file_path = VAULT_PATH / "Needs_Approval" / f"{approval_name}"
        
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'Approval file not found'
            }), 404
        
        # Update status to approved
        content = file_path.read_text()
        
        # Update YAML frontmatter
        if "status: pending" in content:
            content = content.replace("status: pending", "status: approved")
        if "approved: false" in content:
            content = content.replace("approved: false", "approved: true")
        
        file_path.write_text(content)
        
        logger.info(f"Approval granted: {approval_name}")
        
        return jsonify({
            'success': True,
            'message': f'Approval granted for {approval_name}'
        })
        
    except Exception as e:
        logger.error(f"Error approving action: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/approvals/<path:approval_name>/reject', methods=['POST'])
def api_approval_reject(approval_name):
    """Reject a pending action"""
    try:
        # Determine file path
        file_path = VAULT_PATH / "Pending_Approval" / f"{approval_name}"
        if not file_path.exists():
            file_path = VAULT_PATH / "Needs_Approval" / f"{approval_name}"
        
        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'Approval file not found'
            }), 404
        
        # Update status to rejected
        content = file_path.read_text()
        
        if "status: pending" in content:
            content = content.replace("status: pending", "status: rejected")
        if "approved: false" in content:
            content = content.replace("approved: false", "approved: false  # Rejected")
        
        file_path.write_text(content)
        
        # Move to Rejected folder
        rejected_path = VAULT_PATH / "Rejected"
        rejected_path.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.move(str(file_path), str(rejected_path / approval_name))
        
        logger.info(f"Approval rejected: {approval_name}")
        
        return jsonify({
            'success': True,
            'message': f'Approval rejected for {approval_name}'
        })
        
    except Exception as e:
        logger.error(f"Error rejecting action: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# API Routes - Email
# =============================================================================

@app.route('/api/email/list')
def api_email_list():
    """List email triage items"""
    try:
        emails = []
        
        # Check Updates/email_triage folder
        email_path = VAULT_PATH / "Updates" / "email_triage"
        if email_path.exists():
            for file in email_path.glob("*.md"):
                content = file.read_text()
                email_data = parse_email_file(content, file.name)
                emails.append(email_data)
        
        # Also check Needs_Action for email type tasks
        needs_action_path = VAULT_PATH / "Needs_Action"
        if needs_action_path.exists():
            for file in needs_action_path.glob("EMAIL_*.md"):
                content = file.read_text()
                email_data = parse_email_file(content, file.name)
                email_data['location'] = 'needs_action'
                emails.append(email_data)
        
        return jsonify({
            'success': True,
            'data': {
                'total': len(emails),
                'emails': emails
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing emails: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def parse_email_file(content: str, filename: str) -> dict:
    """Parse email triage file"""
    email_data = {
        'filename': filename,
        'from': '',
        'subject': '',
        'priority': 'normal',
        'status': 'pending',
        'summary': '',
        'draft_preview': ''
    }
    
    # Extract metadata
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if key in ['from', 'subject', 'priority', 'status', 'type']:
                        email_data[key] = value
    
    # Extract summary
    if "**Summary:**" in content:
        summary_section = content.split("**Summary:**")[1]
        email_data['summary'] = summary_section.split('\n\n')[0].strip()
    
    # Extract draft preview
    if "**Draft Reply Preview:**" in content:
        draft_section = content.split("**Draft Reply Preview:**")[1]
        if "```" in draft_section:
            email_data['draft_preview'] = draft_section.split("```")[1].strip()[:200] + '...'
    
    return email_data


# =============================================================================
# API Routes - Social Media
# =============================================================================

@app.route('/api/social/list')
def api_social_list():
    """List social media drafts and posts"""
    try:
        posts = []
        
        # Check Updates/social_drafts folder
        drafts_path = VAULT_PATH / "Updates" / "social_drafts"
        if drafts_path.exists():
            for file in drafts_path.glob("*.md"):
                content = file.read_text()
                post_data = parse_social_file(content, file.name)
                post_data['type'] = 'draft'
                posts.append(post_data)
        
        # Check Social_Media folder
        social_path = VAULT_PATH / "Social_Media"
        if social_path.exists():
            for file in social_path.glob("*.md"):
                content = file.read_text()
                post_data = parse_social_file(content, file.name)
                post_data['type'] = 'published'
                posts.append(post_data)
        
        return jsonify({
            'success': True,
            'data': {
                'total': len(posts),
                'posts': posts
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing social posts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def parse_social_file(content: str, filename: str) -> dict:
    """Parse social media file"""
    post_data = {
        'filename': filename,
        'platform': 'unknown',
        'content': '',
        'status': 'draft',
        'scheduled': ''
    }
    
    # Extract metadata
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if key in ['platform', 'status', 'scheduled']:
                        post_data[key] = value
    
    # Extract content
    if "## Content" in content:
        post_data['content'] = content.split("## Content")[1].strip()[:300]
    elif "```" in content:
        post_data['content'] = content.split("```")[1].strip()[:300]
    
    return post_data


# =============================================================================
# API Routes - Accounting
# =============================================================================

@app.route('/api/accounting/summary')
def api_accounting_summary():
    """Get accounting summary"""
    try:
        summary = {
            'invoices': [],
            'transactions': [],
            'reports': []
        }
        
        # Check Accounting folder
        accounting_path = VAULT_PATH / "Accounting"
        if accounting_path.exists():
            # Get invoices
            invoices_file = accounting_path / "Invoices.md"
            if invoices_file.exists():
                content = invoices_file.read_text()
                summary['invoices'] = parse_invoices(content)
            
            # Get transactions
            transactions_file = accounting_path / "Transactions.md"
            if transactions_file.exists():
                content = transactions_file.read_text()
                summary['transactions'] = parse_transactions(content)
            
            # Get reports
            reports_path = accounting_path / "Reports"
            if reports_path.exists():
                for file in reports_path.glob("*.md"):
                    summary['reports'].append({
                        'filename': file.name,
                        'title': file.stem.replace('_', ' ').title()
                    })
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting accounting summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def parse_invoices(content: str) -> list:
    """Parse invoices markdown"""
    invoices = []
    # Simple parsing - look for invoice entries
    lines = content.split('\n')
    current_invoice = {}
    
    for line in lines:
        if line.startswith('### Invoice'):
            if current_invoice:
                invoices.append(current_invoice)
            current_invoice = {'title': line.strip('#').strip()}
        elif ':' in line and current_invoice:
            key, value = line.split(':', 1)
            current_invoice[key.strip().lower().replace(' ', '_')] = value.strip()
    
    if current_invoice:
        invoices.append(current_invoice)
    
    return invoices[-10:]  # Return last 10 invoices


def parse_transactions(content: str) -> list:
    """Parse transactions markdown"""
    transactions = []
    lines = content.split('\n')
    
    for line in lines:
        if line.startswith('-') and '$' in line:
            transactions.append({
                'description': line.strip('- ').split('$')[0].strip(),
                'amount': line.split('$')[1].strip() if '$' in line else ''
            })
    
    return transactions[-20:]  # Return last 20 transactions


# =============================================================================
# API Routes - Health
# =============================================================================

@app.route('/api/health/status')
def api_health_status():
    """Get system health status"""
    try:
        health_file = VAULT_PATH / "Logs" / "health_status.md"
        
        if not health_file.exists():
            return jsonify({
                'success': True,
                'data': {
                    'status': 'unknown',
                    'message': 'No health status available yet'
                }
            })
        
        content = health_file.read_text()
        
        # Parse health status
        status_data = {
            'status': 'unknown',
            'uptime_hours': 0,
            'cpu': 0,
            'memory': 0,
            'disk': 0,
            'checks_performed': 0,
            'processes_restarted': 0,
            'alerts_sent': 0,
            'errors': 0
        }
        
        for line in content.split('\n'):
            if 'status:' in line and 'last_check' not in line:
                status_data['status'] = line.split(':')[1].strip()
            elif 'uptime_hours:' in line:
                status_data['uptime_hours'] = float(line.split(':')[1].strip())
            elif 'Checks Performed:' in line:
                status_data['checks_performed'] = int(line.split(':')[1].strip())
            elif 'Processes Restarted:' in line:
                status_data['processes_restarted'] = int(line.split(':')[1].strip())
            elif 'Alerts Sent:' in line:
                status_data['alerts_sent'] = int(line.split(':')[1].strip())
            elif 'Errors:' in line:
                status_data['errors'] = int(line.split(':')[1].strip())
        
        # Parse table for resource usage
        if '| CPU |' in content:
            for line in content.split('\n'):
                if '| CPU |' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        cpu_str = parts[2].strip().replace('%', '').replace('✅', '').replace('⚠️', '')
                        status_data['cpu'] = float(cpu_str) if cpu_str else 0
                elif '| Memory |' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        mem_str = parts[2].strip().replace('%', '').replace('✅', '').replace('⚠️', '')
                        status_data['memory'] = float(mem_str) if mem_str else 0
                elif '| Disk |' in line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        disk_str = parts[2].strip().replace('%', '').replace('✅', '').replace('⚠️', '')
                        status_data['disk'] = float(disk_str) if disk_str else 0
        
        return jsonify({
            'success': True,
            'data': status_data
        })
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health/logs')
def api_health_logs():
    """Get recent log entries"""
    try:
        logs = []
        
        # Get recent log files
        log_files = ['ai_employee.log', 'health_monitor.log', 'dashboard.log']
        
        for log_name in log_files:
            log_path = LOGS_PATH / log_name
            if log_path.exists():
                # Read last 100 lines
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-100:]
                    for line in lines:
                        logs.append({
                            'source': log_name,
                            'content': line.strip()
                        })
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x['content'][:19] if len(x['content']) > 19 else '', reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'total': len(logs),
                'logs': logs[:50]  # Return last 50 entries
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# API Routes - Briefings
# =============================================================================

@app.route('/api/briefings/list')
def api_briefings_list():
    """List CEO briefings"""
    try:
        briefings = []
        
        briefings_path = VAULT_PATH / "Briefings"
        if briefings_path.exists():
            for file in briefings_path.glob("*.md"):
                content = file.read_text()
                briefing_data = {
                    'filename': file.name,
                    'title': file.stem.replace('_', ' ').title(),
                    'created': '',
                    'period': ''
                }
                
                # Extract metadata
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = parts[1].strip()
                        for line in frontmatter.split("\n"):
                            if ":" in line:
                                key, value = line.split(":", 1)
                                if 'generated' in key.lower():
                                    briefing_data['created'] = value.strip()
                                elif 'period' in key.lower():
                                    briefing_data['period'] = value.strip()
                
                briefings.append(briefing_data)
        
        # Sort by date (newest first)
        briefings.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'total': len(briefings),
                'briefings': briefings
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing briefings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/briefings/<path:briefing_name>')
def api_briefing_detail(briefing_name):
    """Get briefing detail"""
    try:
        briefing_path = VAULT_PATH / "Briefings" / briefing_name
        
        if not briefing_path.exists():
            return jsonify({
                'success': False,
                'error': 'Briefing not found'
            }), 404
        
        content = briefing_path.read_text()
        
        return jsonify({
            'success': True,
            'data': {
                'filename': briefing_name,
                'content': content
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting briefing detail: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# API Routes - Signals/Alerts
# =============================================================================

@app.route('/api/signals/list')
def api_signals_list():
    """List urgent signals/alerts"""
    try:
        signals = []
        
        signals_path = VAULT_PATH / "Signals" / "urgent"
        if signals_path.exists():
            for file in signals_path.glob("*.md"):
                content = file.read_text()
                signal_data = {
                    'filename': file.name,
                    'severity': 'medium',
                    'timestamp': '',
                    'message': ''
                }
                
                # Extract metadata
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = parts[1].strip()
                        for line in frontmatter.split("\n"):
                            if ":" in line:
                                key, value = line.split(":", 1)
                                key = key.strip()
                                value = value.strip()
                                if key == 'severity':
                                    signal_data['severity'] = value
                                elif key == 'timestamp':
                                    signal_data['timestamp'] = value
                                elif key == 'agent_type':
                                    signal_data['agent'] = value
                
                # Extract message
                if "## Message" in content:
                    message_section = content.split("## Message")[1]
                    signal_data['message'] = message_section.split('\n\n')[0].strip()
                
                signals.append(signal_data)
        
        # Sort by timestamp (newest first)
        signals.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'total': len(signals),
                'signals': signals
            }
        })
        
    except Exception as e:
        logger.error(f"Error listing signals: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("AI EMPLOYEE DASHBOARD - PLATINUM TIER")
    print("=" * 60)
    print()
    print(f"Vault Path: {VAULT_PATH}")
    print(f"Logs Path: {LOGS_PATH}")
    print()
    print("Starting Flask server...")
    print()
    print("Access the dashboard at:")
    print("  http://localhost:5000")
    print("  http://127.0.0.1:5000")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
