from datetime import datetime
from pathlib import Path
from base_watcher import BaseWatcher
import logging

from log_manager import setup_logging
from skills.vault_skills import get_vault # Import the singleton vault instance

# Setup logger for LinkedInWatcher (Silver Tier log path)
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="linkedin_watcher")

class LinkedInWatcher(BaseWatcher):
    def __init__(self, vault_path: str):
        super().__init__(vault_path, check_interval=600)  # Check every 10 minutes
        self.post_ideas_path = self.vault_path / 'Post_Ideas'
        self.post_ideas_path.mkdir(parents=True, exist_ok=True)
        self.processed_ideas = set()
        self.vault = get_vault() # Get the vault skills instance
        logger.info("LinkedInWatcher initialized.")

    def check_for_updates(self) -> list:
        logger.info("Checking for new LinkedIn post ideas...")
        new_ideas = []
        for file_path in self.post_ideas_path.glob('*.md'):
            if file_path.name not in self.processed_ideas:
                new_ideas.append({'filepath': file_path})
                self.processed_ideas.add(file_path.name)
        logger.info(f"Found {len(new_ideas)} new LinkedIn post ideas.")
        return new_ideas

    def create_action_file(self, item) -> Path:
        idea_filepath = item['filepath']
        logger.info(f"Creating action file for LinkedIn post idea from: {idea_filepath.name}")
        try:
            with open(idea_filepath, 'r', encoding='utf-8') as f:
                post_content = f.read()

            title = f"LinkedIn Post from Idea: {idea_filepath.stem}"

            content = f"""---
type: linkedin_post_request
title: {title}
status: pending
created: {datetime.now().isoformat()}
source_file: {idea_filepath.name}
---

## LinkedIn Post Content
{post_content}

## Suggested Actions
- [ ] Draft LinkedIn post based on content
- [ ] Seek human approval if necessary
- [ ] Post to LinkedIn via MCP
"""
            # Create a unique filename for the post request in the 'Needs_Action' folder
            timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")
            file_name = f'LINKEDIN_POST_{timestamp}.md'
            file_path = self.vault.needs_action / file_name # Direct path as this watcher *creates* the file

            file_path.write_text(content) # Write content directly
            logger.info(f"Created LinkedIn action file: {file_name} in Needs_Action.")
            return file_path
        except Exception as e:
            logger.error(f"Error creating action file for LinkedIn idea {idea_filepath.name}: {e}")
            raise # Re-raise to be caught by orchestrator