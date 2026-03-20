# Odoo MCP Server

**Tier:** Gold
**Version:** 1.0.0
**Author:** AI Employee Hackathon Team

---

## Overview

The Odoo MCP Server provides enterprise resource planning (ERP) capabilities to the AI Employee system via Odoo's JSON-RPC/XML-RPC API. It enables automated invoice management, payment recording, and financial reporting.

---

## Capabilities

- **Invoice Management**
  - `create_invoice()` - Create customer invoices
  - `list_invoices()` - Retrieve invoices with filters
  - Support for draft/posted states

- **Payment Processing**
  - `record_payment()` - Record payments against invoices
  - Automatic invoice validation

- **Partner Management**
  - Find existing customers/vendors
  - Create new partners automatically

- **Financial Reports**
  - Account balance queries
  - Connection testing

---

## Installation

### Prerequisites

1. Odoo 19+ instance (Community or Enterprise)
2. Python 3.8+
3. Required package: `xmlrpc-client` (included in Python standard library)

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Odoo Connection Settings
ODOO_URL=http://localhost:8069
ODOO_DB=odoo_db
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# Optional
LOG_LEVEL=INFO
```

---

## Usage

### Basic Usage

```python
from mcp.odoo_mcp.server import OdooMCPServer

# Initialize connection
odoo = OdooMCPServer()

# Create an invoice
result = odoo.create_invoice(
    customer_name="Acme Corp",
    items=[
        {"name": "Consulting Services", "quantity": 10, "price": 150.00},
        {"name": "Support", "quantity": 1, "price": 500.00}
    ],
    description="January 2026 Services",
    auto_validate=False  # Keep in draft for approval
)

print(f"Invoice created: {result['invoice_name']}")
print(f"Total amount: ${result['amount_total']}")
```

### List Invoices

```python
# Get all invoices
result = odoo.list_invoices(limit=10)

# Get only posted invoices
result = odoo.list_invoices(status="posted")

# Get invoices for specific customer
result = odoo.list_invoices(partner_name="Acme Corp")

for invoice in result['invoices']:
    print(f"{invoice['name']}: ${invoice['amount']} - {invoice['status']}")
```

### Record Payment

```python
# Record full payment
result = odoo.record_payment(
    invoice_id=123,
    amount=1500.00,
    reference="Bank Transfer #12345"
)

print(result['message'])
```

### Test Connection

```python
result = odoo.test_connection()
if result['connected']:
    print(f"Connected to Odoo {result['odoo_version']}")
else:
    print(f"Connection failed: {result['message']}")
```

---

## API Reference

### `create_invoice()`

Create a new customer invoice.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `customer_name` | str | Yes | - | Customer name |
| `items` | List[Dict] | Yes | - | Invoice line items |
| `description` | str | No | "" | Invoice narration |
| `invoice_date` | str | No | Today | Date (YYYY-MM-DD) |
| `due_date` | str | No | +30 days | Due date (YYYY-MM-DD) |
| `auto_validate` | bool | No | False | Post immediately |

**Item Structure:**
```python
{
    "name": "Service description",
    "quantity": 10,
    "price": 150.00,
    "account_id": 123  # Optional
}
```

**Returns:**
```python
{
    "status": "success",
    "invoice_id": 123,
    "invoice_name": "INV/2026/0001",
    "customer": "Acme Corp",
    "amount_total": 1500.00,
    "amount_untaxed": 1363.64,
    "state": "draft",
    "due_date": "2026-03-17"
}
```

### `list_invoices()`

Retrieve invoices with optional filters.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | str | No | "all" | draft/posted/cancel/all |
| `partner_name` | str | No | None | Filter by customer |
| `limit` | int | No | 10 | Max results |

**Returns:**
```python
{
    "status": "success",
    "count": 5,
    "invoices": [
        {
            "invoice_id": 123,
            "name": "INV/2026/0001",
            "customer": "Acme Corp",
            "date": "2026-02-15",
            "amount": 1500.00,
            "status": "posted",
            "payment_status": "paid"
        }
    ]
}
```

### `record_payment()`

Record a payment for an invoice.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `invoice_id` | int | Yes | - | Odoo invoice ID |
| `amount` | float | Yes | - | Payment amount |
| `payment_date` | str | No | Today | Date (YYYY-MM-DD) |
| `reference` | str | No | "" | Payment reference |

**Returns:**
```python
{
    "status": "success",
    "invoice_id": 123,
    "amount": 1500.00,
    "payment_date": "2026-02-20",
    "message": "Payment of $1500.0 recorded for invoice 123"
}
```

---

## Error Handling

All methods return a dictionary with `status` field:

```python
result = odoo.create_invoice(...)

if result['status'] == 'success':
    # Handle success
    print(f"Invoice: {result['invoice_name']}")
else:
    # Handle error
    print(f"Error: {result['message']}")
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Authentication failed | Wrong credentials | Check ODOO_USERNAME/PASSWORD |
| Connection refused | Odoo not running | Start Odoo server |
| Database not found | Wrong database name | Check ODOO_DB setting |
| Partner not found | Customer doesn't exist | Create customer first or use exact name |

---

## Integration with AI Employee

### With Accounting Manager

```python
from mcp.odoo_mcp import get_odoo_client
from scripts.accounting_manager import AccountingManager

odoo = get_odoo_client()
accounting = AccountingManager()

# Sync invoices from Odoo
invoices = odoo.list_invoices(status="posted")
for inv in invoices['invoices']:
    accounting.log_transaction(
        type="income" if inv['amount'] > 0 else "expense",
        amount=abs(inv['amount']),
        description=inv['name'],
        category="sales"
    )
```

### With CEO Briefing

```python
from mcp.odoo_mcp import get_odoo_client

odoo = get_odoo_client()

# Get financial data for briefing
invoices = odoo.list_invoices(status="posted", limit=30)
total_revenue = sum(inv['amount'] for inv in invoices['invoices'])

briefing_data = {
    'revenue': total_revenue,
    'invoice_count': invoices['count'],
    'pending_payments': len([i for i in invoices['invoices'] if i['payment_status'] != 'paid'])
}
```

---

## Logging

All operations are logged to the AI Employee log system:

```
[2026-03-17 10:30:00] [INFO] [odoo_mcp_server] Initializing Odoo MCP connection to http://localhost:8069
[2026-03-17 10:30:01] [INFO] [odoo_mcp_server] Successfully authenticated as user ID: 2
[2026-03-17 10:30:05] [INFO] [odoo_mcp_server] Created invoice INV/2026/0001 for Acme Corp: $1500.0
[2026-03-17 10:30:10] [INFO] [odoo_mcp_server] Recorded payment: $1500.0 for invoice 123
```

---

## Security Considerations

- Store credentials in environment variables, not in code
- Use HTTPS for production Odoo instances
- Implement proper access control in Odoo
- Enable audit logging in Odoo settings
- Regular backup of Odoo database

---

## Troubleshooting

### Connection Issues

```bash
# Test Odoo is running
curl http://localhost:8069

# Check database exists
# Login to Odoo web interface and verify database

# Test credentials
python -c "from mcp.odoo_mcp.server import OdooMCPServer; odoo = OdooMCPServer(); print(odoo.test_connection())"
```

### Authentication Errors

1. Verify username is correct (email format for Odoo Online)
2. Check password is correct
3. Ensure user has API access permissions
4. Verify database name is exact

### Invoice Creation Fails

1. Check customer exists in Odoo
2. Verify chart of accounts is configured
3. Ensure journal is configured for invoices
4. Check user has invoice creation permissions

---

## Related Files

| File | Purpose |
|------|---------|
| `mcp/odoo_mcp/server.py` | Main implementation |
| `mcp/odoo_mcp/__init__.py` | Module exports |
| `scripts/accounting_manager.py` | Accounting integration |
| `.env.example` | Environment template |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-17 | Initial Gold Tier implementation |
