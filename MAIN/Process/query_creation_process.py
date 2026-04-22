import json
from pathlib import Path
from MAIN.Module.Search_Query import qgeneration
from MAIN.Module.Query_Augmentation import query_augmenter
from MAIN.Module.Util.find_files import find_files_by_extension

def run_query_creation(baseline:int = 0, query_type:str = "hybrid", subpath:str = "default", logs:bool = True):
    """
    :param baseline: 
        0: No augmentation (Use original query text).
        1: Use existing augmented query text from aug_save.
        2: Perform augmentation (and save).
    :param query_type: The type of ES query to generate.
    :param subpath: The subdirectory path to append to the base data path.
    :param logs: If True, prints detailed processing logs.
    """
    print(f"Running query creation process... (Baseline={baseline}, Type={query_type}, Subpath={subpath})")
    
    base_data_path = Path("/Users/moonshim/PycharmProjects/D-RAG/DATA/data")
    input_folder_path = base_data_path / subpath / "query"
    save_path = base_data_path / subpath / "search-query"
    aug_save = base_data_path / subpath / "query-aug"

    # Ensure output directories exist
    if not save_path.exists():
        save_path.mkdir(parents=True, exist_ok=True)
    if not aug_save.exists():
        aug_save.mkdir(parents=True, exist_ok=True)

    # 1. Find all .txt files in the input folder
    if input_folder_path.exists():
        txt_files = find_files_by_extension(str(input_folder_path), "txt")
    else:
        print(f"Error: Input folder not found at {input_folder_path}")
        raise Exception(f"Error: Input folder not found at {input_folder_path}")
        
    for file_path_str in txt_files:
        file_path = Path(file_path_str)
        filename = file_path.name
        base_name = file_path.stem
        if logs: print(f"Processing: {filename}")

        try:
            augmented_text = ""
            
            # Determine which text to use based on baseline mode
            if baseline == 1:
                # Mode 1: Use existing augmented text
                aug_output_path = aug_save / f"{base_name}.txt"
                if aug_output_path.exists():
                    with aug_output_path.open('r', encoding='utf-8') as f:
                        augmented_text = f.read()
                    if logs: print(f"Loaded existing augmented query: {filename}")
                else:
                    print(f"Warning: Augmented query not found for {filename}. Falling back to original.")
                    with file_path.open('r', encoding='utf-8') as f:
                        augmented_text = f.read()
            else:
                # Mode 0 or 2: Read original file first
                with file_path.open('r', encoding='utf-8') as f:
                    original_text = f.read()
                
                if baseline == 2:
                    # Mode 2: Perform augmentation
                    # augmented_text = query_augmenter.augment_query1(original_text, logs=logs)
                    augmented_text = query_augmenter.augment_query2(original_text, logs=logs)
                    
                    # Save the augmented text
                    aug_output_path = aug_save / f"{base_name}.txt"
                    with aug_output_path.open('w', encoding='utf-8') as f:
                        f.write(augmented_text)
                    if logs: print(f"Augmented and saved: {aug_output_path}")
                else:
                    # Mode 0: No augmentation
                    augmented_text = original_text
                    if logs: print(f"Using original query (no augmentation)")

            # 4. Generate the ES Query JSON based on query_type
            if query_type == "exact":
                es_query_dict = qgeneration.generate_exact_match_query(augmented_text)
            elif query_type == "hybrid":
                es_query_dict = qgeneration.generate_hybrid_tiered_query(augmented_text)
            elif query_type == "ngram":
                es_query_dict = qgeneration.generate_ngram_match_query(augmented_text)
            elif query_type == "hybrid_ngram":
                es_query_dict = qgeneration.generate_hybrid_ngram_tiered_query(augmented_text)
            else:
                print(f"Warning: Unknown query_type '{query_type}'. Defaulting to 'hybrid'.")
                es_query_dict = qgeneration.generate_hybrid_tiered_query(augmented_text)

            # 5. Save the JSON query
            json_output_path = save_path / f"{base_name}.json"
            with json_output_path.open('w', encoding='utf-8') as f:
                json.dump(es_query_dict, f, ensure_ascii=False, indent=4)
            if logs: print(f"Saved search query to: {json_output_path}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")


if __name__ == "__main__":
    run_query_creation()
