import pandas as pd
from pathlib import Path
import math
from MAIN.Module.Evaluation import metrics

def calculate_idcg(total_relevant=3, k=5):
    """
    Calculates the Ideal Discounted Cumulative Gain (IDCG), which is the max possible DCG.
    This assumes all relevant items are ranked at the top.
    
    :param total_relevant: The total number of relevant documents (default 3).
    :param k: The number of top results considered (default 5).
    """
    idcg = 0
    # The top 'total_relevant' ranks get a score of 1, up to k
    for i in range(min(total_relevant, k)):
        rank = i + 1
        idcg += 1 / math.log2(rank + 1)
    return idcg

def run_metric_calculation(config_str="default", subpath:str = "default", logs:bool = True):
    """
    Runs the metric calculation process.
    
    :param config_str: A string representing the configuration (e.g., "000hybrid") 
                       used to locate the subfolder containing graded.xlsx.
    :param subpath: The subdirectory path to append to the base data path.
    :param logs: If True, prints detailed processing logs.
    """
    print(f"Running metric calculation process... (Config: {config_str}, Subpath={subpath})")
    
    base_data_path = Path("/Users/moonshim/PycharmProjects/D-RAG/DATA/data")
    base_eval_path = base_data_path / subpath / "evaluation"
    
    # Specific folder based on config
    target_folder = base_eval_path / config_str
    
    # Path to the graded results file
    graded_file_path = target_folder / "graded.xlsx"
    
    if not graded_file_path.exists():
        print(f"Error: Graded file not found at {graded_file_path}")
        return

    # 2. Read the graded file
    try:
        graded_df = pd.read_excel(graded_file_path)
    except Exception as e:
        print(f"Error reading graded file: {e}")
        return
    
    all_metrics = []

    # 3. Process row by row
    for index, row in graded_df.iterrows():
        query_id = row['Query']
        
        # Filter out only 'R' columns and convert to a list of grades
        r_cols = [col for col in graded_df.columns if col.startswith('R')]
        graded_results = row[r_cols].tolist()

        # k = len(r_cols)
        k = 5
        total_relevant = 3

        # Calculate metrics for the current query
        query_metrics = metrics.calculate_metrics(graded_results, total_relevant, k)
        query_metrics['Query'] = query_id
        
        # 4. Calculate nDCG
        # Use updated values for IDCG calculation
        idcg = calculate_idcg(total_relevant, k)
        
        # nDCG is DCG / IDCG
        query_metrics['nDCG'] = query_metrics['DCG'] / idcg if idcg > 0 else 0
        
        all_metrics.append(query_metrics)

    # Create a DataFrame from all the collected metrics
    if not all_metrics:
        print("No metrics were calculated.")
        return
        
    metrics_df = pd.DataFrame(all_metrics)
    
    # Reorder columns to have Query first
    cols = ['Query'] + [col for col in metrics_df.columns if col != 'Query']
    metrics_df = metrics_df[cols]

    # 5. Add a final row for the average of all metrics
    # The mean of RR is MRR, the mean of AP is MAP
    average_metrics = metrics_df.drop(columns=['Query']).mean().to_dict()
    average_metrics['Query'] = 'Average'
    
    # Convert dict to DataFrame to use concat
    average_df = pd.DataFrame([average_metrics])
    
    # Use concat to append the average row
    final_metrics_df = pd.concat([metrics_df, average_df], ignore_index=True)

    # Save the final metrics to a new Excel file in the same folder
    save_path = target_folder / "calculated_metrics.xlsx"
    try:
        final_metrics_df.to_excel(save_path, index=False)
        if logs:
            print(f"Successfully saved calculated metrics to: {save_path}")
            print("\n--- Metrics Summary ---")
            print(final_metrics_df)
    except Exception as e:
        print(f"Error saving metrics file: {e}")

if __name__ == "__main__":
    run_metric_calculation()