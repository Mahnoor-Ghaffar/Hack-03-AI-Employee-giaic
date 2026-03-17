"""
Ralph Wiggum Autonomous Loop Skill Package

Implements autonomous task execution with:
1. Task analysis
2. Plan.md creation  
3. Step-by-step execution with result checking
4. Max 5 iterations safety limit
5. Human approval for risky actions
6. Automatic task movement to Done on completion

Usage:
    from .claude.skills.ralph-wiggum import ralph_wiggum_skill, process_all_pending_tasks
    from .claude.skills.ralph-wiggum.scheduler_integration import on_task_appears
"""

from .ralph_wiggum import (
    ralph_wiggum_skill,
    process_all_pending_tasks,
    RalphWiggumAutonomousLoop,
    TaskStatus,
    RiskLevel,
    assess_risk,
    analyze_task,
    generate_plan,
    request_human_approval,
    MAX_ITERATIONS,
    VAULT_PATH
)

from .scheduler_integration import (
    on_task_appears,
    process_with_ralph_loop,
    setup_filesystem_watcher_callback,
    integrate_with_orchestrator,
    process_all_needs_action,
    scheduled_ralph_processing
)

__all__ = [
    # Main skill functions
    "ralph_wiggum_skill",
    "process_all_pending_tasks",
    "RalphWiggumAutonomousLoop",
    
    # Enums and types
    "TaskStatus",
    "RiskLevel",
    
    # Utility functions
    "assess_risk",
    "analyze_task",
    "generate_plan",
    "request_human_approval",
    
    # Scheduler integration
    "on_task_appears",
    "process_with_ralph_loop",
    "setup_filesystem_watcher_callback",
    "integrate_with_orchestrator",
    "process_all_needs_action",
    "scheduled_ralph_processing",
    
    # Constants
    "MAX_ITERATIONS",
    "VAULT_PATH"
]

__version__ = "1.0.0"
