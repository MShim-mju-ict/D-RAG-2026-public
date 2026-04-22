from pathlib import Path
from typing import List
import re

def find_files_by_extension(path: str, ext: str, sort: bool = True) -> List[str]:
    """
    Find all files with a given extension in a folder.
    Args:
        path (str): Folder path to search in
        ext (str): File extension (e.g. 'csv' or '.csv')
        sort (bool): If True, sorts the files numerically by extracting numbers from filenames.
                     This ensures Q1, Q2, Q10 order instead of Q1, Q10, Q2.
    Returns:
        List[str]: List of full file paths
    """
    folder = Path(path)
    # normalize extension
    if not ext.startswith("."):
        ext = "." + ext

    matching_files = []

    if not folder.exists():
        print(f"Folder does not exist: {folder}")
        return []

    for item in folder.iterdir():
        # skip if not a file
        if not item.is_file():
            continue
        # skip if extension does not match
        if item.suffix != ext:
            continue
        # get absolute path as string
        full_path = str(item.resolve())
        matching_files.append(full_path)

    if sort:
        def natural_sort_key(file_path):
            # Extract filename from path
            filename = Path(file_path).name
            # Extract all number sequences
            numbers = re.findall(r'\d+', filename)
            if numbers:
                # Use the first number found for sorting, padded to 4 digits
                # If multiple numbers exist, this logic might need adjustment based on specific needs
                # For Q1.txt, numbers=['1']. For 150123.json, numbers=['150123']
                num = int(numbers[0])
                return f"{num:03d}"
            else:
                # Fallback for files without numbers, use filename itself
                return filename

        matching_files.sort(key=natural_sort_key)

    return matching_files
