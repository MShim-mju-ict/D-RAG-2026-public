from pathlib import Path
import pandas as pd
from MAIN.Process import index_creation_process
from MAIN.Process import query_creation_process
from MAIN.Process import result_generation_process
from MAIN.Process import evaluation_process
from MAIN.Process import metric_process

def run_all(baseline_config=(0, 0, 0), query_type="hybrid", subpath="0000"):
    """
    Runs the full pipeline with granular control over baseline mode for each step.
    
    :param baseline_config: A tuple of 3 integers (index_baseline, query_baseline, result_baseline)
                            0: No augmentation (Original data).
                            1: Use existing augmented data.
                            2: Perform augmentation (and save).
    :param query_type: The type of ES query to generate ("exact", "hybrid", "ngram", "hybrid_ngram").
    :param subpath: The subdirectory path to append to the base data path.
    """
    index_baseline, query_baseline, result_baseline = baseline_config
    
    # Construct configuration string for evaluation folder
    config_str = f"{index_baseline}{query_baseline}{result_baseline}{query_type}"
    
    print("==========================================")
    print(f"STARTING D-RAG FULL PIPELINE")
    print(f"Config: Index={index_baseline}, Query={query_baseline}, Result={result_baseline} Query Type: {query_type}")
    print(f"Subpath: {subpath}")
    print(f"Run ID: {config_str}")
    print("==========================================\n")

    # 1. Index Creation
    print(">>> Step 1: Index Creation")
    try:
        index_creation_process.run_index_creation(baseline=index_baseline, subpath=subpath, logs=False)
        print(">>> Step 1 Complete\n")
    except Exception as e:
        print(f"!!! Step 1 Failed: {e}")
        return

    # 2. Query Creation
    print(">>> Step 2: Query Creation")
    try:
        query_creation_process.run_query_creation(baseline=query_baseline, query_type=query_type, subpath=subpath, logs=False)
        print(">>> Step 2 Complete\n")
    except Exception as e:
        print(f"!!! Step 2 Failed: {e}")
        return

    # 3. Result Generation
    print(">>> Step 3: Result Generation")
    try:
        result_generation_process.run_result_generation(baseline=result_baseline, subpath=subpath, logs=False)
        print(">>> Step 3 Complete\n")
    except Exception as e:
        print(f"!!! Step 3 Failed: {e}")
        return

    # 4. Evaluation
    print(">>> Step 4: Evaluation")
    try:
        # Pass the config string to create a specific subfolder
        evaluation_process.run_evaluation(config_str=config_str, subpath=subpath, logs=False)
        print(">>> Step 4 Complete\n")
    except Exception as e:
        print(f"!!! Step 4 Failed: {e}")
        return

    # 5. Metric Calculation
    print(">>> Step 5: Metric Calculation")
    try:
        # Pass the config string to locate the correct folder
        metric_process.run_metric_calculation(config_str=config_str, subpath=subpath)
        print(">>> Step 5 Complete\n")
    except Exception as e:
        print(f"!!! Step 5 Failed: {e}")
        return

    print("==========================================")
    print("ALL PROCESSES COMPLETED SUCCESSFULLY")
    print("==========================================")

def compound_results(subpath="0000"):
    """
    Aggregates the final 'Average' row from all calculated_metrics.xlsx files 
    found under /evaluation/{config_str}/.
    
    :param subpath: The subdirectory path to append to the base data path.
    """
    print(f"Compounding results for subpath: {subpath}")
    
    base_data_path = Path("/Users/moonshim/PycharmProjects/D-RAG/DATA/data")
    evaluation_root = base_data_path / subpath / "evaluation"
    
    if not evaluation_root.exists():
        print(f"Error: Evaluation root not found at {evaluation_root}")
        return

    aggregated_data = []

    # Iterate through all subdirectories in the evaluation folder
    for config_dir in evaluation_root.iterdir():
        if config_dir.is_dir():
            metrics_file = config_dir / "calculated_metrics.xlsx"
            
            if metrics_file.exists():
                try:
                    df = pd.read_excel(metrics_file)
                    
                    # Find the 'Average' row
                    # Assuming the Query column has 'Average' or it's the last row
                    average_row = df[df['Query'] == 'Average']
                    
                    if not average_row.empty:
                        # Convert to dict and add Config info
                        row_data = average_row.iloc[0].to_dict()
                        row_data['Config'] = config_dir.name
                        
                        # Remove 'Query' column as it's redundant ('Average')
                        if 'Query' in row_data:
                            del row_data['Query']
                            
                        aggregated_data.append(row_data)
                    else:
                        print(f"Warning: 'Average' row not found in {metrics_file}")
                        
                except Exception as e:
                    print(f"Error reading {metrics_file}: {e}")

    if not aggregated_data:
        print("No data found to compound.")
        return

    # Create DataFrame
    final_df = pd.DataFrame(aggregated_data)
    
    # Create sorting keys
    # Key 1: The suffix (everything after the first 3 chars) e.g., "hybrid", "exact"
    # Key 2: The prefix (first 3 chars) e.g., "000", "112"
    final_df['sort_suffix'] = final_df['Config'].apply(lambda x: x[3:] if len(x) > 3 else "")
    final_df['sort_prefix'] = final_df['Config'].apply(lambda x: x[:3] if len(x) >= 3 else x)
    
    # Sort by suffix first, then prefix
    final_df = final_df.sort_values(by=['sort_suffix', 'sort_prefix'], ascending=[True, True])
    
    # Drop the temporary sorting columns
    final_df = final_df.drop(columns=['sort_suffix', 'sort_prefix'])
    
    # Reorder columns to put Config first
    cols = ['Config'] + [col for col in final_df.columns if col != 'Config']
    final_df = final_df[cols]
    
    # Calculate the overall average of all runs
    average_metrics = final_df.drop(columns=['Config']).mean().to_dict()
    average_metrics['Config'] = 'Total Average'
    
    # Append the final average row
    average_df = pd.DataFrame([average_metrics])
    final_df = pd.concat([final_df, average_df], ignore_index=True)
    
    # Save the compounded results
    output_path = evaluation_root / "compounded_results.xlsx"
    try:
        final_df.to_excel(output_path, index=False)
        print(f"Successfully saved compounded results to: {output_path}")
        print(final_df)
    except Exception as e:
        print(f"Error saving compounded results: {e}")

if __name__ == "__main__":
    """
    Configuration: (Index, Query, Result)
    0: Original / Baseline
    1: Use Existing Augmented
    2: Perform Augmentation
    query_type: The type of ES query to generate ("exact", "hybrid", "ngram", "hybrid_ngram").
    """
    # sub = "testing(3q5e)"
    sub = "0401"
    query_types = ["exact", "hybrid", "ngram", "hybrid_ngram"]
    
    # 1. First, run the initial augmentation setup
    print("=== Running Initial Data Augmentation (2,2,0)")
    run_all((2, 2, 0), query_type="exact", subpath=sub)
        
    print("\n=== Running All Permutations with Existing Augmented Data ===")
    
    # 2. Run all combinations using the pre-augmented data (1s and 0s)
    # Result generation augmentation (index=2) is calculated locally so it can be left as 2
    for qt in query_types:
        run_all((0, 0, 0), query_type=qt, subpath=sub)
        run_all((0, 0, 2), query_type=qt, subpath=sub)
        run_all((1, 0, 0), query_type=qt, subpath=sub)
        run_all((1, 0, 2), query_type=qt, subpath=sub)
        run_all((0, 1, 0), query_type=qt, subpath=sub)
        run_all((0, 1, 2), query_type=qt, subpath=sub)
        run_all((1, 1, 0), query_type=qt, subpath=sub)
        run_all((1, 1, 2), query_type=qt, subpath=sub)

    # 3. Compound the results across everything generated in the evaluation directory
    compound_results(subpath=sub)

    ##**** test mini run
    # run_all((0, 0, 0), query_type="exact", subpath=sub)