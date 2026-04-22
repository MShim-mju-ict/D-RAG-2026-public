from MAIN.Connection.es_conn import get_es_client
import json

def count_documents():
    """
    Counts and prints the total number of documents in the specified Elasticsearch index.
    """
    indexn = "test3"  # Hardcoded index name
    
    try:
        es = get_es_client()
        
        # Check if index exists first
        if not es.indices.exists(index=indexn):
            print(f"Index '{indexn}' does not exist.")
            return

        # Perform the count request
        # body={"query": {"match_all": {}}} is optional as count matches all by default if no query provided,
        # but good for clarity.
        response = es.count(index=indexn)
        
        count = response['count']
        print(f"Total documents in index '{indexn}': {count}")
        
    except Exception as e:
        print(f"Error counting documents in index '{indexn}': {e}")

def print_all_documents():
    """
    Retrieves and prints all documents in the specified Elasticsearch index.
    """
    indexn = "test3"  # Hardcoded index name
    
    try:
        es = get_es_client()
        
        if not es.indices.exists(index=indexn):
            print(f"Index '{indexn}' does not exist.")
            return

        response = es.search(
            index=indexn,
            query={"match_all": {}},
            size=1000  # Adjust size as needed, up to 10000 normally
        )
        
        hits = response['hits']['hits']
        total_hits = response['hits']['total']['value']
        
        print(f"Found {total_hits} documents in index '{indexn}'.")
        print("-" * 50)
        
        for hit in hits:
            doc_id = hit['_id']
            source = hit['_source']
            print(f"Document ID: {doc_id}")
            print(f"Content:\n{json.dumps(source, indent=4, ensure_ascii=False)}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error retrieving documents from index '{indexn}': {e}")

if __name__ == "__main__":
    print_all_documents()
    count_documents()
