import math

def calculate_metrics(graded_results, total_relevant, k=3):
    """
    Calculates IR metrics for a single query based on graded results.

    :param graded_results: List of integers (1 for correct, 0 for incorrect) representing the ranked results.
    :param total_relevant: The total number of relevant documents existing for this query (ground truth count).
    :param k: The number of top results to consider (default 3).
    :return: A dictionary containing Accuracy (Precision), Recall, F1, RR, DCG, and AP.
    """
    # Filter out empty values (e.g., None, NaN, empty strings)
    # We only want to evaluate actual provided answers
    valid_results = [res for res in graded_results if res in (0, 1)]
    
    # Slice the results to consider only up to top k
    results = valid_results[:k]

    relevant_retrieved = sum(results)
    
    # Number of actually retrieved and valid documents up to k
    num_retrieved = len(results)

    # 1. Accuracy (Precision)
    # Calculated based ONLY on the number of results provided, not k
    precision = relevant_retrieved / num_retrieved if num_retrieved > 0 else 0

    # 2. Recall
    # Calculated based on total_relevant ground truths
    recall = relevant_retrieved / total_relevant if total_relevant > 0 else 0

    # 3. F1 Score
    if (precision + recall) > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0

    # 4. Reciprocal Rank (RR)
    # 1 divided by the rank of the first relevant document.
    rr = 0
    for i, grade in enumerate(results):
        if grade == 1:
            rr = 1 / (i + 1)
            break

    # 5. Discounted Cumulative Gain (DCG)
    # Sum of (rel_i / log2(rank_i + 1))
    dcg = 0
    for i, grade in enumerate(results):
        rank = i + 1
        # Using binary relevance (0 or 1)
        dcg += grade / math.log2(rank + 1)

    # 6. Average Precision (AP)
    # Average of Precision@i for every rank i where a relevant document was retrieved.
    # Divided by the total number of relevant documents.
    sum_precision = 0
    running_relevant_count = 0
    
    for i, grade in enumerate(results):
        if grade == 1:
            running_relevant_count += 1
            precision_at_i = running_relevant_count / (i + 1)
            sum_precision += precision_at_i
            
    ap = sum_precision / total_relevant if total_relevant > 0 else 0

    return {
        "Accuracy": precision,
        "Recall": recall,
        "F1": f1,
        "RR": rr,
        "DCG": dcg,
        "AP": ap
    }