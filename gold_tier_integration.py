#!/usr/bin/env python3
"""
Gold Tier Integration Module

Integrates all Gold Tier components with the scheduler and Plan workflow:
- Odoo MCP Server (invoice management)
- Twitter Post Skill (tweet posting with history)
- Social Media Skill (Facebook + Instagram posting)
- Personal Task Handler (personal task management)

Usage:
    from gold_tier_integration import (
        create_invoice_from_plan,
        post_social_from_plan,
        sync_personal_tasks,
        run_gold_tier_cycle
    )
    
    # Run a complete Gold Tier cycle
    result = run_gold_tier_cycle()
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gold_tier_integration')

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', 'AI_Employee_Vault'))
REPORTS_PATH = VAULT_PATH / 'Reports'
LOGS_PATH = VAULT_PATH / 'Logs'
PERSONAL_PATH = VAULT_PATH / 'Personal'

# Ensure directories exist
REPORTS_PATH.mkdir(parents=True, exist_ok=True)
LOGS_PATH.mkdir(parents=True, exist_ok=True)
PERSONAL_PATH.mkdir(parents=True, exist_ok=True)

# Gold Tier log file
GOLD_TIER_LOG = LOGS_PATH / 'gold_tier.log'


def log_gold_tier_action(action: str, data: Dict[str, Any]):
    """Log Gold Tier action to gold_tier.log."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "data": data
    }
    
    with open(GOLD_TIER_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    logger.info(f"{action}: {json.dumps(data, indent=2)}")


class GoldTierIntegration:
    """
    Gold Tier Integration for AI Employee System.
    
    Provides unified access to all Gold Tier capabilities:
    - Odoo ERP integration
    - Twitter posting
    - Facebook/Instagram posting
    - Personal task management
    """
    
    def __init__(self):
        """Initialize Gold Tier Integration."""
        self.odoo = None
        self.twitter = None
        self.social = None
        self.personal = None
        
        logger.info("GoldTierIntegration initialized")
    
    def _init_odoo(self):
        """Initialize Odoo MCP client."""
        try:
            from mcp.odoo_mcp.server import OdooMCPServer
            self.odoo = OdooMCPServer()
            logger.info("Odoo MCP client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Odoo: {e}")
            self.odoo = None
    
    def _init_twitter(self):
        """Initialize Twitter skill."""
        try:
            from .claude.skills.twitter_post.twitter_skill import TwitterSkill
            self.twitter = TwitterSkill()
            logger.info("Twitter skill initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Twitter: {e}")
            self.twitter = None
    
    def _init_social(self):
        """Initialize Social Media skill."""
        try:
            from .claude.skills.social_meta.social_skill import SocialMediaSkill
            self.social = SocialMediaSkill()
            logger.info("Social Media skill initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Social Media: {e}")
            self.social = None
    
    def _init_personal(self):
        """Initialize Personal Task Handler."""
        try:
            from .claude.skills.personal_task_handler.personal_skill import PersonalTaskHandler
            self.personal = PersonalTaskHandler()
            logger.info("Personal Task Handler initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Personal Task Handler: {e}")
            self.personal = None
    
    # ==================== ODOO INTEGRATION ====================
    
    def create_invoice_from_plan(
        self,
        plan_file: str,
        customer_name: str,
        items: List[Dict[str, Any]],
        description: str = "",
        auto_validate: bool = False
    ) -> Dict[str, Any]:
        """
        Create an invoice based on plan data.
        
        Args:
            plan_file: Path to plan file in Needs_Action
            customer_name: Customer name
            items: Invoice line items
            description: Invoice description
            auto_validate: Whether to validate immediately
            
        Returns:
            Invoice creation result
        """
        if not self.odoo:
            self._init_odoo()
        
        if not self.odoo:
            return {"status": "error", "message": "Odoo not available"}
        
        logger.info(f"Creating invoice from plan: {plan_file}")
        
        # Read plan file for reference
        plan_path = VAULT_PATH / "Needs_Action" / plan_file
        plan_content = ""
        if plan_path.exists():
            plan_content = plan_path.read_text(encoding='utf-8')
        
        # Create invoice
        result = self.odoo.create_invoice(
            customer_name=customer_name,
            items=items,
            description=description or f"Generated from plan: {plan_file}",
            auto_validate=auto_validate
        )
        
        # Log action
        log_gold_tier_action("invoice_created", {
            "plan_file": plan_file,
            "customer": customer_name,
            "result": result
        })
        
        # Save invoice record to Reports
        if result.get('status') == 'success':
            invoice_record = {
                "invoice_id": result['invoice_id'],
                "invoice_name": result['invoice_name'],
                "customer": customer_name,
                "amount": result['amount_total'],
                "state": result['state'],
                "due_date": result['due_date'],
                "plan_file": plan_file,
                "created_at": datetime.now().isoformat()
            }
            
            invoice_file = REPORTS_PATH / f"invoice_{result['invoice_id']}.json"
            with open(invoice_file, 'w', encoding='utf-8') as f:
                json.dump(invoice_record, f, indent=2)
        
        return result
    
    def list_invoices_from_period(
        self,
        status: str = "posted",
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List invoices for reporting.
        
        Args:
            status: Invoice status filter
            limit: Maximum results
            
        Returns:
            List of invoices
        """
        if not self.odoo:
            self._init_odoo()
        
        if not self.odoo:
            return {"status": "error", "message": "Odoo not available"}
        
        result = self.odoo.list_invoices(status=status, limit=limit)
        
        log_gold_tier_action("invoices_listed", {
            "status": status,
            "count": result.get('count', 0)
        })
        
        return result
    
    def record_payment_from_plan(
        self,
        invoice_id: int,
        amount: float,
        reference: str = ""
    ) -> Dict[str, Any]:
        """
        Record a payment for an invoice.
        
        Args:
            invoice_id: Odoo invoice ID
            amount: Payment amount
            reference: Payment reference
            
        Returns:
            Payment recording result
        """
        if not self.odoo:
            self._init_odoo()
        
        if not self.odoo:
            return {"status": "error", "message": "Odoo not available"}
        
        result = self.odoo.record_payment(
            invoice_id=invoice_id,
            amount=amount,
            reference=reference
        )
        
        log_gold_tier_action("payment_recorded", {
            "invoice_id": invoice_id,
            "amount": amount,
            "result": result
        })
        
        return result
    
    # ==================== TWITTER INTEGRATION ====================
    
    def post_tweet_from_plan(
        self,
        plan_file: str,
        content: str,
        save_history: bool = True
    ) -> Dict[str, Any]:
        """
        Post a tweet based on plan data.
        
        Args:
            plan_file: Path to plan file
            content: Tweet content
            save_history: Whether to save to history
            
        Returns:
            Tweet posting result
        """
        if not self.twitter:
            self._init_twitter()
        
        if not self.twitter:
            return {"status": "error", "message": "Twitter not available"}
        
        logger.info(f"Posting tweet from plan: {plan_file}")
        
        result = self.twitter.post_tweet(
            content=content,
            save_history=save_history
        )
        
        log_gold_tier_action("tweet_posted", {
            "plan_file": plan_file,
            "content": content[:50] + "..." if len(content) > 50 else content,
            "result": result
        })
        
        return result
    
    def post_thread_from_plan(
        self,
        plan_file: str,
        tweets: List[str],
        save_history: bool = True
    ) -> Dict[str, Any]:
        """
        Post a thread based on plan data.
        
        Args:
            plan_file: Path to plan file
            tweets: List of tweet contents
            save_history: Whether to save to history
            
        Returns:
            Thread posting result
        """
        if not self.twitter:
            self._init_twitter()
        
        if not self.twitter:
            return {"status": "error", "message": "Twitter not available"}
        
        logger.info(f"Posting thread from plan: {plan_file}")
        
        result = self.twitter.post_thread(
            tweets=tweets,
            save_history=save_history
        )
        
        log_gold_tier_action("thread_posted", {
            "plan_file": plan_file,
            "tweet_count": len(tweets),
            "result": result
        })
        
        return result
    
    # ==================== SOCIAL MEDIA INTEGRATION ====================
    
    def post_facebook_from_plan(
        self,
        plan_file: str,
        content: str,
        image_path: str = None,
        link: str = None
    ) -> Dict[str, Any]:
        """
        Post to Facebook based on plan data.
        
        Args:
            plan_file: Path to plan file
            content: Post content
            image_path: Path to image file
            link: URL to share
            
        Returns:
            Facebook posting result
        """
        if not self.social:
            self._init_social()
        
        if not self.social:
            return {"status": "error", "message": "Social Media not available"}
        
        logger.info(f"Posting to Facebook from plan: {plan_file}")
        
        result = self.social.post_facebook(
            content=content,
            image_path=image_path,
            link=link
        )
        
        log_gold_tier_action("facebook_posted", {
            "plan_file": plan_file,
            "content": content[:50] + "..." if len(content) > 50 else content,
            "result": result
        })
        
        return result
    
    def post_instagram_from_plan(
        self,
        plan_file: str,
        content: str,
        image_path: str
    ) -> Dict[str, Any]:
        """
        Post to Instagram based on plan data.
        
        Args:
            plan_file: Path to plan file
            content: Caption content
            image_path: Path to image file
            
        Returns:
            Instagram posting result
        """
        if not self.social:
            self._init_social()
        
        if not self.social:
            return {"status": "error", "message": "Social Media not available"}
        
        logger.info(f"Posting to Instagram from plan: {plan_file}")
        
        result = self.social.post_instagram(
            content=content,
            image_path=image_path
        )
        
        log_gold_tier_action("instagram_posted", {
            "plan_file": plan_file,
            "content": content[:50] + "..." if len(content) > 50 else content,
            "result": result
        })
        
        return result
    
    def post_to_both_from_plan(
        self,
        plan_file: str,
        content: str,
        image_path: str = None,
        facebook_link: str = None
    ) -> Dict[str, Any]:
        """
        Post to both Facebook and Instagram based on plan data.
        
        Args:
            plan_file: Path to plan file
            content: Post content
            image_path: Path to image file
            facebook_link: URL for Facebook
            
        Returns:
            Combined posting result
        """
        if not self.social:
            self._init_social()
        
        if not self.social:
            return {"status": "error", "message": "Social Media not available"}
        
        logger.info(f"Posting to both platforms from plan: {plan_file}")
        
        result = self.social.post_to_both(
            content=content,
            image_path=image_path,
            facebook_link=facebook_link
        )
        
        log_gold_tier_action("cross_posted", {
            "plan_file": plan_file,
            "content": content[:50] + "..." if len(content) > 50 else content,
            "result": result
        })
        
        return result
    
    # ==================== PERSONAL TASK INTEGRATION ====================
    
    def create_task_from_plan(
        self,
        plan_file: str,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: str = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a personal task based on plan data.
        
        Args:
            plan_file: Path to plan file
            title: Task title
            description: Task description
            priority: Task priority
            due_date: Due date (YYYY-MM-DD)
            tags: List of tags
            
        Returns:
            Task creation result
        """
        if not self.personal:
            self._init_personal()
        
        if not self.personal:
            return {"status": "error", "message": "Personal Task Handler not available"}
        
        logger.info(f"Creating task from plan: {plan_file}")
        
        result = self.personal.create_task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags or [f"plan:{plan_file}"]
        )
        
        log_gold_tier_action("task_created", {
            "plan_file": plan_file,
            "title": title,
            "result": result
        })
        
        return result
    
    def sync_plan_tasks(
        self,
        plan_file: str,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sync multiple tasks from a plan.
        
        Args:
            plan_file: Path to plan file
            tasks: List of task definitions
            
        Returns:
            Sync results
        """
        if not self.personal:
            self._init_personal()
        
        if not self.personal:
            return {"status": "error", "message": "Personal Task Handler not available"}
        
        logger.info(f"Syncing {len(tasks)} tasks from plan: {plan_file}")
        
        results = {
            "plan_file": plan_file,
            "total": len(tasks),
            "created": 0,
            "failed": 0,
            "tasks": []
        }
        
        for task_def in tasks:
            result = self.personal.create_task(
                title=task_def.get('title', 'Untitled'),
                description=task_def.get('description', ''),
                priority=task_def.get('priority', 'medium'),
                due_date=task_def.get('due_date'),
                tags=task_def.get('tags', [f"plan:{plan_file}"])
            )
            
            if result.get('status') == 'success':
                results['created'] += 1
            else:
                results['failed'] += 1
            
            results['tasks'].append(result)
        
        log_gold_tier_action("tasks_synced", results)
        
        return results
    
    def get_personal_summary(self) -> Dict[str, Any]:
        """
        Get personal task summary.

        Returns:
            Summary statistics
        """
        if not self.personal:
            self._init_personal()

        if not self.personal:
            return {"status": "error", "message": "Personal Task Handler not available"}

        return self.personal.get_summary()

    def post_social_from_plan(
        self,
        plan_file: str,
        content: str,
        platform: str = "both",
        image_path: str = None,
        facebook_link: str = None
    ) -> Dict[str, Any]:
        """
        Post to social media from plan data.

        Args:
            plan_file: Path to plan file
            content: Post content
            platform: 'facebook', 'instagram', or 'both'
            image_path: Path to image
            facebook_link: URL for Facebook

        Returns:
            Posting result
        """
        if platform == "facebook":
            return self.post_facebook_from_plan(
                plan_file=plan_file,
                content=content,
                image_path=image_path,
                link=facebook_link
            )
        elif platform == "instagram":
            if not image_path:
                return {"status": "error", "message": "Instagram requires an image"}
            return self.post_instagram_from_plan(
                plan_file=plan_file,
                content=content,
                image_path=image_path
            )
        else:  # both
            return self.post_to_both_from_plan(
                plan_file=plan_file,
                content=content,
                image_path=image_path,
                facebook_link=facebook_link
            )

    def sync_personal_tasks(
        self,
        plan_file: str,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sync tasks from plan to personal task handler.

        Args:
            plan_file: Path to plan file
            tasks: List of task definitions

        Returns:
            Sync results
        """
        return self.sync_plan_tasks(
            plan_file=plan_file,
            tasks=tasks
        )


# Convenience functions for direct usage

def create_invoice_from_plan(
    plan_file: str,
    customer_name: str,
    items: List[Dict[str, Any]],
    description: str = "",
    auto_validate: bool = False
) -> Dict[str, Any]:
    """Create an invoice from plan data."""
    integration = GoldTierIntegration()
    return integration.create_invoice_from_plan(
        plan_file=plan_file,
        customer_name=customer_name,
        items=items,
        description=description,
        auto_validate=auto_validate
    )


def post_tweet_from_plan(
    plan_file: str,
    content: str,
    save_history: bool = True
) -> Dict[str, Any]:
    """Post a tweet from plan data."""
    integration = GoldTierIntegration()
    return integration.post_tweet_from_plan(
        plan_file=plan_file,
        content=content,
        save_history=save_history
    )


def post_social_from_plan(
    plan_file: str,
    content: str,
    platform: str = "both",
    image_path: str = None,
    facebook_link: str = None
) -> Dict[str, Any]:
    """
    Post to social media from plan data.
    
    Args:
        plan_file: Path to plan file
        content: Post content
        platform: 'facebook', 'instagram', or 'both'
        image_path: Path to image
        facebook_link: URL for Facebook
    """
    integration = GoldTierIntegration()
    
    if platform == "facebook":
        return integration.post_facebook_from_plan(
            plan_file=plan_file,
            content=content,
            image_path=image_path,
            link=facebook_link
        )
    elif platform == "instagram":
        if not image_path:
            return {"status": "error", "message": "Instagram requires an image"}
        return integration.post_instagram_from_plan(
            plan_file=plan_file,
            content=content,
            image_path=image_path
        )
    else:  # both
        return integration.post_to_both_from_plan(
            plan_file=plan_file,
            content=content,
            image_path=image_path,
            facebook_link=facebook_link
        )


def sync_personal_tasks(
    plan_file: str,
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Sync tasks from plan to personal task handler."""
    integration = GoldTierIntegration()
    return integration.sync_plan_tasks(
        plan_file=plan_file,
        tasks=tasks
    )


def run_gold_tier_cycle() -> Dict[str, Any]:
    """
    Run a complete Gold Tier integration cycle.
    
    This is called by the scheduler to process all Gold Tier actions.
    
    Returns:
        Cycle execution results
    """
    logger.info("Starting Gold Tier integration cycle")
    
    integration = GoldTierIntegration()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "odoo": {"status": "initialized" if integration.odoo else "not_configured"},
        "twitter": {"status": "initialized" if integration.twitter else "not_configured"},
        "social": {"status": "initialized" if integration.social else "not_configured"},
        "personal": {"status": "initialized" if integration.personal else "not_configured"}
    }
    
    # Get personal task summary
    if integration.personal:
        results["personal_summary"] = integration.get_personal_summary()
    
    log_gold_tier_action("gold_tier_cycle", results)
    
    logger.info(f"Gold Tier cycle completed: {json.dumps(results, indent=2)}")
    
    return results


if __name__ == '__main__':
    # Test Gold Tier Integration
    print("=" * 60)
    print("Gold Tier Integration - Test Mode")
    print("=" * 60)
    
    integration = GoldTierIntegration()
    
    # Test initialization
    print("\nInitializing components...")
    integration._init_odoo()
    integration._init_twitter()
    integration._init_social()
    integration._init_personal()
    
    print(f"\nOdoo: {'Available' if integration.odoo else 'Not configured'}")
    print(f"Twitter: {'Available' if integration.twitter else 'Not configured'}")
    print(f"Social Media: {'Available' if integration.social else 'Not configured'}")
    print(f"Personal Tasks: {'Available' if integration.personal else 'Not configured'}")
    
    # Get personal summary
    if integration.personal:
        print("\nPersonal Task Summary:")
        summary = integration.get_personal_summary()
        print(json.dumps(summary, indent=2))
    
    print("\n" + "=" * 60)
