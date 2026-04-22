from elasticsearch import Elasticsearch

def get_es_client():
    es = Elasticsearch(
        "http://localhost:****",#what
        basic_auth=(**,**),
        verify_certs=False,  # only for local testing
        request_timeout=30  # Increase timeout to 30 seconds
    )
    if not es.ping():
        raise RuntimeError("Elasticsearch is not reachable")
    return es