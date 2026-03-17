"""
Test Suite for Human Approval Agent Skill - Silver Tier

This module tests the human-approval skill implementation.

Run: python test_human_approval.py
"""

import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.request_approval import (
    request_approval,
    check_approval_status,
    ApprovalStatus,
    NEEDS_APPROVAL_PATH,
    APPROVED_PATH,
    REJECTED_PATH,
    ACTION_LOG_PATH,
    rename_and_move_file,
    log_approval_action
)


def setup_test_environment():
    """Ensure test directories exist."""
    for path in [NEEDS_APPROVAL_PATH, APPROVED_PATH, REJECTED_PATH, ACTION_LOG_PATH.parent]:
        path.mkdir(parents=True, exist_ok=True)


def cleanup_test_file(filename: str):
    """Remove test file from all folders."""
    import time
    # Small delay to ensure file handles are released
    time.sleep(0.1)
    
    for folder in [NEEDS_APPROVAL_PATH, APPROVED_PATH, REJECTED_PATH]:
        test_file = folder / filename
        if test_file.exists():
            try:
                test_file.unlink()
            except PermissionError:
                # File might be locked, try again with force
                import subprocess
                subprocess.run(['del', '/F', '/Q', str(test_file)], shell=True, capture_output=True)
        # Also check for renamed versions
        for f in folder.glob(f"{filename}*"):
            try:
                f.unlink()
            except PermissionError:
                import subprocess
                subprocess.run(['del', '/F', '/Q', str(f)], shell=True, capture_output=True)


def create_test_approval_file(filename: str, status: str = "pending", content: str = "") -> Path:
    """Create a test approval file."""
    file_path = NEEDS_APPROVAL_PATH / filename
    
    default_content = f"""---
type: test_approval
approval_id: TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}
status: {status}
created: {datetime.now().isoformat()}
---

## Test Approval Request

This is a test approval file for testing the human-approval skill.

## Instructions

To approve: Change status to APPROVED
To reject: Change status to REJECTED
"""
    
    if content:
        file_path.write_text(content)
    else:
        file_path.write_text(default_content)
    
    return file_path


def test_approval_status_detection():
    """Test detection of approval status from file content."""
    print("\n[TEST 1] Testing approval status detection...")
    
    # Test PENDING status
    pending_file = create_test_approval_file("test_pending.md", status="pending")
    status, reason = check_approval_status(pending_file)
    assert status == ApprovalStatus.PENDING, f"Expected PENDING, got {status}"
    print("  [OK] PENDING status detected correctly")
    cleanup_test_file("test_pending.md")
    
    # Test APPROVED status
    approved_content = """---
type: test
status: APPROVED
---
Test content
"""
    approved_file = create_test_approval_file("test_approved.md", content=approved_content)
    status, reason = check_approval_status(approved_file)
    assert status == ApprovalStatus.APPROVED, f"Expected APPROVED, got {status}"
    print("  [OK] APPROVED status detected correctly")
    cleanup_test_file("test_approved.md")
    
    # Test REJECTED status
    rejected_content = """---
type: test
status: REJECTED
rejection_reason: Not approved
---
Test content
"""
    rejected_file = create_test_approval_file("test_rejected.md", content=rejected_content)
    status, reason = check_approval_status(rejected_file)
    assert status == ApprovalStatus.REJECTED, f"Expected REJECTED, got {status}"
    assert "Not approved" in reason, f"Expected rejection reason, got {reason}"
    print("  [OK] REJECTED status detected correctly with reason")
    cleanup_test_file("test_rejected.md")
    
    # Test case-insensitive detection
    case_content = """---
type: test
status: approved
---
Test content
"""
    case_file = create_test_approval_file("test_case.md", content=case_content)
    status, reason = check_approval_status(case_file)
    assert status == ApprovalStatus.APPROVED, f"Expected APPROVED (case-insensitive), got {status}"
    print("  [OK] Case-insensitive status detection works")
    cleanup_test_file("test_case.md")
    
    print("[TEST 1] PASSED: All status detection tests passed\n")


def test_file_renaming():
    """Test file renaming and movement based on status."""
    print("[TEST 2] Testing file renaming and movement...")
    
    # Test approved file renaming
    approved_file = create_test_approval_file("test_rename_approve.md", status="pending")
    result = rename_and_move_file(approved_file, ApprovalStatus.APPROVED)
    assert result == True, "File rename/move should succeed"
    
    # Check file was moved to Approved folder
    moved_files = list(APPROVED_PATH.glob("test_rename_approve.approved*.md"))
    assert len(moved_files) > 0, "File should be in Approved folder"
    print("  [OK] Approved file renamed and moved correctly")
    
    # Test rejected file renaming
    rejected_file = create_test_approval_file("test_rename_reject.md", status="pending")
    result = rename_and_move_file(rejected_file, ApprovalStatus.REJECTED)
    assert result == True, "File rename/move should succeed"
    
    # Check file was moved to Rejected folder
    moved_files = list(REJECTED_PATH.glob("test_rename_reject.rejected*.md"))
    assert len(moved_files) > 0, "File should be in Rejected folder"
    print("  [OK] Rejected file renamed and moved correctly")
    
    print("[TEST 2] PASSED: All file renaming tests passed\n")


def test_timeout_handling():
    """Test timeout handling with short timeout."""
    print("[TEST 3] Testing timeout handling (short timeout: 5 seconds)...")
    
    test_file = create_test_approval_file("test_timeout.md", status="pending")
    
    start_time = time.time()
    
    # Request approval with 5 second timeout (non-blocking test with thread)
    def approval_thread():
        status, reason = request_approval(
            file_path=str(test_file),
            timeout_seconds=5,
            poll_interval=1
        )
        return status, reason
    
    thread = threading.Thread(target=approval_thread)
    thread.start()
    thread.join(timeout=10)  # Wait max 10 seconds
    
    elapsed = time.time() - start_time
    
    # Check that timeout occurred around 5 seconds
    assert elapsed >= 4.5, f"Timeout should be at least 4.5 seconds, got {elapsed}"
    assert elapsed <= 8, f"Timeout should be at most 8 seconds, got {elapsed}"
    
    # Check file was moved to Rejected with .timeout suffix
    timeout_files = list(REJECTED_PATH.glob("test_timeout.timeout*.md"))
    assert len(timeout_files) > 0, "File should be in Rejected folder with .timeout suffix"
    print(f"  [OK] Timeout occurred after {elapsed:.1f} seconds")
    print("  [OK] Timeout file renamed and moved correctly")
    
    print("[TEST 3] PASSED: Timeout handling works correctly\n")


def test_logging():
    """Test that actions are logged to actions.log."""
    print("[TEST 4] Testing logging to actions.log...")
    
    # Clear existing log content for clean test
    if ACTION_LOG_PATH.exists():
        ACTION_LOG_PATH.unlink()
    
    # Log a test action
    log_approval_action("TEST: This is a test log entry")
    
    # Check log file exists and contains our entry
    assert ACTION_LOG_PATH.exists(), "actions.log should exist"
    
    content = ACTION_LOG_PATH.read_text()
    assert "TEST: This is a test log entry" in content, "Log should contain test entry"
    assert "[human-approval]" in content, "Log should contain human-approval tag"
    print("  [OK] Log file created and contains entries")
    print("  [OK] Log entries include human-approval tag")
    
    print("[TEST 4] PASSED: Logging works correctly\n")


def test_file_not_found():
    """Test handling of non-existent file."""
    print("[TEST 5] Testing file not found handling...")
    
    status, reason = request_approval(
        file_path="AI_Employee_Vault/Needs_Approval/nonexistent_file.md",
        timeout_seconds=1,
        poll_interval=1
    )
    
    assert status == ApprovalStatus.REJECTED, f"Expected REJECTED for missing file, got {status}"
    assert "not found" in reason.lower(), f"Reason should mention file not found, got {reason}"
    print("  [OK] Non-existent file handled correctly")
    
    print("[TEST 5] PASSED: File not found handling works correctly\n")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Testing Human Approval Agent Skill")
    print("=" * 60)
    
    setup_test_environment()
    
    try:
        test_approval_status_detection()
        test_file_renaming()
        test_timeout_handling()
        test_logging()
        test_file_not_found()
        
        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("")
        print("Silver Tier Compliance: Human-in-the-loop approval workflow")
        print("[OK] Status detection (APPROVED/REJECTED/PENDING)")
        print("[OK] File renaming (.approved, .rejected, .timeout)")
        print("[OK] Timeout handling")
        print("[OK] Logging to actions.log")
        print("[OK] Error handling (file not found)")
        
        return True
        
    except AssertionError as e:
        print("=" * 60)
        print(f"TEST FAILED: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print("=" * 60)
        print(f"TEST ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
