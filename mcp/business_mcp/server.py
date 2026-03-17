#!/usr/bin/env python3
"""
Business MCP Server - Production-Ready

Provides external business action capabilities to Claude Code via Model Context Protocol (MCP).

Capabilities:
1. Send Email - Send emails via Gmail API
2. Create LinkedIn Post - Post to LinkedIn via browser automation
3. Log Business Activity - Log actions to vault/Logs/business.log

Usage:
    # Direct execution
    python mcp/business_mcp/server.py

    # Via Claude Code MCP configuration
    # Add to ~/.config/claude-code/mcp.json or project .claude/mcp.json

Environment Variables:
    GMAIL_CREDENTIALS_FILE: Path to Gmail credentials (default: gmail_credentials.json)
    VAULT_PATH: Path to AI Employee vault (default: AI_Employee_Vault)
    LINKEDIN_EMAIL: LinkedIn email for automation
    LINKEDIN_PASSWORD: LinkedIn password for automation
    LOG_LEVEL: Logging level (default: INFO)

Author: AI Employee Project
Version: 1.0.0
License: MIT
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('business-mcp-server')

# Environment configuration
GMAIL_CREDENTIALS_FILE = os.getenv('GMAIL_CREDENTIALS_FILE', 'gmail_credentials.json')
VAULT_PATH = Path(os.getenv('VAULT_PATH', 'AI_Employee_Vault'))
LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL', '')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD', '')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Set logging level
logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

# Ensure vault logs directory exists
LOGS_DIR = VAULT_PATH / 'Logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)
BUSINESS_LOG_FILE = LOGS_DIR / 'business.log'


class BusinessMCPServer:
    """
    Business MCP Server Implementation.
    
    Provides tools for common business actions:
    - send_email: Send emails via Gmail
    - post_linkedin: Create LinkedIn posts
    - log_activity: Log business activities
    """

    def __init__(self):
        self.server = Server('business-mcp')
        self._initialize_handlers()
        logger.info('BusinessMCPServer initialized')

    def _initialize_handlers(self):
        """Initialize MCP server handlers and tools."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available business tools."""
            return [
                Tool(
                    name='send_email',
                    description='Send an email via Gmail API. Use for professional communication, '
                               'client responses, and business correspondence.',
                    inputSchema={
                        'type': 'object',
                        'properties': {
                            'to': {
                                'type': 'string',
                                'description': 'Recipient email address'
                            },
                            'subject': {
                                'type': 'string',
                                'description': 'Email subject line'
                            },
                            'body': {
                                'type': 'string',
                                'description': 'Email body content (plain text or HTML)'
                            },
                            'cc': {
                                'type': 'string',
                                'description': 'CC recipients (comma-separated, optional)'
                            },
                            'bcc': {
                                'type': 'string',
                                'description': 'BCC recipients (comma-separated, optional)'
                            }
                        },
                        'required': ['to', 'subject', 'body']
                    }
                ),
                Tool(
                    name='post_linkedin',
                    description='Create a post on LinkedIn. Use for professional updates, '
                               'business announcements, and thought leadership content.',
                    inputSchema={
                        'type': 'object',
                        'properties': {
                            'content': {
                                'type': 'string',
                                'description': 'Post content (max 3000 characters for LinkedIn)'
                            },
                            'visibility': {
                                'type': 'string',
                                'description': 'Post visibility: anyone, connections, group (default: anyone)',
                                'enum': ['anyone', 'connections', 'group']
                            }
                        },
                        'required': ['content']
                    }
                ),
                Tool(
                    name='log_activity',
                    description='Log a business activity to the vault business log. '
                               'Use for tracking actions, decisions, and business events.',
                    inputSchema={
                        'type': 'object',
                        'properties': {
                            'message': {
                                'type': 'string',
                                'description': 'Activity message to log'
                            },
                            'category': {
                                'type': 'string',
                                'description': 'Activity category (email, social, meeting, task, etc.)',
                                'enum': ['email', 'social', 'meeting', 'task', 'call', 'other']
                            },
                            'metadata': {
                                'type': 'object',
                                'description': 'Additional metadata (optional)'
                            }
                        },
                        'required': ['message']
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool execution requests."""
            try:
                if name == 'send_email':
                    result = await self._send_email(arguments)
                elif name == 'post_linkedin':
                    result = await self._post_linkedin(arguments)
                elif name == 'log_activity':
                    result = await self._log_activity(arguments)
                else:
                    raise ValueError(f'Unknown tool: {name}')

                return [TextContent(type='text', text=json.dumps(result, indent=2))]

            except Exception as e:
                logger.error(f'Error executing tool {name}: {e}', exc_info=True)
                return [TextContent(
                    type='text',
                    text=json.dumps({
                        'status': 'error',
                        'error': str(e),
                        'tool': name
                    }, indent=2)
                )]

    async def _send_email(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Send an email via Gmail API.
        
        Args:
            arguments: Dictionary with to, subject, body, and optional cc/bcc
            
        Returns:
            Dictionary with status and message details
        """
        to = arguments.get('to', '')
        subject = arguments.get('subject', '')
        body = arguments.get('body', '')
        cc = arguments.get('cc', '')
        bcc = arguments.get('bcc', '')

        # Validate required fields
        if not to or not subject or not body:
            raise ValueError('Missing required fields: to, subject, and body are required')

        logger.info(f'Sending email to {to} with subject: {subject}')

        try:
            # Import Gmail sending functionality
            from scripts.send_email import send_gmail_email

            # Send the email
            result = send_gmail_email(
                to=to,
                subject=subject,
                body=body,
                cc=cc if cc else None,
                bcc=bcc if bcc else None
            )

            # Log the activity
            await self._log_activity({
                'message': f'Email sent to {to}: {subject}',
                'category': 'email',
                'metadata': {
                    'to': to,
                    'subject': subject,
                    'cc': cc,
                    'bcc': bcc,
                    'result': result
                }
            })

            return {
                'status': 'success',
                'message': f'Email sent successfully to {to}',
                'subject': subject,
                'timestamp': datetime.now().isoformat(),
                'details': result
            }

        except FileNotFoundError:
            # Gmail credentials not found - provide helpful error
            error_msg = (
                'Gmail credentials not found. Please ensure:\n'
                f'1. Gmail credentials file exists at: {GMAIL_CREDENTIALS_FILE}\n'
                '2. Run: python generate_gmail_credentials.py to authenticate\n'
                '3. Set GMAIL_CREDENTIALS_FILE environment variable if using custom path'
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        except Exception as e:
            logger.error(f'Failed to send email: {e}', exc_info=True)
            raise ValueError(f'Failed to send email: {str(e)}')

    async def _post_linkedin(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Create a post on LinkedIn via browser automation.
        
        Args:
            arguments: Dictionary with content and optional visibility
            
        Returns:
            Dictionary with status and post details
        """
        content = arguments.get('content', '')
        visibility = arguments.get('visibility', 'anyone')

        # Validate required fields
        if not content:
            raise ValueError('Missing required field: content is required')

        # Check content length (LinkedIn limit: 3000 characters)
        if len(content) > 3000:
            raise ValueError(f'Content exceeds LinkedIn limit of 3000 characters (current: {len(content)})')

        logger.info(f'Posting to LinkedIn (visibility: {visibility}): {content[:100]}...')

        try:
            # Import LinkedIn posting functionality
            from scripts.post_linkedin import post_to_linkedin

            # Check credentials
            if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
                error_msg = (
                    'LinkedIn credentials not configured. Please set:\n'
                    '1. LINKEDIN_EMAIL environment variable\n'
                    '2. LINKEDIN_PASSWORD environment variable\n'
                    'Or add them to your .env file'
                )
                raise ValueError(error_msg)

            # Post to LinkedIn
            result = await post_to_linkedin(
                content=content,
                email=LINKEDIN_EMAIL,
                password=LINKEDIN_PASSWORD,
                visibility=visibility
            )

            # Log the activity
            await self._log_activity({
                'message': f'LinkedIn post published: {content[:100]}...',
                'category': 'social',
                'metadata': {
                    'content_preview': content[:100],
                    'visibility': visibility,
                    'character_count': len(content),
                    'result': result
                }
            })

            return {
                'status': 'success',
                'message': 'LinkedIn post published successfully',
                'content_preview': content[:100] + '...' if len(content) > 100 else content,
                'character_count': len(content),
                'visibility': visibility,
                'timestamp': datetime.now().isoformat(),
                'details': result
            }

        except ImportError as e:
            error_msg = (
                'LinkedIn automation module not available. Please ensure:\n'
                '1. playwright is installed: pip install playwright\n'
                '2. Playwright browsers installed: playwright install\n'
                '3. scripts/post_linkedin.py exists in your project'
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        except Exception as e:
            logger.error(f'Failed to post to LinkedIn: {e}', exc_info=True)
            raise ValueError(f'Failed to post to LinkedIn: {str(e)}')

    async def _log_activity(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Log a business activity to the vault business log.
        
        Args:
            arguments: Dictionary with message, optional category and metadata
            
        Returns:
            Dictionary with status and log details
        """
        message = arguments.get('message', '')
        category = arguments.get('category', 'other')
        metadata = arguments.get('metadata', {})

        # Validate required fields
        if not message:
            raise ValueError('Missing required field: message is required')

        logger.info(f'Logging activity [{category}]: {message[:100]}...')

        try:
            # Create log entry
            timestamp = datetime.now().isoformat()
            log_entry = {
                'timestamp': timestamp,
                'category': category,
                'message': message,
                'metadata': metadata
            }

            # Format log line
            log_line = f'[{timestamp}] [{category.upper()}] {message}\n'

            # Append to business log file
            with open(BUSINESS_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_line)

            logger.info(f'Activity logged to {BUSINESS_LOG_FILE}')

            return {
                'status': 'success',
                'message': 'Activity logged successfully',
                'log_file': str(BUSINESS_LOG_FILE),
                'entry': log_entry,
                'timestamp': timestamp
            }

        except Exception as e:
            logger.error(f'Failed to log activity: {e}', exc_info=True)
            raise ValueError(f'Failed to log activity: {str(e)}')

    async def run(self):
        """Run the MCP server."""
        logger.info('Starting Business MCP Server...')
        logger.info(f'Vault path: {VAULT_PATH}')
        logger.info(f'Business log: {BUSINESS_LOG_FILE}')

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point."""
    logger.info('=' * 60)
    logger.info('Business MCP Server v1.0.0')
    logger.info('=' * 60)
    logger.info(f'Python version: {sys.version}')
    logger.info(f'Vault path: {VAULT_PATH}')
    logger.info(f'Gmail credentials: {GMAIL_CREDENTIALS_FILE}')
    logger.info(f'Business log: {BUSINESS_LOG_FILE}')
    logger.info('=' * 60)

    # Ensure vault exists
    if not VAULT_PATH.exists():
        logger.warning(f'Vault path does not exist: {VAULT_PATH}')
        VAULT_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f'Created vault directory: {VAULT_PATH}')

    # Ensure logs directory exists
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f'Created logs directory: {LOGS_DIR}')

    # Create business log file if it doesn't exist
    if not BUSINESS_LOG_FILE.exists():
        BUSINESS_LOG_FILE.touch()
        logger.info(f'Created business log: {BUSINESS_LOG_FILE}')

    # Run server
    server = BusinessMCPServer()
    asyncio.run(server.run())


if __name__ == '__main__':
    main()
