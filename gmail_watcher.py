from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from base_watcher import BaseWatcher
from datetime import datetime
from pathlib import Path
import logging

from log_manager import setup_logging
from skills.vault_skills import get_vault # Import the singleton vault instance

# Setup logger for GmailWatcher (Silver Tier log path)
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="gmail_watcher")

class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str):
        super().__init__(vault_path, check_interval=120)
        self.creds = Credentials.from_authorized_user_file(credentials_path)
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.processed_ids = set()
        self.vault = get_vault() # Get the vault skills instance
        logger.info("GmailWatcher initialized.")

    def check_for_updates(self) -> list:
        logger.info("Checking for new Gmail updates...")
        try:
            results = self.service.users().messages().list(
                userId='me', q='is:unread is:important'
            ).execute()
            messages = results.get('messages', [])
            new_messages = [m for m in messages if m['id'] not in self.processed_ids]
            logger.info(f"Found {len(new_messages)} new Gmail messages.")
            return new_messages
        except Exception as e:
            logger.error(f"Error checking for Gmail updates: {e}")
            return []

    def create_action_file(self, message) -> Path:
        logger.info(f"Creating action file for Gmail message ID: {message['id']}")
        try:
            msg = self.service.users().messages().get(
                userId='me', id=message['id']
            ).execute()

            # Extract headers
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}

            content = f"""---
type: email
from: {headers.get('From', 'Unknown')}
subject: {headers.get('Subject', 'No Subject')}
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## Email Content
{msg.get('snippet', '')}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
"""
            # Use vault_skills to write to Needs_Action
            file_name = f'EMAIL_{message["id"]}.md'
            file_path = self.vault.needs_action / file_name # Direct path as this watcher *creates* the file

            file_path.write_text(content) # Write content directly
            self.processed_ids.add(message['id'])
            logger.info(f"Created Gmail action file: {file_name} in Needs_Action.")
            return file_path
        except Exception as e:
            logger.error(f"Error creating action file for Gmail message {message['id']}: {e}")
            raise # Re-raise to be caught by orchestrator