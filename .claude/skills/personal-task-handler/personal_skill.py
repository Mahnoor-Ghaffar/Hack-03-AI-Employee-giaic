#!/usr/bin/env python3
"""
Personal Task Handler Skill - Gold Tier Integration

Provides personal task management capabilities for the AI Employee system.
Tasks are stored in AI_Employee_Vault/Personal/

Capabilities:
- Create personal tasks
- Update task status
- List tasks by status
- Delete tasks
- Archive completed tasks
- Log all actions

Usage:
    from .claude.skills.personal_task_handler.personal_skill import PersonalTaskHandler

    personal = PersonalTaskHandler()
    
    # Create a task
    result = personal.create_task(
        title="Review quarterly reports",
        description="Review Q1 financial reports before meeting",
        priority="high",
        due_date="2026-03-20"
    )
    
    # Update task status
    result = personal.update_task_status(task_id="TASK_001", status="in_progress")

Environment Variables:
    LOG_LEVEL: Logging level (default: INFO)
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_file = os.getenv('PERSONAL_LOG_FILE', 'logs/personal_tasks.log')

# Ensure log directory exists
log_path = Path(log_file)
log_path.parent.mkdir(parents=True, exist_ok=True)

# File handler for personal task logs
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Console handler
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Logger setup
logger = logging.getLogger('personal_task_handler')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', 'AI_Employee_Vault'))
PERSONAL_PATH = VAULT_PATH / 'Personal'
ARCHIVE_PATH = PERSONAL_PATH / 'Archive'

# Ensure directories exist
PERSONAL_PATH.mkdir(parents=True, exist_ok=True)
ARCHIVE_PATH.mkdir(parents=True, exist_ok=True)

# Task file format
TASK_FILE_PATTERN = "{task_id}.json"


class PersonalTaskHandler:
    """
    Personal Task Handler for AI Employee integration.

    Manages personal tasks in the AI Employee Vault.
    """

    def __init__(self, vault_path: Path = None):
        """
        Initialize Personal Task Handler.

        Args:
            vault_path: Path to vault directory
        """
        self.vault_path = vault_path or VAULT_PATH
        self.personal_path = self.vault_path / 'Personal'
        self.archive_path = self.personal_path / 'Archive'

        # Ensure directories exist
        self.personal_path.mkdir(parents=True, exist_ok=True)
        self.archive_path.mkdir(parents=True, exist_ok=True)

        logger.info(f'PersonalTaskHandler initialized at {self.personal_path}')

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: str = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new personal task.

        Args:
            title: Task title
            description: Task description
            priority: Task priority (low, medium, high, urgent)
            due_date: Due date in YYYY-MM-DD format
            tags: List of tags for categorization
            metadata: Additional metadata

        Returns:
            Dictionary with task details and status
        """
        if not title:
            raise ValueError("Task title is required")

        task_id = f"TASK_{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.now().isoformat()

        task = {
            "task_id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "pending",
            "created_at": created_at,
            "updated_at": created_at,
            "due_date": due_date,
            "tags": tags or [],
            "metadata": metadata or {},
            "history": [
                {
                    "action": "created",
                    "timestamp": created_at,
                    "status": "pending"
                }
            ]
        }

        # Save task to file
        task_file = self.personal_path / TASK_FILE_PATTERN.format(task_id=task_id)
        self._save_task(task_file, task)

        result = {
            "status": "success",
            "task_id": task_id,
            "title": title,
            "priority": priority,
            "due_date": due_date,
            "created_at": created_at,
            "file_path": str(task_file)
        }

        logger.info(f"Created task: {task_id} - {title}")
        self._log_action("task_created", result)

        return result

    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with task details
        """
        # Check in personal folder
        task_file = self.personal_path / TASK_FILE_PATTERN.format(task_id=task_id)
        if task_file.exists():
            task = self._load_task(task_file)
            return {
                "status": "success",
                "task": task,
                "location": "personal"
            }

        # Check in archive
        archive_file = self.archive_path / TASK_FILE_PATTERN.format(task_id=task_id)
        if archive_file.exists():
            task = self._load_task(archive_file)
            return {
                "status": "success",
                "task": task,
                "location": "archive"
            }

        return {
            "status": "error",
            "message": f"Task {task_id} not found"
        }

    def update_task_status(
        self,
        task_id: str,
        status: str,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Update a task's status.

        Args:
            task_id: Task ID
            status: New status (pending, in_progress, completed, cancelled)
            notes: Optional notes about the status change

        Returns:
            Dictionary with update result
        """
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

        # Find task
        task_file = self.personal_path / TASK_FILE_PATTERN.format(task_id=task_id)
        is_archived = False

        if not task_file.exists():
            # Check archive
            archive_file = self.archive_path / TASK_FILE_PATTERN.format(task_id=task_id)
            if archive_file.exists():
                task_file = archive_file
                is_archived = True
            else:
                return {
                    "status": "error",
                    "message": f"Task {task_id} not found"
                }

        # Load and update task
        task = self._load_task(task_file)
        old_status = task.get('status', 'pending')

        task['status'] = status
        task['updated_at'] = datetime.now().isoformat()

        # Add to history
        history_entry = {
            "action": "status_change",
            "timestamp": task['updated_at'],
            "old_status": old_status,
            "new_status": status,
            "notes": notes
        }
        task['history'].append(history_entry)

        # Save updated task
        self._save_task(task_file, task)

        # Archive if completed or cancelled
        if status in ['completed', 'cancelled'] and not is_archived:
            self._archive_task(task_id, task)

        result = {
            "status": "success",
            "task_id": task_id,
            "old_status": old_status,
            "new_status": status,
            "updated_at": task['updated_at']
        }

        logger.info(f"Updated task {task_id}: {old_status} -> {status}")
        self._log_action("task_status_updated", result)

        return result

    def update_task(
        self,
        task_id: str,
        title: str = None,
        description: str = None,
        priority: str = None,
        due_date: str = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Update task details.

        Args:
            task_id: Task ID
            title: New title
            description: New description
            priority: New priority
            due_date: New due date
            tags: New tags

        Returns:
            Dictionary with update result
        """
        # Find task
        task_file = self.personal_path / TASK_FILE_PATTERN.format(task_id=task_id)
        is_archived = False

        if not task_file.exists():
            archive_file = self.archive_path / TASK_FILE_PATTERN.format(task_id=task_id)
            if archive_file.exists():
                task_file = archive_file
                is_archived = True
            else:
                return {
                    "status": "error",
                    "message": f"Task {task_id} not found"
                }

        # Load and update task
        task = self._load_task(task_file)

        updates = {}
        if title is not None:
            task['title'] = title
            updates['title'] = title
        if description is not None:
            task['description'] = description
            updates['description'] = description
        if priority is not None:
            task['priority'] = priority
            updates['priority'] = priority
        if due_date is not None:
            task['due_date'] = due_date
            updates['due_date'] = due_date
        if tags is not None:
            task['tags'] = tags
            updates['tags'] = tags

        if not updates:
            return {
                "status": "error",
                "message": "No updates provided"
            }

        task['updated_at'] = datetime.now().isoformat()

        # Add to history
        history_entry = {
            "action": "task_updated",
            "timestamp": task['updated_at'],
            "updates": updates
        }
        task['history'].append(history_entry)

        # Save updated task
        self._save_task(task_file, task)

        result = {
            "status": "success",
            "task_id": task_id,
            "updates": updates,
            "updated_at": task['updated_at']
        }

        logger.info(f"Updated task {task_id}: {updates}")
        self._log_action("task_updated", result)

        return result

    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """
        Delete a task.

        Args:
            task_id: Task ID to delete

        Returns:
            Dictionary with delete result
        """
        # Find task
        task_file = self.personal_path / TASK_FILE_PATTERN.format(task_id=task_id)

        if not task_file.exists():
            archive_file = self.archive_path / TASK_FILE_PATTERN.format(task_id=task_id)
            if archive_file.exists():
                task_file = archive_file
            else:
                return {
                    "status": "error",
                    "message": f"Task {task_id} not found"
                }

        # Load task for logging
        task = self._load_task(task_file)

        # Delete file
        task_file.unlink()

        result = {
            "status": "success",
            "task_id": task_id,
            "title": task.get('title', ''),
            "deleted_at": datetime.now().isoformat()
        }

        logger.info(f"Deleted task: {task_id}")
        self._log_action("task_deleted", result)

        return result

    def list_tasks(
        self,
        status: str = None,
        priority: str = None,
        tag: str = None,
        include_archived: bool = False
    ) -> Dict[str, Any]:
        """
        List tasks with optional filters.

        Args:
            status: Filter by status
            priority: Filter by priority
            tag: Filter by tag
            include_archived: Include archived tasks

        Returns:
            Dictionary with list of tasks
        """
        tasks = []

        # Search personal folder
        for task_file in self.personal_path.glob("TASK_*.json"):
            task = self._load_task(task_file)
            if self._matches_filter(task, status, priority, tag):
                tasks.append(task)

        # Search archive if requested
        if include_archived:
            for task_file in self.archive_path.glob("TASK_*.json"):
                task = self._load_task(task_file)
                if self._matches_filter(task, status, priority, tag):
                    tasks.append(task)

        # Sort by priority and due date
        priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
        tasks.sort(key=lambda t: (
            priority_order.get(t.get('priority', 'medium'), 2),
            t.get('due_date') or '9999-99-99'
        ))

        result = {
            "status": "success",
            "count": len(tasks),
            "tasks": tasks,
            "filters": {
                "status": status,
                "priority": priority,
                "tag": tag,
                "include_archived": include_archived
            }
        }

        logger.info(f"Listed {len(tasks)} tasks")
        return result

    def get_summary(self) -> Dict[str, Any]:
        """
        Get task summary statistics.

        Returns:
            Dictionary with summary statistics
        """
        all_tasks = self.list_tasks(include_archived=False)
        archived_tasks = self.list_tasks(status='completed', include_archived=True)

        tasks = all_tasks.get('tasks', [])

        summary = {
            "total": len(tasks),
            "by_status": {
                "pending": len([t for t in tasks if t.get('status') == 'pending']),
                "in_progress": len([t for t in tasks if t.get('status') == 'in_progress']),
                "completed": len([t for t in tasks if t.get('status') == 'completed']),
                "cancelled": len([t for t in tasks if t.get('status') == 'cancelled'])
            },
            "by_priority": {
                "urgent": len([t for t in tasks if t.get('priority') == 'urgent']),
                "high": len([t for t in tasks if t.get('priority') == 'high']),
                "medium": len([t for t in tasks if t.get('priority') == 'medium']),
                "low": len([t for t in tasks if t.get('priority') == 'low'])
            },
            "overdue": len([
                t for t in tasks
                if t.get('due_date') and
                t.get('status') not in ['completed', 'cancelled'] and
                t.get('due_date') < datetime.now().strftime('%Y-%m-%d')
            ]),
            "archived_count": archived_tasks.get('count', 0)
        }

        return {
            "status": "success",
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }

    def _matches_filter(
        self,
        task: Dict[str, Any],
        status: str = None,
        priority: str = None,
        tag: str = None
    ) -> bool:
        """Check if task matches filters."""
        if status and task.get('status') != status:
            return False
        if priority and task.get('priority') != priority:
            return False
        if tag and tag not in task.get('tags', []):
            return False
        return True

    def _load_task(self, task_file: Path) -> Dict[str, Any]:
        """Load task from file."""
        with open(task_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_task(self, task_file: Path, task: Dict[str, Any]):
        """Save task to file."""
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=2)

    def _archive_task(self, task_id: str, task: Dict[str, Any]):
        """Move task to archive."""
        archive_file = self.archive_path / TASK_FILE_PATTERN.format(task_id=task_id)
        self._save_task(archive_file, task)

        # Remove from personal folder
        personal_file = self.personal_path / TASK_FILE_PATTERN.format(task_id=task_id)
        if personal_file.exists():
            personal_file.unlink()

        logger.info(f"Archived task: {task_id}")

    def _log_action(self, action: str, data: Dict[str, Any]):
        """Log action to log file."""
        logger.info(f"{action}: {json.dumps(data, indent=2)}")


# Convenience function
def get_personal_task_handler() -> PersonalTaskHandler:
    """Get a Personal Task Handler client."""
    return PersonalTaskHandler()


if __name__ == '__main__':
    # Test the skill
    print("=" * 60)
    print("Personal Task Handler - Test Mode")
    print("=" * 60)

    personal = PersonalTaskHandler()

    # Get summary
    summary = personal.get_summary()
    print(f"\nTask Summary: {json.dumps(summary, indent=2)}")

    # List tasks
    tasks = personal.list_tasks()
    print(f"\nTasks: {json.dumps(tasks, indent=2)}")
