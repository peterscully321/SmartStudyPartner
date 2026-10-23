"""Run a small, reproducible category-ranking diagnostic on the sample catalog."""

import random

from recommender import StudyRecommender


def run_evaluation(sample_size=50, top_n=5, seed=42):
    recommender = StudyRecommender()
    sample_count = min(sample_size, len(recommender.df))
    if sample_count == 0:
        print("No catalog rows are available to evaluate.")
        return

    samples = recommender.df.sample(n=sample_count, random_state=seed)
    rng = random.Random(seed)
    relevant_at_k = 0
    query_hits = 0
    evaluated_recommendations = 0

    for _, row in samples.iterrows():
        tags = [tag.strip() for tag in row["Tags"].split(",") if tag.strip()]
        query = " ".join(rng.sample(tags, min(3, len(tags)))) if tags else row["Title"]
        recommendations = recommender.recommend(query, top_n=top_n)
        category_matches = sum(rec["Category"] == row["Category"] for rec in recommendations)
        relevant_at_k += category_matches
        evaluated_recommendations += top_n
        query_hits += category_matches > 0

    precision_at_k = relevant_at_k / evaluated_recommendations if evaluated_recommendations else 0.0
    category_hit_rate = query_hits / sample_count

    print("=" * 56)
    print("SAMPLE CATALOG CATEGORY-RANKING DIAGNOSTIC")
    print("=" * 56)
    print(f"Queries sampled: {sample_count}")
    print(f"Recommendations per query: {top_n}")
    print(f"Category precision@{top_n}: {precision_at_k:.1%}")
    print(f"Category hit rate@{top_n}: {category_hit_rate:.1%}")
    print("These are diagnostic metrics on generated sample data, not a user study or validated quality score.")


if __name__ == "__main__":
    run_evaluation()
