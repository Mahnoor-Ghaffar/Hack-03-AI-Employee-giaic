from datetime import datetime
from playwright.sync_api import sync_playwright
from base_watcher import BaseWatcher
from pathlib import Path
import json
import time
import logging

from log_manager import setup_logging

# Setup logger
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="whatsapp_watcher")

class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str, session_path: str, check_interval: int = 300):
        super().__init__(vault_path, check_interval=check_interval)
        self.session_path = Path(session_path)
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help']
        logger.info(f"WhatsAppWatcher initialized. Session: {self.session_path}")

    def check_for_updates(self) -> list:
        """
        Check WhatsApp Web for new messages.
        Note: This opens a browser, checks for messages, and closes.
        For production, consider using whatsapp-web.js for a persistent session.
        """
        logger.info("Checking WhatsApp for new messages...")
        messages = []
        
        try:
            with sync_playwright() as p:
                # Launch browser in headful mode with slowMo for debugging
                browser = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=False,
                    slow_mo=500  # 500ms delay between actions
                )
                page = browser.pages[0]
                page.goto('https://web.whatsapp.com')
                
                # Wait for chat list to load (with timeout)
                try:
                    page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)
                except Exception as e:
                    logger.warning(f"Could not load WhatsApp Web: {e}")
                    browser.close()
                    return []

                # Find unread messages
                unread = page.query_selector_all('[aria-label*="unread"]')
                for chat in unread:
                    text = chat.inner_text().lower()
                    if any(kw in text for kw in self.keywords):
                        messages.append({'text': text, 'chat': chat})

                browser.close()
                
            logger.info(f"Found {len(messages)} matching WhatsApp messages")
            return messages
            
        except Exception as e:
            logger.error(f"Error checking WhatsApp: {e}")
            return []

    def create_action_file(self, message) -> Path:
        """Create action file for WhatsApp message"""
        content = f'''---
type: whatsapp
from: Unknown_WhatsApp_Contact
subject: New WhatsApp Message (Keyword: {', '.join(self.keywords)})
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## WhatsApp Message Content
{message['text']}

## Suggested Actions
- [ ] Reply to sender
- [ ] Take action based on keywords
- [ ] Archive after processing
'''
        # Using a timestamp for a unique ID
        message_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.needs_action / f'WHATSAPP_{message_id}.md'
        filepath.write_text(content)
        logger.info(f"Created WhatsApp action file: {filepath.name}")
        return filepath


if __name__ == "__main__":
    """Run WhatsAppWatcher in continuous mode for PM2"""
    import sys
    
    vault_path = "AI_Employee_Vault"
    session_path = Path(vault_path) / "whatsapp_session"
    
    watcher = WhatsAppWatcher(
        vault_path=vault_path,
        session_path=str(session_path),
        check_interval=300  # Check every 5 minutes
    )
    
    logger.info("Starting WhatsAppWatcher in continuous mode...")
    logger.info(f"Session path: {session_path}")
    logger.info("Press Ctrl+C to stop")
    
    try:
        watcher.run()  # This runs the infinite loop from BaseWatcher
    except KeyboardInterrupt:
        logger.info("WhatsAppWatcher shutting down (user interrupt)")
        sys.exit(0)
