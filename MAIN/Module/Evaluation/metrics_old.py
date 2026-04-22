import pandas as pd
import numpy as np


def calculate_ir_metrics(evaluated_df):
    """
    Calculates MRR, MAP, and nDCG based on the evaluation DataFrame.
    Assumes rows are ordered by rank (Top 1, Top 2...) within each targetQ.

    :param evaluated_df: DataFrame containing 'targetQ' and 'eval' (1 or 0) columns.
    :return: A tuple (metrics_per_query_df, summary_dict)
    """
    if evaluated_df.empty:
        print("DataFrame is empty. Cannot calculate metrics.")
        return None, None

    metrics_list = []

    # Group by Query to calculate metrics for each search session
    # sort=False ensures we process groups in the order they appear, though not strictly necessary for logic
    grouped = evaluated_df.groupby('targetQ', sort=False)

    for query, group in grouped:
        # Extract the binary relevance scores (1 for match, 0 for miss)
        # We assume the order of rows in 'group' corresponds to Rank 1, Rank 2, etc.
        relevance = group['eval'].values
        k = len(relevance)  # Total items retrieved (e.g., 3)

        # --- 1. MRR (Mean Reciprocal Rank) ---
        # Reciprocal Rank = 1 / Rank of the FIRST relevant item
        try:
            # np.where returns indices where condition is true. [0][0] gets the first index.
            first_relevant_rank_idx = np.where(relevance == 1)[0][0]
            # Rank is index + 1
            rr = 1 / (first_relevant_rank_idx + 1)
        except IndexError:
            # No relevant documents found
            rr = 0.0

        # --- 2. MAP (Mean Average Precision) ---
        # Average of Precision@K for every K where a relevant document was retrieved
        precisions = []
        relevant_count = 0

        for i, is_rel in enumerate(relevance):
            if is_rel == 1:
                relevant_count += 1
                rank = i + 1
                # Precision at this rank = (count of relevant so far) / (current rank)
                precisions.append(relevant_count / rank)

        # If no relevant docs, AP is 0. Otherwise, mean of the collected precisions.
        ap = np.mean(precisions) if precisions else 0.0

        # --- 3. nDCG (Normalized Discounted Cumulative Gain) ---
        # DCG = sum( rel_i / log2(rank_i + 1) )
        ranks = np.arange(1, k + 1)
        discounts = np.log2(ranks + 1)

        dcg = np.sum(relevance / discounts)

        # IDCG (Ideal DCG) = DCG of the relevance list sorted descending (all 1s at top)
        ideal_relevance = sorted(relevance, reverse=True)
        idcg = np.sum(ideal_relevance / discounts)

        ndcg = dcg / idcg if idcg > 0 else 0.0

        metrics_list.append({
            'targetQ': query,
            'MRR': rr,
            'AP': ap,
            'nDCG': ndcg
        })

    # Create a DataFrame for per-query metrics
    metrics_df = pd.DataFrame(metrics_list)

    # Calculate global averages (Mean across all queries)
    summary = {
        'Mean_MRR': metrics_df['MRR'].mean(),
        'MAP': metrics_df['AP'].mean(),  # Mean of AP is MAP
        'Mean_nDCG': metrics_df['nDCG'].mean()
    }

    print("--- Metrics Summary ---")
    for k, v in summary.items():
        print(f"{k}: {v:.4f}")

    return metrics_df, summary


def calculate_ir_metrics2(evaluated_df, global_truth_counts):
    """
    Calculates MRR, MAP, nDCG, and Recall using the Global Truth counts.
    """
    if evaluated_df.empty:
        print("DataFrame is empty.")
        return None, None

    metrics_list = []
    grouped = evaluated_df.groupby('targetQ', sort=False)

    for query, group in grouped:
        relevance = group['eval'].values  # List of 1s and 0s (e.g., [1, 0, 1])
        k = len(relevance)  # Number of docs retrieved (e.g., 3)

        # Get the Total Number of Relevant Docs existing in the universe (Answer Sheet)
        total_relevant = global_truth_counts.get(query, 0)

        # Handle case where a query exists in results but has NO correct answers in Answer Sheet
        if total_relevant == 0:
            metrics_list.append({
                'targetQ': query, 'Recall': 0, 'MRR': 0, 'AP': 0, 'nDCG': 0
            })
            continue

        # --- 1. Recall ---
        # (Relevant Retrieved) / (Total Relevant Global)
        relevant_retrieved = np.sum(relevance)
        recall = relevant_retrieved / total_relevant

        # --- 2. MRR ---
        try:
            first_relevant_idx = np.where(relevance == 1)[0][0]
            mrr = 1 / (first_relevant_idx + 1)
        except IndexError:
            mrr = 0.0

        # --- 3. MAP (Standard Definition) ---
        # AP = Sum(Precision@k for relevant items) / Total_Global_Relevant
        precisions = []
        rel_count_so_far = 0
        for i, is_rel in enumerate(relevance):
            if is_rel == 1:
                rel_count_so_far += 1
                precisions.append(rel_count_so_far / (i + 1))

        # Standard AP divides by the Total Relevant Documents, not just retrieved ones
        ap = np.sum(precisions) / total_relevant

        # --- 4. nDCG ---
        # DCG
        ranks = np.arange(1, k + 1)
        discounts = np.log2(ranks + 1)
        dcg = np.sum(relevance / discounts)

        # IDCG (Ideal DCG)
        # Ideally, we would have 'total_relevant' 1s at the top.
        # But we only have K slots in our result list.
        # So the Ideal list is min(K, total_relevant) ones followed by zeros.
        num_ideal_ones = min(k, total_relevant)
        ideal_relevance = np.array([1] * num_ideal_ones + [0] * (k - num_ideal_ones))

        # Calculate IDCG for those top K slots
        idcg = np.sum(ideal_relevance / discounts)

        ndcg = dcg / idcg if idcg > 0 else 0.0

        metrics_list.append({
            'targetQ': query,
            'Recall': recall,
            'MRR': mrr,
            'AP': ap,
            'nDCG': ndcg
        })

    # Summary
    metrics_df = pd.DataFrame(metrics_list)
    summary = {
        'Mean_Recall': metrics_df['Recall'].mean(),
        'Mean_MRR': metrics_df['MRR'].mean(),
        'MAP': metrics_df['AP'].mean(),
        'Mean_nDCG': metrics_df['nDCG'].mean()
    }

    print("--- Advanced Metrics Summary ---")
    for k, v in summary.items():
        print(f"{k}: {v:.4f}")

    return metrics_df, summary

# Usage:
# df, truth_counts = evaluate_with_global_truth('answer.xlsx', 'results_folder')
# if df is not None:
#     per_query, summary = calculate_advanced_metrics(df, truth_counts)