import os
import pandas as pd
import json

def extract_json_files():
    # Current directory where the script and excel file are located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(current_dir, "json.xlsx")

    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found.")
        return

    try:
        # Read the Excel file
        # Assuming no header, so column 0 is ID, column 1 is JSON content
        # If there is a header, change header=None to header=0
        df = pd.read_excel(excel_file, header=None)
        
        print(f"Processing {len(df)} rows from {excel_file}...")

        for index, row in df.iterrows():
            file_id = str(row[0]).strip()
            json_content = row[1]

            # Ensure the ID is valid for a filename
            if not file_id:
                print(f"Skipping row {index}: Empty ID")
                continue

            # Parse JSON content to ensure it's valid and formatted nicely
            try:
                if isinstance(json_content, str):
                    # Attempt to clean control characters if standard parsing fails
                    # strict=False allows control characters inside strings
                    json_data = json.loads(json_content, strict=False)
                else:
                    # If pandas already parsed it as a dict/list (unlikely for raw cell text but possible)
                    json_data = json_content
                
                output_filename = f"{file_id}.json"
                output_path = os.path.join(current_dir, output_filename)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                
                # print(f"Created {output_filename}")

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON for ID {file_id}: {e}")
                # Fallback: Try manual cleaning of common control characters
                try:
                    cleaned_content = "".join(c for c in json_content if c >= ' ' or c == '\n' or c == '\r' or c == '\t')
                    json_data = json.loads(cleaned_content, strict=False)
                    
                    output_filename = f"{file_id}.json"
                    output_path = os.path.join(current_dir, output_filename)

                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=4)
                    print(f"Recovered ID {file_id} after cleaning control characters.")
                except Exception as e2:
                    print(f"Failed to recover ID {file_id}: {e2}")

            except Exception as e:
                print(f"Error writing file for ID {file_id}: {e}")

        print("Extraction complete.")

    except Exception as e:
        print(f"An error occurred while processing the Excel file: {e}")

if __name__ == "__main__":
    extract_json_files()
