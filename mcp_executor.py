"""
MCP Executor for Platinum Tier
Executes approved actions via MCP servers

This executor runs ONLY on the Local machine (never on Cloud).
It has access to:
- Email send credentials
- Social media posting credentials
- WhatsApp session
- Banking/payment credentials

Usage:
    from mcp_executor import MCPExecutor
    executor = MCPExecutor()
    result = executor.execute_from_file(approval_file_path)
"""

import logging
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

from log_manager import setup_logging

# Setup logging
logger = setup_logging(
    log_file="logs/mcp_executor.log",
    logger_name="mcp_executor"
)


class MCPExecutor:
    """
    Platinum Tier MCP Executor
    
    Executes approved actions from /Pending_Approval/ or /Approved/ folders.
    Only runs on Local machine with full credentials access.
    """

    def __init__(self):
        """Initialize MCP Executor"""
        self.executed_actions = []
        self.failed_actions = []
        
        # Initialize MCP clients (lazy loading)
        self.email_mcp = None
        self.facebook_mcp = None
        self.twitter_mcp = None
        self.odoo_mcp = None
        
        logger.info("MCP Executor initialized (Local only)")

    def _load_mcp_servers(self):
        """Load MCP server modules"""
        try:
            from mcp.business_mcp.server import EmailMCPClient
            self.email_mcp = EmailMCPClient()
            logger.info("Email MCP client loaded")
        except Exception as e:
            logger.warning(f"Could not load Email MCP: {e}")
        
        try:
            from scripts.facebook_mcp_server import FacebookMCPServer
            self.facebook_mcp = FacebookMCPServer()
            logger.info("Facebook MCP client loaded")
        except Exception as e:
            logger.warning(f"Could not load Facebook MCP: {e}")
        
        try:
            from scripts.twitter_mcp_server import TwitterMCPServer
            self.twitter_mcp = TwitterMCPServer()
            logger.info("Twitter MCP client loaded")
        except Exception as e:
            logger.warning(f"Could not load Twitter MCP: {e}")
        
        try:
            from scripts.odoo_mcp_server import OdooMCPServer
            # Load with full credentials (Local only)
            import os
            self.odoo_mcp = OdooMCPServer(
                url=os.getenv('ODOO_URL', 'http://localhost:8069'),
                db=os.getenv('ODOO_DB', 'odoo_db'),
                username=os.getenv('ODOO_USERNAME', 'admin'),
                password=os.getenv('ODOO_PASSWORD', '')
            )
            logger.info("Odoo MCP client loaded")
        except Exception as e:
            logger.warning(f"Could not load Odoo MCP: {e}")

    def execute_from_file(self, approval_file: Path) -> Dict[str, Any]:
        """
        Execute action from approval file.
        
        Args:
            approval_file: Path to approval file in /Pending_Approval/ or /Approved/
        
        Returns:
            Result dictionary with success status and details
        """
        try:
            content = approval_file.read_text()
            
            # Parse YAML frontmatter
            metadata = self._parse_frontmatter(content)
            
            action_type = metadata.get('type', 'unknown')
            
            logger.info(f"Executing action type: {action_type} from {approval_file.name}")
            
            # Route to appropriate executor
            if action_type in ['email_triage', 'email_draft']:
                return self._execute_email_send(content, metadata, approval_file)
            
            elif action_type in ['social_post_draft', 'facebook_post_approval', 'twitter_post_approval']:
                return self._execute_social_post(content, metadata, approval_file)
            
            elif action_type == 'payment_approval':
                return self._execute_payment(content, metadata, approval_file)
            
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return {
                    'success': False,
                    'error': f'Unknown action type: {action_type}'
                }
                
        except Exception as e:
            logger.error(f"Error executing action from {approval_file}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter from markdown content"""
        import re
        
        # Extract frontmatter between --- markers
        match = re.search(r'^---\s*\n(.*?)\n---\s*$', content, re.DOTALL)
        if not match:
            return {}
        
        frontmatter = match.group(1)
        metadata = {}
        
        # Simple YAML parser (handles basic key-value pairs)
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Handle boolean values
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                # Handle lists
                elif value.startswith('[') and value.endswith(']'):
                    value = [v.strip() for v in value[1:-1].split(',')]
                
                metadata[key] = value
        
        return metadata

    def _execute_email_send(self, content: str, metadata: Dict[str, Any], approval_file: Path) -> Dict[str, Any]:
        """Execute email send action"""
        logger.info("Executing email send...")
        
        if not self.email_mcp:
            self._load_mcp_servers()
        
        if not self.email_mcp:
            return {
                'success': False,
                'error': 'Email MCP not available'
            }
        
        try:
            # Extract email details from content
            to_email = metadata.get('to', metadata.get('from', ''))
            subject = metadata.get('subject', 'No subject')
            
            # Extract draft reply from content
            import re
            draft_match = re.search(r'## Draft Reply\s*```(.*?)```', content, re.DOTALL)
            body = draft_match.group(1).strip() if draft_match else "Please see attached."
            
            # Send email
            result = self.email_mcp.send_email(
                to=to_email,
                subject=subject,
                body=body
            )
            
            if result.get('status') == 'success':
                logger.info(f"Email sent successfully to {to_email}")
                self.executed_actions.append({
                    'type': 'email_send',
                    'timestamp': datetime.now().isoformat(),
                    'file': str(approval_file),
                    'result': result
                })
                return {
                    'success': True,
                    'action': 'email_send',
                    'result': result
                }
            else:
                logger.error(f"Email send failed: {result.get('message')}")
                self.failed_actions.append({
                    'type': 'email_send',
                    'timestamp': datetime.now().isoformat(),
                    'file': str(approval_file),
                    'error': result.get('message')
                })
                return result
                
        except Exception as e:
            logger.error(f"Error executing email send: {e}")
            self.failed_actions.append({
                'type': 'email_send',
                'timestamp': datetime.now().isoformat(),
                'file': str(approval_file),
                'error': str(e)
            })
            return {
                'success': False,
                'error': str(e)
            }

    def _execute_social_post(self, content: str, metadata: Dict[str, Any], approval_file: Path) -> Dict[str, Any]:
        """Execute social media post action"""
        platform = metadata.get('platform', 'unknown')
        logger.info(f"Executing {platform} post...")
        
        if not self.facebook_mcp and not self.twitter_mcp:
            self._load_mcp_servers()
        
        try:
            # Extract post content
            import re
            content_match = re.search(r'\*\*Suggested Content:\*\*\s*```\s*(.*?)```', content, re.DOTALL)
            
            if not content_match:
                # Try alternative format
                content_match = re.search(r'\*\*Suggested Tweet:\*\*\s*```\s*(.*?)```', content, re.DOTALL)
            
            post_content = content_match.group(1).strip() if content_match else "No content"
            
            if platform == 'facebook':
                if not self.facebook_mcp:
                    return {'success': False, 'error': 'Facebook MCP not available'}
                
                result = self.facebook_mcp.post_to_facebook(
                    content=post_content,
                    page_name=metadata.get('page_name')
                )
                
            elif platform == 'twitter':
                if not self.twitter_mcp:
                    return {'success': False, 'error': 'Twitter MCP not available'}
                
                result = self.twitter_mcp.post_tweet(content=post_content)
                
            elif platform == 'instagram':
                if not self.facebook_mcp:
                    return {'success': False, 'error': 'Facebook MCP not available'}
                
                result = self.facebook_mcp.post_to_instagram(
                    content=post_content,
                    caption=metadata.get('caption', post_content)
                )
                
            else:
                return {
                    'success': False,
                    'error': f'Unsupported platform: {platform}'
                }
            
            if result.get('status') == 'success':
                logger.info(f"{platform} post successful")
                self.executed_actions.append({
                    'type': f'{platform}_post',
                    'timestamp': datetime.now().isoformat(),
                    'file': str(approval_file),
                    'result': result
                })
                return {
                    'success': True,
                    'action': f'{platform}_post',
                    'result': result
                }
            else:
                logger.error(f"{platform} post failed: {result.get('message')}")
                self.failed_actions.append({
                    'type': f'{platform}_post',
                    'timestamp': datetime.now().isoformat(),
                    'file': str(approval_file),
                    'error': result.get('message')
                })
                return result
                
        except Exception as e:
            logger.error(f"Error executing {platform} post: {e}")
            self.failed_actions.append({
                'type': f'{platform}_post',
                'timestamp': datetime.now().isoformat(),
                'file': str(approval_file),
                'error': str(e)
            })
            return {
                'success': False,
                'error': str(e)
            }

    def _execute_payment(self, content: str, metadata: Dict[str, Any], approval_file: Path) -> Dict[str, Any]:
        """Execute payment action via Odoo"""
        logger.info("Executing payment...")
        
        if not self.odoo_mcp:
            self._load_mcp_servers()
        
        if not self.odoo_mcp:
            return {
                'success': False,
                'error': 'Odoo MCP not available'
            }
        
        try:
            amount = float(metadata.get('amount', 0))
            recipient = metadata.get('recipient', 'Unknown')
            reference = metadata.get('reference', '')
            
            # Record payment in Odoo
            result = self.odoo_mcp.record_payment(
                amount=amount,
                partner_name=recipient,
                reference=reference
            )
            
            if result.get('success'):
                logger.info(f"Payment of ${amount} to {recipient} recorded successfully")
                self.executed_actions.append({
                    'type': 'payment',
                    'timestamp': datetime.now().isoformat(),
                    'file': str(approval_file),
                    'result': result
                })
                return {
                    'success': True,
                    'action': 'payment',
                    'result': result
                }
            else:
                logger.error(f"Payment failed: {result.get('error')}")
                self.failed_actions.append({
                    'type': 'payment',
                    'timestamp': datetime.now().isoformat(),
                    'file': str(approval_file),
                    'error': result.get('error')
                })
                return result
                
        except Exception as e:
            logger.error(f"Error executing payment: {e}")
            self.failed_actions.append({
                'type': 'payment',
                'timestamp': datetime.now().isoformat(),
                'file': str(approval_file),
                'error': str(e)
            })
            return {
                'success': False,
                'error': str(e)
            }

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            'total_executed': len(self.executed_actions),
            'total_failed': len(self.failed_actions),
            'success_rate': len(self.executed_actions) / (len(self.executed_actions) + len(self.failed_actions)) * 100 if (self.executed_actions or self.failed_actions) else 0,
            'executed_actions': self.executed_actions,
            'failed_actions': self.failed_actions
        }


if __name__ == "__main__":
    # Test MCP Executor
    print("MCP Executor Test")
    print("=" * 40)
    
    executor = MCPExecutor()
    stats = executor.get_execution_stats()
    
    print(f"Executed actions: {stats['total_executed']}")
    print(f"Failed actions: {stats['total_failed']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
