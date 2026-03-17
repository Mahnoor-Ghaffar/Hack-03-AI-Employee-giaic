# Accounting Manager - Gold Tier (Simple Vault-Based)

**Version:** 1.0.0  
**Type:** Claude Code Skill / Python Module  
**Category:** Business/Accounting  

---

## Overview

Lightweight vault-based accounting system for the AI Employee Gold Tier hackathon. This is a **simpler alternative to full Odoo ERP** - perfect for hackathon requirements without the complexity.

---

## Features

✅ **Transaction Logging**
- Log income and expenses
- Automatic transaction ID generation
- Category-based organization
- Reference number tracking

✅ **Reports & Summaries**
- Weekly accounting summaries
- Monthly detailed reports
- Profit margin calculations
- Category breakdowns

✅ **Data Management**
- Get transactions with filters
- Calculate totals and balances
- Export to CSV/JSON
- Markdown-based ledger

✅ **Integration Ready**
- Claude Code skill
- Python module import
- CLI interface
- CEO Briefing integration

---

## Installation

No additional dependencies required! Uses Python standard library.

---

## Quick Start

### Option 1: CLI Usage

```bash
# Log income
python scripts/accounting_manager.py log \
  --type income \
  --amount 5000 \
  --description "Client payment - Project Alpha" \
  --category revenue \
  --reference INV-001

# Log expense
python scripts/accounting_manager.py log \
  --type expense \
  --amount 150 \
  --description "Software subscription" \
  --category software

# Get totals
python scripts/accounting_manager.py totals

# Get balance
python scripts/accounting_manager.py balance

# Generate weekly summary
python scripts/accounting_manager.py weekly-summary

# Generate monthly report
python scripts/accounting_manager.py monthly-report --month 3 --year 2026
```

### Option 2: Python Import

```python
from scripts.accounting_manager import AccountingManager

# Initialize
accounting = AccountingManager(vault_path="AI_Employee_Vault")

# Log transaction
result = accounting.log_transaction(
    date="2026-03-14",
    type="income",
    amount=5000.00,
    description="Client payment",
    category="revenue",
    reference="INV-001"
)

# Get totals
totals = accounting.get_totals()
print(f"Balance: ${totals['balance']:,.2f}")
```

### Option 3: Claude Code Skill

Once configured in `.claude/mcp.json`, use naturally:

```
Log an income transaction for $5000 from Client A for Project Alpha.
Reference number INV-001, category revenue.

Generate a weekly summary of all accounting transactions.

What's my current balance?
```

---

## File Structure

```
AI_Employee_Vault/
└── Accounting/
    ├── Current_Month.md        # Main ledger (auto-maintained)
    ├── Weekly_Summaries/       # Weekly summary reports
    │   └── Weekly_Summary_2026-03-10_to_2026-03-16.md
    ├── Monthly_Reports/        # Monthly detailed reports
    │   └── Monthly_Report_2026_03.md
    └── Receipts/               # Receipt references (optional)
```

---

## API Reference

### Initialize

```python
from scripts.accounting_manager import AccountingManager

accounting = AccountingManager(
    vault_path="AI_Employee_Vault"  # Optional, defaults to AI_Employee_Vault
)
```

---

### log_transaction()

Log a new income or expense transaction.

**Parameters:**
- `date` (str): Transaction date (YYYY-MM-DD)
- `type` (str): "income" or "expense"
- `amount` (float): Transaction amount (positive number)
- `description` (str): Transaction description
- `category` (str, optional): Category (revenue, software, rent, etc.)
- `reference` (str, optional): Reference number (invoice ID, etc.)

**Returns:** dict with status and transaction_id

**Example:**
```python
result = accounting.log_transaction(
    date="2026-03-14",
    type="income",
    amount=5000.00,
    description="Client payment - Project Alpha",
    category="revenue",
    reference="INV-001"
)

print(result)
# {
#   "status": "success",
#   "transaction_id": "TXN-20260314-ABC",
#   "file": "AI_Employee_Vault/Accounting/Current_Month.md"
# }
```

---

### get_transactions()

Retrieve transactions with optional filters.

**Parameters:**
- `type` (str, optional): "income" or "expense"
- `start_date` (str, optional): Start date (YYYY-MM-DD)
- `end_date` (str, optional): End date (YYYY-MM-DD)
- `category` (str, optional): Filter by category

**Returns:** list of transaction dicts

**Example:**
```python
# Get all transactions
all_txns = accounting.get_transactions()

# Get income only
income = accounting.get_transactions(type="income")

# Get expenses in date range
march_expenses = accounting.get_transactions(
    type="expense",
    start_date="2026-03-01",
    end_date="2026-03-31"
)

# Get by category
software = accounting.get_transactions(category="software")
```

---

### get_totals()

Get total income, expense, and balance.

**Returns:** dict with totals

**Example:**
```python
totals = accounting.get_totals()

print(f"Income: ${totals['total_income']:,.2f}")
print(f"Expense: ${totals['total_expense']:,.2f}")
print(f"Balance: ${totals['balance']:,.2f}")
print(f"Total transactions: {totals['transaction_count']}")
```

---

### get_balance()

Get current balance (income - expenses).

**Returns:** float

**Example:**
```python
balance = accounting.get_balance()
print(f"Current Balance: ${balance:,.2f}")
```

---

### generate_weekly_summary()

Generate weekly accounting summary report.

**Parameters:**
- `week_start` (str, optional): Week start date (YYYY-MM-DD)
- `week_end` (str, optional): Week end date (YYYY-MM-DD)

**Returns:** dict with summary and file path

**Example:**
```python
result = accounting.generate_weekly_summary(
    week_start="2026-03-10",
    week_end="2026-03-16"
)

print(f"Summary file: {result['summary_file']}")
print(f"Net Profit: ${result['totals']['net_profit']:,.2f}")
```

---

### generate_monthly_report()

Generate monthly accounting report.

**Parameters:**
- `year` (int): Year
- `month` (int): Month (1-12)

**Returns:** dict with report and file path

**Example:**
```python
result = accounting.generate_monthly_report(year=2026, month=3)

print(f"Report file: {result['report_file']}")
print(f"Profit Margin: {result['totals']['profit_margin']:.1f}%")
```

---

### export_to_csv()

Export transactions to CSV file.

**Parameters:**
- `filename` (str): Output CSV filename

**Returns:** str with file path

**Example:**
```python
csv_path = accounting.export_to_csv("march_2026_transactions.csv")
print(f"Exported to: {csv_path}")
```

---

### export_to_json()

Export transactions to JSON file.

**Parameters:**
- `filename` (str): Output JSON filename

**Returns:** str with file path

**Example:**
```python
json_path = accounting.export_to_json("march_2026_transactions.json")
print(f"Exported to: {json_path}")
```

---

## Categories

### Income Categories

| Category | Description |
|----------|-------------|
| `revenue` | Client payments, project fees |
| `refund` | Refunds received |
| `investment` | Capital investments |
| `other_income` | Other income sources |

### Expense Categories

| Category | Description |
|----------|-------------|
| `software` | Software subscriptions, tools |
| `rent` | Office rent, co-working spaces |
| `office` | Office supplies, equipment |
| `marketing` | Advertising, promotions |
| `travel` | Business travel expenses |
| `utilities` | Internet, phone, electricity |
| `professional` | Legal, accounting services |
| `other_expense` | Other expenses |

---

## Ledger File Format

**AI_Employee_Vault/Accounting/Current_Month.md:**

```markdown
---
month: March 2026
created: 2026-03-01
last_updated: 2026-03-14T10:30:00
total_income: 8000.00
total_expense: 1150.00
balance: 6850.00
---

# Accounting Ledger - March 2026

## Transactions

### TXN-20260314-ABC
- **Date:** 2026-03-14
- **Type:** income
- **Amount:** $5,000.00
- **Description:** Client payment - Project Alpha
- **Category:** revenue
- **Reference:** INV-001
- **Logged at:** 2026-03-14T10:30:00

---

### TXN-20260314-DEF
- **Date:** 2026-03-14
- **Type:** expense
- **Amount:** $150.00
- **Description:** Software subscription - Adobe Creative Cloud
- **Category:** software
- **Reference:** SUB-001
- **Logged at:** 2026-03-14T10:35:00

---

## Summary

| Type | Total | Count |
|------|-------|-------|
| Income | $8,000.00 | 2 |
| Expense | $1,150.00 | 3 |
| **Balance** | **$6,850.00** | **5** |
```

---

## Integration Examples

### Gmail Watcher Integration

```python
# When payment received
from scripts.accounting_manager import AccountingManager

accounting = AccountingManager()

# Extract payment from email
payment_amount = 5000.00
sender_name = "Client A"

accounting.log_transaction(
    date=datetime.now().strftime("%Y-%m-%d"),
    type="income",
    amount=payment_amount,
    description=f"Payment received - {sender_name}",
    category="revenue",
    reference=f"EMAIL-{email_id}"
)
```

### Bank Statement Integration

```python
# When processing bank transactions
for transaction in bank_transactions:
    # Auto-categorize based on description
    category = categorize_transaction(transaction['description'])
    
    accounting.log_transaction(
        date=transaction['date'],
        type="expense",  # or "income"
        amount=transaction['amount'],
        description=transaction['description'],
        category=category,
        reference=transaction['id']
    )
```

### CEO Briefing Integration

```python
from scripts.ceo_briefing_generator import CEOBriefingGenerator
from scripts.accounting_manager import AccountingManager

# In CEO Briefing Generator
accounting = AccountingManager()
totals = accounting.get_totals()

briefing_content = f"""
## Financial Performance
- Total Income: ${totals['total_income']:,.2f}
- Total Expenses: ${totals['total_expense']:,.2f}
- Net Profit: ${totals['balance']:,.2f}
- Profit Margin: {(totals['balance']/totals['total_income']*100):.1f}%
"""
```

---

## Testing

### Run Test Suite

```bash
python scripts/test_accounting_manager.py
```

### Manual Testing

```python
from scripts.accounting_manager import AccountingManager

accounting = AccountingManager(vault_path="AI_Employee_Vault")

# Test logging
result = accounting.log_transaction(
    date="2026-03-14",
    type="income",
    amount=1000.00,
    description="Test transaction"
)

# Test retrieval
transactions = accounting.get_transactions()
print(f"Transactions: {len(transactions)}")

# Test totals
totals = accounting.get_totals()
print(f"Balance: ${totals['balance']:,.2f}")
```

---

## Troubleshooting

### Issue: File not found

**Solution:**
- Ensure `AI_Employee_Vault/Accounting/` directory exists
- The system auto-creates `Current_Month.md` on first run

### Issue: Invalid date format

**Solution:**
- Use YYYY-MM-DD format (e.g., "2026-03-14")
- Check for typos in date string

### Issue: Amount validation error

**Solution:**
- Amount must be a positive number
- Use float or int (not string)

### Issue: Summary not updating

**Solution:**
- Check file permissions
- Ensure no other process has the file open
- Review logs: `logs/ai_employee.log`

---

## Best Practices

✅ **DO:**
- Log transactions daily
- Use descriptive descriptions
- Categorize properly
- Include reference numbers
- Generate weekly summaries
- Review monthly reports
- Backup Accounting folder regularly

❌ **DON'T:**
- Skip transaction logging
- Use vague descriptions like "payment"
- Mix personal and business expenses
- Delete Current_Month.md mid-month
- Forget to backup

---

## Backup & Export

### Manual Backup

```bash
# Copy Accounting folder
cp -r AI_Employee_Vault/Accounting backup/Accounting_$(date +%Y%m%d)
```

### Export for External Use

```python
accounting = AccountingManager()

# Export to CSV (Excel compatible)
accounting.export_to_csv("march_2026.csv")

# Export to JSON (programmatic access)
accounting.export_to_json("march_2026.json")
```

---

## Comparison: Simple vs Odoo

| Feature | Simple Accounting | Odoo ERP |
|---------|------------------|----------|
| Setup Time | 5 minutes | 1-2 hours |
| Dependencies | None | Docker, PostgreSQL |
| Complexity | Low | High |
| Performance | Instant | Network dependent |
| Data Format | Markdown | Database |
| Best For | Hackathon, Solo | Production, Team |

**Recommendation:** Use Simple Accounting for hackathon Gold Tier. Upgrade to Odoo for production deployment.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-14 | Initial release |

---

## License

MIT License - Part of Gold Tier AI Employee Project

---

## Support

For issues:
1. Check file permissions
2. Verify date format (YYYY-MM-DD)
3. Ensure amount is numeric
4. Review logs: `logs/ai_employee.log`
5. Run tests: `python scripts/test_accounting_manager.py`

---

**Accounting Manager** - Simple, lightweight vault-based accounting for Gold Tier ✅

Perfect for hackathon requirements without Odoo complexity!
