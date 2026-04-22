from MAIN.Module.Evaluation import evaluator
from pathlib import Path

def run_evaluation(config_str="default", subpath:str = "default", logs:bool = True):
    """
    Runs the evaluation process.
    
    :param config_str: A string representing the configuration (e.g., "000hybrid") 
                       used to create a subfolder for saving results.
    :param subpath: The subdirectory path to append to the base data path.
    :param logs: If True, prints detailed processing logs.
    """
    print(f"Running evaluation process... (Config: {config_str}, Subpath={subpath})")
    
    base_data_path = Path("/Users/moonshim/PycharmProjects/D-RAG/DATA/data")
    folder_path = base_data_path / subpath / "final_result"
    base_save_path = base_data_path / subpath / "evaluation"
    
    # Create specific save path based on config
    save_path = base_save_path / config_str

    # Configuration
    top_k = 0

    # Ensure save directory exists
    if not save_path.exists():
        save_path.mkdir(parents=True, exist_ok=True)
        if logs: print(f"Created save directory: {save_path}")

    # 1. Compile results into a "graded" format
    # The evaluator module handles finding and processing the files.
    graded_df = evaluator.compile_graded_results(str(folder_path), top_k=top_k, logs=logs)

    # 2. Save the compiled DataFrame to the specified save path
    if not graded_df.empty:
        output_file_path = save_path / "graded.xlsx"
        try:
            graded_df.to_excel(output_file_path, index=False)
            if logs: print(f"Successfully saved graded results to: {output_file_path}")
        except Exception as e:
            print(f"Error saving graded Excel file: {e}")
    else:
        print("No data was compiled, so no 'graded.xlsx' file was created.")

if __name__ == "__main__":
    run_evaluation()
