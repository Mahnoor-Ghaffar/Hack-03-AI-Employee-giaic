#!/usr/bin/env python3
"""
Accounting Manager - Gold Tier (Simple Vault-Based)

Lightweight accounting system for tracking income and expenses.
Perfect for hackathon Gold Tier requirements without Odoo complexity.

Capabilities:
- Log income/expense transactions
- Maintain Current_Month.md ledger
- Generate weekly summaries
- Generate monthly reports
- Calculate totals and balances

Usage:
    python scripts/accounting_manager.py log --type income --amount 5000 --description "Client payment"
    python scripts/accounting_manager.py totals
    python scripts/accounting_manager.py weekly-summary
    python scripts/accounting_manager.py monthly-report --month 3 --year 2026

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
from typing import Dict, List, Optional, Any
import hashlib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('accounting_manager')

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', 'AI_Employee_Vault'))
ACCOUNTING_PATH = VAULT_PATH / 'Accounting'
CURRENT_MONTH_FILE = ACCOUNTING_PATH / 'Current_Month.md'
WEEKLY_SUMMARIES_PATH = ACCOUNTING_PATH / 'Weekly_Summaries'
MONTHLY_REPORTS_PATH = ACCOUNTING_PATH / 'Monthly_Reports'


class AccountingManager:
    """
    Vault-based Accounting Manager.
    
    Simple, lightweight accounting system for hackathon Gold Tier.
    """

    def __init__(self, vault_path: str = None):
        """
        Initialize Accounting Manager.
        
        Args:
            vault_path: Path to AI Employee vault
        """
        self.vault_path = Path(vault_path) if vault_path else VAULT_PATH
        self.accounting_path = self.vault_path / 'Accounting'
        self.current_month_file = self.accounting_path / 'Current_Month.md'
        self.weekly_summaries_path = self.accounting_path / 'Weekly_Summaries'
        self.monthly_reports_path = self.accounting_path / 'Monthly_Reports'
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Initialize current month file if needed
        self._initialize_current_month()
        
        logger.info(f'AccountingManager initialized. Vault: {self.vault_path}')

    def _ensure_directories(self):
        """Create necessary directories."""
        self.accounting_path.mkdir(parents=True, exist_ok=True)
        self.weekly_summaries_path.mkdir(parents=True, exist_ok=True)
        self.monthly_reports_path.mkdir(parents=True, exist_ok=True)

    def _initialize_current_month(self):
        """Initialize current month ledger file if it doesn't exist."""
        if not self.current_month_file.exists():
            current_month = datetime.now().strftime('%B %Y')
            content = f"""---
month: {current_month}
created: {datetime.now().strftime('%Y-%m-%d')}
last_updated: {datetime.now().isoformat()}
total_income: 0.00
total_expense: 0.00
balance: 0.00
---

# Accounting Ledger - {current_month}

## Transactions

<!-- Transactions will be logged below -->

## Summary

| Type | Total | Count |
|------|-------|-------|
| Income | $0.00 | 0 |
| Expense | $0.00 | 0 |
| **Balance** | **$0.00** | **0** |
"""
            self.current_month_file.write_text(content)
            logger.info(f'Initialized current month file: {self.current_month_file}')

    def _generate_transaction_id(self, date: str, amount: float, description: str) -> str:
        """
        Generate unique transaction ID.
        
        Args:
            date: Transaction date
            amount: Transaction amount
            description: Transaction description
            
        Returns:
            Unique transaction ID
        """
        # Format: TXN-YYYYMMDD-XXX
        date_str = date.replace('-', '')
        hash_input = f"{date}{amount}{description}{datetime.now().timestamp()}"
        hash_digest = hashlib.md5(hash_input.encode()).hexdigest()[:3].upper()
        return f"TXN-{date_str}-{hash_digest}"

    def _parse_transactions(self) -> List[Dict[str, Any]]:
        """
        Parse transactions from current month file.
        
        Returns:
            List of transaction dictionaries
        """
        if not self.current_month_file.exists():
            return []
        
        content = self.current_month_file.read_text()
        transactions = []
        
        # Split by transaction sections
        sections = content.split('### TXN-')
        
        for section in sections[1:]:  # Skip first section (header)
            try:
                lines = section.strip().split('\n')
                transaction_id = 'TXN-' + lines[0].strip()
                
                transaction = {
                    'transaction_id': transaction_id,
                    'date': None,
                    'type': None,
                    'amount': 0.0,
                    'description': None,
                    'category': None,
                    'reference': None,
                    'logged_at': None
                }
                
                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith('- **Date:**'):
                        transaction['date'] = line.replace('- **Date:**', '').strip()
                    elif line.startswith('- **Type:**'):
                        transaction['type'] = line.replace('- **Type:**', '').strip().lower()
                    elif line.startswith('- **Amount:**'):
                        amount_str = line.replace('- **Amount:**', '').strip().replace('$', '').replace(',', '')
                        transaction['amount'] = float(amount_str)
                    elif line.startswith('- **Description:**'):
                        transaction['description'] = line.replace('- **Description:**', '').strip()
                    elif line.startswith('- **Category:**'):
                        transaction['category'] = line.replace('- **Category:**', '').strip()
                    elif line.startswith('- **Reference:**'):
                        transaction['reference'] = line.replace('- **Reference:**', '').strip()
                    elif line.startswith('- **Logged at:**'):
                        transaction['logged_at'] = line.replace('- **Logged at:**', '').strip()
                
                if transaction['date']:  # Only add if we got at least the date
                    transactions.append(transaction)
                    
            except Exception as e:
                logger.warning(f'Error parsing transaction section: {e}')
                continue
        
        return transactions

    def _update_summary(self):
        """Update summary section in current month file."""
        transactions = self._parse_transactions()
        
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        balance = total_income - total_expense
        
        income_count = len([t for t in transactions if t['type'] == 'income'])
        expense_count = len([t for t in transactions if t['type'] == 'expense'])
        
        content = self.current_month_file.read_text()
        
        # Update frontmatter
        import re
        
        # Update totals in frontmatter
        content = re.sub(
            r'total_income: [\d.]+',
            f'total_income: {total_income:.2f}',
            content
        )
        content = re.sub(
            r'total_expense: [\d.]+',
            f'total_expense: {total_expense:.2f}',
            content
        )
        content = re.sub(
            r'balance: [\d.]+',
            f'balance: {balance:.2f}',
            content
        )
        content = re.sub(
            r'last_updated: [^\n]+',
            f'last_updated: {datetime.now().isoformat()}',
            content
        )
        
        # Update summary table
        summary_table = f"""
## Summary

| Type | Total | Count |
|------|-------|-------|
| Income | ${total_income:,.2f} | {income_count} |
| Expense | ${total_expense:,.2f} | {expense_count} |
| **Balance** | **${balance:,.2f}** | **{income_count + expense_count}** |
"""
        
        # Replace summary table
        content = re.sub(
            r'## Summary\n\n.*?\| \*\*Balance\*\* \|\s*\*\*[\$,\d.]+\*\*\s*\| \*\*\d+\*\*\s*\|',
            summary_table.strip(),
            content,
            flags=re.DOTALL
        )
        
        self.current_month_file.write_text(content)
        logger.info('Updated summary in current month file')

    def log_transaction(
        self,
        date: str,
        type: str,
        amount: float,
        description: str,
        category: str = None,
        reference: str = None
    ) -> Dict[str, Any]:
        """
        Log a new transaction.
        
        Args:
            date: Transaction date (YYYY-MM-DD)
            type: "income" or "expense"
            amount: Transaction amount
            description: Transaction description
            category: Optional category
            reference: Optional reference number
            
        Returns:
            Dictionary with status and transaction details
        """
        # Validation
        if type not in ['income', 'expense']:
            raise ValueError(f"Invalid type: {type}. Must be 'income' or 'expense'")
        
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError(f"Invalid amount: {amount}. Must be positive number")
        
        # Generate transaction ID
        transaction_id = self._generate_transaction_id(date, amount, description)
        
        # Create transaction content
        transaction_content = f"""
### {transaction_id}
- **Date:** {date}
- **Type:** {type}
- **Amount:** ${amount:,.2f}
- **Description:** {description}
- **Category:** {category or 'uncategorized'}
- **Reference:** {reference or 'N/A'}
- **Logged at:** {datetime.now().isoformat()}

---
"""
        
        # Read current file
        content = self.current_month_file.read_text()
        
        # Find position to insert (before "## Summary")
        summary_pos = content.find('## Summary')
        if summary_pos == -1:
            # Append to end
            content += transaction_content
        else:
            # Insert before summary
            content = content[:summary_pos] + transaction_content + content[summary_pos:]
        
        # Write updated content
        self.current_month_file.write_text(content)
        
        # Update summary
        self._update_summary()
        
        logger.info(f'Logged transaction {transaction_id}: {type} ${amount:.2f} - {description}')
        
        return {
            'status': 'success',
            'message': 'Transaction logged successfully',
            'transaction_id': transaction_id,
            'file': str(self.current_month_file),
            'transaction': {
                'date': date,
                'type': type,
                'amount': amount,
                'description': description,
                'category': category,
                'reference': reference
            }
        }

    def get_transactions(
        self,
        type: str = None,
        start_date: str = None,
        end_date: str = None,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve transactions with optional filters.
        
        Args:
            type: Filter by type ("income" or "expense")
            start_date: Filter by start date (YYYY-MM-DD)
            end_date: Filter by end date (YYYY-MM-DD)
            category: Filter by category
            
        Returns:
            List of matching transactions
        """
        transactions = self._parse_transactions()
        
        # Apply filters
        if type:
            transactions = [t for t in transactions if t['type'] == type]
        
        if start_date:
            transactions = [t for t in transactions if t['date'] and t['date'] >= start_date]
        
        if end_date:
            transactions = [t for t in transactions if t['date'] and t['date'] <= end_date]
        
        if category:
            transactions = [t for t in transactions if t['category'] == category]
        
        return transactions

    def get_totals(self) -> Dict[str, Any]:
        """
        Get total income, expense, and balance.
        
        Returns:
            Dictionary with totals
        """
        transactions = self._parse_transactions()
        
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        balance = total_income - total_expense
        
        return {
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance,
            'transaction_count': len(transactions),
            'income_count': len([t for t in transactions if t['type'] == 'income']),
            'expense_count': len([t for t in transactions if t['type'] == 'expense']),
            'period': datetime.now().strftime('%Y-%m')
        }

    def get_balance(self) -> float:
        """
        Get current balance.
        
        Returns:
            Current balance
        """
        totals = self.get_totals()
        return totals['balance']

    def generate_weekly_summary(
        self,
        week_start: str = None,
        week_end: str = None
    ) -> Dict[str, Any]:
        """
        Generate weekly accounting summary.
        
        Args:
            week_start: Week start date (YYYY-MM-DD), defaults to last Monday
            week_end: Week end date (YYYY-MM-DD), defaults to next Sunday
            
        Returns:
            Dictionary with summary data and file path
        """
        # Default to last week
        if not week_start or not week_end:
            today = datetime.now()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday, weeks=1)
            week_start = last_monday.strftime('%Y-%m-%d')
            week_end = (last_monday + timedelta(days=6)).strftime('%Y-%m-%d')
        
        # Get transactions for the week
        transactions = self.get_transactions(
            start_date=week_start,
            end_date=week_end
        )
        
        # Calculate totals
        income_transactions = [t for t in transactions if t['type'] == 'income']
        expense_transactions = [t for t in transactions if t['type'] == 'expense']
        
        total_income = sum(t['amount'] for t in income_transactions)
        total_expense = sum(t['amount'] for t in expense_transactions)
        net_profit = total_income - total_expense
        
        # Group by category
        categories = {}
        for t in transactions:
            cat = t['category'] or 'uncategorized'
            if cat not in categories:
                categories[cat] = 0.0
            categories[cat] += t['amount']
        
        # Create summary file
        summary_date = datetime.now().strftime('%Y%m%d')
        summary_file = self.weekly_summaries_path / f"Weekly_Summary_{week_start}_to_{week_end}.md"
        
        content = f"""---
type: weekly_summary
period_start: {week_start}
period_end: {week_end}
generated: {datetime.now().isoformat()}
---

# Weekly Accounting Summary
**Period:** {week_start} to {week_end}

## Income
- **Total:** ${total_income:,.2f}
- **Transactions:** {len(income_transactions)}

## Expenses
- **Total:** ${total_expense:,.2f}
- **Transactions:** {len(expense_transactions)}

## Net Profit
- **${net_profit:,.2f}**

## Categories
"""
        
        for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            content += f"- {cat.capitalize()}: ${amount:,.2f}\n"
        
        content += f"\n## Transactions\n\n"
        
        for t in sorted(transactions, key=lambda x: x['date'], reverse=True):
            content += f"- {t['date']} | {t['type'].upper()} | ${t['amount']:,.2f} | {t['description']}\n"
        
        summary_file.write_text(content)
        
        logger.info(f'Generated weekly summary: {summary_file}')
        
        return {
            'status': 'success',
            'summary_file': str(summary_file),
            'period': {
                'start': week_start,
                'end': week_end
            },
            'totals': {
                'total_income': total_income,
                'total_expense': total_expense,
                'net_profit': net_profit
            },
            'counts': {
                'income_transactions': len(income_transactions),
                'expense_transactions': len(expense_transactions)
            },
            'categories': categories
        }

    def generate_monthly_report(self, year: int, month: int) -> Dict[str, Any]:
        """
        Generate monthly accounting report.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            Dictionary with report data and file path
        """
        from calendar import monthrange
        
        # Get date range for month
        _, last_day = monthrange(year, month)
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{last_day:02d}"
        
        # Get transactions
        transactions = self.get_transactions(
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate totals
        income_transactions = [t for t in transactions if t['type'] == 'income']
        expense_transactions = [t for t in transactions if t['type'] == 'expense']
        
        total_income = sum(t['amount'] for t in income_transactions)
        total_expense = sum(t['amount'] for t in expense_transactions)
        net_profit = total_income - total_expense
        profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0
        
        # Group expenses by category
        expense_categories = {}
        for t in expense_transactions:
            cat = t['category'] or 'uncategorized'
            if cat not in expense_categories:
                expense_categories[cat] = 0.0
            expense_categories[cat] += t['amount']
        
        # Create report file
        month_name = datetime(year, month, 1).strftime('%B %Y')
        report_file = self.monthly_reports_path / f"Monthly_Report_{year}_{month:02d}.md"
        
        content = f"""---
type: monthly_report
year: {year}
month: {month}
generated: {datetime.now().isoformat()}
---

# Monthly Accounting Report
**Month:** {month_name}

## Summary
- **Total Income:** ${total_income:,.2f}
- **Total Expenses:** ${total_expense:,.2f}
- **Net Profit:** ${net_profit:,.2f}
- **Profit Margin:** {profit_margin:.1f}%

## Income Breakdown

| Date | Description | Amount |
|------|-------------|--------|
"""
        
        for t in sorted(income_transactions, key=lambda x: x['date']):
            content += f"| {t['date']} | {t['description']} | ${t['amount']:,.2f} |\n"
        
        if not income_transactions:
            content += "| - | No income transactions | $0.00 |\n"
        
        content += f"""
## Expense Breakdown

| Date | Description | Amount | Category |
|------|-------------|--------|----------|
"""
        
        for t in sorted(expense_transactions, key=lambda x: x['date']):
            content += f"| {t['date']} | {t['description']} | ${t['amount']:,.2f} | {t['category']} |\n"
        
        if not expense_transactions:
            content += "| - | No expense transactions | $0.00 | - |\n"
        
        content += f"""
## Category Summary

| Category | Amount | Percentage |
|----------|--------|------------|
"""
        
        for cat, amount in sorted(expense_categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total_expense * 100) if total_expense > 0 else 0
            content += f"| {cat.capitalize()} | ${amount:,.2f} | {percentage:.1f}% |\n"
        
        report_file.write_text(content)
        
        logger.info(f'Generated monthly report: {report_file}')
        
        return {
            'status': 'success',
            'report_file': str(report_file),
            'period': {
                'year': year,
                'month': month,
                'month_name': month_name
            },
            'totals': {
                'total_income': total_income,
                'total_expense': total_expense,
                'net_profit': net_profit,
                'profit_margin': profit_margin
            },
            'counts': {
                'income_transactions': len(income_transactions),
                'expense_transactions': len(expense_transactions)
            },
            'expense_categories': expense_categories
        }

    def export_to_csv(self, filename: str) -> str:
        """
        Export transactions to CSV.
        
        Args:
            filename: Output CSV filename
            
        Returns:
            Path to CSV file
        """
        transactions = self._parse_transactions()
        
        csv_path = Path(filename)
        
        with open(csv_path, 'w') as f:
            f.write("Date,Type,Amount,Description,Category,Reference,Transaction_ID\n")
            for t in sorted(transactions, key=lambda x: x['date']):
                f.write(f"{t['date']},{t['type']},{t['amount']},\"{t['description']}\",{t['category']},{t['reference']},{t['transaction_id']}\n")
        
        logger.info(f'Exported {len(transactions)} transactions to {csv_path}')
        return str(csv_path)

    def export_to_json(self, filename: str) -> str:
        """
        Export transactions to JSON.
        
        Args:
            filename: Output JSON filename
            
        Returns:
            Path to JSON file
        """
        transactions = self._parse_transactions()
        totals = self.get_totals()
        
        data = {
            'generated_at': datetime.now().isoformat(),
            'totals': totals,
            'transactions': transactions
        }
        
        json_path = Path(filename)
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f'Exported {len(transactions)} transactions to {json_path}')
        return str(json_path)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Accounting Manager - Gold Tier')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Log transaction command
    log_parser = subparsers.add_parser('log', help='Log a transaction')
    log_parser.add_argument('--type', required=True, choices=['income', 'expense'], help='Transaction type')
    log_parser.add_argument('--amount', type=float, required=True, help='Transaction amount')
    log_parser.add_argument('--description', required=True, help='Transaction description')
    log_parser.add_argument('--category', help='Transaction category')
    log_parser.add_argument('--reference', help='Reference number')
    log_parser.add_argument('--date', help='Transaction date (YYYY-MM-DD, default: today)')
    
    # Totals command
    subparsers.add_parser('totals', help='Get total income, expense, and balance')
    
    # Balance command
    subparsers.add_parser('balance', help='Get current balance')
    
    # Weekly summary command
    weekly_parser = subparsers.add_parser('weekly-summary', help='Generate weekly summary')
    weekly_parser.add_argument('--start', help='Week start date (YYYY-MM-DD)')
    weekly_parser.add_argument('--end', help='Week end date (YYYY-MM-DD)')
    
    # Monthly report command
    monthly_parser = subparsers.add_parser('monthly-report', help='Generate monthly report')
    monthly_parser.add_argument('--month', type=int, required=True, help='Month (1-12)')
    monthly_parser.add_argument('--year', type=int, required=True, help='Year')
    
    # Export commands
    export_csv_parser = subparsers.add_parser('export-csv', help='Export to CSV')
    export_csv_parser.add_argument('--filename', required=True, help='Output CSV filename')
    
    export_json_parser = subparsers.add_parser('export-json', help='Export to JSON')
    export_json_parser.add_argument('--filename', required=True, help='Output JSON filename')
    
    args = parser.parse_args()
    
    # Initialize accounting manager
    accounting = AccountingManager()
    
    try:
        if args.command == 'log':
            date = args.date or datetime.now().strftime('%Y-%m-%d')
            result = accounting.log_transaction(
                date=date,
                type=args.type,
                amount=args.amount,
                description=args.description,
                category=args.category,
                reference=args.reference
            )
            print(json.dumps(result, indent=2))
            
        elif args.command == 'totals':
            totals = accounting.get_totals()
            print("\n=== Accounting Totals ===")
            print(f"Total Income:   ${totals['total_income']:,.2f}")
            print(f"Total Expense:  ${totals['total_expense']:,.2f}")
            print(f"Balance:        ${totals['balance']:,.2f}")
            print(f"Transactions:   {totals['transaction_count']}")
            print()
            
        elif args.command == 'balance':
            balance = accounting.get_balance()
            print(f"\nCurrent Balance: ${balance:,.2f}\n")
            
        elif args.command == 'weekly-summary':
            result = accounting.generate_weekly_summary(
                week_start=args.start,
                week_end=args.end
            )
            print(f"\nWeekly summary generated: {result['summary_file']}\n")
            print(f"Period: {result['period']['start']} to {result['period']['end']}")
            print(f"Total Income:  ${result['totals']['total_income']:,.2f}")
            print(f"Total Expense: ${result['totals']['total_expense']:,.2f}")
            print(f"Net Profit:    ${result['totals']['net_profit']:,.2f}\n")
            
        elif args.command == 'monthly-report':
            result = accounting.generate_monthly_report(
                year=args.year,
                month=args.month
            )
            print(f"\nMonthly report generated: {result['report_file']}\n")
            print(f"Period: {result['period']['month_name']}")
            print(f"Total Income:   ${result['totals']['total_income']:,.2f}")
            print(f"Total Expense:  ${result['totals']['total_expense']:,.2f}")
            print(f"Net Profit:     ${result['totals']['net_profit']:,.2f}")
            print(f"Profit Margin:  {result['totals']['profit_margin']:.1f}%\n")
            
        elif args.command == 'export-csv':
            csv_path = accounting.export_to_csv(args.filename)
            print(f"\nExported to CSV: {csv_path}\n")
            
        elif args.command == 'export-json':
            json_path = accounting.export_to_json(args.filename)
            print(f"\nExported to JSON: {json_path}\n")
            
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f'Error: {e}', exc_info=True)
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
