"""Content-based ranking for the Smart Study Partner demo catalog."""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


REQUIRED_COLUMNS = (
    "Resource_ID",
    "Title",
    "Category",
    "Description",
    "Level",
    "Format",
    "Tags",
)


class StudyRecommender:
    def __init__(self, data_path=None):
        path = Path(data_path) if data_path is not None else Path(__file__).with_name("study_resources.csv")
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path
        self.data_path = path
        self.df = None
        self.tfidf_matrix = None
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.load_data()

    def load_data(self):
        if not self.data_path.is_file():
            raise FileNotFoundError(
                f"Resource catalog not found at {self.data_path}. "
                "Restore study_resources.csv or run generate_data.py."
            )

        try:
            df = pd.read_csv(self.data_path, dtype=str).fillna("")
        except pd.errors.EmptyDataError as exc:
            raise ValueError("Resource catalog is empty.") from exc
        except pd.errors.ParserError as exc:
            raise ValueError("Resource catalog is not a valid CSV file.") from exc
        missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
        if missing:
            raise ValueError("Resource catalog is missing required columns: " + ", ".join(missing))
        if df.empty:
            raise ValueError("Resource catalog has no rows.")

        # Keep only fields used by the app and tolerate blank cells in edited CSVs.
        self.df = df.loc[:, REQUIRED_COLUMNS].copy()
        self.df["Content"] = self.df[["Title", "Category", "Description", "Tags"]].agg(" ".join, axis=1)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df["Content"])

    def recommend(self, query, top_n=5, category_filter=None, level_filter=None, format_filter=None):
        if self.df is None or self.tfidf_matrix is None:
            return []

        query = str(query or "").strip()
        if not query:
            return []
        try:
            top_n = int(top_n)
        except (TypeError, ValueError):
            return []
        if top_n < 1:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).ravel()
        # Stable sorting keeps the CSV order for equal scores and makes results repeatable.
        ranked_indices = np.argsort(-scores, kind="stable")

        results = []
        for idx in ranked_indices:
            row = self.df.iloc[idx]
            if category_filter and row["Category"] != category_filter:
                continue
            if level_filter and row["Level"] != level_filter:
                continue
            if format_filter and row["Format"] != format_filter:
                continue
            if scores[idx] <= 0:
                continue

            results.append(
                {
                    "Resource_ID": row["Resource_ID"],
                    "Title": row["Title"],
                    "Category": row["Category"],
                    "Description": row["Description"],
                    "Level": row["Level"],
                    "Format": row["Format"],
                    "Tags": row["Tags"],
                    "SimilarityScore": round(float(scores[idx]), 4),
                }
            )
            if len(results) >= top_n:
                break

        return results

    def get_categories(self):
        return sorted(self.df["Category"].dropna().unique().tolist()) if self.df is not None else []

    def get_levels(self):
        return sorted(value for value in self.df["Level"].dropna().unique().tolist() if value) if self.df is not None else []

    def get_formats(self):
        return sorted(value for value in self.df["Format"].dropna().unique().tolist() if value) if self.df is not None else []
