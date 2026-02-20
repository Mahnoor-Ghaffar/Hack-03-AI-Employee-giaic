"""
Log Manager - Prevent log files from growing forever.

This script checks log files and rotates them if they exceed 1 MB.
When a file is too large, it gets renamed with a timestamp and a fresh empty file is created.

Usage:
    python log_manager.py
"""

import os
from datetime import datetime
from pathlib import Path

# Maximum file size in bytes (1 MB = 1024 * 1024 bytes)
MAX_FILE_SIZE = 1 * 1024 * 1024


def get_file_size(file_path: Path) -> int:
    """
    Get the size of a file in bytes.
    Returns 0 if the file doesn't exist.
    """
    if file_path.exists():
        return file_path.stat().st_size
    return 0


def rotate_log_file(file_path: Path):
    """
    Rotate a log file by renaming it with a timestamp and creating a fresh empty file.
    
    Example:
        System_Log.md -> System_Log_2026-01-29_143022.md
    """
    # Get the file parts (name and extension)
    stem = file_path.stem  # filename without extension
    suffix = file_path.suffix  # extension (e.g., .md, .log)
    parent = file_path.parent  # parent directory
    
    # Create timestamp string for the backup filename
    # Format: YYYY-MM-DD_HHMMSS (e.g., 2026-01-29_143022)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    
    # Build the new name with timestamp
    new_name = f"{stem}_{timestamp}{suffix}"
    backup_path = parent / new_name
    
    # Rename the old file to the backup name
    file_path.rename(backup_path)
    print(f"Rotated: {file_path} -> {backup_path}")
    
    # Create a fresh empty file with the original name
    file_path.touch()
    print(f"Created fresh empty file: {file_path}")


def check_and_rotate(file_path: Path):
    """
    Check if a log file exceeds the size limit and rotate it if needed.
    """
    if not file_path.exists():
        print(f"File does not exist (skipping): {file_path}")
        return
    
    # Get current file size
    size_bytes = get_file_size(file_path)
    size_mb = size_bytes / (1024 * 1024)
    
    print(f"Checking: {file_path}")
    print(f"  Current size: {size_mb:.2f} MB")
    
    # Check if file exceeds the limit
    if size_bytes > MAX_FILE_SIZE:
        print(f"  File exceeds 1 MB limit - rotating...")
        rotate_log_file(file_path)
    else:
        print(f"  File is within limit - no action needed")


def main():
    """
    Main function - check all log files and rotate if needed.
    """
    print("=" * 50)
    print("Log Manager - Checking log files for rotation")
    print("=" * 50)
    print()
    
    # Define the log files to check
    # These are relative to the current directory
    log_files = [
        Path("System_Log.md"),
        Path("Logs/watcher_errors.log"),
    ]
    
    # Check each log file
    for log_file in log_files:
        check_and_rotate(log_file)
        print()
    
    print("=" * 50)
    print("Log check complete!")
    print("=" * 50)


if __name__ == '__main__':
    main()
