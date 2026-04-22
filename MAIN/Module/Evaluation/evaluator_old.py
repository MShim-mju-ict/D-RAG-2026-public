import os
import pandas as pd


def evaluate(answer_sheet_path, results_folder_path):
    """
    Evaluates search result Excel files against a ground truth Answer Sheet.

    :param answer_sheet_path: Full file path to the Answer Sheet Excel file.
    :param results_folder_path: Directory path containing the Result Excel files.
    """

    # 1. Read the Answer Sheet
    # Ensure IDs are read as strings to prevent mismatch (e.g., 123 vs "123")
    try:
        ans_df = pd.read_excel(answer_sheet_path, dtype={'ID': str})
    except Exception as e:
        print(f"Error reading Answer Sheet: {e}")
        return

    # 2. Create a Lookup Dictionary for O(1) performance
    # Key: (targetQ, ID), Value: match status (1 or 0)
    # We filter specifically for where the 'match' column indicates a true positive.
    # Adjust the condition (x == True or x == 1 or x == 'TRUE') based on your specific Excel data.
    truth_set = set()
    for _, row in ans_df.iterrows():
        # Clean data: strip whitespace from strings
        t_q = str(row['targetQ']).strip()
        doc_id = str(row['ID']).strip()
        is_match = row['match']

        # Assume boolean True, integer 1, or string "TRUE"/"True" means a match
        if is_match == 1 or is_match is True or str(is_match).upper() == 'TRUE':
            truth_set.add((t_q, doc_id))

    all_result_dfs = []

    # 3. Iterate through Result Files
    if not os.path.exists(results_folder_path):
        print(f"Error: Results folder not found at {results_folder_path}")
        return

    for filename in os.listdir(results_folder_path):
        if filename.endswith(".xlsx") and not filename.startswith("~$"):
            file_path = os.path.join(results_folder_path, filename)

            # The filename (without extension) is the targetQ
            query_name = os.path.splitext(filename)[0]

            try:
                # Read result file, ensuring ID is string
                res_df = pd.read_excel(file_path, dtype={'ID': str})

                # Add 'targetQ' column
                res_df['targetQ'] = query_name

                # 4. Perform Evaluation
                # Check if (query_name, ID) exists in our truth_set
                res_df['eval'] = res_df['ID'].apply(
                    lambda x: 1 if (query_name, str(x).strip()) in truth_set else 0
                )

                all_result_dfs.append(res_df)

            except Exception as e:
                print(f"Error processing file {filename}: {e}")

    # 5. Concatenate and Print
    if all_result_dfs:
        final_df = pd.concat(all_result_dfs, ignore_index=True)

        # Reorder columns to ensure targetQ and eval are visible at the end or start as preferred
        # Ensuring standard columns exist (handling optional Explanation column)
        cols = [c for c in final_df.columns if c not in ['targetQ', 'eval']]
        final_cols = cols + ['targetQ', 'eval']
        final_df = final_df[final_cols]

        print("--- Final Evaluation DataFrame ---")
        print(final_df)

        return final_df
    else:
        print("No valid result files were processed.")
        return pd.DataFrame()


def evaluate2(answer_sheet_path, results_folder_path):
    """
    Evaluates results and calculates the Global Truth count (total correct answers) per query.

    :return: (final_df, global_truth_counts)
             - final_df: The combined dataframe of results with 1/0 evaluation.
             - global_truth_counts: Dictionary {targetQ: total_number_of_relevant_docs}
    """

    # --- 1. Load Answer Sheet & Calculate Global Truth Counts ---
    try:
        ans_df = pd.read_excel(answer_sheet_path, dtype={'ID': str})
    except Exception as e:
        print(f"Error reading Answer Sheet: {e}")
        return None, None

    # Filter for valid matches only (match == 1/True)
    # This creates the "Truth Set"
    true_rows = ans_df[
        (ans_df['match'] == 1) |
        (ans_df['match'] == True) |
        (ans_df['match'].astype(str).str.upper() == 'TRUE')
        ]

    # Count how many correct answers exist for each targetQ
    # Dictionary format: {'CovidSearch': 5, 'VaccineInfo': 2, ...}
    global_truth_counts = true_rows.groupby('targetQ')['ID'].count().to_dict()

    # Create lookup set for O(1) evaluation
    truth_set = set(zip(true_rows['targetQ'].astype(str).str.strip(),
                        true_rows['ID'].astype(str).str.strip()))

    # --- 2. Process Result Files (Same as before) ---
    all_result_dfs = []

    if not os.path.exists(results_folder_path):
        print(f"Error: Folder {results_folder_path} not found.")
        return None, None

    for filename in os.listdir(results_folder_path):
        if filename.endswith(".xlsx") and not filename.startswith("~$"):
            file_path = os.path.join(results_folder_path, filename)
            query_name = os.path.splitext(filename)[0]

            try:
                res_df = pd.read_excel(file_path, dtype={'ID': str})
                res_df['targetQ'] = query_name

                # Check match against truth_set
                res_df['eval'] = res_df['ID'].apply(
                    lambda x: 1 if (query_name, str(x).strip()) in truth_set else 0
                )
                all_result_dfs.append(res_df)

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # --- 3. Finalize ---
    if all_result_dfs:
        final_df = pd.concat(all_result_dfs, ignore_index=True)
        return final_df, global_truth_counts
    else:
        return pd.DataFrame(), global_truth_counts