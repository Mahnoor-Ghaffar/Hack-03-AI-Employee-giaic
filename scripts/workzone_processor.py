#!/usr/bin/env python3
# =============================================================================
# Work-Zone Processor
# =============================================================================
# Implements Cloud vs Local work-zone architecture with:
# - Claim-by-move rule
# - Single-writer rule for Dashboard.md
# - File ownership tracking
# =============================================================================

import os
import json
import shutil
import hashlib
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


# =============================================================================
# Configuration
# =============================================================================

class Zone(Enum):
    CLOUD = "cloud"
    LOCAL = "local"


# Work-zone folder structure
VAULT_ROOT = Path(__file__).parent.parent / "AI_Employee_Vault"

ZONES = {
    Zone.CLOUD: VAULT_ROOT / "In_Progress" / "cloud",
    Zone.LOCAL: VAULT_ROOT / "In_Progress" / "local",
}

NEEDS_ACTION = VAULT_ROOT / "Needs_Action"
PENDING_APPROVAL = VAULT_ROOT / "Pending_Approval"
APPROVED = VAULT_ROOT / "Approved"
DONE = VAULT_ROOT / "Done"
REJECTED = VAULT_ROOT / "Rejected"

# Ownership tracking file
OWNERSHIP_FILE = VAULT_ROOT / ".workzone_ownership.json"
DASHBOARD_LOCK = VAULT_ROOT / ".dashboard.lock"

# Cloud responsibilities
CLOUD_TASKS = ["email", "social"]

# Local responsibilities (final actions)
LOCAL_TASKS = ["send_email", "post_social", "whatsapp", "payments", "approvals"]


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class FileOwnership:
    """Tracks file ownership and zone assignment"""
    file_path: str
    owner: Zone
    claimed_at: str
    task_type: str
    status: str = "in_progress"
    original_path: str = ""


@dataclass
class DashboardLock:
    """Lock for Dashboard.md single-writer rule"""
    locked_by: Zone
    locked_at: str
    expires_at: str


# =============================================================================
# Ownership Manager
# =============================================================================

class OwnershipManager:
    """Manages file ownership and claim-by-move rule"""
    
    def __init__(self):
        self.ownership_file = OWNERSHIP_FILE
        self.ownership_data = self._load_ownership()
    
    def _load_ownership(self) -> Dict:
        """Load ownership tracking data"""
        if self.ownership_file.exists():
            with open(self.ownership_file, 'r') as f:
                return json.load(f)
        return {"files": {}, "history": []}
    
    def _save_ownership(self):
        """Save ownership tracking data"""
        with open(self.ownership_file, 'w') as f:
            json.dump(self.ownership_data, f, indent=2)
    
    def claim_file(self, file_path: Path, zone: Zone, task_type: str) -> Optional[FileOwnership]:
        """
        Claim a file by moving it to a zone.
        Implements claim-by-move rule: moving a file claims ownership.
        """
        file_key = str(file_path)
        
        # Check if already claimed
        if file_key in self.ownership_data["files"]:
            existing = self.ownership_data["files"][file_key]
            if existing["status"] == "in_progress":
                return None  # Already claimed by someone
        
        # Create ownership record
        ownership = FileOwnership(
            file_path=file_key,
            owner=zone,
            claimed_at=datetime.now().isoformat(),
            task_type=task_type,
            original_path=str(file_path)
        )
        
        # Record ownership
        self.ownership_data["files"][file_key] = asdict(ownership)
        self.ownership_data["history"].append({
            "action": "claim",
            "file": file_key,
            "zone": zone.value,
            "timestamp": datetime.now().isoformat()
        })
        
        self._save_ownership()
        return ownership
    
    def release_file(self, file_path: Path, zone: Zone, new_status: str = "completed"):
        """Release file ownership after completion"""
        file_key = str(file_path)
        
        if file_key in self.ownership_data["files"]:
            self.ownership_data["files"][file_key]["status"] = new_status
            self.ownership_data["history"].append({
                "action": "release",
                "file": file_key,
                "zone": zone.value,
                "status": new_status,
                "timestamp": datetime.now().isoformat()
            })
            self._save_ownership()
    
    def get_owner(self, file_path: Path) -> Optional[Zone]:
        """Get current owner of a file"""
        file_key = str(file_path)
        if file_key in self.ownership_data["files"]:
            owner = self.ownership_data["files"][file_key]["owner"]
            return Zone(owner)
        return None
    
    def get_zone_files(self, zone: Zone) -> List[FileOwnership]:
        """Get all files owned by a zone"""
        files = []
        for file_data in self.ownership_data["files"].values():
            if file_data["owner"] == zone.value and file_data["status"] == "in_progress":
                files.append(FileOwnership(**file_data))
        return files


# =============================================================================
# Dashboard Lock Manager
# =============================================================================

class DashboardLockManager:
    """
    Implements single-writer rule for Dashboard.md
    Only one zone can write to Dashboard.md at a time
    """
    
    def __init__(self):
        self.lock_file = DASHBOARD_LOCK
        self.timeout = 300  # 5 minutes lock timeout
    
    def acquire_lock(self, zone: Zone) -> bool:
        """
        Acquire write lock for Dashboard.md
        Returns True if lock acquired, False otherwise
        """
        now = datetime.now()
        
        try:
            # Try to acquire lock
            if self.lock_file.exists():
                with open(self.lock_file, 'r') as f:
                    try:
                        lock_data = json.load(f)
                        expires = datetime.fromisoformat(lock_data["expires_at"])
                        
                        # Check if lock is expired
                        if now < expires and lock_data["locked_by"] != zone.value:
                            return False  # Lock held by other zone
                    except (json.JSONDecodeError, KeyError):
                        pass  # Corrupted lock, will overwrite
            
            # Acquire lock
            lock = DashboardLock(
                locked_by=zone.value,
                locked_at=now.isoformat(),
                expires_at=(now.timestamp() + self.timeout)
            )
            
            with open(self.lock_file, 'w') as f:
                json.dump(asdict(lock), f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error acquiring dashboard lock: {e}")
            return False
    
    def release_lock(self, zone: Zone):
        """Release write lock for Dashboard.md"""
        try:
            if self.lock_file.exists():
                with open(self.lock_file, 'r') as f:
                    lock_data = json.load(f)
                    if lock_data.get("locked_by") == zone.value:
                        self.lock_file.unlink()
        except Exception as e:
            print(f"Error releasing dashboard lock: {e}")
    
    def write_dashboard(self, zone: Zone, content: str) -> bool:
        """
        Write to Dashboard.md with single-writer guarantee
        """
        dashboard_path = VAULT_ROOT / "Dashboard.md"
        
        if not self.acquire_lock(zone):
            print(f"[{zone.value}] Cannot write Dashboard.md - locked by other zone")
            return False
        
        try:
            with open(dashboard_path, 'w') as f:
                f.write(content)
            return True
        finally:
            self.release_lock(zone)


# =============================================================================
# Work-Zone Processor
# =============================================================================

class WorkZoneProcessor:
    """
    Main processor for Cloud vs Local work-zone architecture
    """
    
    def __init__(self):
        self.ownership_mgr = OwnershipManager()
        self.dashboard_lock_mgr = DashboardLockManager()
    
    def get_task_zone(self, task_type: str) -> Zone:
        """Determine which zone handles a task type"""
        if task_type in CLOUD_TASKS:
            return Zone.CLOUD
        elif task_type in LOCAL_TASKS:
            return Zone.LOCAL
        else:
            # Default based on folder location
            return Zone.CLOUD
    
    def process_needs_action(self, task_type: str) -> List[Path]:
        """
        Process files in Needs_Action folder.
        Cloud claims email/social tasks and moves to In_Progress/cloud.
        """
        zone = self.get_task_zone(task_type)
        source_folder = NEEDS_ACTION / task_type
        dest_folder = ZONES[zone]
        
        if not source_folder.exists():
            return []
        
        claimed_files = []
        
        for file_path in source_folder.iterdir():
            if file_path.is_file():
                # Try to claim the file
                ownership = self.ownership_mgr.claim_file(file_path, zone, task_type)
                
                if ownership:
                    # Move file to zone folder (claim-by-move)
                    dest_path = dest_folder / file_path.name
                    shutil.move(str(file_path), str(dest_path))
                    claimed_files.append(dest_path)
                    
                    print(f"[{zone.value}] Claimed: {file_path.name} -> {dest_folder.name}")
        
        return claimed_files
    
    def move_to_pending_approval(self, file_path: Path, task_type: str, zone: Zone):
        """
        Move completed work to Pending_Approval for human review.
        Cloud writes approval files only.
        """
        dest_folder = PENDING_APPROVAL / task_type
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        dest_path = dest_folder / file_path.name
        shutil.move(str(file_path), str(dest_path))
        
        # Create approval marker file
        approval_file = dest_folder / f"{file_path.stem}.approval.json"
        with open(approval_file, 'w') as f:
            json.dump({
                "file": file_path.name,
                "zone": zone.value,
                "status": "pending_approval",
                "created_at": datetime.now().isoformat()
            }, f, indent=2)
        
        self.ownership_mgr.release_file(file_path, zone, "pending_approval")
        print(f"[{zone.value}] Moved to approval: {file_path.name}")
    
    def process_approval(self, file_name: str, approved: bool):
        """
        Process approval decision (Local responsibility).
        Moves file to Approved or Rejected.
        """
        # Find file in Pending_Approval
        for task_type in CLOUD_TASKS:
            pending_folder = PENDING_APPROVAL / task_type
            file_path = pending_folder / file_name
            
            if file_path.exists():
                if approved:
                    dest = APPROVED / file_name
                    status = "approved"
                else:
                    dest = REJECTED / file_name
                    status = "rejected"
                
                shutil.move(str(file_path), str(dest))
                
                # Remove approval marker
                approval_marker = pending_folder / f"{file_name}.approval.json"
                if approval_marker.exists():
                    approval_marker.unlink()
                
                print(f"[local] {status.capitalize()}: {file_name}")
                return
        
        print(f"[local] File not found: {file_name}")
    
    def execute_final_action(self, file_name: str, action_type: str):
        """
        Execute final send/post action (Local responsibility only).
        This is where actual sending/posting happens.
        """
        # Find approved file
        file_path = APPROVED / file_name
        
        if not file_path.exists():
            print(f"[local] File not found in Approved: {file_name}")
            return False
        
        # Local-only actions
        if action_type == "send_email":
            return self._send_email(file_path)
        elif action_type == "post_social":
            return self._post_social(file_path)
        elif action_type == "whatsapp":
            return self._send_whatsapp(file_path)
        elif action_type == "payments":
            return self._process_payment(file_path)
        else:
            print(f"[local] Unknown action type: {action_type}")
            return False
    
    def _send_email(self, file_path: Path) -> bool:
        """Send email (Local only - has SMTP credentials)"""
        print(f"[local] Sending email: {file_path.name}")
        # Actual email sending logic here
        # Move to Done after sending
        dest = DONE / file_path.name
        shutil.move(str(file_path), str(dest))
        return True
    
    def _post_social(self, file_path: Path) -> bool:
        """Post to social media (Local only - has API tokens)"""
        print(f"[local] Posting to social: {file_path.name}")
        # Actual social posting logic here
        dest = DONE / file_path.name
        shutil.move(str(file_path), str(dest))
        return True
    
    def _send_whatsapp(self, file_path: Path) -> bool:
        """Send WhatsApp message (Local only - has session)"""
        print(f"[local] Sending WhatsApp: {file_path.name}")
        dest = DONE / file_path.name
        shutil.move(str(file_path), str(dest))
        return True
    
    def _process_payment(self, file_path: Path) -> bool:
        """Process payment (Local only - has payment credentials)"""
        print(f"[local] Processing payment: {file_path.name}")
        dest = DONE / file_path.name
        shutil.move(str(file_path), str(dest))
        return True
    
    def update_dashboard(self, zone: Zone, updates: Dict) -> bool:
        """
        Update Dashboard.md with single-writer guarantee.
        """
        dashboard_path = VAULT_ROOT / "Dashboard.md"
        
        # Read current content
        current_content = ""
        if dashboard_path.exists():
            with open(dashboard_path, 'r') as f:
                current_content = f.read()
        
        # Apply updates (zone-specific sections)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if zone == Zone.CLOUD:
            # Cloud updates draft counts
            update_section = f"""
## Cloud Work Zone (Updated: {timestamp})
- Email drafts pending: {updates.get('email_drafts', 0)}
- Social drafts pending: {updates.get('social_drafts', 0)}
"""
        else:
            # Local updates approval counts
            update_section = f"""
## Local Work Zone (Updated: {timestamp})
- Pending approvals: {updates.get('pending_approvals', 0)}
- Actions completed today: {updates.get('actions_completed', 0)}
"""
        
        # Write with lock
        new_content = current_content + "\n" + update_section
        return self.dashboard_lock_mgr.write_dashboard(zone, new_content)
    
    def get_status(self) -> Dict:
        """Get current work-zone status"""
        return {
            "cloud": {
                "in_progress": len(list(ZONES[Zone.CLOUD].iterdir())) if ZONES[Zone.CLOUD].exists() else 0,
                "files": [f.name for f in ZONES[Zone.CLOUD].iterdir()] if ZONES[Zone.CLOUD].exists() else []
            },
            "local": {
                "in_progress": len(list(ZONES[Zone.LOCAL].iterdir())) if ZONES[Zone.LOCAL].exists() else 0,
                "files": [f.name for f in ZONES[Zone.LOCAL].iterdir()] if ZONES[Zone.LOCAL].exists() else []
            },
            "pending_approval": {
                "email": len(list((PENDING_APPROVAL / "email").iterdir())) if (PENDING_APPROVAL / "email").exists() else 0,
                "social": len(list((PENDING_APPROVAL / "social").iterdir())) if (PENDING_APPROVAL / "social").exists() else 0
            },
            "approved": len(list(APPROVED.iterdir())) if APPROVED.exists() else 0,
            "done": len(list(DONE.iterdir())) if DONE.exists() else 0
        }


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    import sys
    
    processor = WorkZoneProcessor()
    
    if len(sys.argv) < 2:
        print("Work-Zone Processor")
        print("")
        print("Usage: python workzone_processor.py <command> [args]")
        print("")
        print("Commands:")
        print("  process <task_type>     - Process Needs_Action files (email/social)")
        print("  approve <file> [yes/no] - Approve/reject pending file")
        print("  execute <file> <action> - Execute final action (send_email/post_social)")
        print("  status                  - Show work-zone status")
        print("  dashboard <zone>        - Update dashboard (cloud/local)")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "process":
        task_type = sys.argv[2] if len(sys.argv) > 2 else "email"
        processor.process_needs_action(task_type)
    
    elif command == "approve":
        if len(sys.argv) < 4:
            print("Usage: approve <file> <yes|no>")
            sys.exit(1)
        file_name = sys.argv[2]
        approved = sys.argv[3].lower() == "yes"
        processor.process_approval(file_name, approved)
    
    elif command == "execute":
        if len(sys.argv) < 4:
            print("Usage: execute <file> <action>")
            sys.exit(1)
        file_name = sys.argv[2]
        action = sys.argv[3]
        processor.execute_final_action(file_name, action)
    
    elif command == "status":
        status = processor.get_status()
        print(json.dumps(status, indent=2))
    
    elif command == "dashboard":
        if len(sys.argv) < 3:
            print("Usage: dashboard <cloud|local>")
            sys.exit(1)
        zone = Zone(sys.argv[2])
        processor.update_dashboard(zone, {})
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
