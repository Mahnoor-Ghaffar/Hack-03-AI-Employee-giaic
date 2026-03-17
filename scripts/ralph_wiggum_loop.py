"""
Ralph Wiggum Persistence Loop - Gold Tier

Implements the "Ralph Wiggum" pattern for autonomous multi-step task completion.
This stop hook intercepts Claude's exit and re-injects prompts until tasks are complete.

Pattern:
1. Orchestrator creates state file with prompt
2. Claude works on task
3. Claude tries to exit
4. Stop hook checks: Is task file in /Done?
5. YES → Allow exit (complete)
6. NO → Block exit, re-inject prompt, show previous output (loop continues)
7. Repeat until complete or max iterations

Usage:
    python scripts/ralph_wiggum_loop.py --prompt "Process all files in Needs_Action" --max-iterations 10
"""

import sys
import os
import time
import argparse
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from enum import Enum

from log_manager import setup_logging

# Setup logging
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="ralph_wiggum")


class TaskStatus(Enum):
    """Task completion status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class RalphWiggumLoop:
    """
    Ralph Wiggum Persistence Loop Manager.
    
    Keeps Claude Code working on tasks until completion or max iterations.
    """
    
    def __init__(
        self,
        vault_path: str = "AI_Employee_Vault",
        max_iterations: int = 10,
        max_duration_minutes: int = 60,
        check_interval_seconds: int = 5
    ):
        """
        Initialize Ralph Wiggum Loop.
        
        Args:
            vault_path: Path to AI Employee vault
            max_iterations: Maximum number of iterations before giving up
            max_duration_minutes: Maximum duration to run (minutes)
            check_interval_seconds: Interval between completion checks
        """
        self.vault_path = Path(vault_path)
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.done_path = self.vault_path / "Done"
        self.in_progress_path = self.vault_path / "In_Progress"
        self.ralph_state_path = self.vault_path / "Ralph_State"
        
        # Ensure directories exist
        for path in [self.needs_action_path, self.done_path, self.in_progress_path, self.ralph_state_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        self.max_iterations = max_iterations
        self.max_duration = timedelta(minutes=max_duration_minutes)
        self.check_interval = check_interval_seconds
        
        self.start_time = datetime.now()
        self.current_iteration = 0
        self.current_task_id = None
        
        logger.info(f"RalphWiggumLoop initialized: max_iterations={max_iterations}, max_duration={max_duration_minutes}min")
    
    def create_task(
        self,
        prompt: str,
        task_id: str = None,
        priority: str = "normal"
    ) -> Path:
        """
        Create a new task for Ralph loop to process.
        
        Args:
            prompt: Task prompt/description
            task_id: Optional task ID (auto-generated if not provided)
            priority: Task priority (low, normal, high)
            
        Returns:
            Path to created task file
        """
        if not task_id:
            task_id = f"TASK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task_file = self.ralph_state_path / f"{task_id}.md"
        
        content = f"""---
type: ralph_task
task_id: {task_id}
priority: {priority}
status: pending
created: {datetime.now().isoformat()}
max_iterations: {self.max_iterations}
max_duration_minutes: {self.max_duration.total_seconds() // 60}
---

# Ralph Wiggum Task

## Task Prompt
{prompt}

## Execution Log
"""
        
        task_file.write_text(content)
        self.current_task_id = task_id
        
        logger.info(f"Created Ralph task: {task_id}")
        return task_file
    
    def check_task_completion(self, task_id: str) -> Tuple[TaskStatus, str]:
        """
        Check if task is complete by looking for completion indicators.
        
        Completion strategies:
        1. File moved to /Done folder
        2. Specific promise string in output
        3. Task state file marked complete
        
        Args:
            task_id: Task ID to check
            
        Returns:
            Tuple of (TaskStatus, reason/message)
        """
        # Strategy 1: Check if task file moved to Done
        done_file = self.done_path / f"{task_id}.md"
        if done_file.exists():
            return (TaskStatus.COMPLETED, f"Task file moved to Done folder")
        
        # Strategy 2: Check state file for completion markers
        state_file = self.ralph_state_path / f"{task_id}.md"
        if state_file.exists():
            content = state_file.read_text()
            
            # Check for completion promise
            if "TASK_COMPLETE" in content or "task_completed" in content.lower():
                return (TaskStatus.COMPLETED, "Completion promise detected")
            
            # Check for failure markers
            if "TASK_FAILED" in content or "task_failed" in content.lower():
                return (TaskStatus.FAILED, "Failure marker detected")
            
            # Check status in frontmatter
            if "status: completed" in content.lower():
                return (TaskStatus.COMPLETED, "Status marked as completed")
            elif "status: failed" in content.lower():
                return (TaskStatus.FAILED, "Status marked as failed")
        
        # Strategy 3: Check if any related files in Done
        for done_file in self.done_path.glob(f"*{task_id}*.md"):
            return (TaskStatus.COMPLETED, f"Related file in Done: {done_file.name}")
        
        # Default: still pending
        return (TaskStatus.IN_PROGRESS, "Task still in progress")
    
    def run_claude_iteration(
        self,
        prompt: str,
        task_id: str,
        previous_output: str = None,
        model: str = "opus"
    ) -> Tuple[bool, str]:
        """
        Run a single Claude Code iteration.
        
        Args:
            prompt: Prompt to send to Claude
            task_id: Task ID for tracking
            previous_output: Previous iteration output (for context)
            model: Claude model to use
            
        Returns:
            Tuple of (success, output)
        """
        # Build enhanced prompt with previous context
        enhanced_prompt = prompt
        
        if previous_output:
            enhanced_prompt = f"""{prompt}

---

## Previous Attempt Output
{previous_output}

## Instructions
Review the previous output above. If the task is not yet complete, continue working on it.
If you encountered an error, try a different approach.
Remember to move completed task files to the /Done folder when finished.
"""
        
        # Log iteration
        self.current_iteration += 1
        logger.info(f"Starting iteration {self.current_iteration}/{self.max_iterations}")
        
        # Update state file
        state_file = self.ralph_state_path / f"{task_id}.md"
        if state_file.exists():
            content = state_file.read_text()
            content += f"\n\n## Iteration {self.current_iteration} - {datetime.now().isoformat()}\n"
            content += f"Prompt: {enhanced_prompt[:500]}...\n"
            state_file.write_text(content)
        
        try:
            # Run Claude Code with the prompt
            # Note: This is a simplified implementation
            # In production, you'd use the Claude Code CLI or API properly
            
            cmd = [
                "claude",
                "--prompt", enhanced_prompt,
                "--model", model
            ]
            
            # For demonstration, we'll simulate the Claude call
            # In production, uncomment and use:
            # result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            # output = result.stdout + result.stderr
            
            output = f"[Simulated Claude output for iteration {self.current_iteration}]"
            success = True
            
            # Append output to state file
            if state_file.exists():
                content = state_file.read_text()
                content += f"\nOutput:\n{output}\n"
                state_file.write_text(content)
            
            return (success, output)
            
        except subprocess.TimeoutExpired:
            logger.error(f"Claude iteration {self.current_iteration} timed out")
            return (False, "Timeout expired")
        except Exception as e:
            logger.error(f"Claude iteration {self.current_iteration} failed: {e}")
            return (False, str(e))
    
    def run(
        self,
        prompt: str,
        task_id: str = None,
        completion_promise: str = "TASK_COMPLETE",
        check_file_movement: bool = True
    ) -> Tuple[TaskStatus, str, int]:
        """
        Run the Ralph Wiggum persistence loop.
        
        Args:
            prompt: Task prompt
            task_id: Optional task ID
            completion_promise: String to look for indicating completion
            check_file_movement: Also check if file moved to /Done
            
        Returns:
            Tuple of (final status, reason, iterations used)
        """
        # Create task if no ID provided
        if not task_id:
            task_id = f"RALPH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task_file = self.create_task(prompt, task_id)
        self.current_task_id = task_id
        
        logger.info(f"Starting Ralph Wiggum loop for task: {task_id}")
        logger.info(f"Prompt: {prompt[:200]}...")
        
        previous_output = ""
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Check duration limit
            elapsed = datetime.now() - self.start_time
            if elapsed > self.max_duration:
                logger.warning(f"Max duration ({self.max_duration}) exceeded")
                self._update_state(task_id, TaskStatus.TIMEOUT, f"Timeout after {elapsed}")
                return (TaskStatus.TIMEOUT, f"Timeout after {elapsed}", iteration)
            
            # Run Claude iteration
            success, output = self.run_claude_iteration(
                prompt=prompt,
                task_id=task_id,
                previous_output=previous_output,
                model="opus"
            )
            
            previous_output = output
            
            # Check for completion
            if check_file_movement:
                status, reason = self.check_task_completion(task_id)
                
                if status == TaskStatus.COMPLETED:
                    logger.info(f"Task completed: {task_id} - {reason}")
                    self._update_state(task_id, TaskStatus.COMPLETED, reason)
                    return (TaskStatus.COMPLETED, reason, iteration)
                
                elif status == TaskStatus.FAILED:
                    logger.warning(f"Task failed: {task_id} - {reason}")
                    self._update_state(task_id, TaskStatus.FAILED, reason)
                    return (TaskStatus.FAILED, reason, iteration)
            
            # Check for completion promise in output
            if completion_promise in output:
                logger.info(f"Completion promise detected: {task_id}")
                self._update_state(task_id, TaskStatus.COMPLETED, "Completion promise found")
                return (TaskStatus.COMPLETED, "Completion promise detected", iteration)
            
            # Log progress
            logger.info(f"Iteration {iteration}/{self.max_iterations} - Task still in progress")
            
            # Wait before next iteration
            time.sleep(self.check_interval)
        
        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached for task: {task_id}")
        self._update_state(task_id, TaskStatus.FAILED, f"Max iterations ({self.max_iterations}) reached")
        return (TaskStatus.FAILED, f"Max iterations reached", iteration)
    
    def _update_state(self, task_id: str, status: TaskStatus, reason: str):
        """
        Update task state file.
        
        Args:
            task_id: Task ID
            status: Task status
            reason: Status reason
        """
        state_file = self.ralph_state_path / f"{task_id}.md"
        
        if state_file.exists():
            content = state_file.read_text()
            
            # Update status in frontmatter
            content = content.replace("status: pending", f"status: {status.value}")
            content += f"\n\n## Final Status\n- **Status:** {status.value}\n- **Reason:** {reason}\n- **Completed at:** {datetime.now().isoformat()}\n"
            
            state_file.write_text(content)
    
    def get_task_history(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task execution history.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task history dictionary
        """
        state_file = self.ralph_state_path / f"{task_id}.md"
        
        if not state_file.exists():
            return None
        
        content = state_file.read_text()
        metadata = {}
        
        # Parse frontmatter
        if content.startswith("---"):
            try:
                end = content.index("---", 3)
                frontmatter = content[4:end].strip()
                
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()
            except (ValueError, IndexError):
                pass
        
        return {
            "task_id": task_id,
            "metadata": metadata,
            "state_file": str(state_file)
        }


def run_ralph_loop(
    prompt: str,
    vault_path: str = "AI_Employee_Vault",
    max_iterations: int = 10,
    max_duration_minutes: int = 60
) -> Tuple[TaskStatus, str, int]:
    """
    Convenience function to run Ralph Wiggum loop.
    
    Args:
        prompt: Task prompt
        vault_path: Path to vault
        max_iterations: Maximum iterations
        max_duration_minutes: Maximum duration
        
    Returns:
        Tuple of (status, reason, iterations)
    """
    loop = RalphWiggumLoop(
        vault_path=vault_path,
        max_iterations=max_iterations,
        max_duration_minutes=max_duration_minutes
    )
    
    return loop.run(prompt=prompt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum Persistence Loop - Keep Claude working until task completion"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Task prompt to process"
    )
    parser.add_argument(
        "--vault",
        default="AI_Employee_Vault",
        help="Path to AI Employee vault"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum number of iterations (default: 10)"
    )
    parser.add_argument(
        "--max-duration",
        type=int,
        default=60,
        help="Maximum duration in minutes (default: 60)"
    )
    parser.add_argument(
        "--task-id",
        help="Optional task ID"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("Ralph Wiggum Persistence Loop")
    print(f"{'='*60}")
    print(f"Task: {args.prompt[:100]}...")
    print(f"Max Iterations: {args.max_iterations}")
    print(f"Max Duration: {args.max_duration} minutes")
    print(f"{'='*60}\n")
    
    # Run the loop
    loop = RalphWiggumLoop(
        vault_path=args.vault,
        max_iterations=args.max_iterations,
        max_duration_minutes=args.max_duration
    )
    
    status, reason, iterations = loop.run(
        prompt=args.prompt,
        task_id=args.task_id
    )
    
    print(f"\n{'='*60}")
    print(f"Task Complete!")
    print(f"Status: {status.value}")
    print(f"Reason: {reason}")
    print(f"Iterations: {iterations}")
    print(f"{'='*60}\n")
    
    # Exit with appropriate code
    sys.exit(0 if status == TaskStatus.COMPLETED else 1)
