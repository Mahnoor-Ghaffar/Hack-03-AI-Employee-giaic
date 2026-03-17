"""
Odoo MCP Server - Gold Tier Integration

Provides Odoo ERP capabilities to the AI Employee system via JSON-RPC API.
Supports Odoo 19+ Community and Enterprise editions.

Capabilities:
- Create and manage invoices
- Record payments
- Generate financial reports
- Manage customers and vendors
- Track accounting transactions
- Create journal entries

Usage:
    from scripts.odoo_mcp_server import OdooMCPServer
    
    odoo = OdooMCPServer()
    result = odoo.create_invoice(
        customer_name="Acme Corp",
        items=[{"name": "Consulting", "quantity": 10, "price": 150.00}],
        description="January 2026 Consulting Services"
    )
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import xmlrpc.client

from log_manager import setup_logging

# Setup logging
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="odoo_mcp")

# Configuration from environment
ODOO_URL = Path(".env").exists() and next(
    (line.split("=")[1].strip() for line in Path(".env").read_text().splitlines() 
     if line.startswith("ODOO_URL=")), 
    "http://localhost:8069"
) or "http://localhost:8069"

ODOO_DB = Path(".env").exists() and next(
    (line.split("=")[1].strip() for line in Path(".env").read_text().splitlines() 
     if line.startswith("ODOO_DB=")), 
    "odoo_db"
) or "odoo_db"

ODOO_USERNAME = Path(".env").exists() and next(
    (line.split("=")[1].strip() for line in Path(".env").read_text().splitlines() 
     if line.startswith("ODOO_USERNAME=")), 
    "admin"
) or "admin"

ODOO_PASSWORD = Path(".env").exists() and next(
    (line.split("=")[1].strip() for line in Path(".env").read_text().splitlines() 
     if line.startswith("ODOO_PASSWORD=")), 
    "admin"
) or "admin"


class OdooMCPServer:
    """
    Odoo MCP Server for AI Employee integration.
    
    Uses Odoo's external JSON-RPC API for all operations.
    Reference: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
    """
    
    def __init__(
        self,
        url: str = None,
        db: str = None,
        username: str = None,
        password: str = None
    ):
        """
        Initialize Odoo MCP connection.
        
        Args:
            url: Odoo instance URL (e.g., http://localhost:8069)
            db: Database name
            username: Odoo username (email)
            password: Odoo password
        """
        self.url = url or ODOO_URL
        self.db = db or ODOO_DB
        self.username = username or ODOO_USERNAME
        self.password = password or ODOO_PASSWORD
        
        self.uid = None
        self.common = None
        self.models = None
        
        logger.info(f"Initializing Odoo MCP connection to {self.url}")
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Odoo and establish session."""
        try:
            # Common endpoint for authentication
            common_url = f"{self.url}/xmlrpc/2/common"
            self.common = xmlrpc.client.ServerProxy(common_url)
            
            # Authenticate and get user ID
            self.uid = self.common.authenticate(
                self.db,
                self.username,
                self.password,
                {}
            )
            
            if not self.uid:
                raise Exception("Authentication failed. Check credentials.")
            
            # Models endpoint for operations
            models_url = f"{self.url}/xmlrpc/2/object"
            self.models = xmlrpc.client.ServerProxy(models_url)
            
            logger.info(f"Successfully authenticated as user ID: {self.uid}")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Odoo: {e}")
            raise
    
    def _execute(self, model: str, method: str, *args, **kwargs):
        """
        Execute a method on an Odoo model.
        
        Args:
            model: Odoo model name (e.g., 'account.move')
            method: Method to call (e.g., 'create', 'search', 'read')
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method
            
        Returns:
            Method result
        """
        if not self.uid:
            raise Exception("Not authenticated. Call _authenticate() first.")
        
        try:
            result = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model,
                method,
                args,
                kwargs
            )
            logger.debug(f"Executed {method} on {model}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing {method} on {model}: {e}")
            raise
    
    # ==================== INVOICE MANAGEMENT ====================
    
    def create_invoice(
        self,
        customer_name: str,
        items: List[Dict[str, Any]],
        description: str = "",
        invoice_date: str = None,
        due_date: str = None,
        auto_validate: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new customer invoice.
        
        Args:
            customer_name: Customer name (must exist in Odoo)
            items: List of invoice lines [{"name": str, "quantity": float, "price": float, "account_id": int}]
            description: Invoice description/narration
            invoice_date: Invoice date (YYYY-MM-DD), defaults to today
            due_date: Due date (YYYY-MM-DD), defaults to invoice_date + 30 days
            auto_validate: If True, validate invoice immediately (default: False for approval workflow)
            
        Returns:
            Dictionary with invoice_id, name, amount, and status
        """
        try:
            # Find customer
            customer_id = self._find_partner(customer_name)
            if not customer_id:
                # Create new customer
                customer_id = self._create_partner(customer_name)
            
            # Prepare invoice lines
            invoice_lines = []
            for item in items:
                line_vals = {
                    "name": item.get("name", "Service"),
                    "quantity": item.get("quantity", 1),
                    "price_unit": item.get("price", 0),
                }
                if "account_id" in item:
                    line_vals["account_id"] = item["account_id"]
                invoice_lines.append((0, 0, line_vals))
            
            # Prepare invoice
            invoice_date = invoice_date or datetime.now().strftime("%Y-%m-%d")
            due_date = due_date or (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            invoice_vals = {
                "move_type": "out_invoice",
                "partner_id": customer_id,
                "invoice_date": invoice_date,
                "invoice_date_due": due_date,
                "narration": description,
                "invoice_line_ids": invoice_lines,
                "state": "draft" if not auto_validate else "posted"
            }
            
            # Create invoice
            invoice_id = self._execute("account.move", "create", invoice_vals)
            
            # Get invoice details
            invoice_data = self._execute(
                "account.move",
                "read",
                [invoice_id],
                ["name", "amount_total", "amount_untaxed", "state"]
            )[0]
            
            result = {
                "status": "success",
                "invoice_id": invoice_id,
                "invoice_name": invoice_data.get("name", f"INV/{invoice_id}"),
                "customer": customer_name,
                "amount_total": invoice_data.get("amount_total", 0),
                "amount_untaxed": invoice_data.get("amount_untaxed", 0),
                "state": invoice_data.get("state", "draft"),
                "due_date": due_date
            }
            
            logger.info(f"Created invoice {result['invoice_name']} for {customer_name}: ${result['amount_total']}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create invoice: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_invoices(
        self,
        status: str = "all",
        partner_name: str = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve invoices with optional filters.
        
        Args:
            status: Filter by status ('draft', 'posted', 'cancel', 'all')
            partner_name: Filter by customer/vendor name
            limit: Maximum number of results
            
        Returns:
            Dictionary with list of invoices
        """
        try:
            domain = []
            
            # Filter by status
            if status != "all":
                domain.append(("state", "=", status))
            
            # Filter by partner
            if partner_name:
                partner_id = self._find_partner(partner_name)
                if partner_id:
                    domain.append(("partner_id", "=", partner_id))
            
            # Search invoices
            invoice_ids = self._execute(
                "account.move",
                "search",
                domain,
                {"limit": limit, "order": "invoice_date desc"}
            )
            
            # Read invoice details
            invoices = self._execute(
                "account.move",
                "read",
                invoice_ids,
                ["name", "partner_id", "invoice_date", "amount_total", "state", "payment_state"]
            )
            
            # Format results
            formatted_invoices = []
            for inv in invoices:
                partner_data = self._execute(
                    "res.partner",
                    "read",
                    [inv["partner_id"][0]],
                    ["name"]
                )[0] if inv.get("partner_id") else {"name": "Unknown"}
                
                formatted_invoices.append({
                    "invoice_id": inv["id"],
                    "name": inv.get("name", ""),
                    "customer": partner_data.get("name", "Unknown"),
                    "date": inv.get("invoice_date", ""),
                    "amount": inv.get("amount_total", 0),
                    "status": inv.get("state", ""),
                    "payment_status": inv.get("payment_state", "")
                })
            
            return {
                "status": "success",
                "count": len(formatted_invoices),
                "invoices": formatted_invoices
            }
            
        except Exception as e:
            logger.error(f"Failed to get invoices: {e}")
            return {"status": "error", "message": str(e)}
    
    def record_payment(
        self,
        invoice_id: int,
        amount: float,
        payment_date: str = None,
        reference: str = ""
    ) -> Dict[str, Any]:
        """
        Record a payment for an invoice.
        
        Args:
            invoice_id: Odoo invoice ID
            amount: Payment amount
            payment_date: Payment date (YYYY-MM-DD), defaults to today
            reference: Payment reference/narration
            
        Returns:
            Dictionary with payment result
        """
        try:
            payment_date = payment_date or datetime.now().strftime("%Y-%m-%d")
            
            # Create payment register
            payment_vals = {
                "invoice_ids": [(4, invoice_id)],
                "amount": amount,
                "payment_date": payment_date,
                "payment_reference": reference or f"Payment for INV/{invoice_id}",
            }
            
            # Use payment register wizard
            payment_register = self._execute(
                "account.payment.register",
                "create",
                {
                    "invoice_ids": [(6, 0, [invoice_id])],
                    "amount": amount,
                    "payment_date": payment_date,
                    "payment_reference": reference or f"Payment for invoice {invoice_id}"
                }
            )
            
            # Create payment
            self._execute(
                "account.payment.register",
                "action_create_payments",
                [payment_register]
            )
            
            # Update invoice state
            self._execute(
                "account.move",
                "action_post",
                [invoice_id]
            )
            
            result = {
                "status": "success",
                "invoice_id": invoice_id,
                "amount": amount,
                "payment_date": payment_date,
                "message": f"Payment of ${amount} recorded for invoice {invoice_id}"
            }
            
            logger.info(f"Recorded payment: ${amount} for invoice {invoice_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to record payment: {e}")
            return {"status": "error", "message": str(e)}
    
    # ==================== FINANCIAL REPORTS ====================
    
    def get_financial_report(
        self,
        report_type: str = "profit_loss",
        date_from: str = None,
        date_to: str = None
    ) -> Dict[str, Any]:
        """
        Generate financial report.
        
        Args:
            report_type: Type of report ('profit_loss', 'balance_sheet', 'cash_flow')
            date_from: Start date (YYYY-MM-DD), defaults to start of fiscal year
            date_to: End date (YYYY-MM-DD), defaults to today
            
        Returns:
            Dictionary with report data
        """
        try:
            date_to = date_to or datetime.now().strftime("%Y-%m-%d")
            
            # Default to current fiscal year
            if not date_from:
                date_from = datetime.now().replace(month=1, day=1).strftime("%Y-%m-%d")
            
            if report_type == "profit_loss":
                return self._get_profit_loss(date_from, date_to)
            elif report_type == "balance_sheet":
                return self._get_balance_sheet(date_from, date_to)
            elif report_type == "trial_balance":
                return self._get_trial_balance(date_from, date_to)
            else:
                return {"status": "error", "message": f"Unknown report type: {report_type}"}
                
        except Exception as e:
            logger.error(f"Failed to generate financial report: {e}")
            return {"status": "error", "message": str(e)}
    
    def _get_profit_loss(self, date_from: str, date_to: str) -> Dict[str, Any]:
        """Get profit and loss statement."""
        try:
            # Get income and expense accounts
            income_accounts = self._execute(
                "account.account",
                "search",
                [("user_type_id.type", "=", "income")]
            )
            expense_accounts = self._execute(
                "account.account",
                "search",
                [("user_type_id.type", "=", "expense")]
            )
            
            # Calculate income
            income_lines = self._execute(
                "account.move.line",
                "search_read",
                [
                    ("account_id", "in", income_accounts),
                    ("date", ">=", date_from),
                    ("date", "<=", date_to),
                    ("parent_state", "=", "posted")
                ],
                ["balance", "credit", "debit"]
            )
            total_income = sum(line.get("credit", 0) - line.get("debit", 0) for line in income_lines)
            
            # Calculate expenses
            expense_lines = self._execute(
                "account.move.line",
                "search_read",
                [
                    ("account_id", "in", expense_accounts),
                    ("date", ">=", date_from),
                    ("date", "<=", date_to),
                    ("parent_state", "=", "posted")
                ],
                ["balance", "credit", "debit"]
            )
            total_expenses = sum(line.get("debit", 0) - line.get("credit", 0) for line in expense_lines)
            
            net_profit = total_income - total_expenses
            
            return {
                "status": "success",
                "report_type": "profit_loss",
                "period": f"{date_from} to {date_to}",
                "income": total_income,
                "expenses": total_expenses,
                "net_profit": net_profit,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get profit and loss: {e}")
            return {"status": "error", "message": str(e)}
    
    def _get_balance_sheet(self, date_from: str, date_to: str) -> Dict[str, Any]:
        """Get balance sheet."""
        try:
            # Get asset and liability accounts
            asset_accounts = self._execute(
                "account.account",
                "search",
                [("user_type_id.type", "=", "asset")]
            )
            liability_accounts = self._execute(
                "account.account",
                "search",
                [("user_type_id.type", "=", "liability")]
            )
            equity_accounts = self._execute(
                "account.account",
                "search",
                [("user_type_id.type", "=", "equity")]
            )
            
            # Calculate balances (simplified - would need opening balances for accuracy)
            def get_balance(accounts):
                lines = self._execute(
                    "account.move.line",
                    "search_read",
                    [
                        ("account_id", "in", accounts),
                        ("date", "<=", date_to),
                        ("parent_state", "=", "posted")
                    ],
                    ["balance", "credit", "debit"]
                )
                return sum(line.get("debit", 0) - line.get("credit", 0) for line in lines)
            
            total_assets = get_balance(asset_accounts)
            total_liabilities = get_balance(liability_accounts)
            total_equity = get_balance(equity_accounts)
            
            return {
                "status": "success",
                "report_type": "balance_sheet",
                "as_of": date_to,
                "assets": total_assets,
                "liabilities": total_liabilities,
                "equity": total_equity,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get balance sheet: {e}")
            return {"status": "error", "message": str(e)}
    
    def _get_trial_balance(self, date_from: str, date_to: str) -> Dict[str, Any]:
        """Get trial balance."""
        # Simplified implementation
        return {
            "status": "success",
            "report_type": "trial_balance",
            "period": f"{date_from} to {date_to}",
            "message": "Trial balance report - implementation in progress",
            "generated_at": datetime.now().isoformat()
        }
    
    # ==================== PARTNER MANAGEMENT ====================
    
    def _find_partner(self, name: str) -> Optional[int]:
        """Find partner by name."""
        try:
            partner_ids = self._execute(
                "res.partner",
                "search",
                [("name", "=ilike", name)],
                {"limit": 1}
            )
            return partner_ids[0] if partner_ids else None
        except Exception as e:
            logger.error(f"Error finding partner: {e}")
            return None
    
    def _create_partner(self, name: str, email: str = None, phone: str = None) -> int:
        """Create new partner (customer/vendor)."""
        try:
            partner_vals = {
                "name": name,
                "company_type": "company",
            }
            if email:
                partner_vals["email"] = email
            if phone:
                partner_vals["phone"] = phone
            
            partner_id = self._execute("res.partner", "create", partner_vals)
            logger.info(f"Created partner: {name} (ID: {partner_id})")
            return partner_id
        except Exception as e:
            logger.error(f"Failed to create partner: {e}")
            raise
    
    def get_partner(self, partner_id: int) -> Dict[str, Any]:
        """Get partner details."""
        try:
            partner_data = self._execute(
                "res.partner",
                "read",
                [partner_id],
                ["name", "email", "phone", "vat", "street", "city", "country_id"]
            )[0]
            
            return {
                "status": "success",
                "partner_id": partner_id,
                "name": partner_data.get("name", ""),
                "email": partner_data.get("email", ""),
                "phone": partner_data.get("phone", ""),
                "vat": partner_data.get("vat", ""),
                "address": partner_data.get("street", ""),
                "city": partner_data.get("city", ""),
            }
        except Exception as e:
            logger.error(f"Failed to get partner: {e}")
            return {"status": "error", "message": str(e)}
    
    # ==================== JOURNAL ENTRIES ====================
    
    def create_journal_entry(
        self,
        date: str,
        lines: List[Dict[str, Any]],
        reference: str = "",
        auto_post: bool = False
    ) -> Dict[str, Any]:
        """
        Create a journal entry.
        
        Args:
            date: Entry date (YYYY-MM-DD)
            lines: Journal lines [{"account_id": int, "debit": float, "credit": float, "name": str}]
            reference: Entry reference
            auto_post: If True, post immediately (default: False)
            
        Returns:
            Dictionary with entry result
        """
        try:
            # Prepare journal lines
            line_vals = []
            for line in lines:
                line_vals.append((0, 0, {
                    "account_id": line["account_id"],
                    "debit": line.get("debit", 0),
                    "credit": line.get("credit", 0),
                    "name": line.get("name", reference or "Journal Entry")
                }))
            
            # Create journal entry
            entry_vals = {
                "date": date,
                "line_ids": line_vals,
                "ref": reference,
                "state": "posted" if auto_post else "draft"
            }
            
            entry_id = self._execute("account.move", "create", entry_vals)
            
            if auto_post:
                self._execute("account.move", "action_post", [entry_id])
            
            return {
                "status": "success",
                "entry_id": entry_id,
                "date": date,
                "reference": reference,
                "state": "posted" if auto_post else "draft"
            }
            
        except Exception as e:
            logger.error(f"Failed to create journal entry: {e}")
            return {"status": "error", "message": str(e)}
    
    # ==================== UTILITY METHODS ====================
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Odoo connection and return server info."""
        try:
            version = self.common.version()
            return {
                "status": "success",
                "connected": True,
                "url": self.url,
                "database": self.db,
                "user_id": self.uid,
                "odoo_version": version.get("server_version", "unknown"),
                "server_info": version
            }
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "message": str(e)
            }
    
    def get_account_balance(self, account_code: str, date_to: str = None) -> Dict[str, Any]:
        """Get account balance."""
        try:
            date_to = date_to or datetime.now().strftime("%Y-%m-%d")
            
            # Find account
            account_ids = self._execute(
                "account.account",
                "search",
                [("code", "=", account_code)]
            )
            
            if not account_ids:
                return {"status": "error", "message": f"Account {account_code} not found"}
            
            # Get balance
            account_data = self._execute(
                "account.account",
                "read",
                account_ids,
                ["name", "balance", "debit", "credit"]
            )[0]
            
            return {
                "status": "success",
                "account_code": account_code,
                "account_name": account_data.get("name", ""),
                "balance": account_data.get("balance", 0),
                "debit": account_data.get("debit", 0),
                "credit": account_data.get("credit", 0),
                "as_of": date_to
            }
            
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            return {"status": "error", "message": str(e)}


# Convenience functions for direct usage

def create_odoo_connection() -> OdooMCPServer:
    """Create and return Odoo MCP connection."""
    return OdooMCPServer()


def test_odoo_connection() -> Dict[str, Any]:
    """Test Odoo connection."""
    try:
        odoo = OdooMCPServer()
        return odoo.test_connection()
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Test connection
    print("Testing Odoo MCP connection...")
    result = test_odoo_connection()
    print(json.dumps(result, indent=2))
