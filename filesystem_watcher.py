from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import shutil
import time
import logging
from base_watcher import BaseWatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str, needs_action_path: Path):
        super().__init__()
        self.vault_path = Path(vault_path)
        self.needs_action = needs_action_path
        self.logger = logging.getLogger(self.__class__.__name__)

    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        dest = self.needs_action / f'FILE_{source.name}'
        self.logger.info(f'Detected new file: {source}')
        try:
            shutil.copy2(source, dest)
            self.create_metadata(source, dest)
            self.logger.info(f'Copied {source.name} to {dest} and created metadata.')
        except Exception as e:
            self.logger.error(f'Error processing {source.name}: {e}')

    def create_metadata(self, source: Path, dest: Path):
        meta_path = dest.with_suffix('.md')
        content = f'''---
type: file_drop
original_name: {source.name}
size: {source.stat().st_size}
---

New file dropped for processing.
'''
        meta_path.write_text(content)

class FileSystemWatcher(BaseWatcher):
    def __init__(self, vault_path: str, watch_folder: str):
        super().__init__(vault_path, check_interval=1)
        self.watch_folder = Path(watch_folder)
        self.event_handler = DropFolderHandler(vault_path, self.needs_action)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.watch_folder, recursive=False)

    def check_for_updates(self) -> list:
        # The watchdog observer handles updates asynchronously, so this method is not directly used for polling.
        # It will just return an empty list as changes are handled by on_created event.
        return []

    def create_action_file(self, item) -> Path:
        # This method is not used as the event handler directly creates action files.
        raise NotImplementedError("create_action_file is handled by the event handler.")

    def run(self):
        self.logger.info(f'Starting {self.__class__.__name__} to watch {self.watch_folder}')
        self.observer.start()
        try:
            while True:
                time.sleep(1) # Keep the main thread alive
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

if __name__ == '__main__':
    # Example Usage: Create a 'drop_zone' folder and point the watcher to it
    # Files placed in 'drop_zone' will be copied to 'AI_Employee_Vault/Needs_Action'
    vault_root = "AI_Employee_Vault"
    drop_zone_path = "drop_zone"
    Path(vault_root).mkdir(exist_ok=True)
    (Path(vault_root) / "Needs_Action").mkdir(exist_ok=True)
    Path(drop_zone_path).mkdir(exist_ok=True)

    watcher = FileSystemWatcher(vault_root, drop_zone_path)
    watcher.run()
