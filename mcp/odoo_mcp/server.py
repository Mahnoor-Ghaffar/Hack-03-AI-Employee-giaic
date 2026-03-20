#!/usr/bin/env python3
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
    from mcp.odoo_mcp.server import OdooMCPServer

    odoo = OdooMCPServer()
    result = odoo.create_invoice(
        customer_name="Acme Corp",
        items=[{"name": "Consulting", "quantity": 10, "price": 150.00}],
        description="January 2026 Consulting Services"
    )

Environment Variables:
    ODOO_URL: Odoo instance URL (default: http://localhost:8069)
    ODOO_DB: Database name (default: odoo_db)
    ODOO_USERNAME: Odoo username (default: admin)
    ODOO_PASSWORD: Odoo password (default: admin)
    LOG_LEVEL: Logging level (default: INFO)
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import xmlrpc.client

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('odoo_mcp_server')

# Configuration from environment
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'odoo_db')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')


class OdooMCPServer:
    """
    Odoo MCP Server for AI Employee integration.

    Uses Odoo's external XML-RPC API for all operations.
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

    def list_invoices(
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


# Convenience function for quick access
def get_odoo_client() -> OdooMCPServer:
    """Get an authenticated Odoo MCP client."""
    return OdooMCPServer()


if __name__ == '__main__':
    # Test the server
    print("=" * 60)
    print("Odoo MCP Server - Test Mode")
    print("=" * 60)
    
    try:
        odoo = OdooMCPServer()
        result = odoo.test_connection()
        print(f"Connection test: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Connection failed: {e}")
        print("\nMake sure Odoo is running and credentials are correct.")
        print("Set environment variables:")
        print("  ODOO_URL=http://your-odoo-url:8069")
        print("  ODOO_DB=your_database")
        print("  ODOO_USERNAME=your_username")
        print("  ODOO_PASSWORD=your_password")
