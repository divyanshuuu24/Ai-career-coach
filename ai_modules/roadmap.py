"""
ai_modules/roadmap.py
-----------------------
Generates a personalized 6-month (24-week) learning roadmap based on
the list of missing skills identified by the Skill Gap Analyzer.

The roadmap is organized into 6 monthly phases, each containing 4
weekly milestones with a focus skill, learning resources, and a
mini-project suggestion.
"""

LEARNING_RESOURCES = {
    "default": ["freeCodeCamp", "Coursera", "YouTube tutorials", "Official documentation"],
}

PHASE_THEMES = [
    "Foundations & Fundamentals",
    "Core Skill Building",
    "Applied Practice",
    "Intermediate Projects",
    "Advanced Topics & Tools",
    "Portfolio & Job Readiness",
]


class RoadmapGenerator:
    def generate(self, target_career: str, missing_skills: list):
        """
        missing_skills: list of dicts from SkillGapAnalyzer (skill, priority, certification, project)
        Returns a structured 6-month roadmap as a list of phase dicts.
        """
        if not missing_skills:
            missing_skills = [{
                "skill": "advanced specialization",
                "priority": "Medium",
                "certification": "Explore an advanced certification in your field",
                "project": "Build a capstone project showcasing your expertise",
            }]

        # Cycle through missing skills across the 6 months so every month has a focus.
        months = []
        skill_count = len(missing_skills)

        for month_index in range(6):
            skill_info = missing_skills[month_index % skill_count]
            weeks = []
            week_focus = [
                f"Learn the fundamentals of {skill_info['skill'].title()}",
                f"Practice {skill_info['skill'].title()} with guided exercises",
                f"Work on: {skill_info['project']}",
                f"Review, polish, and document your {skill_info['skill'].title()} project",
            ]
            for w, focus in enumerate(week_focus, start=1):
                weeks.append({
                    "week": w,
                    "focus": focus,
                    "resources": LEARNING_RESOURCES["default"],
                })

            months.append({
                "month": month_index + 1,
                "theme": PHASE_THEMES[month_index],
                "target_skill": skill_info["skill"].title(),
                "priority": skill_info["priority"],
                "recommended_certification": skill_info["certification"],
                "mini_project": skill_info["project"],
                "weeks": weeks,
            })

        return {
            "target_career": target_career,
            "duration": "6 months",
            "months": months,
        }
