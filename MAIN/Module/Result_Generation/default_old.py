import os
import re
import json
import pandas as pd
from MAIN.Connection.es_conn import get_es_client

def execute_query(index_name, query_file_path, save_path):
    es = get_es_client()
    """
    Executes an Elasticsearch query from a JSON file and saves results to a txt file.

    :param index_name: The name of the ES evaluation to search.
    :param query_file_path: Path to the JSON file containing the ES query.
    :param save_path: Folder where the output results will be saved.
    """
    # 1. Load the query from the JSON file
    with open(query_file_path, 'r', encoding='utf-8') as f:
        try:
            query_dict = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse JSON query from {query_file_path}: {e}")
            return

    # 2. Run the query on the Elasticsearch evaluation
    try:
        response = es.search(
            index=index_name,
            body=query_dict
        )
        hits = response.get('hits', {}).get('hits', [])
    except Exception as e:
        print(f"Error: Failed to execute search on evaluation '{index_name}': {e}")
        return

    # 3. Prepare the save location
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Use the name of the JSON input for the output txt file
    base_name = os.path.splitext(os.path.basename(query_file_path))[0]
    output_txt_path = os.path.join(save_path, f"{base_name}.txt")

    # 4. Save the results to the txt file
    with open(output_txt_path, 'w', encoding='utf-8') as out_f:
        if not hits:
            out_f.write("No results found for this query.")
        else:
            for hit in hits:
                # Extracting document ID and the source content
                doc_id = hit.get('_id', 'Unknown ID')
                score = hit.get('_score', 0)
                source = hit.get('_source', {})

                out_f.write(f"--- Document ID: {doc_id} (Score: {score}) ---\n")
                # Pretty print the source data including 'augmeta' and 'description'
                out_f.write(json.dumps(source, ensure_ascii=False, indent=2))
                out_f.write("\n\n")

    print(f"Search results successfully saved to: {output_txt_path}")

def export_top_3(txt_file_path, save_path):
    """
        Parses a text file containing ES search results, extracts the ID, Name, and URL
        of the top 3 documents, and saves them as an Excel file.
        """
    # 1. Read the file content
    try:
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {txt_file_path}")
        return

    # 2. Split content by the header pattern
    # UPDATED REGEX: Added parentheses around the score value (.+?) to capture it.
    # This forces re.split to return: [pre_text, ID, Score, JSON_Body, ID, Score, JSON_Body...]
    header_pattern = re.compile(r"--- Document ID: (.+?) \(Score: (.+?)\) ---")
    parts = header_pattern.split(content)

    results = []

    # 3. Iterate through parsed parts to extract Top 3
    # We start at index 1.
    # The structure now repeats every 3 elements:
    # parts[i] = ID
    # parts[i+1] = Score
    # parts[i+2] = JSON Body
    for i in range(1, len(parts), 3):

        # Safety Check: Prevent "list index out of range" if file ends unexpectedly
        if i + 2 >= len(parts):
            break

        if len(results) >= 3:
            break  # Stop once we have 3 valid results

        doc_id = parts[i].strip()
        # score = parts[i+1].strip()  # Score is available here if needed
        json_body = parts[i + 2].strip()

        try:
            # Parse the JSON body
            data = json.loads(json_body)

            # Extract only the requested fields
            entry = {
                "ID": doc_id,
                "Name": data.get("name", "N/A"),
                "URL": data.get("url", "N/A")
            }
            results.append(entry)

        except json.JSONDecodeError:
            # Skip invalid JSON blocks (e.g., empty lines at end of file)
            continue

    # 4. Check if we found data
    if not results:
        print("No valid documents found to export.")
        return

    # 5. Create DataFrame and Save
    df = pd.DataFrame(results)

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    base_name = os.path.splitext(os.path.basename(txt_file_path))[0]
    output_excel_path = os.path.join(save_path, f"{base_name}.xlsx")

    try:
        df.to_excel(output_excel_path, index=False)
        print(f"Successfully saved Top {len(df)} results to: {output_excel_path}")
        print(df)
    except Exception as e:
        print(f"Error saving Excel file: {e}")