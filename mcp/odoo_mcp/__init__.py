"""
Odoo MCP Server Module - Gold Tier Integration

Provides Odoo ERP capabilities via JSON-RPC/XML-RPC API.
"""

from .server import OdooMCPServer, get_odoo_client

__all__ = ['OdooMCPServer', 'get_odoo_client']
__version__ = '1.0.0'
