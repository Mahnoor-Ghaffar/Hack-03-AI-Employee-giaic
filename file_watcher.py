"""
File Watcher with Error Handling

This script watches a folder for new files and automatically processes them.
It includes robust error handling to ensure the script never crashes unexpectedly.
"""

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import shutil
import time
import logging
from datetime import datetime
from base_watcher import BaseWatcher

# Configure logging for general info messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def log_error_to_file(error_message: str, log_path: Path):
    """
    Write error messages to a log file with timestamp.
    
    This ensures errors are persisted even if they don't appear in console.
    """
    # Ensure the Logs directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Append error with timestamp to the log file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {error_message}\n")


class DropFolderHandler(FileSystemEventHandler):
    """
    Handles file system events (like new files being created).
    When a new file is detected, it copies it to the Needs_Action folder.
    """
    
    def __init__(self, vault_path: str, needs_action_path: Path):
        super().__init__()
        self.vault_path = Path(vault_path)
        self.needs_action = needs_action_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_log_path = Path("Logs/watcher_errors.log")

    def on_created(self, event):
        """
        Called when a file or directory is created.
        We only process files, not directories.
        """
        if event.is_directory:
            return
        
        source = Path(event.src_path)
        dest = self.needs_action / f'FILE_{source.name}'
        
        self.logger.info(f'Detected new file: {source}')
        
        try:
            # Copy the file to the Needs_Action folder
            shutil.copy2(source, dest)
            # Create accompanying metadata file
            self.create_metadata(source, dest)
            self.logger.info(f'Copied {source.name} to {dest} and created metadata.')
        except Exception as e:
            # Log error to both console and file
            error_msg = f'Error processing {source.name}: {e}'
            self.logger.error(error_msg)
            log_error_to_file(error_msg, self.error_log_path)

    def create_metadata(self, source: Path, dest: Path):
        """
        Creates a markdown metadata file alongside the copied file.
        """
        meta_path = dest.with_suffix('.md')
        content = f'''---
type: file_drop
original_name: {source.name}
size: {source.stat().st_size}
---

New file dropped for processing.
'''
        meta_path.write_text(content, encoding='utf-8')


class FileSystemWatcher(BaseWatcher):
    """
    Main watcher class that monitors a folder for changes.
    Includes error handling to prevent crashes.
    """
    
    def __init__(self, vault_path: str, watch_folder: str):
        super().__init__(vault_path, check_interval=1)
        self.watch_folder = Path(watch_folder)
        self.needs_action = Path(vault_path) / "Needs_Action"
        
        # Ensure required folders exist before setting up the handler
        self._ensure_folders_exist()
        
        self.event_handler = DropFolderHandler(vault_path, self.needs_action)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.watch_folder, recursive=False)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_log_path = Path("Logs/watcher_errors.log")

    def _ensure_folders_exist(self):
        """
        Create Inbox and Needs_Action folders if they don't exist.
        This prevents errors when the script starts or runs.
        """
        # Create Inbox folder (the folder being watched)
        self.watch_folder.mkdir(parents=True, exist_ok=True)
        self.logger.info(f'Ensured Inbox folder exists: {self.watch_folder}')
        
        # Create Needs_Action folder (where processed files go)
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.logger.info(f'Ensured Needs_Action folder exists: {self.needs_action}')

    def check_for_updates(self) -> list:
        """
        Returns a list of updates. 
        Note: Watchdog handles changes asynchronously via events, so this returns empty.
        """
        return []

    def create_action_file(self, item) -> Path:
        """
        Not used - the event handler creates action files directly.
        """
        raise NotImplementedError("create_action_file is handled by the event handler.")

    def run(self):
        """
        Start the watcher and keep it running.
        Wrapped in try/except to catch any unexpected errors.
        """
        self.logger.info(f'Starting {self.__class__.__name__} to watch {self.watch_folder}')
        
        try:
            self.observer.start()
            
            # Main loop - keeps running until interrupted
            while True:
                time.sleep(1)  # Keep the main thread alive
                
        except KeyboardInterrupt:
            # User pressed Ctrl+C - gracefully shut down
            self.logger.info('Received shutdown signal, stopping watcher...')
            self.observer.stop()
            
        except Exception as e:
            # Catch any unexpected errors to prevent crash
            error_msg = f'Unexpected error in FileSystemWatcher: {e}'
            self.logger.error(error_msg)
            log_error_to_file(error_msg, self.error_log_path)
            self.observer.stop()
            
        finally:
            # Always join the observer thread (cleanup)
            self.observer.join()
            self.logger.info('Watcher stopped.')


if __name__ == '__main__':
    # Script monitors the "Inbox" folder.
    # Whenever a new file appears, it creates a task file in "Needs_Action".
    
    vault_root = "AI_Employee_Vault"
    inbox_path = "Inbox"
    
    # Create base directories if they don't exist
    Path(vault_root).mkdir(exist_ok=True)
    Path(inbox_path).mkdir(exist_ok=True)

    # Initialize and run the watcher
    watcher = FileSystemWatcher(vault_root, inbox_path)
    watcher.run()
