"""
ai_modules/recommender.py
--------------------------
Core AI recommendation engine.

Approach:
    1. Load the careers dataset (name, required skills, salary, etc.).
    2. Build a TF-IDF vector space over each career's "required_skills" text.
    3. Vectorize the user's own skills + interests text the same way.
    4. Compute cosine similarity between the user vector and every career
       vector to get a 0-1 match score per career.
    5. Return the top-N careers ranked by match percentage, enriched with
       a human-readable "why this suits you" explanation.

This is a lightweight, dependency-friendly implementation of the
"Sentence Transformers / Cosine Similarity" requirement: TF-IDF + cosine
similarity is fast, needs no large model downloads, and is easy to run
locally, while still being genuinely similarity-based AI matching.
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class CareerRecommender:
    def __init__(self, dataset_path: str):
        self.df = pd.read_csv(dataset_path)
        self.df["required_skills"] = self.df["required_skills"].fillna("")
        # Fit one shared TF-IDF vectorizer over all careers' skill text.
        self.vectorizer = TfidfVectorizer(token_pattern=r"[a-zA-Z0-9\+\#\.]+")
        self.career_matrix = self.vectorizer.fit_transform(self.df["required_skills"])

    @staticmethod
    def _normalize_skills(skills_text: str) -> str:
        """Turn a free-text / comma separated skills string into a clean, space-joined string."""
        if not skills_text:
            return ""
        parts = [s.strip().lower() for s in skills_text.replace(";", ",").split(",") if s.strip()]
        return " ".join(parts)

    def recommend(self, user_skills: str, user_interests: str = "", preferred_industry: str = "", top_n: int = 3):
        """
        Return the top_n careers best matching the user's profile.

        Each result dict contains: career_name, match_percentage, salary_range,
        description, future_demand, industry, required_skills, reason.
        """
        combined_text = self._normalize_skills(user_skills) + " " + self._normalize_skills(user_interests)
        combined_text = combined_text.strip() or "general"

        user_vector = self.vectorizer.transform([combined_text])
        similarities = cosine_similarity(user_vector, self.career_matrix).flatten()

        results_df = self.df.copy()
        results_df["similarity"] = similarities

        # Small boost for careers matching the user's preferred industry.
        if preferred_industry:
            industry_lower = preferred_industry.strip().lower()
            results_df["similarity"] += results_df["industry"].str.lower().apply(
                lambda x: 0.05 if industry_lower and industry_lower in x else 0.0
            )

        results_df = results_df.sort_values("similarity", ascending=False).head(top_n)

        user_skill_set = set(self._normalize_skills(user_skills).split())
        recommendations = []
        for rank, (_, row) in enumerate(results_df.iterrows(), start=1):
            required = set(s.strip() for s in row["required_skills"].split(","))
            matched_skills = sorted(required & user_skill_set) if user_skill_set else []
            match_pct = round(min(row["similarity"], 1.0) * 100, 1)

            if matched_skills:
                reason = (
                    f"You already have {len(matched_skills)} relevant skill(s) "
                    f"({', '.join(matched_skills[:5])}) that directly align with this role, "
                    f"and your interests point toward the {row['industry']} industry."
                )
            else:
                reason = (
                    f"This role aligns with your stated interests and career goal in the "
                    f"{row['industry']} industry, and is a strong growth path from your current profile."
                )

            recommendations.append({
                "rank": rank,
                "career_name": row["career_name"],
                "match_percentage": match_pct,
                "salary_range": row["salary_range"],
                "description": row["description"],
                "future_demand": row["future_demand"],
                "industry": row["industry"],
                "required_skills": row["required_skills"],
                "education": row["education"],
                "reason": reason,
            })

        return recommendations

    def get_career_by_name(self, career_name: str):
        """Fetch a single career row (as dict) by exact name match."""
        row = self.df[self.df["career_name"].str.lower() == career_name.strip().lower()]
        if row.empty:
            return None
        return row.iloc[0].to_dict()
