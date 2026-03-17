import os
import shutil
import sys

VAULT_BASE_PATH = "AI_Employee_Vault/"
ALLOWED_FOLDERS = ["Inbox", "Needs_Action", "Done"]

def move_task(filename, source_folder, destination_folder):
    if source_folder not in ALLOWED_FOLDERS or destination_folder not in ALLOWED_FOLDERS:
        print(f"Error: Invalid source or destination folder. Allowed folders are {', '.join(ALLOWED_FOLDERS)}.")
        sys.exit(1)

    source_path = os.path.join(VAULT_BASE_PATH, source_folder, filename)
    destination_path = os.path.join(VAULT_BASE_PATH, destination_folder, filename)

    if not os.path.exists(source_path):
        print(f"Error: File not found at {source_path}")
        sys.exit(1)

    try:
        shutil.move(source_path, destination_path)
        print(f"Successfully moved '{filename}' from '{source_folder}/' to '{destination_folder}/'.")
    except Exception as e:
        print(f"Error moving file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python move_task.py <filename> <source_folder> <destination_folder>")
        sys.exit(1)

    filename = sys.argv[1]
    source_folder = sys.argv[2]
    destination_folder = sys.argv[3]

    move_task(filename, source_folder, destination_folder)
