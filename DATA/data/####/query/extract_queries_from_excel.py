import os
import pandas as pd

def extract_query_files():
    # Current directory where the script and excel file are located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(current_dir, "queries.xlsx")

    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found.")
        return

    try:
        # Read the Excel file
        # Assuming no header, so column 0 is ID, column 1 is Query content
        df = pd.read_excel(excel_file, header=None)
        
        print(f"Processing {len(df)} rows from {excel_file}...")

        for index, row in df.iterrows():
            # Get the ID (e.g., 1, 2, 3)
            query_id_raw = row[0]
            query_content = row[1]

            # Handle potential NaN or empty values
            if pd.isna(query_id_raw):
                print(f"Skipping row {index}: Empty ID")
                continue
            
            # Convert ID to string and strip whitespace
            query_id = str(query_id_raw).strip()
            
            # Construct filename: Q{id}.txt
            output_filename = f"Q{query_id}.txt"
            output_path = os.path.join(current_dir, output_filename)

            # Ensure query content is a string (handle NaN or numbers)
            if pd.isna(query_content):
                query_text = ""
            else:
                query_text = str(query_content)

            try:
                # Write the query content to the text file
                # Using 'w' mode and utf-8 encoding
                # Newlines in the excel cell are preserved in the string
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(query_text)
                
                # print(f"Created {output_filename}")

            except Exception as e:
                print(f"Error writing file for ID {query_id}: {e}")

        print("Extraction complete.")

    except Exception as e:
        print(f"An error occurred while processing the Excel file: {e}")

if __name__ == "__main__":
    extract_query_files()
