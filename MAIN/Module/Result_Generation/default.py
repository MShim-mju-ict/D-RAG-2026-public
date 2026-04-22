import os
import json
import pandas as pd
from MAIN.Connection.es_conn import get_es_client

def execute_query_to_excel(index_name, query_content, output_filename, save_path, logs=True):
    """
    Executes an Elasticsearch query from a JSON string and saves results to an Excel file.

    :param index_name: The name of the ES index to search.
    :param query_content: The JSON string content of the query.
    :param output_filename: The name of the output file (without extension).
    :param save_path: Folder where the output Excel file will be saved.
    :param logs: If True, prints detailed processing logs.
    """
    es = get_es_client()

    # 1. Parse the query string
    try:
        query_dict = json.loads(query_content)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse query content for {output_filename}: {e}")
        return

    # 2. Run the query on the Elasticsearch index
    try:
        response = es.search(
            index=index_name,
            body=query_dict
        )
        hits = response.get('hits', {}).get('hits', [])
    except Exception as e:
        print(f"Error: Failed to execute search on index '{index_name}': {e}")
        return

    # 3. Prepare the save location
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    output_excel_path = os.path.join(save_path, f"{output_filename}.xlsx")
    output_txt_path = os.path.join(save_path, f"{output_filename}.txt")


    # 4. Process the results into a list of dictionaries
    results_data = []
    if not hits:
        if logs: print(f"No results found for query: {output_filename}")
    else:
        for hit in hits:
            doc_id = hit.get('_id', 'Unknown ID')
            score = hit.get('_score', 0)
            source = hit.get('_source', {})
            
            results_data.append({
                'ID': doc_id,
                'Score': score,
                'Source': json.dumps(source, ensure_ascii=False) # Store source as a JSON string
            })

    # 5-1. Create a DataFrame and save to Excel
    if results_data:
        df = pd.DataFrame(results_data)
        try:
            df.to_excel(output_excel_path, index=False)
            if logs: print(f"Search results successfully saved to: {output_excel_path}")
        except Exception as e:
            print(f"Error saving Excel file: {e}")
    else:
        # Create an empty excel file with the correct columns if no results
        empty_df = pd.DataFrame(columns=['ID', 'Score', 'Source'])
        try:
            empty_df.to_excel(output_excel_path, index=False)
            if logs: print(f"No results found. Empty Excel file with headers created at: {output_excel_path}")
        except Exception as e:
            print(f"Error saving empty Excel file: {e}")

    # 5-2. Also Save the results to the txt file
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
