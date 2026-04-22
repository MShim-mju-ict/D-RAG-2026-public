import os
import json


def generate_ESQ1(file_path, save_path=""):
    """
    Generates an ES query that matches keywords across multiple document fields.

    :param file_path: Path to the .txt file with rows of keywords.
    :param save_path: Folder to save the resulting JSON query.
    """
    # Define the target columns
    target_fields = ["name", "alternateName", "description", "keywords", "augmeta"]
    must_clauses = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Split keywords by comma and clean whitespace
            keywords = [k.strip() for k in line.split(',') if k.strip()]

            if not keywords:
                continue

            # Inner 'should' (OR) logic for the row
            should_clauses = []
            for kw in keywords:
                # Use multi_match to search across all specified columns
                should_clauses.append({
                    "multi_match": {
                        "query": kw,
                        "fields": target_fields
                    }
                })

            # Add to the outer 'must' (AND) logic
            must_clauses.append({
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            })

    # Final Query Structure
    es_query = {
        "query": {
            "bool": {
                "must": must_clauses
            }
        }
    }

    query_json_str = json.dumps(es_query, ensure_ascii=False, indent=4)

    # Save logic
    if save_path:
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        full_save_path = os.path.join(save_path, f"{base_name}.json")

        with open(full_save_path, 'w', encoding='utf-8') as out_f:
            out_f.write(query_json_str)
        print(f"Multi-field query saved to: {full_save_path}")

    return query_json_str


def generate_ESQ2(file_path, save_path=""):
    """
    Generates an ES query where matching more rows results in a higher score.
    A full match (all rows) will naturally outscore partial matches.
    """
    target_fields = ["name", "alternateName", "description", "keywords", "augmeta"]
    row_clauses = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            keywords = [k.strip() for k in line.split(',') if k.strip()]
            if not keywords:
                continue

            # Each row is an OR group (should) across multiple fields
            row_should_clauses = []
            for kw in keywords:
                row_should_clauses.append({
                    "multi_match": {
                        "query": kw,
                        "fields": target_fields
                    }
                })

            # Wrap each row in its own bool-should so it acts as a single "unit" of matching
            row_clauses.append({
                "bool": {
                    "should": row_should_clauses,
                    "minimum_should_match": 1
                }
            })

    # The final query puts all row-units into a 'should' array.
    # Scoring:
    # - Match 1 row = base score
    # - Match 2 rows = higher score
    # - Match ALL rows = highest score
    es_query = {
        "query": {
            "bool": {
                "should": row_clauses
            }
        }
    }

    query_json_str = json.dumps(es_query, ensure_ascii=False, indent=4)

    # Save logic
    if save_path:
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_file = os.path.join(save_path, f"{base_name}.json")

        with open(output_file, 'w', encoding='utf-8') as out_f:
            out_f.write(query_json_str)
        print(f"Tiered scoring query saved to: {output_file}")

    return query_json_str