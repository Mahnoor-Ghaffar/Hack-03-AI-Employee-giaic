"""
Ralph Wiggum Scheduler Integration

Integrates the Ralph Wiggum Autonomous Loop with the existing AI Employee scheduler.
This module provides hooks for the orchestrator to process tasks autonomously.

Usage:
    from .claude.skills.ralph-wiggum.scheduler_integration import (
        on_task_appears,
        process_with_ralph_loop
    )
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from log_manager import setup_logging
from .ralph_wiggum import (
    RalphWiggumAutonomousLoop,
    TaskStatus,
    analyze_task,
    generate_plan,
    MAX_ITERATIONS,
    VAULT_PATH,
    NEEDS_ACTION_PATH,
    DONE_PATH,
    PLANS_PATH
)

# Setup logging
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="ralph_scheduler")


# =============================================================================
# Event Handlers for Scheduler Integration
# =============================================================================

def on_task_appears(
    task_file: Path,
    auto_process: bool = True,
    max_iterations: int = MAX_ITERATIONS
) -> Dict[str, Any]:
    """
    Called when a new task appears in Needs_Action folder.
    
    This is the main entry point for scheduler integration.
    It triggers the Ralph Wiggum loop to process the task autonomously.
    
    Behavior:
    1. Analyze task
    2. Create Plan.md
    3. Execute first step
    4. Check result
    5. Continue next step
    6. Repeat until completed
    7. Move task to Done
    
    Args:
        task_file: Path to the task file that appeared
        auto_process: Whether to automatically process the task
        max_iterations: Maximum iterations for the loop
    
    Returns:
        Dictionary with task processing results
    """
    logger.info(f"Ralph Wiggum: Task appeared - {task_file.name}")
    
    result = {
        "task_file": str(task_file),
        "timestamp": datetime.now().isoformat(),
        "auto_process": auto_process,
        "status": "pending",
        "details": {}
    }
    
    if not auto_process:
        # Just analyze and create plan, don't execute
        logger.info(f"Analysis mode for {task_file.name}")
        result["status"] = "analyzed"
        result["details"] = _analyze_only(task_file)
    else:
        # Full autonomous processing
        logger.info(f"Autonomous processing for {task_file.name}")
        result["status"] = "processing"
        result["details"] = _process_with_loop(task_file, max_iterations)
    
    return result


def _analyze_only(task_file: Path) -> Dict[str, Any]:
    """
    Analyze task and create plan without executing.
    
    Args:
        task_file: Path to task file
    
    Returns:
        Analysis results
    """
    try:
        content = task_file.read_text(encoding="utf-8")
        analysis = analyze_task(content, task_file)
        plan_content = generate_plan(analysis, content)
        
        # Save plan
        plan_file = PLANS_PATH / f"Plan_{task_file.stem}.md"
        plan_file.write_text(plan_content)
        
        logger.info(f"Plan created: {plan_file.name}")
        
        return {
            "analysis": analysis,
            "plan_path": str(plan_file),
            "complexity": analysis.get("estimated_complexity", "unknown"),
            "risk_level": analysis.get("risk_level", "unknown")
        }
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {
            "error": str(e)
        }


def _process_with_loop(
    task_file: Path,
    max_iterations: int
) -> Dict[str, Any]:
    """
    Process task with full Ralph Wiggum loop.
    
    Args:
        task_file: Path to task file
        max_iterations: Maximum iterations
    
    Returns:
        Processing results
    """
    try:
        loop = RalphWiggumAutonomousLoop(
            max_iterations=max_iterations
        )
        
        status, reason = loop.process_task_file(task_file)
        
        return {
            "status": status.value,
            "reason": reason,
            "iterations": loop.iteration_count,
            "completed_steps": len(loop.completed_steps),
            "plan_path": str(loop.current_plan) if loop.current_plan else None
        }
    
    except Exception as e:
        logger.error(f"Loop processing failed: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }


def process_with_ralph_loop(
    task_file: Path,
    max_iterations: int = MAX_ITERATIONS,
    on_complete: Optional[Callable[[TaskStatus, str], None]] = None
) -> Dict[str, Any]:
    """
    Process a task with Ralph Wiggum loop.
    
    This is a convenience function for direct scheduler integration.
    
    Args:
        task_file: Path to task file
        max_iterations: Maximum iterations
        on_complete: Optional callback when task completes
    
    Returns:
        Processing results
    """
    logger.info(f"Processing task with Ralph loop: {task_file.name}")
    
    loop = RalphWiggumAutonomousLoop(
        max_iterations=max_iterations
    )
    
    status, reason = loop.process_task_file(task_file)
    
    # Call completion callback if provided
    if on_complete:
        on_complete(status, reason)
    
    return {
        "task": str(task_file),
        "status": status.value,
        "reason": reason,
        "iterations": loop.iteration_count,
        "plan": str(loop.current_plan) if loop.current_plan else None
    }


def setup_filesystem_watcher_callback(
    vault_path: Path = VAULT_PATH,
    auto_process: bool = True
) -> Callable[[str], None]:
    """
    Create a callback function for FileSystemWatcher integration.
    
    This callback can be registered with the existing FileSystemWatcher
    to automatically process new tasks with Ralph Wiggum loop.
    
    Args:
        vault_path: Path to AI Employee vault
        auto_process: Whether to auto-process tasks
    
    Returns:
        Callback function for FileSystemWatcher
    """
    def ralph_callback(file_path: str):
        """Callback for FileSystemWatcher."""
        task_file = Path(file_path)
        
        # Only process .md files in Needs_Action
        if task_file.suffix != ".md":
            return
        
        if "Needs_Action" not in str(task_file):
            return
        
        logger.info(f"FileSystemWatcher callback: {task_file.name}")
        
        # Process task
        result = on_task_appears(
            task_file=task_file,
            auto_process=auto_process
        )
        
        logger.info(f"Ralph Wiggum result: {result.get('status')}")
    
    return ralph_callback


def integrate_with_orchestrator():
    """
    Integration function for orchestrator_gold.py
    
    This function provides the hooks needed to integrate
    Ralph Wiggum with the existing Gold Tier orchestrator.
    
    Usage in orchestrator.py:
        from .claude.skills.ralph-wiggum.scheduler_integration import integrate_with_orchestrator
        ralph_hooks = integrate_with_orchestrator()
        # Use ralph_hooks['on_task'] when processing files
    """
    logger.info("Ralph Wiggum: Integrating with orchestrator...")
    
    return {
        "on_task_appears": on_task_appears,
        "process_with_loop": process_with_ralph_loop,
        "setup_watcher_callback": setup_filesystem_watcher_callback,
        "max_iterations": MAX_ITERATIONS
    }


def process_all_needs_action(
    vault_path: Path = VAULT_PATH,
    max_iterations: int = MAX_ITERATIONS
) -> Dict[str, Any]:
    """
    Process all tasks in Needs_Action folder.
    
    This is called by the scheduler to batch-process pending tasks.
    
    Args:
        vault_path: Path to AI Employee vault
        max_iterations: Maximum iterations per task
    
    Returns:
        Summary of processing results
    """
    logger.info("Ralph Wiggum: Processing all pending tasks...")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total": 0,
        "completed": 0,
        "failed": 0,
        "tasks": []
    }
    
    loop = RalphWiggumAutonomousLoop(
        vault_path=vault_path,
        max_iterations=max_iterations
    )
    
    # Process all .md files in Needs_Action
    needs_action_path = vault_path / "Needs_Action"
    
    for task_file in needs_action_path.glob("*.md"):
        # Skip plan files
        if task_file.name.startswith("Plan_"):
            continue
        
        results["total"] += 1
        
        status, reason = loop.process_task_file(task_file)
        
        results["tasks"].append({
            "file": task_file.name,
            "status": status.value,
            "reason": reason
        })
        
        if status == TaskStatus.COMPLETED:
            results["completed"] += 1
        else:
            results["failed"] += 1
    
    logger.info(
        f"Ralph Wiggum batch complete: {results['completed']}/{results['total']} successful"
    )
    
    return results


# =============================================================================
# Scheduled Task Function
# =============================================================================

def scheduled_ralph_processing(
    vault_path: Path = VAULT_PATH,
    max_iterations: int = MAX_ITERATIONS
) -> Dict[str, Any]:
    """
    Scheduled task function for cron/Task Scheduler integration.
    
    This can be called periodically (e.g., every 5 minutes) to process
    any pending tasks in the Needs_Action folder.
    
    Args:
        vault_path: Path to AI Employee vault
        max_iterations: Maximum iterations
    
    Returns:
        Processing summary
    """
    logger.info("Ralph Wiggum: Scheduled processing run...")
    
    return process_all_needs_action(
        vault_path=vault_path,
        max_iterations=max_iterations
    )


if __name__ == "__main__":
    # Test integration
    print("Ralph Wiggum Scheduler Integration")
    print("=" * 50)
    
    # Test with sample task
    test_task = NEEDS_ACTION_PATH / "test_ralph_task.md"
    
    if test_task.exists():
        print(f"Processing test task: {test_task.name}")
        result = on_task_appears(test_task, auto_process=True)
        print(f"Result: {result}")
    else:
        print(f"Test task not found: {test_task}")
        print(f"Needs_Action path: {NEEDS_ACTION_PATH.absolute()}")
    
    print("\nIntegration hooks available:")
    hooks = integrate_with_orchestrator()
    for hook_name in hooks:
        print(f"  - {hook_name}")
