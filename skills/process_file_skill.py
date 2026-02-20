import os
from claude_agent_sdk.agent import Agent
from claude_agent_sdk.tools import Tool

class ProcessFileSkill(Agent):
    def __init__(self):
        super().__init__()
        self.add_tool(Tool('read_file', self._read_file, 'Reads content from a specified file path.'))
        self.add_tool(Tool('write_file', self._write_file, 'Writes content to a specified file path.'))
        self.add_tool(Tool('move_file', self._move_file, 'Moves a file from a source path to a destination path.'))

    def _read_file(self, file_path: str) -> str:
        """Reads content from a specified file path."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File not found at {file_path}"

    def _write_file(self, file_path: str, content: str):
        """Writes content to a specified file path."""
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return f"Content successfully written to {file_path}"
        except Exception as e:
            return f"Error writing to file {file_path}: {e}"

    def _move_file(self, source_path: str, destination_path: str):
        """Moves a file from a source path to a destination path."""
        try:
            os.rename(source_path, destination_path)
            return f"File moved from {source_path} to {destination_path}"
        except FileNotFoundError:
            return f"Error: File not found at {source_path}"
        except Exception as e:
            return f"Error moving file from {source_path} to {destination_path}: {e}"

    def process_file_task(self, file_path: str):
        content = self._read_file(file_path)
        if content.startswith("Error:"):
            return content

        # Simple processing: summarize and create a new file, then move original
        summary = f"Summary of {file_path}:\n\n" + "\n".join([line for line in content.split('\n') if line.strip() and not line.strip().startswith('--')])[:200] + "..."

        summary_file_path = file_path.replace('Needs_Action', 'Done').replace('.md', '_summary.md')
        self._write_file(summary_file_path, summary)

        self._move_file(file_path, file_path.replace('Needs_Action', 'Done'))

        return f"Processed {file_path}. Summary in {summary_file_path}. Original moved to Done."

