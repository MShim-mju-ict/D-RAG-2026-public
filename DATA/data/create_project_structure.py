import os
import sys
import shutil

def create_project_structure(folder_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_template_path = os.path.join(base_dir, "####")
    new_folder_path = os.path.join(base_dir, folder_name)

    if not os.path.exists(source_template_path):
        print(f"Error: Template folder '####' not found in {base_dir}")
        return

    if os.path.exists(new_folder_path):
        print(f"Error: Destination folder '{folder_name}' already exists at {new_folder_path}")
        return

    try:
        print(f"Copying template from {source_template_path} to {new_folder_path}...")
        shutil.copytree(source_template_path, new_folder_path)
        print(f"Successfully created new project structure: {new_folder_path}")
    except Exception as e:
        print(f"Error copying folder: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_project_structure.py <folder_name>")
        # Optional: Ask for input if argument not provided
        folder_name = input("Enter the name of the new folder: ")
        if folder_name:
             create_project_structure(folder_name)
    else:
        create_project_structure(sys.argv[1])
