# Process File Skill

**Module:** `skills.process_file_skill`

## Description

This skill processes files from the AI Employee vault, reads their content, and generates summaries. It's designed to handle task files dropped into the `Needs_Action` folder.

## Function Signature

```python
process_file_skill(file_path: str) -> str
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | str | Absolute or relative path to the file to process |

## Returns

| Type | Description |
|------|-------------|
| str | Success message with summary file path, or error message |

## Usage Example

```python
from skills.process_file_skill import process_file_skill

result = process_file_skill("AI_Employee_Vault/Needs_Action/task_001.md")
print(result)
```

## Workflow

1. Reads the specified file from the vault
2. Extracts content and metadata
3. Generates a summary
4. Creates a `.summary.md` file alongside the original
5. Returns status message

## Error Handling

- Returns error message if file doesn't exist
- Returns error message if file is not readable
- Logs all errors for debugging

## Related Files

- `AI_Employee_Vault/Needs_Action/` - Input folder for pending tasks
- `AI_Employee_Vault/Done/` - Output folder for completed tasks
- `AI_Employee_Vault/Dashboard.md` - Status updates written here
