import re
import os
import pandas as pd
from MAIN.Connection.es_conn import get_es_client

def get_url_by_id_strict(indexn: str, id: str) -> str:
    es = get_es_client()
    try:
        response = es.get(index=indexn, id=id)
        return response["_source"]["url"]
    except Exception as e:
        print(f"Error fetching URL for ID {id}: {e}")
        return "N/A"

def parse_result_to_excel(content, save_path, name, logs=True):
    """
    Parses a text file with entries formatted as:
    **ID: ... Name: ... URL: ... expl: ...**
    and saves the extracted data to an Excel file.

    :param content: contents of the response
    :param save_path: Folder where the output .xlsx file will be saved.
    :param name: Name of output .xlsx file to be saved.
    :param logs: If True, prints detailed processing logs.
    """

    # 1. Define Regex Pattern
    # This pattern handles the bold markers (**), spaces, and specifically looks for the keys.
    # It assumes the order is always ID -> Name -> -> expl
    # 'expl' captures everything until the end of the line or the closing '**'
    pattern = r"ID:\s*(?P<id>\S+)\s+Name:\s*(?P<name>.+?)\s+expl:\s*(?P<expl>.+?)(?=\*\*|\n|$)"

    # 2. Find all matches
    matches = re.finditer(pattern, content, flags=re.IGNORECASE)

    data_list = []
    for match in matches:
        entry = {
            "ID": match.group("id").strip(),
            "Name": match.group("name").strip(),
            "URL": get_url_by_id_strict("test3", match.group("id").strip()),
            "Explanation": match.group("expl").strip()
        }
        data_list.append(entry)

    # 3. Prepare Save Path
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    output_excel_path = os.path.join(save_path, f"{name}.xlsx")

    # 4. Create DataFrame and Save
    if not data_list:
        if logs: print(f"No matching data found for {name}. Creating empty Excel file with headers.")
        # Create empty DataFrame with expected columns
        df = pd.DataFrame(columns=["ID", "Name", "URL", "Explanation"])
    else:
        df = pd.DataFrame(data_list)

    try:
        df.to_excel(output_excel_path, index=False)
        if logs: print(f"Successfully saved {len(df)} entries to: {output_excel_path}")
    except Exception as e:
        print(f"Error saving Excel file: {e}")