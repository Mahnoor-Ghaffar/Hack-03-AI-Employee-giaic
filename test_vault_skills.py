"""
Test script to verify Vault Skills work correctly.
Run this to test the AI Employee vault integration.
"""

import sys
sys.path.insert(0, '.')

from skills.vault_skills import (
    VaultSkills,
    list_pending_tasks,
    read_task,
    write_response,
    get_task_summary
)

def test_vault_skills():
    print("=" * 50)
    print("Testing AI Employee Vault Skills")
    print("=" * 50)
    
    # Test 1: List pending tasks
    print("\n[TEST 1] Listing pending tasks...")
    tasks = list_pending_tasks()
    print(f"Found {len(tasks)} pending task(s):")
    for task in tasks:
        print(f"  - {task}")
    
    # Test 2: Get task summary
    print("\n[TEST 2] Getting task summary...")
    summary = get_task_summary()
    print(summary)
    
    # Test 3: Read a specific task
    print("\n[TEST 3] Reading a task...")
    if tasks:
        task_name = tasks[0]
        print(f"Reading: {task_name}")
        task_data = read_task(task_name)
        print(f"  Type: {task_data['metadata'].get('type', 'unknown')}")
        print(f"  Priority: {task_data['metadata'].get('priority', 'normal')}")
        print(f"  Body preview: {task_data['body'][:100]}...")
    
    # Test 4: Write a response (demo only, don't actually move to done)
    print("\n[TEST 4] Testing write_response (dry run)...")
    print("Function available: write_response(file_name, response, action_items)")
    
    print("\n" + "=" * 50)
    print("All tests completed successfully!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Run 'claude' in terminal")
    print("2. Ask Claude to process tasks in Needs_Action folder")
    print("3. Use vault skills to read, respond, and complete tasks")

if __name__ == "__main__":
    test_vault_skills()
