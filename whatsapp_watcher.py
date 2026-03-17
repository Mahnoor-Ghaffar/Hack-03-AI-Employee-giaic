from playwright.sync_api import sync_playwright
from base_watcher import BaseWatcher
from pathlib import Path
import json
import time

class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path: str, session_path: str):
        super().__init__(vault_path, check_interval=30)
        self.session_path = Path(session_path)
        self.keywords = ['urgent', 'asap', 'invoice', 'payment', 'help']

    def check_for_updates(self) -> list:
        with sync_playwright() as p:
            # Launch browser in headful mode with slowMo for debugging
            browser = p.chromium.launch_persistent_context(
                self.session_path,
                headless=False,
                slow_mo=1000  # 1000ms delay between actions for debugging
            )
            page = browser.pages[0]
            page.goto('https://web.whatsapp.com')
            page.wait_for_selector('[data-testid="chat-list"]')

            # Find unread messages
            unread = page.query_selector_all('[aria-label*="unread"]')
            messages = []
            for chat in unread:
                text = chat.inner_text().lower()
                if any(kw in text for kw in self.keywords):
                    messages.append({'text': text, 'chat': chat})

            # Keep browser open for 30 seconds for debugging
            print("Keeping browser open for 30 seconds for debugging...")
            time.sleep(30)

            browser.close()
            return messages

    def create_action_file(self, message) -> Path:
        # For simplicity, using a generic sender and the full text as content.
        # In a real scenario, you'd extract more specific sender/chat info from 'message['chat']'
        # and potentially fetch full message content.
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
        # Using a hash of the message text for a unique ID, or a timestamp
        message_id = hash(message['text']) # Placeholder for a more robust unique ID
        filepath = self.needs_action / f'WHATSAPP_{message_id}.md'
        filepath.write_text(content)
        return filepath
