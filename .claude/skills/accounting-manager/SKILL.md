# Accounting Manager Skill

**Version:** 1.0.0  
**Type:** Claude Code Skill  
**Category:** Business/Accounting  

---

## Overview

Lightweight vault-based accounting system for tracking income and expenses. Perfect for hackathon Gold Tier requirements without the complexity of full Odoo ERP.

---

## Capabilities

| Function | Description |
|----------|-------------|
| `log_transaction()` | Log income or expense transaction |
| `get_transactions()` | Retrieve transactions by date/type |
| `generate_weekly_summary()` | Generate weekly accounting summary |
| `generate_monthly_report()` | Generate monthly income/expense report |
| `get_totals()` | Get total income, expense, and balance |
| `get_balance()` | Calculate current balance |

---

## File Structure

```
AI_Employee_Vault/
└── Accounting/
    ├── Current_Month.md        # Main accounting ledger
    ├── Weekly_Summaries/       # Weekly summary reports
    ├── Monthly_Reports/        # Monthly reports
    └── Receipts/               # Receipt references
```

---

## Usage

### Import the Skill

```python
from .claude.skills.accounting_manager.scripts.accounting_manager import AccountingManager

accounting = AccountingManager(vault_path="AI_Employee_Vault")
```

---

### Log Transaction

```python
# Log income
result = accounting.log_transaction(
    date="2026-03-14",
    type="income",
    amount=5000.00,
    description="Client payment - Project Alpha",
    category="revenue",
    reference="INV-001"
)

# Log expense
result = accounting.log_transaction(
    date="2026-03-14",
    type="expense",
    amount=150.00,
    description="Software subscription - Adobe Creative Cloud",
    category="software",
    reference="SUB-001"
)
```

**Response:**
```json
{
  "status": "success",
  "message": "Transaction logged successfully",
  "transaction_id": "TXN-20260314-001",
  "file": "AI_Employee_Vault/Accounting/Current_Month.md"
}
```

---

### Get Transactions

```python
# Get all transactions
transactions = accounting.get_transactions()

# Get by type
income = accounting.get_transactions(type="income")
expenses = accounting.get_transactions(type="expense")

# Get by date range
march_transactions = accounting.get_transactions(
    start_date="2026-03-01",
    end_date="2026-03-31"
)

# Get by category
software_expenses = accounting.get_transactions(
    type="expense",
    category="software"
)
```

---

### Generate Weekly Summary

```python
summary = accounting.generate_weekly_summary(
    week_start="2026-03-10",
    week_end="2026-03-16"
)
```

**Output:**
```markdown
# Weekly Accounting Summary
**Period:** March 10-16, 2026

## Income
- Total: $8,500.00
- Transactions: 3

## Expenses
- Total: $450.00
- Transactions: 5

## Net Profit
- $8,050.00

## Categories
- Revenue: $8,500.00
- Software: $150.00
- Office Supplies: $200.00
- Marketing: $100.00
```

---

### Generate Monthly Report

```python
report = accounting.generate_monthly_report(
    year=2026,
    month=3
)
```

**Output:**
```markdown
# Monthly Accounting Report
**Month:** March 2026

## Summary
- Total Income: $25,000.00
- Total Expenses: $3,500.00
- Net Profit: $21,500.00
- Profit Margin: 86%

## Income Breakdown
| Date | Description | Amount |
|------|-------------|--------|
| 2026-03-05 | Client A - Project Alpha | $5,000.00 |
| 2026-03-12 | Client B - Website Design | $8,000.00 |
| ... | ... | ... |

## Expense Breakdown
| Date | Description | Amount | Category |
|------|-------------|--------|----------|
| 2026-03-01 | Office Rent | $1,000.00 | rent |
| 2026-03-05 | Software Subscription | $150.00 | software |
| ... | ... | ... | ... |

## Category Summary
| Category | Amount | Percentage |
|----------|--------|------------|
| Software | $450.00 | 12.9% |
| Rent | $1,000.00 | 28.6% |
| Marketing | $800.00 | 22.9% |
| ... | ... | ... |
```

---

### Get Totals

```python
totals = accounting.get_totals()
```

**Response:**
```json
{
  "total_income": 25000.00,
  "total_expense": 3500.00,
  "balance": 21500.00,
  "transaction_count": 28,
  "period": "2026-03"
}
```

---

### Get Balance

```python
balance = accounting.get_balance()
print(f"Current Balance: ${balance}")
```

---

## Transaction Schema

Each transaction has the following structure:

```markdown
---
transaction_id: TXN-20260314-001
date: 2026-03-14
type: income  # or expense
amount: 5000.00
description: Client payment - Project Alpha
category: revenue
reference: INV-001
logged_at: 2026-03-14T10:30:00
---
```

---

## Categories

### Income Categories
- `revenue` - Client payments, project fees
- `refund` - Refunds received
- `investment` - Capital investments
- `other_income` - Other income sources

### Expense Categories
- `software` - Software subscriptions, tools
- `office` - Office supplies, rent
- `marketing` - Advertising, promotions
- `travel` - Business travel expenses
- `utilities` - Internet, phone, electricity
- `professional` - Legal, accounting services
- `other_expense` - Other expenses

---

## CLI Usage

```bash
# Log income
python scripts/accounting_manager.py log --type income --amount 5000 --description "Client payment" --category revenue

# Log expense
python scripts/accounting_manager.py log --type expense --amount 150 --description "Software subscription" --category software

# Get totals
python scripts/accounting_manager.py totals

# Generate weekly summary
python scripts/accounting_manager.py weekly-summary

# Generate monthly report
python scripts/accounting_manager.py monthly-report --month 3 --year 2026
```

---

## Integration with AI Employee

### Automatic Transaction Logging

The accounting manager integrates with other watchers:

```python
# When payment received (Gmail watcher)
accounting.log_transaction(
    date=datetime.now().strftime("%Y-%m-%d"),
    type="income",
    amount=payment_amount,
    description=f"Payment received - {sender_name}",
    category="revenue"
)

# When expense detected (Bank statement)
accounting.log_transaction(
    date=transaction_date,
    type="expense",
    amount=transaction_amount,
    description=transaction_description,
    category="software"  # auto-categorized
)
```

---

## CEO Briefing Integration

```python
# In CEO Briefing Generator
from .claude.skills.accounting_manager.scripts.accounting_manager import AccountingManager

accounting = AccountingManager()
totals = accounting.get_totals()

briefing = f"""
## Financial Performance
- Total Income: ${totals['total_income']:,.2f}
- Total Expenses: ${totals['total_expense']:,.2f}
- Net Profit: ${totals['balance']:,.2f}
- Profit Margin: {(totals['balance']/totals['total_income']*100):.1f}%
"""
```

---

## Error Handling

```python
try:
    result = accounting.log_transaction(
        date="2026-03-14",
        type="income",
        amount=5000.00,
        description="Client payment"
    )
except ValueError as e:
    print(f"Validation error: {e}")
except FileNotFoundError as e:
    print(f"File error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Best Practices

✅ **DO:**
- Log transactions daily
- Use descriptive descriptions
- Categorize properly
- Include reference numbers (invoice IDs)
- Generate weekly summaries
- Review monthly reports

❌ **DON'T:**
- Skip transaction logging
- Use vague descriptions like "payment"
- Mix personal and business expenses
- Forget to backup accounting files

---

## Backup & Export

```python
# Export to CSV
accounting.export_to_csv("accounting_export_march_2026.csv")

# Export to JSON
accounting.export_to_json("accounting_export_march_2026.json")

# Backup vault
import shutil
shutil.copytree("AI_Employee_Vault/Accounting", "backup/Accounting_backup_20260314")
```

---

## File Format Example

**AI_Employee_Vault/Accounting/Current_Month.md:**

```markdown
---
month: March 2026
created: 2026-03-01
last_updated: 2026-03-14T10:30:00
total_income: 25000.00
total_expense: 3500.00
balance: 21500.00
---

# Accounting Ledger - March 2026

## Transactions

### TXN-20260301-001
- **Date:** 2026-03-01
- **Type:** expense
- **Amount:** $1,000.00
- **Description:** Office Rent - March 2026
- **Category:** rent
- **Reference:** RENT-MAR-2026

---

### TXN-20260305-001
- **Date:** 2026-03-05
- **Type:** income
- **Amount:** $5,000.00
- **Description:** Client A - Project Alpha Payment
- **Category:** revenue
- **Reference:** INV-001

---

### TXN-20260305-002
- **Date:** 2026-03-05
- **Type:** expense
- **Amount:** $150.00
- **Description:** Adobe Creative Cloud Subscription
- **Category:** software
- **Reference:** SUB-001

---

## Summary

| Type | Total | Count |
|------|-------|-------|
| Income | $25,000.00 | 8 |
| Expense | $3,500.00 | 12 |
| **Balance** | **$21,500.00** | **20** |
```

---

## API Reference

### `AccountingManager(vault_path)`

Initialize accounting manager.

**Parameters:**
- `vault_path` (str): Path to AI Employee vault

---

### `log_transaction(date, type, amount, description, category=None, reference=None)`

Log a new transaction.

**Parameters:**
- `date` (str): Transaction date (YYYY-MM-DD)
- `type` (str): "income" or "expense"
- `amount` (float): Transaction amount
- `description` (str): Transaction description
- `category` (str, optional): Category
- `reference` (str, optional): Reference number

**Returns:** dict with status and transaction_id

---

### `get_transactions(type=None, start_date=None, end_date=None, category=None)`

Retrieve transactions.

**Parameters:**
- `type` (str, optional): "income" or "expense"
- `start_date` (str, optional): Start date (YYYY-MM-DD)
- `end_date` (str, optional): End date (YYYY-MM-DD)
- `category` (str, optional): Filter by category

**Returns:** list of transaction dicts

---

### `generate_weekly_summary(week_start, week_end)`

Generate weekly summary report.

**Parameters:**
- `week_start` (str): Week start date (YYYY-MM-DD)
- `week_end` (str): Week end date (YYYY-MM-DD)

**Returns:** dict with summary and file path

---

### `generate_monthly_report(year, month)`

Generate monthly report.

**Parameters:**
- `year` (int): Year
- `month` (int): Month (1-12)

**Returns:** dict with report and file path

---

### `get_totals()`

Get total income, expense, and balance.

**Returns:** dict with totals

---

### `get_balance()`

Get current balance.

**Returns:** float

---

### `export_to_csv(filename)`

Export transactions to CSV.

**Parameters:**
- `filename` (str): Output CSV filename

**Returns:** str with file path

---

### `export_to_json(filename)`

Export transactions to JSON.

**Parameters:**
- `filename` (str): Output JSON filename

**Returns:** str with file path

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
1. Check file permissions in Accounting folder
2. Verify date format (YYYY-MM-DD)
3. Ensure amount is numeric
4. Review logs: `logs/ai_employee.log`

---

**Accounting Manager Skill** - Simple, lightweight vault-based accounting for hackathon Gold Tier ✅
