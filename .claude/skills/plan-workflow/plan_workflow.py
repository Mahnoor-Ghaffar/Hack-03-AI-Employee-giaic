#!/usr/bin/env python3
"""
Plan Workflow Skill - Platinum Tier Integration

Provides structured task planning and execution capabilities for the AI Employee system.
Reads plan files from AI_Employee_Vault/Plans/ and coordinates execution across all
Gold Tier integrations (Odoo, Twitter, Facebook/Instagram, Personal Tasks).

Capabilities:
- Create and manage plan files
- Execute plan steps with proper action routing
- Support for human approval workflow
- Integration with scheduler and Plan workflow

Usage:
    from .claude.skills.plan_workflow.plan_workflow import PlanWorkflow

    plan = PlanWorkflow()

    # Create a plan
    result = plan.create_plan(
        name="Q1_Social_Media_Campaign",
        title="Q1 Social Media Campaign",
        priority="high",
        steps=[
            {"action": "twitter.post_tweet", "content": "Launch announcement!"},
            {"action": "social.post_facebook", "content": "Facebook post"}
        ]
    )

    # Execute a plan
    result = plan.execute_plan("Q1_Social_Media_Campaign.md")

Environment Variables:
    VAULT_PATH: Path to vault directory (default: AI_Employee_Vault)
    LOG_LEVEL: Logging level (default: INFO)
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('plan_workflow')

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', 'AI_Employee_Vault'))
PLANS_PATH = VAULT_PATH / 'Plans'
REPORTS_PATH = VAULT_PATH / 'Reports'
LOGS_PATH = VAULT_PATH / 'Logs'

# Ensure directories exist
PLANS_PATH.mkdir(parents=True, exist_ok=True)
REPORTS_PATH.mkdir(parents=True, exist_ok=True)
LOGS_PATH.mkdir(parents=True, exist_ok=True)

# Plan file pattern
PLAN_FILE_PATTERN = "{name}.md"


class PlanWorkflow:
    """
    Plan Workflow for AI Employee integration.

    Manages plan files and coordinates execution across all Gold Tier integrations.
    """

    # Supported actions mapping
    SUPPORTED_ACTIONS = {
        'odoo.create_invoice': 'odoo',
        'odoo.list_invoices': 'odoo',
        'odoo.record_payment': 'odoo',
        'twitter.post_tweet': 'twitter',
        'twitter.post_thread': 'twitter',
        'social.post_facebook': 'social',
        'social.post_instagram': 'social',
        'social.post_instagram_carousel': 'social',
        'social.post_to_both': 'social',
        'personal.create_task': 'personal',
        'personal.update_task': 'personal',
        'personal.update_task_status': 'personal',
        'personal.delete_task': 'personal',
    }

    def __init__(self, vault_path: Path = None):
        """
        Initialize Plan Workflow.

        Args:
            vault_path: Path to vault directory
        """
        self.vault_path = vault_path or VAULT_PATH
        self.plans_path = self.vault_path / 'Plans'
        self.reports_path = self.vault_path / 'Reports'
        self.logs_path = self.vault_path / 'Logs'

        # Ensure directories exist
        self.plans_path.mkdir(parents=True, exist_ok=True)
        self.reports_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Initialize integration clients (lazy loading)
        self._odoo = None
        self._twitter = None
        self._social = None
        self._personal = None

        logger.info(f'PlanWorkflow initialized at {self.plans_path}')

    # ==================== PLAN MANAGEMENT ====================

    def create_plan(
        self,
        name: str,
        title: str,
        steps: List[Dict[str, Any]],
        priority: str = "medium",
        due_date: str = None,
        tags: List[str] = None,
        requires_approval: bool = True,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Create a new plan file.

        Args:
            name: Plan file name (without .md)
            title: Plan title
            steps: List of plan steps with action and parameters
            priority: Task priority (low, medium, high, urgent)
            due_date: Due date in YYYY-MM-DD format
            tags: List of tags for categorization
            requires_approval: Whether to require human approval
            description: Plan description

        Returns:
            Dictionary with plan details and status
        """
        if not name:
            raise ValueError("Plan name is required")
        if not title:
            raise ValueError("Plan title is required")
        if not steps:
            raise ValueError("At least one step is required")

        created_at = datetime.now().strftime("%Y-%m-%d")
        plan_file = self.plans_path / PLAN_FILE_PATTERN.format(name=name)

        # Build plan markdown content
        content = self._build_plan_markdown(
            title=title,
            priority=priority,
            due_date=due_date,
            tags=tags,
            description=description,
            steps=steps,
            requires_approval=requires_approval
        )

        # Save plan file
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(content)

        result = {
            "status": "success",
            "plan_name": name,
            "title": title,
            "file_path": str(plan_file),
            "steps_count": len(steps),
            "created_at": created_at
        }

        logger.info(f"Created plan: {name} with {len(steps)} steps")
        self._log_action("plan_created", result)

        return result

    def read_plan(self, plan_file: str) -> Dict[str, Any]:
        """
        Read and parse a plan file.

        Args:
            plan_file: Plan file name (with or without .md)

        Returns:
            Dictionary with parsed plan data
        """
        # Add .md extension if missing
        if not plan_file.endswith('.md'):
            plan_file += '.md'

        plan_path = self.plans_path / plan_file

        if not plan_path.exists():
            return {
                "status": "error",
                "message": f"Plan file not found: {plan_file}"
            }

        try:
            content = plan_path.read_text(encoding='utf-8')
            parsed = self._parse_plan_markdown(content)
            parsed['file_name'] = plan_file
            parsed['file_path'] = str(plan_path)

            return {
                "status": "success",
                "plan": parsed
            }
        except Exception as e:
            logger.error(f"Failed to parse plan {plan_file}: {e}")
            return {
                "status": "error",
                "message": f"Failed to parse plan: {e}"
            }

    def update_plan(
        self,
        plan_file: str,
        status: str = None,
        priority: str = None,
        due_date: str = None,
        add_step: Dict[str, Any] = None,
        complete_step_index: int = None
    ) -> Dict[str, Any]:
        """
        Update a plan file.

        Args:
            plan_file: Plan file name
            status: New status (pending, in_progress, completed, cancelled)
            priority: New priority
            due_date: New due date
            add_step: Step to add
            complete_step_index: Index of step to mark complete

        Returns:
            Dictionary with update result
        """
        result = self.read_plan(plan_file)
        if result['status'] == 'error':
            return result

        plan = result['plan']
        plan_path = self.plans_path / plan_file

        updates = {}

        if status:
            plan['status'] = status
            updates['status'] = status

        if priority:
            plan['priority'] = priority
            updates['priority'] = priority

        if due_date:
            plan['due_date'] = due_date
            updates['due_date'] = due_date

        if add_step:
            plan['steps'].append(add_step)
            updates['add_step'] = True

        if complete_step_index is not None:
            if 0 <= complete_step_index < len(plan['steps']):
                plan['steps'][complete_step_index]['status'] = 'completed'
                plan['steps'][complete_step_index]['completed_at'] = datetime.now().isoformat()
                updates['complete_step'] = complete_step_index

        # Rewrite plan file
        content = self._build_plan_markdown(
            title=plan['title'],
            priority=plan.get('priority', 'medium'),
            due_date=plan.get('due_date'),
            tags=plan.get('tags'),
            description=plan.get('description', ''),
            steps=plan['steps'],
            requires_approval=plan.get('requires_approval', True),
            status=plan.get('status', 'pending')
        )

        with open(plan_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "status": "success",
            "plan_file": plan_file,
            "updates": updates
        }

    def list_plans(
        self,
        status: str = None,
        priority: str = None,
        tag: str = None
    ) -> Dict[str, Any]:
        """
        List plans with optional filters.

        Args:
            status: Filter by status
            priority: Filter by priority
            tag: Filter by tag

        Returns:
            Dictionary with list of plans
        """
        plans = []

        for plan_file in self.plans_path.glob("*.md"):
            result = self.read_plan(plan_file.name)
            if result['status'] == 'success':
                plan = result['plan']

                # Apply filters
                if status and plan.get('status') != status:
                    continue
                if priority and plan.get('priority') != priority:
                    continue
                if tag and tag not in plan.get('tags', []):
                    continue

                plans.append(plan)

        # Sort by priority and due date
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        plans.sort(key=lambda p: (
            priority_order.get(p.get('priority', 'medium'), 2),
            p.get('due_date') or '9999-99-99'
        ))

        return {
            "status": "success",
            "count": len(plans),
            "plans": plans
        }

    # ==================== PLAN EXECUTION ====================

    def execute_plan(
        self,
        plan_file: str,
        require_approval: bool = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute all steps in a plan.

        Args:
            plan_file: Plan file name
            require_approval: Require human approval (default from plan)
            dry_run: Validate without executing

        Returns:
            Dictionary with execution results
        """
        result = self.read_plan(plan_file)
        if result['status'] == 'error':
            return result

        plan = result['plan']

        # Check if already completed
        if plan.get('status') == 'completed':
            return {
                "status": "skipped",
                "message": "Plan already completed",
                "plan_file": plan_file
            }

        # Check approval requirement
        if require_approval is None:
            require_approval = plan.get('requires_approval', True)

        if require_approval and plan.get('status') != 'approved':
            return {
                "status": "pending_approval",
                "message": "Plan requires approval before execution",
                "plan_file": plan_file
            }

        logger.info(f"Executing plan: {plan_file} ({len(plan['steps'])} steps)")

        results = []
        executed = 0
        failed = 0
        skipped = 0

        for i, step in enumerate(plan['steps']):
            # Skip completed steps
            if step.get('status') == 'completed':
                skipped += 1
                results.append({"step": i, "status": "skipped", "reason": "already completed"})
                continue

            # Execute step
            step_result = self.execute_step(plan_file, i, dry_run=dry_run)
            results.append(step_result)

            if step_result.get('status') == 'success':
                executed += 1
                # Mark step as completed
                self.update_plan(plan_file, complete_step_index=i)
            else:
                failed += 1

        # Update plan status
        if failed == 0 and executed > 0:
            self.update_plan(plan_file, status='completed')
            final_status = 'success'
        elif failed > 0:
            self.update_plan(plan_file, status='in_progress')
            final_status = 'partial'
        else:
            final_status = 'skipped'

        return {
            "status": final_status,
            "plan_file": plan_file,
            "total_steps": len(plan['steps']),
            "executed": executed,
            "failed": failed,
            "skipped": skipped,
            "results": results
        }

    def execute_step(
        self,
        plan_file: str,
        step_index: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a single plan step.

        Args:
            plan_file: Plan file name
            step_index: Step index (0-based)
            dry_run: Validate without executing

        Returns:
            Dictionary with step execution result
        """
        result = self.read_plan(plan_file)
        if result['status'] == 'error':
            return result

        plan = result['plan']

        if step_index < 0 or step_index >= len(plan['steps']):
            return {
                "status": "error",
                "message": f"Invalid step index: {step_index}"
            }

        step = plan['steps'][step_index]
        action = step.get('action', '')

        # Validate action
        if action not in self.SUPPORTED_ACTIONS:
            return {
                "status": "error",
                "message": f"Unsupported action: {action}"
            }

        logger.info(f"Executing step {step_index}: {action}")

        if dry_run:
            return {
                "status": "success",
                "step": step_index,
                "action": action,
                "dry_run": True,
                "params": step
            }

        # Route to appropriate handler
        module = self.SUPPORTED_ACTIONS[action]

        try:
            if module == 'odoo':
                return self._execute_odoo_action(action, step)
            elif module == 'twitter':
                return self._execute_twitter_action(action, step)
            elif module == 'social':
                return self._execute_social_action(action, step)
            elif module == 'personal':
                return self._execute_personal_action(action, step)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown module: {module}"
                }
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return {
                "status": "error",
                "step": step_index,
                "action": action,
                "message": str(e)
            }

    def validate_plan(self, plan_file: str) -> Dict[str, Any]:
        """
        Validate a plan file.

        Args:
            plan_file: Plan file name

        Returns:
            Dictionary with validation results
        """
        result = self.read_plan(plan_file)
        if result['status'] == 'error':
            return result

        plan = result['plan']
        errors = []
        warnings = []

        # Validate required fields
        if not plan.get('title'):
            errors.append("Missing title")

        if not plan.get('steps'):
            errors.append("No steps defined")

        # Validate steps
        for i, step in enumerate(plan.get('steps', [])):
            action = step.get('action', '')
            if not action:
                errors.append(f"Step {i}: Missing action")
            elif action not in self.SUPPORTED_ACTIONS:
                errors.append(f"Step {i}: Unsupported action '{action}'")

        # Validate dates
        due_date = plan.get('due_date')
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                errors.append(f"Invalid due date format: {due_date} (expected YYYY-MM-DD)")

        # Validate priority
        priority = plan.get('priority', 'medium')
        if priority not in ['low', 'medium', 'high', 'urgent']:
            warnings.append(f"Unknown priority level: {priority}")

        return {
            "status": "valid" if not errors else "invalid",
            "plan_file": plan_file,
            "errors": errors,
            "warnings": warnings,
            "step_count": len(plan.get('steps', []))
        }

    # ==================== ACTION EXECUTORS ====================

    def _execute_odoo_action(
        self,
        action: str,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Odoo action."""
        if not self._odoo:
            try:
                from mcp.odoo_mcp.server import OdooMCPServer
                self._odoo = OdooMCPServer()
            except Exception as e:
                return {"status": "error", "message": f"Odoo initialization failed: {e}"}

        params = step.get('params', step)

        if action == 'odoo.create_invoice':
            return self._odoo.create_invoice(
                customer_name=params.get('customer_name', params.get('customer', '')),
                items=params.get('items', []),
                description=params.get('description', ''),
                auto_validate=params.get('auto_validate', False)
            )
        elif action == 'odoo.list_invoices':
            return self._odoo.list_invoices(
                status=params.get('status', 'all'),
                partner_name=params.get('partner_name'),
                limit=params.get('limit', 10)
            )
        elif action == 'odoo.record_payment':
            return self._odoo.record_payment(
                invoice_id=params.get('invoice_id'),
                amount=params.get('amount', 0),
                payment_date=params.get('payment_date'),
                reference=params.get('reference', '')
            )
        else:
            return {"status": "error", "message": f"Unknown Odoo action: {action}"}

    def _execute_twitter_action(
        self,
        action: str,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Twitter action."""
        if not self._twitter:
            try:
                from .claude.skills.twitter_post.twitter_skill import TwitterSkill
                self._twitter = TwitterSkill()
            except Exception as e:
                return {"status": "error", "message": f"Twitter initialization failed: {e}"}

        params = step.get('params', step)

        if action == 'twitter.post_tweet':
            return self._twitter.post_tweet(
                content=params.get('content', params.get('text', '')),
                reply_to=params.get('reply_to'),
                save_history=params.get('save_history', True)
            )
        elif action == 'twitter.post_thread':
            return self._twitter.post_thread(
                tweets=params.get('tweets', []),
                save_history=params.get('save_history', True)
            )
        else:
            return {"status": "error", "message": f"Unknown Twitter action: {action}"}

    def _execute_social_action(
        self,
        action: str,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Social Media action."""
        if not self._social:
            try:
                from .claude.skills.social_meta.social_skill import SocialMediaSkill
                self._social = SocialMediaSkill()
            except Exception as e:
                return {"status": "error", "message": f"Social Media initialization failed: {e}"}

        params = step.get('params', step)

        if action == 'social.post_facebook':
            return self._social.post_facebook(
                content=params.get('content', ''),
                image_path=params.get('image_path'),
                link=params.get('link'),
                scheduled_time=params.get('scheduled_time')
            )
        elif action == 'social.post_instagram':
            return self._social.post_instagram(
                content=params.get('content', ''),
                image_path=params.get('image_path', ''),
                location_id=params.get('location_id'),
                share_to_facebook=params.get('share_to_facebook', False)
            )
        elif action == 'social.post_instagram_carousel':
            return self._social.post_instagram_carousel(
                content=params.get('content', ''),
                image_paths=params.get('image_paths', []),
                share_to_facebook=params.get('share_to_facebook', False)
            )
        elif action == 'social.post_to_both':
            return self._social.post_to_both(
                content=params.get('content', ''),
                image_path=params.get('image_path'),
                facebook_link=params.get('facebook_link')
            )
        else:
            return {"status": "error", "message": f"Unknown Social action: {action}"}

    def _execute_personal_action(
        self,
        action: str,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Personal Task action."""
        if not self._personal:
            try:
                from .claude.skills.personal_task_handler.personal_skill import PersonalTaskHandler
                self._personal = PersonalTaskHandler()
            except Exception as e:
                return {"status": "error", "message": f"Personal Task Handler initialization failed: {e}"}

        params = step.get('params', step)

        if action == 'personal.create_task':
            return self._personal.create_task(
                title=params.get('title', ''),
                description=params.get('description', ''),
                priority=params.get('priority', 'medium'),
                due_date=params.get('due_date'),
                tags=params.get('tags'),
                metadata=params.get('metadata')
            )
        elif action == 'personal.update_task':
            return self._personal.update_task(
                task_id=params.get('task_id', ''),
                title=params.get('title'),
                description=params.get('description'),
                priority=params.get('priority'),
                due_date=params.get('due_date'),
                tags=params.get('tags')
            )
        elif action == 'personal.update_task_status':
            return self._personal.update_task_status(
                task_id=params.get('task_id', ''),
                status=params.get('status', ''),
                notes=params.get('notes')
            )
        elif action == 'personal.delete_task':
            return self._personal.delete_task(
                task_id=params.get('task_id', '')
            )
        else:
            return {"status": "error", "message": f"Unknown Personal action: {action}"}

    # ==================== UTILITY METHODS ====================

    def _build_plan_markdown(
        self,
        title: str,
        steps: List[Dict[str, Any]],
        priority: str = "medium",
        due_date: str = None,
        tags: List[str] = None,
        description: str = "",
        requires_approval: bool = True,
        status: str = "pending"
    ) -> str:
        """Build plan markdown content."""
        created = datetime.now().strftime("%Y-%m-%d")
        tags_str = ", ".join(tags) if tags else ""

        content = f"""# Plan: {title}

**Status:** {status}
**Priority:** {priority}
**Created:** {created}
**Due:** {due_date or 'Not set'}
**Tags:** {tags_str}
**Requires Approval:** {requires_approval}

## Overview

{description or 'No description provided.'}

## Steps

"""
        for i, step in enumerate(steps, 1):
            action = step.get('action', 'unknown')
            step_status = step.get('status', 'pending')
            completed_at = step.get('completed_at', '')

            content += f"### Step {i}: {action}\n"

            if step_status == 'completed':
                content += f"**Status:** ✅ Completed ({completed_at})\n"
            else:
                content += f"**Status:** ⏳ Pending\n"

            # Add step parameters
            for key, value in step.items():
                if key not in ['action', 'status', 'completed_at']:
                    if isinstance(value, dict):
                        content += f"- **{key}:**\n"
                        for k, v in value.items():
                            content += f"  - {k}: {v}\n"
                    elif isinstance(value, list):
                        content += f"- **{key}:**\n"
                        for item in value:
                            if isinstance(item, dict):
                                content += "  - " + ", ".join(f"{k}: {v}" for k, v in item.items()) + "\n"
                            else:
                                content += f"  - {item}\n"
                    else:
                        content += f"- **{key}:** {value}\n"

            content += "\n"

        content += """## Approval

"""
        if requires_approval:
            content += """- **Requires Approval:** Yes
- **Approved By:**
- **Approved At:**
"""
        else:
            content += """- **Requires Approval:** No
"""

        content += f"""
---
*Generated by AI Employee Plan Workflow Skill*
*Last Updated: {datetime.now().isoformat()}*
"""
        return content

    def _parse_plan_markdown(self, content: str) -> Dict[str, Any]:
        """Parse plan markdown content."""
        plan = {
            'title': '',
            'status': 'pending',
            'priority': 'medium',
            'created': '',
            'due_date': None,
            'tags': [],
            'description': '',
            'steps': [],
            'requires_approval': True
        }

        # Parse header metadata
        status_match = re.search(r'\*\*Status:\*\*\s*(\w+)', content)
        if status_match:
            plan['status'] = status_match.group(1)

        priority_match = re.search(r'\*\*Priority:\*\*\s*(\w+)', content)
        if priority_match:
            plan['priority'] = priority_match.group(1)

        created_match = re.search(r'\*\*Created:\*\*\s*([\d-]+)', content)
        if created_match:
            plan['created'] = created_match.group(1)

        due_match = re.search(r'\*\*Due:\*\*\s*([\d-]+|Not set)', content)
        if due_match and due_match.group(1) != 'Not set':
            plan['due_date'] = due_match.group(1)

        tags_match = re.search(r'\*\*Tags:\*\*\s*(.+)', content)
        if tags_match:
            plan['tags'] = [t.strip() for t in tags_match.group(1).split(',')]

        approval_match = re.search(r'\*\*Requires Approval:\*\*\s*(Yes|No|true|false)', content, re.IGNORECASE)
        if approval_match:
            plan['requires_approval'] = approval_match.group(1).lower() in ['yes', 'true']

        # Parse title
        title_match = re.search(r'^# Plan:\s*(.+)$', content, re.MULTILINE)
        if title_match:
            plan['title'] = title_match.group(1).strip()

        # Parse description (Overview section)
        overview_match = re.search(r'## Overview\s*\n\n(.+?)\n\n## Steps', content, re.DOTALL)
        if overview_match:
            plan['description'] = overview_match.group(1).strip()

        # Parse steps
        step_pattern = r'### Step \d+:\s*(\S+)\s*\n(?:\*\*Status:\*\*\s*[^\n]+\n)?(.+?)(?=### Step \d+|## Approval|$)'
        step_matches = re.finditer(step_pattern, content, re.DOTALL)

        for match in step_matches:
            action = match.group(1).strip()
            params_text = match.group(2)

            step = {'action': action}

            # Parse parameters
            param_pattern = r'-\s*\*\*(\w+):\*\*\s*(.+?)(?=\n-|\Z)'
            param_matches = re.finditer(param_pattern, params_text, re.DOTALL)

            for param_match in param_matches:
                key = param_match.group(1)
                value = param_match.group(2).strip()

                # Try to parse value
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif re.match(r'^\d+\.?\d*$', value):
                    try:
                        value = float(value)
                    except ValueError:
                        pass

                step[key] = value

            plan['steps'].append(step)

        return plan

    def _log_action(self, action: str, data: Dict[str, Any]):
        """Log action to plan_workflow.log."""
        log_file = self.logs_path / 'plan_workflow.log'

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "data": data
        }

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')

        logger.info(f"{action}: {json.dumps(data, indent=2)}")


# Convenience function
def get_plan_workflow() -> PlanWorkflow:
    """Get a Plan Workflow client."""
    return PlanWorkflow()


if __name__ == '__main__':
    # Test the skill
    print("=" * 60)
    print("Plan Workflow Skill - Test Mode")
    print("=" * 60)

    plan = PlanWorkflow()

    # List existing plans
    plans = plan.list_plans()
    print(f"\nExisting Plans: {json.dumps(plans, indent=2)}")

    # Create a test plan
    test_result = plan.create_plan(
        name="Test_Plan",
        title="Test Plan for Platinum Tier",
        priority="medium",
        steps=[
            {
                "action": "twitter.post_tweet",
                "content": "Testing plan workflow! #AI #Automation"
            },
            {
                "action": "personal.create_task",
                "title": "Review test results",
                "priority": "high",
                "due_date": "2026-03-20"
            }
        ],
        description="This is a test plan to verify the Plan Workflow skill.",
        requires_approval=False
    )
    print(f"\nCreated Test Plan: {json.dumps(test_result, indent=2)}")

    # Validate plan
    validation = plan.validate_plan("Test_Plan.md")
    print(f"\nValidation Result: {json.dumps(validation, indent=2)}")

    print("\nNote: To execute plans, configure all required credentials in environment variables.")
