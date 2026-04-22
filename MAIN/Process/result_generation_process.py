from pathlib import Path
from MAIN.Module.Result_Generation import default, result_gen
from MAIN.Module.Util.find_files import find_files_by_extension
from MAIN.Module.Util.parse_response import parse_result_to_excel
from MAIN.Module.Util.save_as_file import save_string_to_txt


def run_result_generation(baseline:int = 2, subpath:str = "default", logs:bool = True):
    """
    :param baseline: 
        0: No augmentation (Use raw search results).
        2: Perform augmentation (and save).
    :param subpath: The subdirectory path to append to the base data path.
    :param logs: If True, prints detailed processing logs.
    """
    print(f"Running result generation process... (Baseline={baseline}, Subpath={subpath})")
    index_name = "test3"
    
    base_data_path = Path("/Users/moonshim/PycharmProjects/D-RAG/DATA/data")
    squery_folder_path = base_data_path / subpath / "search-query"
    query_folder_path = base_data_path / subpath / "query"
    save_path1 = base_data_path / subpath / "search_result"
    save_path2 = base_data_path / subpath / "final_result"

    # 1. Find all .json files in the query folder
    if squery_folder_path.exists():
        json_files = find_files_by_extension(str(squery_folder_path), "json")
    else:
        print(f"Error: Query folder not found at {squery_folder_path}")
        raise Exception("Search Query folder unavailable")

    for file_path_str in json_files:
        file_path = Path(file_path_str)
        filename = file_path.name
        query_id = file_path.stem

        if logs: print(f"Processing: {filename}")

        # 2. Read the file content here (Processor layer)
        try:
            with file_path.open('r', encoding='utf-8') as f:
                query_content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            continue

        # 3. Pass the content string to the Module layer
        default.execute_query_to_excel(index_name, query_content, query_id, str(save_path1), logs=logs)

        # 4. Result Augmentation
        if baseline == 0:
            if logs: print(f"Mode 0: Skipping augmentation for {query_id}")
            
            sresult_xlsx_path = save_path1 / f"{query_id}.xlsx"
            final_xlsx_path = save_path2 / f"{query_id}.xlsx"
            
            if not save_path2.exists():
                save_path2.mkdir(parents=True, exist_ok=True)

            # Copy the raw excel result to final result folder
            if sresult_xlsx_path.exists():
                import shutil
                shutil.copy(sresult_xlsx_path, final_xlsx_path)
                if logs: print(f"Copied raw result to: {final_xlsx_path}")
            else:
                print(f"Warning: Raw result Excel not found at {sresult_xlsx_path}")
            
            continue

        # Mode 2: Perform Augmentation
        uq_path = query_folder_path / f"{query_id}.txt"
        sresult_path = save_path1 / f"{query_id}.txt"

        try:
            with uq_path.open('r', encoding='utf-8') as f:
                query_content = f.read()
        except Exception as e:
            print(f"Error reading file {uq_path}: {e}")
            continue

        try:
            with sresult_path.open('r', encoding='utf-8') as f:
                result_content = f.read()
        except Exception as e:
            print(f"Error reading file {sresult_path}: {e}")
            continue

        # fin = result_gen.result_aug1(query_content,result_content, logs=logs)
        fin = result_gen.result_aug2(query_content, result_content, logs=logs)


        save_string_to_txt(query_id, str(save_path2), fin, logs=logs)
        parse_result_to_excel(fin, str(save_path2), query_id, logs=logs)


if __name__ == "__main__":
    run_result_generation()
