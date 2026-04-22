import json
from MAIN.Connection.es_conn import get_es_client

def setup_index(index_name, recreate_index=False):
    """
    Handles the creation or recreation of an Elasticsearch index.
    """
    es = get_es_client()
    if es.indices.exists(index=index_name):
        if recreate_index:
            es.indices.delete(index=index_name)
            print(f"Deleted existing index: {index_name}")
            es.indices.create(index=index_name)
            print(f"Created fresh index: {index_name}")
        else:
            print(f"Index {index_name} already exists. Proceeding with updates/additions.")
    else:
        es.indices.create(index=index_name)
        print(f"Created new index: {index_name}")

def index_document(index_name, doc_id, data, logs=True):
    """
    Indexes a single document into Elasticsearch.

    :param index_name: Name of the target Elasticsearch index.
    :param doc_id: The ID for the document.
    :param data: The dictionary containing document data.
    :param logs: If True, prints success message.
    """
    es = get_es_client()
    try:
        es.index(
            index=index_name,
            id=doc_id,
            document=data
        )
        if logs: print(f"Indexed document ID: {doc_id}")
    except Exception as e:
        print(f"Failed to index document {doc_id}: {str(e)}")
