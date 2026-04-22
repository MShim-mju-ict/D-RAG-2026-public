import json

# --- GLOBAL DEFAULTS ---
# Abstracted out to prevent hardcoding inside every function.
DEFAULT_FIELDS = ["name", "alternateName", "description", "keywords", "augmeta"]
DEFAULT_SOURCE = ["name", "alternateName", "description", "keywords"]
DEFAULT_SIZE = 10


# --- HELPER FUNCTIONS ---
def _parse_query_text(query_text):
    """Helper to parse raw query text into rows of cleaned keywords."""
    rows = []
    if not query_text:
        return rows

    for line in query_text.strip().split('\n'):
        keywords = [k.strip() for k in line.split(',') if k.strip()]
        if keywords:
            rows.append(keywords)
    return rows


def _create_standard_clauses(keywords, fields):
    """Helper to create standard multi_match clauses for basic matching."""
    return [{"multi_match": {"query": kw, "fields": fields}} for kw in keywords]


def _create_phrase_clauses(keywords, fields):
    """Helper to create phrase match clauses. Replaces problematic wildcards."""
    clauses = []
    for kw in keywords:
        if len(kw) < 2:
            clauses.append({"multi_match": {"query": kw, "fields": fields}})
        else:
            clauses.append({"multi_match": {"query": kw, "fields": fields, "type": "phrase"}})
    return clauses


# --- 1. STANDARD MATCH (ALL ROWS REQUIRED) ---
def generate_exact_match_query(query_text, target_fields=None, size=None):
    """
    Generates an ES query where ALL rows must have at least one keyword match (AND logic).
    (Note: Uses standard multi_match, utilizing the analyzer rather than strict exact term matching).
    """
    fields = target_fields if target_fields is not None else DEFAULT_FIELDS
    sz = size if size is not None else DEFAULT_SIZE

    rows_of_keywords = _parse_query_text(query_text)
    if not rows_of_keywords:
        return {"query": {"match_all": {}}}

    must_clauses = []
    for keywords in rows_of_keywords:
        row_should = _create_standard_clauses(keywords, fields)
        must_clauses.append({"bool": {"should": row_should, "minimum_should_match": 1}})

    return {
        "size": sz,
        "_source": DEFAULT_SOURCE,
        "query": {"bool": {"must": must_clauses}}
    }


# --- 2. HYBRID MATCH (TIER 1 STRICT, TIER 2 LOOSE) ---
def generate_hybrid_tiered_query(query_text, target_fields=None, size=None):
    """
    Generates a 2-tiered ES query:
    1. Tier 1 (Must match ANY from EVERY row) - Boosted
    2. Tier 2 (Must match ANY from ANY row) - Standard
    """
    fields = target_fields if target_fields is not None else DEFAULT_FIELDS
    sz = size if size is not None else DEFAULT_SIZE

    rows_of_keywords = _parse_query_text(query_text)
    if not rows_of_keywords:
        return {"query": {"match_all": {}}}

    must_clauses = []
    should_clauses = []

    for keywords in rows_of_keywords:
        row_should = _create_standard_clauses(keywords, fields)
        must_clauses.append({"bool": {"should": row_should, "minimum_should_match": 1}})
        should_clauses.extend(row_should)

    return {
        "size": sz,
        "_source": DEFAULT_SOURCE,
        "query": {
            "bool": {
                "should": [
                    {"bool": {"must": must_clauses, "boost": 10.0}},
                    {"bool": {"should": should_clauses, "minimum_should_match": 1, "boost": 1.0}}
                ],
                "minimum_should_match": 1
            }
        }
    }


# --- 3. PHRASE MATCH (ALL ROWS REQUIRED) ---
def generate_ngram_match_query(query_text, target_fields=None, size=None):
    """
    Generates an ES query where ALL rows must have at least one keyword match (AND logic).
    (Note: Replaced N-gram wildcards with `phrase` matching for correct Korean tokenization).
    """
    fields = target_fields if target_fields is not None else DEFAULT_FIELDS
    sz = size if size is not None else DEFAULT_SIZE

    rows_of_keywords = _parse_query_text(query_text)
    if not rows_of_keywords:
        return {"query": {"match_all": {}}}

    must_clauses = []
    for keywords in rows_of_keywords:
        row_should = _create_phrase_clauses(keywords, fields)
        must_clauses.append({"bool": {"should": row_should, "minimum_should_match": 1}})

    return {
        "size": sz,
        "_source": DEFAULT_SOURCE,
        "query": {"bool": {"must": must_clauses}}
    }


# --- 4. HYBRID PHRASE MATCH (TIER 1 STRICT, TIER 2 LOOSE) ---
def generate_hybrid_ngram_tiered_query(query_text, target_fields=None, size=None):
    """
    Generates a 2-tiered ES query utilizing phrase matching for robust token handling.
    1. Tier 1 (Must match ANY from EVERY row) - Boosted
    2. Tier 2 (Must match ANY from ANY row) - Standard
    """
    fields = target_fields if target_fields is not None else DEFAULT_FIELDS
    sz = size if size is not None else DEFAULT_SIZE

    rows_of_keywords = _parse_query_text(query_text)
    if not rows_of_keywords:
        return {"query": {"match_all": {}}}

    must_clauses = []
    should_clauses = []

    for keywords in rows_of_keywords:
        row_clauses = _create_phrase_clauses(keywords, fields)
        must_clauses.append({"bool": {"should": row_clauses, "minimum_should_match": 1}})
        should_clauses.extend(row_clauses)

    return {
        "size": sz,
        "_source": DEFAULT_SOURCE,
        "query": {
            "bool": {
                "should": [
                    {"bool": {"must": must_clauses, "boost": 10.0}},
                    {"bool": {"should": should_clauses, "minimum_should_match": 1, "boost": 1.0}}
                ],
                "minimum_should_match": 1
            }
        }
    }