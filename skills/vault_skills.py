"""
Vault Skills for AI Employee

These skills enable Claude Code to interact with the Obsidian vault:
- Read task files from Needs_Action
- Write responses and updates
- Move files between folders (Inbox → Needs_Action → Done)
- Update the Dashboard
"""

import shutil
from pathlib import Path
from datetime import datetime


class VaultSkills:
    """Collection of skills for vault operations."""
    
    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / "Inbox"
        self.needs_action = self.vault_path / "Needs_Action"
        self.done = self.vault_path / "Done"
        self.dashboard = self.vault_path / "Dashboard.md"
        
        # Ensure folders exist
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.done.mkdir(parents=True, exist_ok=True)
    
    def read_task(self, file_name: str) -> dict:
        """
        Read a task file from Needs_Action folder.
        
        Args:
            file_name: Name of the file (e.g., 'task_001.md')
            
        Returns:
            Dictionary with task content and metadata
        """
        file_path = self.needs_action / file_name
        
        if not file_path.exists():
            return {"error": f"Task file not found: {file_name}"}
        
        content = file_path.read_text()
        
        # Parse frontmatter (YAML between ---)
        metadata = {}
        body = content
        
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                body = parts[2].strip()
                
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()
        
        return {
            "file_name": file_name,
            "metadata": metadata,
            "body": body,
            "full_content": content
        }
    
    def write_response(self, file_name: str, response: str, action_items: list = None) -> str:
        """
        Write a response to a task file.
        
        Args:
            file_name: Name of the task file
            response: The AI's response/content
            action_items: List of action items (checkboxes)
            
        Returns:
            Path to the response file
        """
        file_path = self.needs_action / file_name
        
        if not file_path.exists():
            return f"Error: Task file not found: {file_name}"
        
        # Read original content
        original = file_path.read_text()
        
        # Append response
        response_section = f"""

---
## AI Response
**Generated:** {datetime.now().isoformat()}

{response}

"""
        
        if action_items:
            response_section += "### Action Items\n"
            for item in action_items:
                response_section += f"- [ ] {item}\n"
        
        file_path.write_text(original + response_section)
        return f"Response written to {file_name}"
    
    def move_to_done(self, file_name: str, summary: str = None) -> str:
        """
        Move a completed task to the Done folder.
        
        Args:
            file_name: Name of the file to move
            summary: Optional completion summary
            
        Returns:
            Status message
        """
        source = self.needs_action / file_name
        dest = self.done / file_name
        
        if not source.exists():
            return f"Error: File not found in Needs_Action: {file_name}"
        
        # Add completion metadata if summary provided
        if summary:
            content = source.read_text()
            content += f"""

---
## Completed
**Completed:** {datetime.now().isoformat()}
**Summary:** {summary}
"""
            source.write_text(content)
        
        # Move file
        shutil.move(str(source), str(dest))
        return f"Moved {file_name} to Done folder"
    
    def move_to_needs_action(self, file_name: str) -> str:
        """
        Move a file from Inbox to Needs_Action.
        
        Args:
            file_name: Name of the file to move
            
        Returns:
            Status message
        """
        source = self.inbox / file_name
        dest = self.needs_action / file_name
        
        if not source.exists():
            return f"Error: File not found in Inbox: {file_name}"
        
        shutil.move(str(source), str(dest))
        return f"Moved {file_name} to Needs_Action folder"
    
    def update_dashboard(self, section: str, content: str) -> str:
        """
        Update a section of the Dashboard.md file.
        
        Args:
            section: Section name to update
            content: New content for the section
            
        Returns:
            Status message
        """
        if not self.dashboard.exists():
            self.dashboard.write_text("# Dashboard\n\n")
        
        current = self.dashboard.read_text()
        
        # Check if section exists
        section_header = f"## {section}"
        
        if section_header in current:
            # Replace existing section (simplified - replaces until next ## or end)
            lines = current.split("\n")
            new_lines = []
            in_section = False
            
            for line in lines:
                if line.startswith("## ") and section in line:
                    in_section = True
                    new_lines.append(section_header)
                    new_lines.append(content)
                elif in_section and line.startswith("## "):
                    in_section = False
                    new_lines.append(line)
                elif not in_section:
                    new_lines.append(line)
            
            self.dashboard.write_text("\n".join(new_lines))
        else:
            # Add new section
            self.dashboard.write_text(current + f"\n{section_header}\n\n{content}\n")
        
        return f"Dashboard updated: {section}"
    
    def list_pending_tasks(self) -> list:
        """
        List all pending tasks in Needs_Action folder.
        
        Returns:
            List of task file names
        """
        if not self.needs_action.exists():
            return []
        
        return [f.name for f in self.needs_action.iterdir() if f.suffix == ".md"]
    
    def get_task_summary(self) -> str:
        """
        Get a summary of all pending tasks.
        
        Returns:
            Formatted summary string
        """
        tasks = self.list_pending_tasks()
        
        if not tasks:
            return "No pending tasks."
        
        summary = f"**Pending Tasks:** {len(tasks)}\n\n"
        for task in tasks:
            task_data = self.read_task(task)
            task_type = task_data["metadata"].get("type", "unknown")
            priority = task_data["metadata"].get("priority", "normal")
            summary += f"- **{task}** (Type: {task_type}, Priority: {priority})\n"
        
        return summary


# Convenience functions for direct import
_vault = None

def get_vault():
    """Get singleton vault instance."""
    global _vault
    if _vault is None:
        _vault = VaultSkills()
    return _vault

def read_task(file_name: str) -> dict:
    """Read a task from Needs_Action."""
    return get_vault().read_task(file_name)

def write_response(file_name: str, response: str, action_items: list = None) -> str:
    """Write a response to a task."""
    return get_vault().write_response(file_name, response, action_items)

def move_to_done(file_name: str, summary: str = None) -> str:
    """Move a task to Done folder."""
    return get_vault().move_to_done(file_name, summary)

def move_to_needs_action(file_name: str) -> str:
    """Move a file from Inbox to Needs_Action."""
    return get_vault().move_to_needs_action(file_name)

def update_dashboard(section: str, content: str) -> str:
    """Update dashboard section."""
    return get_vault().update_dashboard(section, content)

def list_pending_tasks() -> list:
    """List all pending tasks."""
    return get_vault().list_pending_tasks()

def get_task_summary() -> str:
    """Get summary of pending tasks."""
    return get_vault().get_task_summary()
