import os
from pathlib import Path

def save_string_to_txt(filename, save_location, content_string, logs=True):
    """
    Saves a string to a text file.

    :param filename: The name of the file (e.g., 'output.txt')
    :param save_location: The folder path where the file should be saved (can be str or Path)
    :param content_string: The string content to write to the file
    :param logs: If True, prints detailed processing logs.
    """
    # Ensure save_location is a Path object
    if isinstance(save_location, str):
        save_path = Path(save_location)
    else:
        save_path = save_location
    
    # 1. Ensure the directory exists
    if not save_path.exists():
        save_path.mkdir(parents=True, exist_ok=True)
        if logs: print(f"Created directory: {save_path}")

    # 2. Construct the full file path
    # Adds .txt extension if missing
    if not filename.endswith('.txt'):
        filename += '.txt'

    full_path = save_path / filename

    # 3. Write the content to the file
    try:
        with full_path.open('w', encoding='utf-8') as f:
            f.write(content_string)
        if logs: print(f"Successfully saved to: {full_path}")
    except Exception as e:
        print(f"Error saving file: {e}")
