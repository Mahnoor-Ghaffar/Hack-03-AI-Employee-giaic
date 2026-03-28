"""
FileSystem Watcher for AI Employee - Silver Tier

This module monitors the Inbox folder (AI_Employee_Vault/Inbox) for new .md files.
When a new file appears, it:
1. Moves the file to Needs_Action using vault_skills.move_to_needs_action()
2. Triggers the task-planner skill using the T class from Claude SDK 0.1.39
3. Writes the plan to Plan_*.md in Needs_Action using vault_skills.write_plan()
"""

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from pathlib import Path
import time
import logging
import asyncio
import argparse

from log_manager import setup_logging
from skills.vault_skills import get_vault, write_plan
from claude_sdk_wrapper import T

# Setup logger for filesystem_watcher (Silver Tier log path)
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="filesystem_watcher")


class InboxHandler(FileSystemEventHandler):
    """
    Handles file system events for the Inbox folder.
    When a new .md file is created, it moves it to Needs_Action and triggers task-planner.
    """
    
    def __init__(self):
        super().__init__()
        self.vault = get_vault()
        logger.info("InboxHandler initialized with vault skills.")

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        source_path = Path(event.src_path)

        # Only process .md and .txt files in the Inbox folder
        if source_path.suffix.lower() not in ['.md', '.txt']:
            logger.debug(f"Ignoring non-markdown file: {source_path.name}")
            return

        # Verify the file is directly in Inbox (not in a subfolder)
        if source_path.parent != self.vault.inbox:
            logger.debug(f"Ignoring file not in Inbox root: {source_path}")
            return

        file_name = source_path.name
        logger.info(f'Detected new markdown file in Inbox: {file_name}')

        # Small delay to ensure file is fully written
        time.sleep(0.5)

        # Step 1: Move file from Inbox to Needs_Action using vault_skills
        move_result = self.vault.move_to_needs_action(file_name)
        logger.info(f"Move result: {move_result}")

        if "Error" not in move_result:
            # Step 2: Trigger task-planner skill automatically using T class
            self._trigger_task_planner(file_name)
        else:
            logger.error(f"Failed to move {file_name} to Needs_Action, skipping task-planner trigger.")

    def _trigger_task_planner(self, file_name: str):
        """
        Trigger the task-planner skill to generate a plan for the new task file.

        Args:
            file_name: Name of the file in Needs_Action to process.
        """
        try:
            # Create the task-planner prompt
            plan_prompt = f"""Process the task file '{file_name}' located in AI_Employee_Vault/Needs_Action.

Your responsibilities:
1. Read and analyze the content of the task file
2. Generate a detailed, step-by-step implementation plan
3. Return the plan in markdown format with clear sections and checkboxes for action items.

File to process: {file_name}
"""
            # Use T class to spawn the task-planner subagent (run in foreground to wait for result)
            task = T(
                description=f"Process new task file {file_name} with task-planner skill",
                prompt=plan_prompt,
                subagent_type='task-planner',
                model='opus',
                run_in_background=False,  # Run in foreground to get the plan content
                allowed_tools=["Read", "Write", "Glob", "Edit", "Bash", "Skill"],
                system_prompt="""You are a task-planner specialist for the AI Employee system.
Your role is to analyze task files in Needs_Action and generate detailed implementation plans."""
            )

            # Get the plan output from the task
            plan_content = task.output
            logger.info(f"Task-planner completed for {file_name}. Task ID: {task.task_id}")

            # Write the plan to a file using vault_skills
            if plan_content:
                plan_result = write_plan(file_name, plan_content)
                logger.info(f"Plan file created: {plan_result}")
            else:
                logger.warning(f"No plan content generated for {file_name}")

        except Exception as e:
            logger.error(f"Error triggering task-planner skill for {file_name}: {e}")


class FileSystemWatcher:
    """
    Main watcher class that monitors the Inbox folder for new markdown files.
    Uses watchdog for event-driven file monitoring.
    """
    
    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        """
        Initialize the FileSystemWatcher.
        
        Args:
            vault_path: Path to the AI Employee Vault root directory.
        """
        self.vault_path = Path(vault_path)
        self.inbox_path = self.vault_path / "Inbox"
        
        # Ensure Inbox folder exists
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize the event handler
        self.event_handler = InboxHandler()
        
        # Set up the observer
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.inbox_path),
            recursive=False
        )
        
        logger.info(f"FileSystemWatcher initialized to monitor Inbox: {self.inbox_path}")

    def start(self):
        """Start the file watcher."""
        logger.info(f'Starting {self.__class__.__name__} to watch {self.inbox_path}')
        self.observer.start()

    def stop(self):
        """Stop the file watcher."""
        logger.info(f'Stopping {self.__class__.__name__}')
        self.observer.stop()
        self.observer.join()
        logger.info(f'{self.__class__.__name__} stopped.')

    def run(self):
        """
        Run the file watcher in the foreground.
        Blocks until interrupted (Ctrl+C).
        """
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def process_existing_files(self):
        """
        Process all existing .md and .txt files in the Inbox folder.
        Useful for catching up on files that were added while the watcher was not running.
        """
        logger.info("Processing existing files in Inbox...")
        
        # Get all .md and .txt files in Inbox (not in subfolders)
        md_files = [f for f in self.inbox_path.iterdir() 
                    if f.is_file() and f.suffix.lower() in ['.md', '.txt']]
        
        if not md_files:
            logger.info("No existing .md or .txt files found in Inbox.")
            return
        
        logger.info(f"Found {len(md_files)} existing .md/.txt file(s) to process.")
        
        for file_path in md_files:
            file_name = file_path.name
            logger.info(f"Processing existing file: {file_name}")
            
            # Simulate the on_created event handling
            move_result = self.event_handler.vault.move_to_needs_action(file_name)
            logger.info(f"Move result: {move_result}")
            
            if "Error" not in move_result:
                self.event_handler._trigger_task_planner(file_name)
            else:
                logger.error(f"Failed to move {file_name} to Needs_Action, skipping task-planner trigger.")
        
        logger.info(f"Completed processing {len(md_files)} existing file(s).")


if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='FileSystem Watcher for AI Employee - Silver Tier')
    parser.add_argument(
        '--process-existing',
        action='store_true',
        help='Process existing .md files in Inbox on startup'
    )
    args = parser.parse_args()

    # Example Usage: Monitor the AI_Employee_Vault/Inbox folder

    # Ensure required directories exist
    vault_root = "AI_Employee_Vault"
    Path(vault_root).mkdir(exist_ok=True)
    (Path(vault_root) / "Needs_Action").mkdir(exist_ok=True)
    (Path(vault_root) / "Inbox").mkdir(exist_ok=True)
    (Path(vault_root) / "Done").mkdir(exist_ok=True)
    (Path(vault_root) / "Logs").mkdir(exist_ok=True)

    logger.info("Starting FileSystemWatcher in standalone mode...")
    logger.info(f"Monitoring: {Path(vault_root).resolve() / 'Inbox'}")
    logger.info("Press Ctrl+C to stop.")

    watcher = FileSystemWatcher(vault_root)
    
    # Process existing files if flag is set
    if args.process_existing:
        watcher.process_existing_files()
    
    watcher.run()
