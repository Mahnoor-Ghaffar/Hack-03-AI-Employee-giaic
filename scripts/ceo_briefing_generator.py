"""
Weekly Business Audit & CEO Briefing Generator - Gold Tier

Generates comprehensive weekly business reports including:
- Financial performance (from Odoo)
- Completed tasks analysis
- Social media metrics
- Bottlenecks identification
- Proactive suggestions
- Upcoming deadlines

Trigger: Scheduled every Monday at 7:00 AM

Usage:
    python scripts/ceo_briefing_generator.py
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import shutil

from log_manager import setup_logging

# Setup logging
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="ceo_briefing")


class CEOBriefingGenerator:
    """
    Weekly CEO Briefing Generator.
    
    Aggregates data from multiple sources to create comprehensive business reports.
    """
    
    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        """
        Initialize CEO Briefing Generator.
        
        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = Path(vault_path)
        self.briefings_path = self.vault_path / "Briefings"
        self.done_path = self.vault_path / "Done"
        self.accounting_path = self.vault_path / "Accounting"
        self.social_media_path = self.vault_path / "Social_Media"
        
        # Ensure directories exist
        self.briefings_path.mkdir(parents=True, exist_ok=True)
        self.accounting_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("CEO Briefing Generator initialized")
    
    def generate_weekly_briefing(
        self,
        week_start: datetime = None,
        include_financials: bool = True,
        include_social: bool = True,
        include_tasks: bool = True
    ) -> Dict[str, Any]:
        """
        Generate weekly CEO briefing.
        
        Args:
            week_start: Start of week (defaults to last Monday)
            include_financials: Include financial report from Odoo
            include_social: Include social media metrics
            include_tasks: Include completed tasks analysis
            
        Returns:
            Dictionary with briefing data and file path
        """
        if not week_start:
            # Default to last Monday
            today = datetime.now()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday, weeks=1)
        
        week_end = week_start + timedelta(days=6)  # Sunday
        
        logger.info(f"Generating weekly briefing: {week_start.date()} to {week_end.date()}")
        
        briefing_data = {
            "period": {
                "start": week_start.strftime("%Y-%m-%d"),
                "end": week_end.strftime("%Y-%m-%d"),
                "generated_at": datetime.now().isoformat()
            },
            "executive_summary": "",
            "financial_performance": {},
            "completed_tasks": [],
            "bottlenecks": [],
            "social_media_performance": {},
            "proactive_suggestions": [],
            "upcoming_deadlines": []
        }
        
        # Gather data from different sources
        if include_financials:
            briefing_data["financial_performance"] = self._gather_financial_data(week_start, week_end)
        
        if include_tasks:
            briefing_data["completed_tasks"] = self._gather_completed_tasks(week_start, week_end)
            briefing_data["bottlenecks"] = self._identify_bottlenecks(week_start, week_end)
        
        if include_social:
            briefing_data["social_media_performance"] = self._gather_social_media_metrics(week_start, week_end)
        
        # Generate proactive suggestions
        briefing_data["proactive_suggestions"] = self._generate_suggestions(briefing_data)
        
        # Get upcoming deadlines
        briefing_data["upcoming_deadlines"] = self._get_upcoming_deadlines()
        
        # Generate executive summary
        briefing_data["executive_summary"] = self._generate_executive_summary(briefing_data)
        
        # Create briefing document
        briefing_file = self._create_briefing_document(briefing_data, week_start)
        
        logger.info(f"Weekly briefing generated: {briefing_file}")
        
        return {
            "status": "success",
            "briefing_file": str(briefing_file),
            "data": briefing_data
        }
    
    def _gather_financial_data(
        self,
        week_start: datetime,
        week_end: datetime
    ) -> Dict[str, Any]:
        """
        Gather financial data from Odoo.
        
        Args:
            week_start: Start of week
            week_end: End of week
            
        Returns:
            Financial performance data
        """
        financial_data = {
            "revenue": 0,
            "expenses": 0,
            "profit": 0,
            "outstanding_invoices": 0,
            "paid_invoices": 0,
            "currency": "USD",
            "trend": "stable"
        }
        
        try:
            from scripts.odoo_mcp_server import OdooMCPServer
            
            odoo = OdooMCPServer()
            
            # Test connection
            conn_result = odoo.test_connection()
            if conn_result.get("connected"):
                # Get invoices for the period
                invoices_result = odoo.get_invoices(
                    status="posted",
                    limit=100
                )
                
                if invoices_result.get("status") == "success":
                    invoices = invoices_result.get("invoices", [])
                    
                    # Calculate revenue and outstanding
                    for invoice in invoices:
                        amount = invoice.get("amount", 0)
                        payment_state = invoice.get("payment_status", "")
                        
                        if payment_state == "paid":
                            financial_data["paid_invoices"] += amount
                            financial_data["revenue"] += amount
                        elif payment_state in ("not_paid", "partial"):
                            financial_data["outstanding_invoices"] += amount
                    
                    # Get profit and loss report
                    pl_report = odoo.get_financial_report(
                        report_type="profit_loss",
                        date_from=week_start.strftime("%Y-%m-%d"),
                        date_to=week_end.strftime("%Y-%m-%d")
                    )
                    
                    if pl_report.get("status") == "success":
                        financial_data["revenue"] = pl_report.get("income", financial_data["revenue"])
                        financial_data["expenses"] = pl_report.get("expenses", financial_data["expenses"])
                        financial_data["profit"] = pl_report.get("net_profit", financial_data["profit"])
                    
                    # Determine trend
                    if financial_data["profit"] > 0:
                        financial_data["trend"] = "positive"
                    elif financial_data["profit"] < 0:
                        financial_data["trend"] = "negative"
                    
                    logger.info(f"Gathered financial data: Revenue=${financial_data['revenue']}, Profit=${financial_data['profit']}")
                else:
                    logger.warning(f"Could not get invoices: {invoices_result.get('message')}")
            else:
                logger.warning(f"Odoo not connected: {conn_result.get('message')}")
                
        except ImportError:
            logger.warning("Odoo MCP server not available. Using placeholder financial data.")
        except Exception as e:
            logger.error(f"Error gathering financial data: {e}")
        
        return financial_data
    
    def _gather_completed_tasks(
        self,
        week_start: datetime,
        week_end: datetime
    ) -> List[Dict[str, Any]]:
        """
        Gather completed tasks from vault.
        
        Args:
            week_start: Start of week
            week_end: End of week
            
        Returns:
            List of completed tasks
        """
        completed_tasks = []
        
        try:
            if not self.done_path.exists():
                logger.warning("Done folder not found")
                return completed_tasks
            
            # Get all .md files in Done folder
            done_files = list(self.done_path.glob("*.md"))
            
            for file in done_files:
                try:
                    content = file.read_text()
                    
                    # Parse frontmatter
                    metadata = self._parse_frontmatter(content)
                    
                    # Check if completed within date range
                    completed_date = metadata.get("completed_date", "")
                    if completed_date:
                        try:
                            task_date = datetime.fromisoformat(completed_date)
                            if week_start <= task_date <= week_end:
                                completed_tasks.append({
                                    "task_name": file.stem,
                                    "task_type": metadata.get("type", "unknown"),
                                    "completed_date": completed_date,
                                    "summary": metadata.get("summary", content[:200])
                                })
                        except ValueError:
                            pass
                    
                except Exception as e:
                    logger.debug(f"Error reading done file {file}: {e}")
            
            logger.info(f"Gathered {len(completed_tasks)} completed tasks")
            
        except Exception as e:
            logger.error(f"Error gathering completed tasks: {e}")
        
        return completed_tasks
    
    def _identify_bottlenecks(
        self,
        week_start: datetime,
        week_end: datetime
    ) -> List[Dict[str, Any]]:
        """
        Identify bottlenecks from task analysis.
        
        Args:
            week_start: Start of week
            week_end: End of week
            
        Returns:
            List of identified bottlenecks
        """
        bottlenecks = []
        
        # Analyze tasks in Needs_Action for old items
        needs_action_path = self.vault_path / "Needs_Action"
        
        if needs_action_path.exists():
            for file in needs_action_path.glob("*.md"):
                try:
                    created_date = file.stat().st_ctime
                    created_datetime = datetime.fromtimestamp(created_date)
                    age_days = (datetime.now() - created_datetime).days
                    
                    if age_days > 7:  # Older than 1 week
                        bottlenecks.append({
                            "task": file.stem,
                            "age_days": age_days,
                            "issue": f"Task pending for {age_days} days",
                            "severity": "high" if age_days > 14 else "medium"
                        })
                except Exception as e:
                    logger.debug(f"Error analyzing file {file}: {e}")
        
        # Check for rejected approvals
        rejected_path = self.vault_path / "Rejected"
        if rejected_path.exists():
            rejected_count = len(list(rejected_path.glob("*.md")))
            if rejected_count > 0:
                bottlenecks.append({
                    "task": "approval_rejections",
                    "count": rejected_count,
                    "issue": f"{rejected_count} actions rejected or timed out",
                    "severity": "medium"
                })
        
        logger.info(f"Identified {len(bottlenecks)} bottlenecks")
        return bottlenecks
    
    def _gather_social_media_metrics(
        self,
        week_start: datetime,
        week_end: datetime
    ) -> Dict[str, Any]:
        """
        Gather social media metrics.
        
        Args:
            week_start: Start of week
            week_end: End of week
            
        Returns:
            Social media performance data
        """
        metrics = {
            "linkedin": {
                "posts": 0,
                "engagement": "N/A"
            },
            "facebook": {
                "posts": 0,
                "engagement": "N/A"
            },
            "instagram": {
                "posts": 0,
                "engagement": "N/A"
            },
            "twitter": {
                "tweets": 0,
                "engagement": "N/A"
            }
        }
        
        try:
            if not self.social_media_path.exists():
                logger.warning("Social_Media folder not found")
                return metrics
            
            # Count posts by platform
            for file in self.social_media_path.glob("*.md"):
                try:
                    content = file.read_text()
                    
                    if "platform: linkedin" in content.lower():
                        metrics["linkedin"]["posts"] += 1
                    elif "platform: facebook" in content.lower():
                        metrics["facebook"]["posts"] += 1
                    elif "platform: instagram" in content.lower():
                        metrics["instagram"]["posts"] += 1
                    elif "platform: twitter" in content.lower():
                        metrics["twitter"]["tweets"] += 1
                    
                except Exception as e:
                    logger.debug(f"Error reading social media file {file}: {e}")
            
            logger.info(f"Gathered social media metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Error gathering social media metrics: {e}")
        
        return metrics
    
    def _generate_suggestions(self, briefing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate proactive suggestions based on briefing data.
        
        Args:
            briefing_data: Complete briefing data
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Financial suggestions
        financials = briefing_data.get("financial_performance", {})
        if financials.get("outstanding_invoices", 0) > 0:
            suggestions.append({
                "category": "finance",
                "priority": "high",
                "suggestion": f"Follow up on ${financials['outstanding_invoices']} in outstanding invoices",
                "action": "Review Accounts Receivable and send payment reminders"
            })
        
        if financials.get("trend") == "negative":
            suggestions.append({
                "category": "finance",
                "priority": "high",
                "suggestion": "Revenue trend is negative this week",
                "action": "Review pricing strategy and sales pipeline"
            })
        
        # Task management suggestions
        bottlenecks = briefing_data.get("bottlenecks", [])
        if len(bottlenecks) > 0:
            high_severity = [b for b in bottlenecks if b.get("severity") == "high"]
            if high_severity:
                suggestions.append({
                    "category": "productivity",
                    "priority": "high",
                    "suggestion": f"{len(high_severity)} high-priority bottlenecks identified",
                    "action": "Review and prioritize aging tasks in Needs_Action folder"
                })
        
        # Social media suggestions
        social = briefing_data.get("social_media_performance", {})
        total_posts = sum(platform.get("posts", 0) for platform in social.values())
        if total_posts == 0:
            suggestions.append({
                "category": "marketing",
                "priority": "medium",
                "suggestion": "No social media activity this week",
                "action": "Create and schedule social media content for next week"
            })
        
        logger.info(f"Generated {len(suggestions)} proactive suggestions")
        return suggestions
    
    def _get_upcoming_deadlines(self) -> List[Dict[str, Any]]:
        """
        Get upcoming deadlines from tasks and business goals.
        
        Returns:
            List of upcoming deadlines
        """
        deadlines = []
        
        # Check Business_Goals.md for deadlines
        business_goals_path = self.vault_path / "Business_Goals.md"
        if business_goals_path.exists():
            try:
                content = business_goals_path.read_text()
                
                # Look for dates in the next 2 weeks
                # This is simplified - would need better date parsing in production
                lines = content.split("\n")
                for line in lines:
                    if "due" in line.lower() or "deadline" in line.lower():
                        deadlines.append({
                            "source": "Business_Goals.md",
                            "description": line.strip(),
                            "type": "business_goal"
                        })
            except Exception as e:
                logger.debug(f"Error reading Business_Goals.md: {e}")
        
        # Check Plans folder for project deadlines
        plans_path = self.vault_path / "Plans"
        if plans_path.exists():
            for file in plans_path.glob("*.md"):
                try:
                    content = file.read_text()
                    if "deadline" in content.lower() or "due" in content.lower():
                        deadlines.append({
                            "source": file.name,
                            "description": "Project deadline found",
                            "type": "project"
                        })
                except Exception as e:
                    logger.debug(f"Error reading plan file {file}: {e}")
        
        # Add next week's expected deadlines
        next_week = datetime.now() + timedelta(days=7)
        deadlines.append({
            "source": "recurring",
            "description": f"Weekly briefing due by {next_week.strftime('%A, %B %d')}",
            "type": "recurring",
            "date": next_week.strftime("%Y-%m-%d")
        })
        
        logger.info(f"Found {len(deadlines)} upcoming deadlines")
        return deadlines
    
    def _generate_executive_summary(self, briefing_data: Dict[str, Any]) -> str:
        """
        Generate executive summary from briefing data.
        
        Args:
            briefing_data: Complete briefing data
            
        Returns:
            Executive summary text
        """
        summary_parts = []
        
        # Financial summary
        financials = briefing_data.get("financial_performance", {})
        if financials:
            revenue = financials.get("revenue", 0)
            profit = financials.get("profit", 0)
            trend = financials.get("trend", "stable")
            
            if trend == "positive":
                summary_parts.append(f"Strong financial performance with ${revenue:,.2f} revenue and ${profit:,.2f} profit.")
            elif trend == "negative":
                summary_parts.append(f"Challenging week with ${revenue:,.2f} revenue. Attention needed.")
            else:
                summary_parts.append(f"Stable financial performance with ${revenue:,.2f} revenue.")
        
        # Tasks summary
        tasks = briefing_data.get("completed_tasks", [])
        if tasks:
            summary_parts.append(f"{len(tasks)} tasks completed this week.")
        
        # Bottlenecks summary
        bottlenecks = briefing_data.get("bottlenecks", [])
        if bottlenecks:
            high_priority = len([b for b in bottlenecks if b.get("severity") == "high"])
            if high_priority > 0:
                summary_parts.append(f"{high_priority} high-priority bottlenecks require attention.")
        
        # Social media summary
        social = briefing_data.get("social_media_performance", {})
        total_posts = sum(platform.get("posts", 0) for platform in social.values())
        if total_posts > 0:
            summary_parts.append(f"{total_posts} social media posts published.")
        else:
            summary_parts.append("No social media activity this week.")
        
        return " ".join(summary_parts) if summary_parts else "Weekly briefing generated. Review sections below for details."
    
    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML frontmatter from markdown content.
        
        Args:
            content: Markdown content with frontmatter
            
        Returns:
            Dictionary of frontmatter fields
        """
        metadata = {}
        
        if content.startswith("---"):
            try:
                end = content.index("---", 3)
                frontmatter = content[4:end].strip()
                
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()
                
            except (ValueError, IndexError):
                pass
        
        return metadata
    
    def _create_briefing_document(
        self,
        briefing_data: Dict[str, Any],
        week_start: datetime
    ) -> Path:
        """
        Create formatted briefing markdown document.
        
        Args:
            briefing_data: Briefing data
            week_start: Start of week
            
        Returns:
            Path to created briefing file
        """
        week_end = week_start + timedelta(days=6)
        filename = f"CEO_Briefing_{week_start.strftime('%Y-%m-%d')}_to_{week_end.strftime('%Y-%m-%d')}.md"
        filepath = self.briefings_path / filename
        
        financials = briefing_data.get("financial_performance", {})
        tasks = briefing_data.get("completed_tasks", [])
        bottlenecks = briefing_data.get("bottlenecks", [])
        social = briefing_data.get("social_media_performance", {})
        suggestions = briefing_data.get("proactive_suggestions", [])
        deadlines = briefing_data.get("upcoming_deadlines", [])

        # Pre-build suggestion blocks to avoid backslash in f-string expression
        suggestion_blocks = []
        for s in suggestions:
            block = f"### {s['category'].title()} (Priority: {s['priority']})\n{s['suggestion']}\n\n**Action:** {s['action']}\n"
            suggestion_blocks.append(block)
        suggestions_text = chr(10).join(suggestion_blocks) if suggestions else '*No suggestions at this time.*'

        content = f"""---
type: ceo_briefing
period_start: {briefing_data['period']['start']}
period_end: {briefing_data['period']['end']}
generated: {briefing_data['period']['generated_at']}
---

# Monday Morning CEO Briefing

**Period:** {week_start.strftime('%B %d, %Y')} - {week_end.strftime('%B %d, %Y')}
**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

---

## Executive Summary

{briefing_data['executive_summary']}

---

## Financial Performance

| Metric | Amount | Status |
|--------|--------|--------|
| Revenue | ${financials.get('revenue', 0):,.2f} | {financials.get('trend', 'N/A')} |
| Expenses | ${financials.get('expenses', 0):,.2f} | |
| Profit | ${financials.get('profit', 0):,.2f} | |
| Outstanding Invoices | ${financials.get('outstanding_invoices', 0):,.2f} | |
| Paid Invoices | ${financials.get('paid_invoices', 0):,.2f} | |

---

## Completed Tasks

{'✅ ' + chr(10).join([f"- **{task['task_name']}** ({task['completed_date']})" for task in tasks]) if tasks else '*No tasks completed this week.*'}

---

## Bottlenecks Identified

{chr(10).join([f"⚠️ **{b['task']}**: {b['issue']} (Severity: {b['severity']})" for b in bottlenecks]) if bottlenecks else '*No bottlenecks identified.*'}

---

## Social Media Performance

| Platform | Posts | Engagement |
|----------|-------|------------|
| LinkedIn | {social.get('linkedin', {}).get('posts', 0)} | {social.get('linkedin', {}).get('engagement', 'N/A')} |
| Facebook | {social.get('facebook', {}).get('posts', 0)} | {social.get('facebook', {}).get('engagement', 'N/A')} |
| Instagram | {social.get('instagram', {}).get('posts', 0)} | {social.get('instagram', {}).get('engagement', 'N/A')} |
| Twitter | {social.get('twitter', {}).get('tweets', 0)} | {social.get('twitter', {}).get('engagement', 'N/A')} |

---

## Proactive Suggestions

{suggestions_text}

---

## Upcoming Deadlines

{chr(10).join([f"- **{d['description']}** ({d.get('date', 'TBD')})" for d in deadlines]) if deadlines else '*No upcoming deadlines.*'}

---

## Next Week's Focus

Based on this week's performance, recommended focus areas:

1. {'Address outstanding invoices and improve cash flow' if financials.get('outstanding_invoices', 0) > 0 else 'Maintain current financial momentum'}
2. {'Clear aging tasks from Needs_Action queue' if bottlenecks else 'Continue efficient task completion'}
3. {'Increase social media presence' if social.get('linkedin', {}).get('posts', 0) + social.get('facebook', {}).get('posts', 0) + social.get('twitter', {}).get('tweets', 0) == 0 else 'Maintain consistent social media activity'}

---

*This briefing was automatically generated by your AI Employee Gold Tier system.*
"""
        
        filepath.write_text(content)
        logger.info(f"Created briefing document: {filepath}")
        
        return filepath


def generate_ceo_briefing() -> Dict[str, Any]:
    """
    Convenience function to generate CEO briefing.
    
    Returns:
        Result dictionary with briefing file path
    """
    generator = CEOBriefingGenerator()
    return generator.generate_weekly_briefing()


if __name__ == "__main__":
    # Test CEO Briefing Generator
    print("Testing CEO Briefing Generator...")
    
    generator = CEOBriefingGenerator()
    result = generator.generate_weekly_briefing()
    
    if result.get("status") == "success":
        print(f"\n✅ Weekly briefing generated successfully!")
        print(f"📄 Briefing file: {result['briefing_file']}")
        print(f"\n📊 Summary:")
        print(f"   Period: {result['data']['period']['start']} to {result['data']['period']['end']}")
        print(f"   Revenue: ${result['data']['financial_performance'].get('revenue', 0):,.2f}")
        print(f"   Completed Tasks: {len(result['data']['completed_tasks'])}")
        print(f"   Bottlenecks: {len(result['data']['bottlenecks'])}")
        print(f"   Suggestions: {len(result['data']['proactive_suggestions'])}")
    else:
        print(f"\n❌ Briefing generation failed: {result}")
