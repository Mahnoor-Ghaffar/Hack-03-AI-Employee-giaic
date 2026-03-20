#!/usr/bin/env python3
# =============================================================================
# CEO Weekly Briefing Generator
# =============================================================================
# Generates automated weekly CEO briefing every Sunday
# Reads: /Done folder, Accounting data
# Summarizes: Revenue, Completed tasks, Pending approvals, Issues
# Output: /Vault/Briefings/YYYY-MM-DD_CEO_Briefing.md
# =============================================================================

import os
import sys
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict


# =============================================================================
# Configuration
# =============================================================================

# Base paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
VAULT_ROOT = PROJECT_ROOT / "AI_Employee_Vault"

# Input folders
DONE_FOLDER = VAULT_ROOT / "Done"
ACCOUNTING_FOLDER = VAULT_ROOT / "Accounting"
PENDING_APPROVAL_FOLDER = VAULT_ROOT / "Pending_Approval"
LOGS_FOLDER = VAULT_ROOT / "Logs"
REJECTED_FOLDER = VAULT_ROOT / "Rejected"

# Output folder
BRIEFINGS_FOLDER = VAULT_ROOT / "Briefings"

# Briefing file naming
BRIEFING_DATE_FORMAT = "%Y-%m-%d"
BRIEFING_FILENAME_FORMAT = "%Y-%m-%d_CEO_Briefing.md"


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class RevenueData:
    """Revenue information from accounting"""
    total_revenue: float = 0.0
    pending_invoices: float = 0.0
    paid_invoices: float = 0.0
    invoice_count: int = 0
    payment_count: int = 0
    currency: str = "$"


@dataclass
class TaskSummary:
    """Completed tasks summary"""
    total_completed: int = 0
    by_category: Dict[str, int] = None
    by_day: Dict[str, int] = None
    
    def __post_init__(self):
        if self.by_category is None:
            self.by_category = {}
        if self.by_day is None:
            self.by_day = {}


@dataclass
class PendingApproval:
    """Pending approval item"""
    filename: str
    category: str
    created_date: str
    days_pending: int


@dataclass
class Issue:
    """Issue/error item"""
    source: str
    description: str
    count: int
    last_occurrence: str


@dataclass
class WeeklyBriefing:
    """Complete weekly briefing data"""
    period_start: str
    period_end: str
    generated_at: str
    revenue: RevenueData
    completed_tasks: TaskSummary
    pending_approvals: List[PendingApproval]
    issues: List[Issue]
    highlights: List[str]
    recommendations: List[str]


# =============================================================================
# Data Collectors
# =============================================================================

class RevenueCollector:
    """Collects revenue data from Accounting folder"""
    
    def __init__(self, accounting_folder: Path):
        self.folder = accounting_folder
    
    def collect(self, start_date: datetime, end_date: datetime) -> RevenueData:
        """Collect revenue data for the period"""
        revenue = RevenueData()
        
        if not self.folder.exists():
            return revenue
        
        # Look for invoice and payment files
        for file_path in self.folder.iterdir():
            if not file_path.is_file():
                continue
            
            try:
                content = file_path.read_text()
                
                # Extract amounts from invoices
                if self._is_invoice(file_path):
                    amount = self._extract_amount(content)
                    if amount:
                        revenue.invoice_count += 1
                        if self._is_paid(content):
                            revenue.paid_invoices += amount
                        else:
                            revenue.pending_invoices += amount
                
                # Extract payment amounts
                elif self._is_payment(file_path):
                    amount = self._extract_amount(content)
                    if amount:
                        revenue.payment_count += 1
                        revenue.paid_invoices += amount
                
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        revenue.total_revenue = revenue.paid_invoices
        return revenue
    
    def _is_invoice(self, file_path: Path) -> bool:
        """Check if file is an invoice"""
        name = file_path.name.lower()
        return "invoice" in name or "inv-" in name or name.startswith("inv")
    
    def _is_payment(self, file_path: Path) -> bool:
        """Check if file is a payment record"""
        name = file_path.name.lower()
        return "payment" in name or "receipt" in name or "paid" in name
    
    def _extract_amount(self, content: str) -> Optional[float]:
        """Extract amount from file content"""
        # Look for patterns like $100.00, 100.00, Amount: 100
        patterns = [
            r'\$[\d,]+\.?\d*',
            r'amount[:\s]*\$?[\d,]+\.?\d*',
            r'total[:\s]*\$?[\d,]+\.?\d*',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                text = match.group()
                # Extract just the number
                numbers = re.findall(r'[\d,]+\.?\d*', text)
                if numbers:
                    try:
                        return float(numbers[0].replace(',', ''))
                    except ValueError:
                        pass
        return None
    
    def _is_paid(self, content: str) -> bool:
        """Check if invoice is marked as paid"""
        paid_indicators = ['paid', 'payment received', 'settled', 'completed']
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in paid_indicators)


class TaskCollector:
    """Collects completed tasks from Done folder"""
    
    def __init__(self, done_folder: Path):
        self.folder = done_folder
    
    def collect(self, start_date: datetime, end_date: datetime) -> TaskSummary:
        """Collect completed tasks for the period"""
        summary = TaskSummary()
        by_category = defaultdict(int)
        by_day = defaultdict(int)
        
        if not self.folder.exists():
            return summary
        
        for file_path in self.folder.iterdir():
            if not file_path.is_file():
                continue
            
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # Check if within period
                if start_date <= mtime <= end_date:
                    summary.total_completed += 1
                    
                    # Categorize by file type/folder
                    category = self._categorize(file_path)
                    by_category[category] += 1
                    
                    # Group by day
                    day_name = mtime.strftime("%A")
                    by_day[day_name] += 1
                    
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        summary.by_category = dict(by_category)
        summary.by_day = dict(by_day)
        return summary
    
    def _categorize(self, file_path: Path) -> str:
        """Categorize task by file type or content"""
        name = file_path.name.lower()
        suffix = file_path.suffix.lower()
        
        # By file extension
        if suffix == '.md':
            # By filename patterns
            if 'email' in name:
                return 'Email'
            elif 'social' in name or 'post' in name or 'linkedin' in name:
                return 'Social Media'
            elif 'invoice' in name or 'payment' in name:
                return 'Accounting'
            elif 'report' in name:
                return 'Reports'
            elif 'plan' in name:
                return 'Planning'
            elif 'brief' in name:
                return 'Briefings'
        
        # By parent folder
        parent = file_path.parent.name.lower()
        if 'email' in parent:
            return 'Email'
        elif 'social' in parent:
            return 'Social Media'
        
        return 'Other'


class ApprovalCollector:
    """Collects pending approvals"""
    
    def __init__(self, pending_folder: Path):
        self.folder = pending_folder
    
    def collect(self) -> List[PendingApproval]:
        """Collect all pending approvals"""
        approvals = []
        
        if not self.folder.exists():
            return approvals
        
        now = datetime.now()
        
        for category_folder in self.folder.iterdir():
            if not category_folder.is_dir():
                continue
            
            category = category_folder.name
            
            for file_path in category_folder.iterdir():
                if not file_path.is_file():
                    continue
                
                # Skip approval marker files
                if file_path.suffix == '.json':
                    continue
                
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    days_pending = (now - mtime).days
                    
                    approvals.append(PendingApproval(
                        filename=file_path.name,
                        category=category,
                        created_date=mtime.strftime(BRIEFING_DATE_FORMAT),
                        days_pending=days_pending
                    ))
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        
        # Sort by days pending (oldest first)
        approvals.sort(key=lambda x: x.days_pending, reverse=True)
        return approvals


class IssueCollector:
    """Collects issues from logs and rejected items"""
    
    def __init__(self, logs_folder: Path, rejected_folder: Path):
        self.logs_folder = logs_folder
        self.rejected_folder = rejected_folder
    
    def collect(self, start_date: datetime, end_date: datetime) -> List[Issue]:
        """Collect issues for the period"""
        issues = []
        error_counts = defaultdict(lambda: {"count": 0, "last": None})
        
        # Collect from logs
        if self.logs_folder.exists():
            for log_file in self.logs_folder.iterdir():
                if not log_file.is_file() or log_file.suffix not in ['.log', '.md']:
                    continue
                
                try:
                    content = log_file.read_text()
                    
                    # Find error patterns
                    error_patterns = [
                        (r'ERROR[:\s]+(.+)', 'Error'),
                        (r'FAILED[:\s]+(.+)', 'Failed'),
                        (r'EXCEPTION[:\s]+(.+)', 'Exception'),
                        (r'CRITICAL[:\s]+(.+)', 'Critical'),
                    ]
                    
                    for pattern, issue_type in error_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches[:10]:  # Limit per file
                            key = f"{issue_type}: {match[:50]}"
                            error_counts[key]["count"] += 1
                            error_counts[key]["last"] = datetime.now().strftime(BRIEFING_DATE_FORMAT)
                            
                except Exception as e:
                    pass
        
        # Collect from rejected folder
        if self.rejected_folder.exists():
            for file_path in self.rejected_folder.iterdir():
                if file_path.is_file():
                    try:
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if start_date <= mtime <= end_date:
                            key = f"Rejected: {file_path.name}"
                            error_counts[key]["count"] += 1
                            error_counts[key]["last"] = mtime.strftime(BRIEFING_DATE_FORMAT)
                    except Exception:
                        pass
        
        # Convert to Issue list
        for desc, data in error_counts.items():
            if data["count"] > 0:
                issues.append(Issue(
                    source="System",
                    description=desc,
                    count=data["count"],
                    last_occurrence=data["last"] or "Unknown"
                ))
        
        # Sort by count (most frequent first)
        issues.sort(key=lambda x: x.count, reverse=True)
        return issues[:20]  # Limit to top 20


# =============================================================================
# Briefing Generator
# =============================================================================

class BriefingGenerator:
    """Generates the weekly CEO briefing"""
    
    def __init__(self):
        self.revenue_collector = RevenueCollector(ACCOUNTING_FOLDER)
        self.task_collector = TaskCollector(DONE_FOLDER)
        self.approval_collector = ApprovalCollector(PENDING_APPROVAL_FOLDER)
        self.issue_collector = IssueCollector(LOGS_FOLDER, REJECTED_FOLDER)
    
    def generate(self, week_start: Optional[datetime] = None) -> WeeklyBriefing:
        """Generate briefing for the given week"""
        if week_start is None:
            # Default: last week (Monday to Sunday)
            today = datetime.now()
            # Go back to last Monday
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday, weeks=1)
        
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        # Collect data
        revenue = self.revenue_collector.collect(week_start, week_end)
        completed_tasks = self.task_collector.collect(week_start, week_end)
        pending_approvals = self.approval_collector.collect()
        issues = self.issue_collector.collect(week_start, week_end)
        
        # Generate highlights and recommendations
        highlights = self._generate_highlights(revenue, completed_tasks)
        recommendations = self._generate_recommendations(revenue, completed_tasks, 
                                                         pending_approvals, issues)
        
        return WeeklyBriefing(
            period_start=week_start.strftime(BRIEFING_DATE_FORMAT),
            period_end=week_end.strftime(BRIEFING_DATE_FORMAT),
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            revenue=revenue,
            completed_tasks=completed_tasks,
            pending_approvals=pending_approvals,
            issues=issues,
            highlights=highlights,
            recommendations=recommendations
        )
    
    def _generate_highlights(self, revenue: RevenueData, 
                             tasks: TaskSummary) -> List[str]:
        """Generate key highlights"""
        highlights = []
        
        # Revenue highlights
        if revenue.total_revenue > 0:
            highlights.append(f"Revenue: {revenue.currency}{revenue.total_revenue:,.2f} collected")
        
        if revenue.pending_invoices > 0:
            highlights.append(f"{revenue.currency}{revenue.pending_invoices:,.2f} in pending invoices")
        
        # Task highlights
        if tasks.total_completed > 0:
            highlights.append(f"{tasks.total_completed} tasks completed this week")
            
            # Top category
            if tasks.by_category:
                top_cat = max(tasks.by_category.items(), key=lambda x: x[1])
                highlights.append(f"Most active: {top_cat[0]} ({top_cat[1]} tasks)")
        
        # Busiest day
        if tasks.by_day:
            busiest_day = max(tasks.by_day.items(), key=lambda x: x[1])
            highlights.append(f"Busiest day: {busiest_day[0]} ({busiest_day[1]} tasks)")
        
        return highlights
    
    def _generate_recommendations(self, revenue: RevenueData,
                                   tasks: TaskSummary,
                                   pending_approvals: List[PendingApproval],
                                   issues: List[Issue]) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        # Pending approvals
        if pending_approvals:
            old_approvals = [a for a in pending_approvals if a.days_pending > 2]
            if old_approvals:
                recommendations.append(
                    f"Review {len(old_approvals)} pending approval(s) over 2 days old"
                )
        
        # Revenue follow-up
        if revenue.pending_invoices > 0:
            recommendations.append(
                f"Follow up on {revenue.currency}{revenue.pending_invoices:,.2f} in unpaid invoices"
            )
        
        # Issues
        if issues:
            critical_issues = [i for i in issues if i.count > 5]
            if critical_issues:
                recommendations.append(
                    f"Investigate recurring issues ({len(critical_issues)} types with 5+ occurrences)"
                )
        
        # Productivity
        if tasks.total_completed > 0:
            if tasks.total_completed < 10:
                recommendations.append(
                    "Consider reviewing workflow efficiency (low task completion)"
                )
        
        return recommendations


# =============================================================================
# Report Writer
# =============================================================================

class BriefingWriter:
    """Writes briefing to markdown file"""
    
    def __init__(self, output_folder: Path):
        self.folder = output_folder
        self.folder.mkdir(parents=True, exist_ok=True)
    
    def write(self, briefing: WeeklyBriefing) -> Path:
        """Write briefing to file"""
        filename = f"{briefing.period_start}_CEO_Briefing.md"
        file_path = self.folder / filename
        
        content = self._format_briefing(briefing)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        return file_path
    
    def _format_briefing(self, briefing: WeeklyBriefing) -> str:
        """Format briefing as markdown"""
        content = f"""# CEO Weekly Briefing

**Period:** {briefing.period_start} to {briefing.period_end}  
**Generated:** {briefing.generated_at}

---

## Executive Summary

"""
        
        # Highlights
        if briefing.highlights:
            content += "### Key Highlights\n\n"
            for highlight in briefing.highlights:
                content += f"- ✅ {highlight}\n"
            content += "\n"
        
        # Revenue Section
        content += f"""---

## Revenue Summary

| Metric | Amount |
|--------|--------|
| Total Revenue | {briefing.revenue.currency}{briefing.revenue.total_revenue:,.2f} |
| Paid Invoices | {briefing.revenue.currency}{briefing.revenue.paid_invoices:,.2f} |
| Pending Invoices | {briefing.revenue.currency}{briefing.revenue.pending_invoices:,.2f} |
| Invoice Count | {briefing.revenue.invoice_count} |
| Payments Received | {briefing.revenue.payment_count} |

"""
        
        # Completed Tasks Section
        content += """---

## Completed Tasks

"""
        content += f"**Total Completed:** {briefing.completed_tasks.total_completed}\n\n"
        
        if briefing.completed_tasks.by_category:
            content += "### By Category\n\n"
            content += "| Category | Count |\n"
            content += "|----------|-------|\n"
            for cat, count in sorted(briefing.completed_tasks.by_category.items(), 
                                     key=lambda x: x[1], reverse=True):
                content += f"| {cat} | {count} |\n"
            content += "\n"
        
        if briefing.completed_tasks.by_day:
            content += "### By Day\n\n"
            content += "| Day | Tasks |\n"
            content += "|-----|-------|\n"
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            for day in day_order:
                if day in briefing.completed_tasks.by_day:
                    content += f"| {day} | {briefing.completed_tasks.by_day[day]} |\n"
            content += "\n"
        
        # Pending Approvals Section
        content += """---

## Pending Approvals

"""
        if briefing.pending_approvals:
            content += f"**Total Pending:** {len(briefing.pending_approvals)}\n\n"
            content += "| File | Category | Created | Days Pending |\n"
            content += "|------|----------|---------|--------------|\n"
            for approval in briefing.pending_approvals[:15]:  # Limit display
                days_emoji = "⚠️" if approval.days_pending > 2 else ""
                content += f"| {approval.filename} | {approval.category} | {approval.created_date} | {approval.days_pending} {days_emoji} |\n"
            
            if len(briefing.pending_approvals) > 15:
                content += f"\n*...and {len(briefing.pending_approvals) - 15} more*\n"
        else:
            content += "*No pending approvals*\n"
        content += "\n"
        
        # Issues Section
        content += """---

## Issues & Errors

"""
        if briefing.issues:
            content += "| Issue | Count | Last Occurrence |\n"
            content += "|-------|-------|------------------|\n"
            for issue in briefing.issues[:10]:  # Limit display
                content += f"| {issue.description[:50]} | {issue.count} | {issue.last_occurrence} |\n"
            
            if len(briefing.issues) > 10:
                content += f"\n*...and {len(briefing.issues) - 10} more*\n"
        else:
            content += "*No issues detected*\n"
        content += "\n"
        
        # Recommendations Section
        content += """---

## Recommendations

"""
        if briefing.recommendations:
            for i, rec in enumerate(briefing.recommendations, 1):
                content += f"{i}. {rec}\n"
        else:
            content += "*No specific recommendations this week*\n"
        content += "\n"
        
        # Footer
        content += f"""---

*Report generated automatically by AI Employee System*  
*Next briefing: {(datetime.strptime(briefing.period_end, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")}*
"""
        
        return content


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate CEO Weekly Briefing")
    parser.add_argument(
        "--week-start",
        type=str,
        help="Start date of week (YYYY-MM-DD). Default: last Monday"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output folder. Default: AI_Employee_Vault/Briefings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show briefing without saving"
    )
    
    args = parser.parse_args()
    
    # Parse week start if provided
    week_start = None
    if args.week_start:
        try:
            week_start = datetime.strptime(args.week_start, BRIEFING_DATE_FORMAT)
        except ValueError:
            print(f"Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Set output folder
    output_folder = Path(args.output) if args.output else BRIEFINGS_FOLDER
    
    # Generate briefing
    print("Generating CEO Weekly Briefing...")
    generator = BriefingGenerator()
    briefing = generator.generate(week_start)
    
    # Output
    if args.dry_run:
        writer = BriefingWriter(output_folder)
        print(writer._format_briefing(briefing))
    else:
        writer = BriefingWriter(output_folder)
        file_path = writer.write(briefing)
        print(f"Briefing generated: {file_path}")
        
        # Print summary
        print(f"\nPeriod: {briefing.period_start} to {briefing.period_end}")
        print(f"Revenue: ${briefing.revenue.total_revenue:,.2f}")
        print(f"Tasks Completed: {briefing.completed_tasks.total_completed}")
        print(f"Pending Approvals: {len(briefing.pending_approvals)}")
        print(f"Issues: {len(briefing.issues)}")


if __name__ == "__main__":
    main()
