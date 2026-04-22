import json
from pathlib import Path
from elasticsearch.dsl import Boolean
import time
from MAIN.Connection.es_conn import get_es_client

from MAIN.Module.Index_Creation import default, augment
from MAIN.Module.Util.find_files import find_files_by_extension

def run_index_creation(recreate_index:Boolean = True, baseline:int = 0, subpath:str = "default", logs:bool = True):
    """
    :param recreate_index: default True. replaces the index with a new index.
    :param baseline: 
        0: No augmentation (Index original data).
        1: Use existing augmented data from save_path.
        2: Perform augmentation (and save).
    :param subpath: The subdirectory path (e.g., "sample" or "0126/sample") to append to the base data path.
    :param logs: If True, prints detailed processing logs.
    """
    print(f"Running Index creation process... (Baseline={baseline}, Subpath={subpath})")
    
    base_data_path = Path("/Users/moonshim/PycharmProjects/D-RAG/DATA/data")
    folder = base_data_path / subpath / "json"
    save_path = base_data_path / subpath / "meta-aug"
    indexn = "test3"

    # 1. Setup the index (create or recreate)
    default.setup_index(indexn, recreate_index)

    # 2. Prepare Save Path if needed
    if save_path and not save_path.exists():
        save_path.mkdir(parents=True, exist_ok=True)
        if logs: print(f"Created save directory: {save_path}")

    # 3. Find all JSON files using the utility function
    if folder.exists():
        json_files = find_files_by_extension(str(folder), "json")
        
        for file_path_str in json_files:
            file_path = Path(file_path_str)
            filename = file_path.name
            doc_id = file_path.stem

            try:
                # Determine which data to index based on baseline mode
                if baseline == 1:
                    # Mode 1: Use existing augmented data
                    augmented_file_path = save_path / filename
                    if augmented_file_path.exists():
                        with augmented_file_path.open('r', encoding='utf-8') as f:
                            augmented_data = json.load(f)
                        if logs: print(f"Loaded existing augmented file: {filename}")
                    else:
                        print(f"Warning: Augmented file not found for {filename}. Falling back to original.")
                        with file_path.open('r', encoding='utf-8') as f:
                            augmented_data = json.load(f)
                else:
                    # Mode 0 or 2: Read original file first
                    with file_path.open('r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if baseline == 2:
                        # Mode 2: Perform augmentation
                        if logs: print(f"Augmenting document: {filename}")
                        augmented_data = augment.augment_document(data)
                        
                        # Save the augmented data
                        if save_path:
                            output_file_path = save_path / filename
                            with output_file_path.open('w', encoding='utf-8') as out_f:
                                json.dump(augmented_data, out_f, ensure_ascii=False, indent=4)
                            if logs: print(f"Saved augmented file: {filename}")
                    else:
                        # Mode 0: No augmentation
                        augmented_data = data
                        if logs: print(f"Using original data (no augmentation): {filename}")

                # 5. Index the document
                default.index_document(indexn, doc_id, augmented_data, logs=logs)

            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON in file {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                
        # Force a refresh of the Elasticsearch index so the new documents are searchable immediately
        try:
            es = get_es_client()
            es.indices.refresh(index=indexn)
            if logs: print(f"Successfully refreshed index {indexn}")
        except Exception as e:
            print(f"Failed to refresh index {indexn}: {e}")
            
    else:
        print(f"Error: Input folder not found at {folder}")

if __name__ == "__main__":
    run_index_creation()