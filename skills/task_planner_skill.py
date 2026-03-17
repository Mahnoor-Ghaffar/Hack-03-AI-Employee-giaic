"""
Task Planner Skill for AI Employee - Silver Tier

This module implements the TaskPlannerSkill using Claude Agent SDK 0.1.39.
It reads task files from Needs_Action, generates step-by-step plans using Claude,
and saves the plans as Plan_*.md in the Needs_Action folder.

Usage:
    The skill can be triggered via the T class:
    
    task = T(
        description="Generate plan for task_file.md",
        prompt="Process the task file and create a plan.",
        subagent_type='task-planner',
        model='opus',
        run_in_background=False
    )
"""

import logging
from pathlib import Path
from claude_agent_sdk.agent import Agent
from claude_agent_sdk.tools import Tool

from log_manager import setup_logging
from skills.vault_skills import get_vault
from claude_sdk_wrapper import T

# Setup logger for the skill (Silver Tier log path)
logger = setup_logging(log_file="logs/ai_employee.log", logger_name="task-planner")


class TaskPlannerSkill(Agent):
    """
    Claude Agent Skill for planning tasks based on markdown file content.
    
    Reads a task .md file from Needs_Action, uses Claude to generate a 
    step-by-step plan, and writes the plan as Plan_*.md back into Needs_Action.
    """
    
    def __init__(self):
        super().__init__()
        self.vault = get_vault()
        logger.info("TaskPlannerSkill initialized.")

        # Add a tool for processing task files
        self.add_tool(Tool(
            'process_task_file_for_planning',
            self._process_task_file_for_planning,
            'Analyzes a markdown file in Needs_Action, generates a step-by-step plan using Claude, and saves it as Plan_*.md in Needs_Action.'
        ))
        
        # Add a direct planning tool using T class
        self.add_tool(Tool(
            'generate_plan_with_subagent',
            self._generate_plan_with_subagent,
            'Spawns a subagent to generate a plan for a task file using the T class.'
        ))

    def _process_task_file_for_planning(self, file_name: str) -> str:
        """
        Reads a task file, generates a plan using a subagent via T class, and saves the plan.

        Args:
            file_name: The name of the markdown file in AI_Employee_Vault/Needs_Action.

        Returns:
            A status message indicating success or failure.
        """
        logger.info(f"TaskPlannerSkill received request to plan for: {file_name}")

        # Step 1: Read the content of the task file
        task_data = self.vault.read_task(file_name)
        if "error" in task_data:
            logger.error(f"Failed to read task file {file_name}: {task_data['error']}")
            return f"Error: Failed to read task file {file_name}. {task_data['error']}"

        task_content = task_data["full_content"]
        logger.debug(f"Successfully read content for {file_name}. Content length: {len(task_content)}")

        # Step 2: Use T class to spawn a general-purpose subagent for planning
        plan_prompt = f"""
Analyze the following task description from the file '{file_name}' and create a detailed, step-by-step implementation plan.

The plan should:
1. Break down the task into clear, actionable steps
2. Identify any dependencies between steps
3. Suggest tools or resources needed
4. Include estimated effort for each step (if determinable)
5. Be formatted in markdown with checkboxes for action items

---
Task File Content:
{task_content}
---

Generate the step-by-step plan now. Output only the plan content in markdown format.
"""

        try:
            # Spawn subagent using T class (blocking mode for immediate result)
            task = T(
                description=f"Generate step-by-step plan for file: {file_name}",
                prompt=plan_prompt,
                subagent_type='general-purpose',
                model='opus',
                run_in_background=False,  # Block until complete
                allowed_tools=["Read", "Write", "Glob", "Edit", "Bash"],
                system_prompt="""You are a planning specialist. Your job is to analyze task descriptions 
and create detailed, actionable implementation plans. Output only the plan in markdown format."""
            )
            
            plan_content = task.output
            
            if not plan_content:
                logger.error(f"Planning subagent for {file_name} returned empty plan.")
                return f"Error: Planning subagent for {file_name} returned empty plan."

            logger.debug(f"Received plan content from subagent for {file_name}.")

            # Step 3: Save the generated plan as Plan_*.md in Needs_Action
            plan_filepath_str = self.vault.write_plan(file_name, plan_content)

            if "Error" in plan_filepath_str:
                logger.error(f"Failed to write plan for {file_name}: {plan_filepath_str}")
                return f"Error: Failed to write plan for {file_name}. {plan_filepath_str}"

            logger.info(f"Successfully generated and saved plan for {file_name} to {plan_filepath_str}")
            return f"Plan for {file_name} generated and saved to {plan_filepath_str}"

        except Exception as e:
            logger.error(f"An unexpected error occurred during planning for {file_name}: {e}")
            return f"Error: An unexpected error occurred during planning for {file_name}: {e}"

    def _generate_plan_with_subagent(self, file_name: str) -> str:
        """
        Alternative method that uses T class directly for planning.
        
        Args:
            file_name: The name of the markdown file to process.
            
        Returns:
            Status message.
        """
        logger.info(f"Using T class subagent for planning: {file_name}")
        
        # Read task content
        task_data = self.vault.read_task(file_name)
        if "error" in task_data:
            return f"Error: {task_data['error']}"
        
        task_content = task_data["full_content"]
        
        # Create planning prompt
        prompt = f"""Read and analyze the task file '{file_name}' with the following content:

{task_content}

Generate a comprehensive step-by-step plan and save it as 'Plan_{Path(file_name).stem}.md' 
in the Needs_Action folder.

The plan should include:
- Clear objectives
- Ordered steps with checkboxes
- Any required resources or dependencies
"""
        
        try:
            # Use T class to spawn the planning subagent
            task = T(
                description=f"Create implementation plan for {file_name}",
                prompt=prompt,
                subagent_type='general-purpose',
                model='opus',
                run_in_background=False,
                allowed_tools=["Read", "Write", "Glob", "Edit"],
            )
            
            if task.output:
                # Save the plan if the subagent didn't already do it
                result = self.vault.write_plan(file_name, task.output)
                logger.info(f"Plan generated via T class: {result}")
                return result
            else:
                return "Error: Subagent returned no output"
                
        except Exception as e:
            logger.error(f"Error in T class planning for {file_name}: {e}")
            return f"Error: {e}"

    def run(self, file_name: str) -> str:
        """
        Main entry point for the skill.
        
        Args:
            file_name: Name of the task file to process.
            
        Returns:
            Status message.
        """
        logger.info(f"TaskPlannerSkill.run() called for: {file_name}")
        return self._process_task_file_for_planning(file_name)


# Convenience function for direct usage
def plan_task(file_name: str) -> str:
    """
    Convenience function to plan a task file.
    
    Args:
        file_name: Name of the task file in Needs_Action.
        
    Returns:
        Status message.
    """
    skill = TaskPlannerSkill()
    return skill.run(file_name)


if __name__ == '__main__':
    # Example usage for testing
    import sys
    
    if len(sys.argv) > 1:
        file_to_plan = sys.argv[1]
    else:
        file_to_plan = "test_task.md"
    
    logger.info(f"Running TaskPlannerSkill for: {file_to_plan}")
    result = plan_task(file_to_plan)
    logger.info(f"Result: {result}")
