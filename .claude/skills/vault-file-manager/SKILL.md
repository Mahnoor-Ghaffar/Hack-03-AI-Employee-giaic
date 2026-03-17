# vault-file-manager Skill

**Purpose:** Manage task workflow by moving task files between predefined folders within the `AI_Employee_Vault/`.

**Usage:**
This skill moves a specified file from a source folder to a destination folder. The supported folders are `Inbox/`, `Needs_Action/`, and `Done/`.

**Arguments:**
*   `filename`: The name of the file to move (e.g., `my_task.md`).
*   `source_folder`: The current folder of the file (e.g., `Inbox`).
*   `destination_folder`: The target folder for the file (e.g., `Needs_Action`).

**Example Invocation:**
```bash
python scripts/move_task.py "01.md" "Needs_Action" "Done"
```
