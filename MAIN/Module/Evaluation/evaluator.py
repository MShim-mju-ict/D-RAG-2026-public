import pandas as pd
from pathlib import Path
from MAIN.Module.Util.find_files import find_files_by_extension

def is_correct(result_id, query_id):
    """
    Grades a single result ID based on the defined rule.
    Rule: A 6-digit ID is correct if:
          1. It has exactly 6 digits.
          2. The 1st digit is '1'.
          3. The 2nd & 3rd digits match the query_id (padded to 2 digits).
          4. The 4th digit is '1'.
    
    :param result_id: The ID of the search result document.
    :param query_id: The numeric ID of the query being evaluated.
    :return: 1 if correct, 0 if incorrect.
    """
    # Ensure result_id is a string and has 6 digits
    try:
        result_id_str = str(int(result_id))
        if len(result_id_str) != 6:
            # raise ValueError # Removed raise to avoid spamming console for non-matching IDs
            return 0
    except (ValueError, TypeError):
        # print("Error: Result ID must be a 6-digit number.") # Optional logging
        return 0 # Not a valid integer-like ID

    # Format query_id to be a two-digit string (e.g., 5 -> "05")
    query_id_str = f"{query_id:02d}"

    # Check the conditions
    # 1. First digit is '1'
    # 2. 2nd and 3rd digits match query_id
    # 3. 4th digit is '1' (True)
    if (result_id_str[0] == '1' and 
        result_id_str[1:3] == query_id_str and 
        result_id_str[3] == '1'):
        return 1
    else:
        return 0

def compile_graded_results(final_result_folder, top_k=0, logs=True):
    """
    Reads all Excel files, extracts results, and grades them.
    
    :param final_result_folder: Path to the folder with result Excel files.
    :param top_k: The number of top results to evaluate. If 0, evaluate ALL results.
    :param logs: If True, prints detailed processing logs.
    """
    folder_path = Path(final_result_folder)
    compiled_data = []

    if not folder_path.exists():
        print(f"Error: Folder not found at {final_result_folder}")
        return pd.DataFrame()

    files_str = find_files_by_extension(str(folder_path), ".xlsx")
    files_str = [f for f in files_str if not Path(f).name.startswith('~$')]

    # Determine max_k across all files if top_k is 0 (to ensure consistent columns)
    max_results_found = 0

    # First pass to find max rows if top_k is 0
    if top_k == 0:
        for file_path_str in files_str:
            try:
                df = pd.read_excel(file_path_str)
                if len(df) > max_results_found:
                    max_results_found = len(df)
            except:
                pass
        current_k = max_results_found
    else:
        current_k = top_k

    for file_path_str in files_str:
        file_path = Path(file_path_str)
        try:
            # 1. Get numeric Query ID from filename
            filename_stem = file_path.stem
            numeric_part = ''.join(filter(str.isdigit, filename_stem))
            query_id = int(numeric_part) if numeric_part else 0

            # 2. Read rows from the Excel file
            # If top_k is 0, read all rows (nrows=None)
            nrows = top_k if top_k > 0 else None
            df = pd.read_excel(file_path, nrows=nrows)

            # 3. Extract IDs
            # If df is empty, top_ids will be empty list []
            if not df.empty:
                top_ids = df.iloc[:, 0].tolist()
            else:
                top_ids = []
            
            # Pad with None if fewer than current_k results
            while len(top_ids) < current_k:
                top_ids.append(None)
            
            # If we read all rows but some files have more than others, truncate to max found
            # (Only relevant if top_k=0 and files vary in length, we align to the longest)
            if len(top_ids) > current_k:
                 top_ids = top_ids[:current_k]

            # 4. Create the row with graded results
            row = {"Query": query_id}
            
            # Add IDs first
            for i in range(current_k):
                row[f"ID{i+1}"] = top_ids[i]
                
            # Add Grades (R) next
            for i in range(current_k):
                result_id = top_ids[i]
                row[f"R{i+1}"] = is_correct(result_id, query_id)
            
            compiled_data.append(row)

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    # 5. Create and sort final DataFrame
    if not compiled_data:
        return pd.DataFrame()
        
    final_df = pd.DataFrame(compiled_data)
    
    if logs: print("Sorting results by Query ID...")
    try:
        final_df = final_df.sort_values('Query').reset_index(drop=True)
        
        # Explicitly reorder columns to ensure Query, ID1..IDk, R1..Rk order
        cols = ['Query'] + [f'ID{i+1}' for i in range(current_k)] + [f'R{i+1}' for i in range(current_k)]
        # Filter cols to only those present in df
        cols = [c for c in cols if c in final_df.columns]
        final_df = final_df[cols]

        if logs: print("Sorting complete.")
    except Exception as e:
        print(f"Sorting failed: {e}")

    return final_df
