"""
Ralph Wiggum Autonomous Loop - AI Employee Skill

Implements autonomous task execution with:
1. Task analysis
2. Plan.md creation
3. Step-by-step execution with result checking
4. Max 5 iterations safety limit
5. Human approval for risky actions
6. Automatic task movement to Done on completion

Integration: Works with existing scheduler/orchestrator
"""

import os
import sys
import json
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Callable
from enum import Enum
import threading
import re

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import from project
from log_manager import setup_logging

# Setup logging
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="ralph_wiggum_skill")


# =============================================================================
# Configuration
# =============================================================================

VAULT_PATH = Path("AI_Employee_Vault")
NEEDS_ACTION_PATH = VAULT_PATH / "Needs_Action"
DONE_PATH = VAULT_PATH / "Done"
PLANS_PATH = VAULT_PATH / "Plans"
PENDING_APPROVAL_PATH = VAULT_PATH / "Pending_Approval"
NEEDS_APPROVAL_PATH = VAULT_PATH / "Needs_Approval"

# Safety limits
MAX_ITERATIONS = 5  # Ralph Wiggum safety limit
DEFAULT_ITERATION_DELAY = 2  # seconds between iterations
RISKY_ACTION_THRESHOLD = 0.7  # Confidence threshold for requiring approval


# =============================================================================
# Enums and Types
# =============================================================================

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations"
    TIMEOUT = "timeout"


class RiskLevel(Enum):
    """Action risk level for approval workflow."""
    LOW = "low"  # Auto-approve
    MEDIUM = "medium"  # Log and notify
    HIGH = "high"  # Require human approval


# =============================================================================
# Risk Assessment
# =============================================================================

RISKY_ACTIONS = [
    # Financial actions
    "send_email", "send", "email", "payment", "invoice", "transfer", "money",
    # Data modification
    "delete", "remove", "destroy", "erase", "format", "wipe",
    # External systems
    "post", "publish", "tweet", "facebook", "linkedin", "instagram",
    # System changes
    "install", "uninstall", "configure", "deploy", "restart", "shutdown",
    # Approval keywords
    "approve", "reject", "authorize", "confirm", "verify"
]

RISKY_PATTERNS = [
    r"\$\d+",  # Dollar amounts
    r"\d+%",  # Percentages
    r"urgent", r"immediate", r"asap",  # Urgency indicators
    r"confidential", r"secret", r"private",  # Sensitivity indicators
]


def assess_risk(action_description: str, context: Dict[str, Any] = None) -> RiskLevel:
    """
    Assess the risk level of an action.
    
    Args:
        action_description: Description of the action to assess
        context: Additional context for risk assessment
    
    Returns:
        RiskLevel enum value
    """
    text = action_description.lower()
    risk_score = 0
    
    # Check for risky action keywords
    for keyword in RISKY_ACTIONS:
        if keyword in text:
            risk_score += 1
    
    # Check for risky patterns
    for pattern in RISKY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            risk_score += 2
    
    # Check context for additional risk factors
    if context:
        if context.get("involves_money", False):
            risk_score += 3
        if context.get("involves_personal_data", False):
            risk_score += 2
        if context.get("external_visibility", False):
            risk_score += 1
        if context.get("irreversible", False):
            risk_score += 3
    
    # Determine risk level
    if risk_score >= 5:
        return RiskLevel.HIGH
    elif risk_score >= 2:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW


# =============================================================================
# Plan Generation
# =============================================================================

def analyze_task(task_content: str, task_file: Path) -> Dict[str, Any]:
    """
    Analyze a task to extract key information.
    
    Args:
        task_content: Content of the task file
        task_file: Path to the task file
    
    Returns:
        Dictionary with task analysis results
    """
    analysis = {
        "task_file": str(task_file),
        "task_name": task_file.stem,
        "created": datetime.now().isoformat(),
        "content_length": len(task_content),
        "estimated_complexity": "unknown",
        "required_actions": [],
        "dependencies": [],
        "risk_factors": [],
        "suggested_steps": []
    }
    
    # Extract metadata from frontmatter if present
    if task_content.startswith("---"):
        try:
            end = task_content.index("---", 3)
            frontmatter = task_content[4:end].strip()
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == "type":
                        analysis["task_type"] = value
                    elif key == "priority":
                        analysis["priority"] = value
                    elif key == "deadline":
                        analysis["deadline"] = value
        except (ValueError, IndexError):
            pass
    
    # Analyze content for action items
    content_lower = task_content.lower()
    
    # Detect required actions
    if any(word in content_lower for word in ["email", "send", "reply"]):
        analysis["required_actions"].append("email_communication")
    if any(word in content_lower for word in ["post", "publish", "social"]):
        analysis["required_actions"].append("social_media_posting")
    if any(word in content_lower for word in ["file", "document", "process"]):
        analysis["required_actions"].append("file_processing")
    if any(word in content_lower for word in ["analyze", "review", "check"]):
        analysis["required_actions"].append("analysis_review")
    if any(word in content_lower for word in ["create", "generate", "write"]):
        analysis["required_actions"].append("content_creation")
    if any(word in content_lower for word in ["move", "copy", "organize"]):
        analysis["required_actions"].append("file_organization")
    
    # Estimate complexity
    action_count = len(analysis["required_actions"])
    if action_count == 0:
        analysis["estimated_complexity"] = "simple"
    elif action_count <= 2:
        analysis["estimated_complexity"] = "moderate"
    else:
        analysis["estimated_complexity"] = "complex"
    
    # Assess risk
    risk = assess_risk(task_content, analysis)
    analysis["risk_level"] = risk.value
    
    if risk == RiskLevel.HIGH:
        analysis["risk_factors"].append("High risk action detected - requires approval")
    elif risk == RiskLevel.MEDIUM:
        analysis["risk_factors"].append("Medium risk action - log and notify")
    
    return analysis


def generate_plan(analysis: Dict[str, Any], task_content: str) -> str:
    """
    Generate a step-by-step execution plan.
    
    Args:
        analysis: Task analysis results
        task_content: Original task content
    
    Returns:
        Markdown formatted plan
    """
    plan = f"""---
type: execution_plan
task_name: {analysis.get('task_name', 'unknown')}
task_file: {analysis.get('task_file', 'unknown')}
created: {datetime.now().isoformat()}
complexity: {analysis.get('estimated_complexity', 'unknown')}
risk_level: {analysis.get('risk_level', 'unknown')}
max_iterations: {MAX_ITERATIONS}
status: pending
---

# Execution Plan: {analysis.get('task_name', 'Unknown Task')}

## Task Analysis

- **Complexity:** {analysis.get('estimated_complexity', 'unknown')}
- **Risk Level:** {analysis.get('risk_level', 'unknown')}
- **Required Actions:** {', '.join(analysis.get('required_actions', ['none']))}
- **Risk Factors:** {', '.join(analysis.get('risk_factors', ['none'])) or 'None identified'}

## Original Task Content

```
{task_content[:500]}{'...' if len(task_content) > 500 else ''}
```

## Execution Steps

"""
    
    # Generate steps based on required actions
    steps = []
    step_num = 1
    
    # Step 1: Always start with analysis
    steps.append(f"### Step {step_num}: Analyze Task Requirements\n- [ ] Review task content thoroughly\n- [ ] Identify all required actions\n- [ ] Check for dependencies or prerequisites\n- [ ] Verify available resources and permissions")
    step_num += 1
    
    # Add steps for each required action
    action_steps = {
        "email_communication": f"""### Step {step_num}: Handle Email Communication
- [ ] Draft email content
- [ ] Verify recipient addresses
- [ ] Check for attachments
- [ ] Review for approval if risky
- [ ] Send email or queue for approval""",
        
        "social_media_posting": f"""### Step {step_num}: Handle Social Media Posting
- [ ] Prepare post content
- [ ] Check platform requirements
- [ ] Add relevant hashtags
- [ ] Review for approval
- [ ] Publish or schedule post""",
        
        "file_processing": f"""### Step {step_num}: Process Files
- [ ] Locate input files
- [ ] Validate file formats
- [ ] Process file content
- [ ] Save results to appropriate location
- [ ] Update task status""",
        
        "analysis_review": f"""### Step {step_num}: Perform Analysis/Review
- [ ] Gather relevant data
- [ ] Apply analysis criteria
- [ ] Document findings
- [ ] Generate recommendations
- [ ] Save analysis report""",
        
        "content_creation": f"""### Step {step_num}: Create Content
- [ ] Define content requirements
- [ ] Draft initial content
- [ ] Review and refine
- [ ] Format for intended use
- [ ] Save to appropriate location""",
        
        "file_organization": f"""### Step {step_num}: Organize Files
- [ ] Identify source files
- [ ] Determine target locations
- [ ] Move/copy files
- [ ] Update file references
- [ ] Verify organization"""
    }
    
    for action in analysis.get("required_actions", []):
        if action in action_steps:
            steps.append(action_steps[action])
            step_num += 1
    
    # Final step: Always complete and move to Done
    steps.append(f"""### Step {step_num}: Complete Task
- [ ] Verify all steps completed
- [ ] Update task status to completed
- [ ] Move task file to Done folder
- [ ] Log completion summary
- [ ] Mark TASK_COMPLETE""")
    
    plan += "\n\n".join(steps)
    
    plan += f"""

## Completion Criteria

Task is considered complete when:
1. All checklist items above are marked as done
2. Task file is moved to `AI_Employee_Vault/Done/`
3. Completion summary is logged
4. `TASK_COMPLETE` marker is present in output

## Safety Controls

- **Maximum Iterations:** {MAX_ITERATIONS}
- **Human Approval Required:** {analysis.get('risk_level') == 'high'}
- **Risk Level:** {analysis.get('risk_level', 'unknown')}

---
*Generated by Ralph Wiggum Autonomous Loop*
"""
    
    return plan


# =============================================================================
# Step Execution
# =============================================================================

class StepResult(Enum):
    """Result of executing a single step."""
    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_APPROVAL = "needs_approval"
    SKIPPED = "skipped"
    PARTIAL = "partial"


def execute_step(
    step_description: str,
    step_num: int,
    context: Dict[str, Any]
) -> Tuple[StepResult, str]:
    """
    Execute a single step from the plan.
    
    This is a placeholder that would be replaced with actual execution logic.
    In production, this would call appropriate skills/APIs.
    
    Args:
        step_description: Description of the step to execute
        step_num: Step number
        context: Execution context
    
    Returns:
        Tuple of (StepResult, result_message)
    """
    logger.info(f"Executing step {step_num}: {step_description[:100]}...")
    
    # Check if step requires approval
    risk = assess_risk(step_description, context)
    
    if risk == RiskLevel.HIGH:
        return (StepResult.NEEDS_APPROVAL, f"Step {step_num} requires human approval (high risk)")
    
    # Simulate step execution
    # In production, this would call actual skills
    try:
        # Placeholder for actual execution
        time.sleep(0.5)  # Simulate work
        
        return (StepResult.SUCCESS, f"Step {step_num} completed successfully")
    
    except Exception as e:
        return (StepResult.FAILED, f"Step {step_num} failed: {str(e)}")


# =============================================================================
# Human Approval Integration
# =============================================================================

def request_human_approval(
    task_name: str,
    step_description: str,
    plan_path: Path,
    timeout_seconds: int = 3600
) -> Tuple[bool, str]:
    """
    Request human approval for a risky action.
    
    Args:
        task_name: Name of the task
        step_description: Description of the step requiring approval
        plan_path: Path to the plan file
        timeout_seconds: Approval timeout
    
    Returns:
        Tuple of (approved, reason)
    """
    approval_id = f"RALPH_{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    approval_file = PENDING_APPROVAL_PATH / f"{approval_id}.md"
    
    approval_content = f"""---
type: ralph_wiggum_approval
task_name: {task_name}
approval_id: {approval_id}
status: pending
created: {datetime.now().isoformat()}
timeout_seconds: {timeout_seconds}
---

# Human Approval Required

## Task
**Name:** {task_name}
**Plan:** {plan_path}

## Action Requiring Approval

```
{step_description}
```

## Risk Assessment
This action has been flagged as high-risk and requires human approval.

## Instructions

To approve this action:
1. Edit this file
2. Change `status: pending` to `status: approved`
3. Add any comments or modifications
4. Save the file

To reject:
1. Edit this file
2. Change `status: pending` to `status: rejected`
3. Add rejection reason
4. Save the file

## Status Check

The Ralph Wiggum loop will check this file every 10 seconds.
Timeout: {timeout_seconds} seconds ({timeout_seconds/60:.1f} minutes)

---
*Generated by Ralph Wiggum Autonomous Loop*
"""
    
    # Ensure directory exists
    PENDING_APPROVAL_PATH.mkdir(parents=True, exist_ok=True)
    
    # Write approval file
    approval_file.write_text(approval_content)
    logger.info(f"Created approval request: {approval_file}")
    
    # Move to Needs_Approval for processing
    needs_approval_file = NEEDS_APPROVAL_PATH / f"{approval_id}.md"
    shutil.move(str(approval_file), str(needs_approval_file))
    
    # Wait for approval
    start_time = time.time()
    poll_interval = 10  # Check every 10 seconds
    
    while time.time() - start_time < timeout_seconds:
        time.sleep(poll_interval)
        
        if needs_approval_file.exists():
            content = needs_approval_file.read_text().lower()
            
            if "status: approved" in content:
                logger.info(f"Approval GRANTED for {task_name}")
                # Move to Done
                done_file = DONE_PATH / f"{approval_id}_approved.md"
                shutil.move(str(needs_approval_file), str(done_file))
                return (True, "Human approval granted")
            
            elif "status: rejected" in content:
                logger.warning(f"Approval REJECTED for {task_name}")
                # Move to Done with rejection
                done_file = DONE_PATH / f"{approval_id}_rejected.md"
                shutil.move(str(needs_approval_file), str(done_file))
                return (False, "Human approval rejected")
    
    # Timeout
    logger.warning(f"Approval TIMEOUT for {task_name}")
    if needs_approval_file.exists():
        done_file = DONE_PATH / f"{approval_id}_timeout.md"
        shutil.move(str(needs_approval_file), str(done_file))
    
    return (False, f"Approval timeout after {timeout_seconds} seconds")


# =============================================================================
# Main Ralph Wiggum Loop
# =============================================================================

class RalphWiggumAutonomousLoop:
    """
    Ralph Wiggum Autonomous Loop Manager.
    
    Implements the complete workflow:
    1. Analyze task
    2. Create Plan.md
    3. Execute first step
    4. Check result
    5. Continue next step
    6. Repeat until completed
    7. Move task to Done
    """
    
    def __init__(
        self,
        vault_path: Path = VAULT_PATH,
        max_iterations: int = MAX_ITERATIONS,
        iteration_delay: float = DEFAULT_ITERATION_DELAY
    ):
        """
        Initialize Ralph Wiggum Autonomous Loop.
        
        Args:
            vault_path: Path to AI Employee vault
            max_iterations: Maximum iterations (safety limit)
            iteration_delay: Delay between iterations in seconds
        """
        self.vault_path = vault_path
        self.needs_action_path = vault_path / "Needs_Action"
        self.done_path = vault_path / "Done"
        self.plans_path = vault_path / "Plans"
        self.pending_approval_path = vault_path / "Pending_Approval"
        self.needs_approval_path = vault_path / "Needs_Approval"
        
        # Ensure directories exist
        for path in [self.needs_action_path, self.done_path, self.plans_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        self.max_iterations = max_iterations
        self.iteration_delay = iteration_delay
        
        # State tracking
        self.current_task = None
        self.current_plan = None
        self.iteration_count = 0
        self.completed_steps = []
        self.failed_steps = []
        
        logger.info(f"RalphWiggumAutonomousLoop initialized: max_iterations={max_iterations}")
    
    def process_task_file(self, task_file: Path) -> Tuple[TaskStatus, str]:
        """
        Process a single task file through the autonomous loop.
        
        Args:
            task_file: Path to the task file
        
        Returns:
            Tuple of (final_status, reason)
        """
        logger.info(f"Processing task: {task_file}")
        
        # Read task content
        try:
            task_content = task_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read task file: {e}")
            return (TaskStatus.FAILED, f"Failed to read task file: {e}")
        
        # Step 1: Analyze task
        logger.info("Step 1: Analyzing task...")
        analysis = analyze_task(task_content, task_file)
        self.current_task = analysis
        
        # Step 2: Generate plan
        logger.info("Step 2: Creating Plan.md...")
        plan_content = generate_plan(analysis, task_content)
        plan_file = self.plans_path / f"Plan_{task_file.stem}.md"
        plan_file.write_text(plan_content)
        self.current_plan = plan_file
        logger.info(f"Plan created: {plan_file}")
        
        # Step 3-6: Execute loop
        logger.info("Step 3-6: Starting execution loop...")
        status, reason = self._execute_loop(task_content, task_file, plan_content)
        
        # Step 7: Move to Done if completed
        if status == TaskStatus.COMPLETED:
            logger.info("Step 7: Moving task to Done...")
            self._move_to_done(task_file, analysis)
        
        return (status, reason)
    
    def _execute_loop(
        self,
        task_content: str,
        task_file: Path,
        plan_content: str
    ) -> Tuple[TaskStatus, str]:
        """
        Execute the autonomous loop.
        
        Args:
            task_content: Original task content
            task_file: Path to task file
            plan_content: Generated plan content
        
        Returns:
            Tuple of (final_status, reason)
        """
        self.iteration_count = 0
        self.completed_steps = []
        self.failed_steps = []
        
        # Parse steps from plan
        steps = self._parse_steps(plan_content)
        total_steps = len(steps)
        
        logger.info(f"Starting loop with {total_steps} steps, max {self.max_iterations} iterations")
        
        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            logger.info(f"=== Iteration {self.iteration_count}/{self.max_iterations} ===")
            
            steps_completed_this_iteration = 0
            
            for i, step in enumerate(steps):
                step_num = i + 1
                
                # Skip already completed steps
                if step_num in self.completed_steps:
                    continue
                
                # Check if step failed in previous iteration
                if step_num in self.failed_steps:
                    # Retry failed steps
                    logger.info(f"Retrying failed step {step_num}")
                
                # Execute step
                step_desc = step.get("description", "")[:200]
                result, message = execute_step(
                    step_desc,
                    step_num,
                    {"task": self.current_task, "plan": self.current_plan}
                )
                
                if result == StepResult.SUCCESS:
                    self.completed_steps.append(step_num)
                    steps_completed_this_iteration += 1
                    logger.info(f"Step {step_num} completed: {message}")
                
                elif result == StepResult.NEEDS_APPROVAL:
                    # Request human approval
                    logger.info(f"Step {step_num} requires approval")
                    approved, reason = request_human_approval(
                        task_name=task_file.stem,
                        step_description=step_desc,
                        plan_path=self.current_plan
                    )
                    
                    if approved:
                        self.completed_steps.append(step_num)
                        steps_completed_this_iteration += 1
                        logger.info(f"Step {step_num} approved and completed")
                    else:
                        logger.warning(f"Step {step_num} approval denied: {reason}")
                        if "rejected" in reason.lower():
                            return (TaskStatus.FAILED, f"Step {step_num} rejected by human")
                        elif "timeout" in reason.lower():
                            return (TaskStatus.TIMEOUT, f"Step {step_num} approval timeout")
                
                elif result == StepResult.FAILED:
                    self.failed_steps.append(step_num)
                    logger.error(f"Step {step_num} failed: {message}")
                
                # Check if all steps completed
                if len(self.completed_steps) == total_steps:
                    logger.info("All steps completed!")
                    return (TaskStatus.COMPLETED, f"Completed in {self.iteration_count} iterations")
            
            # Check if any progress was made this iteration
            if steps_completed_this_iteration == 0 and self.failed_steps:
                logger.warning("No progress made this iteration, some steps failed")
                # Could implement retry logic or backoff here
            
            # Delay before next iteration
            if self.iteration_count < self.max_iterations:
                time.sleep(self.iteration_delay)
        
        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        return (TaskStatus.MAX_ITERATIONS, f"Max iterations reached, {len(self.completed_steps)}/{total_steps} steps completed")
    
    def _parse_steps(self, plan_content: str) -> List[Dict[str, Any]]:
        """
        Parse steps from plan content.
        
        Args:
            plan_content: Plan markdown content
        
        Returns:
            List of step dictionaries
        """
        steps = []
        
        # Find all step sections
        step_pattern = r"### Step \d+:(.+?)(?=### Step|$)"
        matches = re.findall(step_pattern, plan_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            step_text = match.strip()
            # Extract description from first line
            description = step_text.split("\n")[0].strip()
            
            steps.append({
                "description": description,
                "full_text": step_text
            })
        
        return steps
    
    def _move_to_done(self, task_file: Path, analysis: Dict[str, Any]):
        """
        Move completed task to Done folder.
        
        Args:
            task_file: Path to task file
            analysis: Task analysis results
        """
        try:
            # Read current content
            content = task_file.read_text(encoding="utf-8")
            
            # Add completion metadata
            completion_marker = f"""

---
## Completed by Ralph Wiggum Autonomous Loop
- **Completed:** {datetime.now().isoformat()}
- **Iterations:** {self.iteration_count}
- **Steps Completed:** {len(self.completed_steps)}
- **Plan:** {self.current_plan}
- **Status:** TASK_COMPLETE
"""
            
            # Append completion info
            content += completion_marker
            
            # Write updated content
            task_file.write_text(content, encoding="utf-8")
            
            # Move to Done
            dest_file = self.done_path / task_file.name
            shutil.move(str(task_file), str(dest_file))
            
            # Also move plan to Done
            if self.current_plan and self.current_plan.exists():
                plan_dest = self.done_path / self.current_plan.name
                shutil.move(str(self.current_plan), str(plan_dest))
            
            logger.info(f"Task moved to Done: {dest_file}")
            
        except Exception as e:
            logger.error(f"Failed to move task to Done: {e}")


# =============================================================================
# Scheduler Integration
# =============================================================================

def process_all_pending_tasks(
    vault_path: Path = VAULT_PATH,
    max_iterations: int = MAX_ITERATIONS
) -> Dict[str, Any]:
    """
    Process all pending tasks in Needs_Action folder.
    
    Integrates with existing scheduler by processing tasks
    that appear in the Needs_Action folder.
    
    Args:
        vault_path: Path to AI Employee vault
        max_iterations: Maximum iterations per task
    
    Returns:
        Summary dictionary with processing results
    """
    logger.info("Ralph Wiggum: Processing all pending tasks...")
    
    needs_action_path = vault_path / "Needs_Action"
    done_path = vault_path / "Done"
    
    results = {
        "processed": 0,
        "completed": 0,
        "failed": 0,
        "tasks": []
    }
    
    # Create loop manager
    loop_manager = RalphWiggumAutonomousLoop(
        vault_path=vault_path,
        max_iterations=max_iterations
    )
    
    # Process all .md files in Needs_Action
    for task_file in needs_action_path.glob("*.md"):
        # Skip plan files
        if task_file.name.startswith("Plan_"):
            continue
        
        logger.info(f"Processing: {task_file.name}")
        results["processed"] += 1
        
        # Process task
        status, reason = loop_manager.process_task_file(task_file)
        
        results["tasks"].append({
            "file": task_file.name,
            "status": status.value,
            "reason": reason
        })
        
        if status == TaskStatus.COMPLETED:
            results["completed"] += 1
        else:
            results["failed"] += 1
    
    logger.info(f"Ralph Wiggum completed: {results['completed']}/{results['processed']} tasks successful")
    
    return results


def ralph_wiggum_skill(
    action: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Main skill interface for Ralph Wiggum Autonomous Loop.
    
    Actions:
    - "process_task": Process a single task file
    - "process_all": Process all pending tasks
    - "analyze": Analyze a task without executing
    - "create_plan": Create a plan for a task
    - "get_status": Get status of a task
    
    Args:
        action: Action to perform
        **kwargs: Action-specific arguments
    
    Returns:
        Result dictionary
    """
    actions = {
        "process_task": lambda: _skill_process_task(kwargs),
        "process_all": lambda: _skill_process_all(kwargs),
        "analyze": lambda: _skill_analyze(kwargs),
        "create_plan": lambda: _skill_create_plan(kwargs),
        "get_status": lambda: _skill_get_status(kwargs)
    }
    
    if action not in actions:
        return {
            "status": "error",
            "message": f"Unknown action: {action}. Valid: {list(actions.keys())}"
        }
    
    try:
        return actions[action]()
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def _skill_process_task(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single task."""
    task_path = kwargs.get("task_path")
    if not task_path:
        return {"status": "error", "message": "task_path required"}
    
    task_file = Path(task_path)
    if not task_file.exists():
        return {"status": "error", "message": f"Task file not found: {task_path}"}
    
    loop_manager = RalphWiggumAutonomousLoop(
        max_iterations=kwargs.get("max_iterations", MAX_ITERATIONS)
    )
    
    status, reason = loop_manager.process_task_file(task_file)
    
    return {
        "status": status.value,
        "reason": reason,
        "task": task_path,
        "plan": str(loop_manager.current_plan) if loop_manager.current_plan else None
    }


def _skill_process_all(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Process all pending tasks."""
    vault_path = kwargs.get("vault_path", VAULT_PATH)
    max_iterations = kwargs.get("max_iterations", MAX_ITERATIONS)
    
    return process_all_pending_tasks(
        vault_path=Path(vault_path),
        max_iterations=max_iterations
    )


def _skill_analyze(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a task without executing."""
    task_path = kwargs.get("task_path")
    if not task_path:
        return {"status": "error", "message": "task_path required"}
    
    task_file = Path(task_path)
    if not task_file.exists():
        return {"status": "error", "message": f"Task file not found: {task_path}"}
    
    content = task_file.read_text(encoding="utf-8")
    analysis = analyze_task(content, task_file)
    
    return {
        "status": "success",
        "analysis": analysis
    }


def _skill_create_plan(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Create a plan for a task."""
    task_path = kwargs.get("task_path")
    if not task_path:
        return {"status": "error", "message": "task_path required"}
    
    task_file = Path(task_path)
    if not task_file.exists():
        return {"status": "error", "message": f"Task file not found: {task_path}"}
    
    content = task_file.read_text(encoding="utf-8")
    analysis = analyze_task(content, task_file)
    plan_content = generate_plan(analysis, content)
    
    # Save plan
    plans_path = VAULT_PATH / "Plans"
    plans_path.mkdir(parents=True, exist_ok=True)
    plan_file = plans_path / f"Plan_{task_file.stem}.md"
    plan_file.write_text(plan_content)
    
    return {
        "status": "success",
        "plan_path": str(plan_file),
        "analysis": analysis
    }


def _skill_get_status(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Get status of a task."""
    task_path = kwargs.get("task_path")
    if not task_path:
        return {"status": "error", "message": "task_path required"}
    
    task_file = Path(task_path)
    
    # Check various locations
    locations = {
        "needs_action": VAULT_PATH / "Needs_Action" / task_file.name,
        "done": VAULT_PATH / "Done" / task_file.name,
        "plans": VAULT_PATH / "Plans" / f"Plan_{task_file.stem}.md"
    }
    
    status_info = {
        "task": task_path,
        "locations": {}
    }
    
    for loc_name, loc_path in locations.items():
        status_info["locations"][loc_name] = loc_path.exists()
    
    # Try to read status from file if it exists
    for loc_path in locations.values():
        if loc_path.exists():
            content = loc_path.read_text()
            if "status: completed" in content.lower() or "TASK_COMPLETE" in content:
                status_info["status"] = "completed"
            elif "status: failed" in content.lower():
                status_info["status"] = "failed"
            elif "status: pending" in content.lower():
                status_info["status"] = "pending"
            break
    
    return {
        "status": "success",
        "info": status_info
    }


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum Autonomous Loop - AI Employee Task Processor"
    )
    parser.add_argument(
        "--action",
        choices=["process_task", "process_all", "analyze", "create_plan"],
        default="process_all",
        help="Action to perform"
    )
    parser.add_argument(
        "--task",
        help="Path to task file (for process_task, analyze, create_plan)"
    )
    parser.add_argument(
        "--vault",
        default=str(VAULT_PATH),
        help="Path to AI Employee vault"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=MAX_ITERATIONS,
        help=f"Maximum iterations (default: {MAX_ITERATIONS})"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("Ralph Wiggum Autonomous Loop")
    print(f"{'='*60}")
    print(f"Action: {args.action}")
    print(f"Vault: {args.vault}")
    print(f"Max Iterations: {args.max_iterations}")
    print(f"{'='*60}\n")
    
    if args.action == "process_all":
        result = ralph_wiggum_skill(
            action="process_all",
            vault_path=args.vault,
            max_iterations=args.max_iterations
        )
        print(json.dumps(result, indent=2))
    
    elif args.action == "process_task":
        if not args.task:
            print("Error: --task required for process_task")
            sys.exit(1)
        
        result = ralph_wiggum_skill(
            action="process_task",
            task_path=args.task,
            max_iterations=args.max_iterations
        )
        print(json.dumps(result, indent=2))
    
    elif args.action == "analyze":
        if not args.task:
            print("Error: --task required for analyze")
            sys.exit(1)
        
        result = ralph_wiggum_skill(
            action="analyze",
            task_path=args.task
        )
        print(json.dumps(result, indent=2))
    
    elif args.action == "create_plan":
        if not args.task:
            print("Error: --task required for create_plan")
            sys.exit(1)
        
        result = ralph_wiggum_skill(
            action="create_plan",
            task_path=args.task
        )
        print(json.dumps(result, indent=2))
