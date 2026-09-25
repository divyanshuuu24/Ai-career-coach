"""
ai_modules/skill_gap.py
------------------------
Compares a user's current skills against the skills required for a
target career, and enriches each missing skill with priority,
suggested certification, and a suggested mini-project using the
skills_certifications.csv reference dataset.
"""

import pandas as pd


class SkillGapAnalyzer:
    def __init__(self, skills_dataset_path: str):
        self.skills_df = pd.read_csv(skills_dataset_path)
        self.skills_df["skill"] = self.skills_df["skill"].str.lower().str.strip()

    @staticmethod
    def _clean_list(text: str):
        if not text:
            return []
        return sorted(set(s.strip().lower() for s in text.replace(";", ",").split(",") if s.strip()))

    def analyze(self, user_skills: str, required_skills: str):
        """
        Returns a dict with:
            existing_skills  : skills the user already has that the role needs
            missing_skills    : list of dicts (skill, priority, certification, project)
            coverage_percent  : % of required skills already possessed
        """
        user_set = set(self._clean_list(user_skills))
        required_set = set(self._clean_list(required_skills))

        existing = sorted(required_set & user_set)
        missing = sorted(required_set - user_set)

        enriched_missing = []
        for skill in missing:
            ref = self.skills_df[self.skills_df["skill"] == skill]
            if not ref.empty:
                row = ref.iloc[0]
                enriched_missing.append({
                    "skill": skill,
                    "priority": row["priority"],
                    "certification": row["certification"],
                    "project": row["project_idea"],
                })
            else:
                enriched_missing.append({
                    "skill": skill,
                    "priority": "Medium",
                    "certification": f"Search for a reputable online course in {skill.title()}",
                    "project": f"Build a small project applying {skill.title()}",
                })

        # Sort missing skills so High priority appears first.
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        enriched_missing.sort(key=lambda x: priority_order.get(x["priority"], 1))

        coverage_percent = round((len(existing) / len(required_set)) * 100, 1) if required_set else 0.0

        return {
            "existing_skills": existing,
            "missing_skills": enriched_missing,
            "coverage_percent": coverage_percent,
        }
