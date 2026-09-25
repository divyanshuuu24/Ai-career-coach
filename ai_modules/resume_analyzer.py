"""
ai_modules/resume_analyzer.py
-------------------------------
Extracts text from an uploaded PDF resume, detects technical skills
present in it, scores the resume against best-practice heuristics, and
recommends suitable job roles using the CareerRecommender engine.
"""

import re
import pdfplumber


# Master list of skills the analyzer scans for (kept in sync with the
# careers dataset vocabulary so detected skills are meaningful).
MASTER_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql", "html", "css",
    "react", "node.js", "flask", "django", "machine learning", "deep learning",
    "tensorflow", "pytorch", "pandas", "numpy", "data visualization", "statistics",
    "aws", "azure", "docker", "kubernetes", "linux", "git", "rest api", "mongodb",
    "power bi", "tableau", "excel", "figma", "ui/ux", "agile", "scrum",
    "networking", "cybersecurity", "ethical hacking", "cryptography", "nlp",
    "computer vision", "communication", "leadership", "project management",
    "solidity", "blockchain", "unity", "selenium", "testing", "cloud computing",
]

# Sections / keywords a strong resume is generally expected to contain.
BEST_PRACTICE_KEYWORDS = [
    "summary", "experience", "education", "skills", "projects",
    "certification", "achievements", "contact",
]

ACTION_VERBS = [
    "developed", "built", "designed", "implemented", "led", "managed",
    "created", "improved", "optimized", "launched", "analyzed",
]


class ResumeAnalyzer:
    def __init__(self, recommender=None):
        # Reuse the same recommender engine to suggest suitable roles.
        self.recommender = recommender

    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """Extract raw text from every page of the PDF resume."""
        text_chunks = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_chunks.append(page_text)
        return "\n".join(text_chunks)

    def detect_skills(self, text: str):
        text_lower = text.lower()
        found = [skill for skill in MASTER_SKILLS if re.search(r"\b" + re.escape(skill) + r"\b", text_lower)]
        return sorted(set(found))

    def missing_keywords(self, text: str):
        text_lower = text.lower()
        missing = [kw for kw in BEST_PRACTICE_KEYWORDS if kw not in text_lower]
        return missing

    def score_resume(self, text: str, detected_skills: list, missing_keywords: list) -> float:
        """
        Heuristic scoring out of 100:
            - up to 40 points for breadth of detected technical skills
            - up to 25 points for having standard resume sections
            - up to 15 points for using strong action verbs
            - up to 10 points for adequate length (not too short/long)
            - up to 10 points for including quantifiable results (numbers/%)
        """
        score = 0.0
        text_lower = text.lower()

        # Skills breadth (cap at 10 skills for full marks).
        score += min(len(detected_skills), 10) / 10 * 40

        # Standard sections present.
        sections_present = len(BEST_PRACTICE_KEYWORDS) - len(missing_keywords)
        score += (sections_present / len(BEST_PRACTICE_KEYWORDS)) * 25

        # Action verbs usage.
        verbs_found = sum(1 for v in ACTION_VERBS if v in text_lower)
        score += min(verbs_found, 5) / 5 * 15

        # Length check: ideal resume text roughly 300-1200 words.
        word_count = len(text_lower.split())
        if 300 <= word_count <= 1200:
            score += 10
        elif word_count > 0:
            score += 5

        # Quantifiable achievements (numbers / percentages).
        if re.search(r"\d+%|\d+\+|\$\d+", text_lower):
            score += 10

        return round(min(score, 100.0), 1)

    def generate_suggestions(self, detected_skills, missing_keywords, score) -> list:
        suggestions = []
        if missing_keywords:
            suggestions.append(
                f"Add a clear '{missing_keywords[0].title()}' section — recruiters and ATS systems look for it explicitly."
            )
        if len(detected_skills) < 6:
            suggestions.append("List more relevant technical skills explicitly in a dedicated 'Skills' section.")
        if score < 60:
            suggestions.append("Use strong action verbs (e.g., 'developed', 'led', 'optimized') to describe your achievements.")
        suggestions.append("Quantify your achievements with numbers or percentages wherever possible (e.g., 'improved performance by 30%').")
        suggestions.append("Keep your resume concise — ideally 1-2 pages with 300-1200 words of core content.")
        suggestions.append("Tailor your resume's keywords to match the specific job description you are applying for.")
        return suggestions

    def suggest_roles(self, detected_skills: list, top_n: int = 3):
        if not self.recommender:
            return []
        skills_text = ", ".join(detected_skills)
        recs = self.recommender.recommend(skills_text, top_n=top_n)
        return [r["career_name"] for r in recs]

    def analyze(self, pdf_path: str) -> dict:
        text = self.extract_text(pdf_path)
        detected = self.detect_skills(text)
        missing_kw = self.missing_keywords(text)
        score = self.score_resume(text, detected, missing_kw)
        suggestions = self.generate_suggestions(detected, missing_kw, score)
        roles = self.suggest_roles(detected)

        return {
            "resume_score": score,
            "detected_skills": detected,
            "missing_keywords": missing_kw,
            "suggestions": suggestions,
            "suggested_roles": roles,
            "word_count": len(text.split()),
        }
