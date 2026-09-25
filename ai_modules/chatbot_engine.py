"""
ai_modules/chatbot_engine.py
-------------------------------
A lightweight, fully offline (no external API key required) career
chatbot. It uses intent matching (keyword + TF-IDF similarity against
a small library of Q&A intents) to answer common career questions:
job-role explanations, learning paths, interview prep, resume advice,
and project ideas.

Design note: keeping this rule-based/TF-IDF driven (rather than
calling an external LLM API) means the whole application runs locally
out of the box with zero API keys and zero internet dependency.
"""

import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


INTENTS = [
    {
        "tag": "greeting",
        "patterns": ["hello", "hi", "hey", "good morning", "good evening"],
        "responses": [
            "Hello! I'm your AI Career Coach assistant. Ask me about career paths, skills, interview prep, or resumes!",
            "Hi there! How can I help with your career journey today?",
        ],
    },
    {
        "tag": "interview_prep",
        "patterns": [
            "interview tips", "how to prepare for interview", "interview preparation",
            "technical interview", "behavioral interview questions",
        ],
        "responses": [
            "Great interview prep tips: 1) Research the company and role thoroughly. "
            "2) Practice the STAR method (Situation, Task, Action, Result) for behavioral questions. "
            "3) Review core technical concepts and practice coding problems if it's a tech role. "
            "4) Prepare 2-3 thoughtful questions to ask the interviewer. "
            "5) Do a mock interview with a friend or record yourself answering common questions."
        ],
    },
    {
        "tag": "resume_advice",
        "patterns": [
            "resume advice", "improve my resume", "resume tips", "how to write a resume", "cv tips",
        ],
        "responses": [
            "Resume tips: Keep it to 1-2 pages, use strong action verbs (built, led, optimized), "
            "quantify achievements with numbers/percentages, tailor keywords to the job description, "
            "and make sure you have clear Skills, Experience, Education, and Projects sections. "
            "You can also use our Resume Analyzer page for a personalized score!"
        ],
    },
    {
        "tag": "learning_path",
        "patterns": [
            "how to learn", "learning path", "roadmap", "where to start learning", "study plan",
        ],
        "responses": [
            "A good learning path: 1) Master the fundamentals first. 2) Build small projects as you learn "
            "each concept. 3) Get a certification to validate your knowledge. 4) Contribute to open-source "
            "or build a portfolio project. 5) Apply your skills to real problems. "
            "Check out our Learning Roadmap page for a personalized 6-month plan!"
        ],
    },
    {
        "tag": "project_ideas",
        "patterns": [
            "project ideas", "what project should i build", "portfolio project", "suggest a project",
        ],
        "responses": [
            "Some strong beginner-to-intermediate project ideas: a personal portfolio website, "
            "a data dashboard analyzing a public dataset, a REST API with authentication, "
            "a machine learning model deployed as a web app, or a mobile to-do/habit tracker app. "
            "Pick something that solves a real problem you personally care about — it shows better in interviews."
        ],
    },
    {
        "tag": "salary",
        "patterns": ["salary", "how much do they earn", "pay range", "average salary"],
        "responses": [
            "Salaries vary widely by location, experience, and company size. Check the salary range shown "
            "on your Career Recommendation results — it reflects typical industry figures for that role."
        ],
    },
    {
        "tag": "career_change",
        "patterns": ["switch careers", "career change", "change my career", "pivot career"],
        "responses": [
            "Switching careers is very achievable! Start by identifying transferable skills you already have, "
            "take our Career Assessment to find aligned roles, then focus on closing the top 2-3 skill gaps "
            "with targeted courses and a portfolio project before applying."
        ],
    },
    {
        "tag": "thanks",
        "patterns": ["thank you", "thanks", "appreciate it"],
        "responses": ["You're welcome! Wishing you the best in your career journey. 🚀"],
    },
    {
        "tag": "goodbye",
        "patterns": ["bye", "goodbye", "see you"],
        "responses": ["Goodbye! Come back anytime you need career guidance."],
    },
]

FALLBACK_RESPONSES = [
    "That's a great question — could you rephrase it? I can help with career paths, skill roadmaps, "
    "interview prep, resume advice, and project ideas.",
    "I'm not fully sure about that one yet, but I'd recommend checking our Career Recommendation and "
    "Skill Gap Analysis pages for personalized, data-driven guidance.",
]


class CareerChatbot:
    def __init__(self):
        self.tags = []
        self.pattern_texts = []
        for intent in INTENTS:
            for pattern in intent["patterns"]:
                self.tags.append(intent["tag"])
                self.pattern_texts.append(pattern)

        self.vectorizer = TfidfVectorizer()
        self.pattern_matrix = self.vectorizer.fit_transform(self.pattern_texts)
        self.responses_by_tag = {intent["tag"]: intent["responses"] for intent in INTENTS}

    def _job_role_lookup(self, message: str, recommender=None):
        """If the message mentions a known career name, describe that role."""
        if not recommender:
            return None
        message_lower = message.lower()
        for career_name in recommender.df["career_name"]:
            if career_name.lower() in message_lower:
                row = recommender.get_career_by_name(career_name)
                return (
                    f"{row['career_name']} ({row['industry']}): {row['description']} "
                    f"Typical salary range: {row['salary_range']}. Key skills needed: {row['required_skills']}. "
                    f"Future demand: {row['future_demand']}."
                )
        return None

    def get_response(self, message: str, recommender=None) -> str:
        message = (message or "").strip()
        if not message:
            return "Please type a question and I'll do my best to help!"

        # 1) Check if the user is asking about a specific career/job role.
        role_answer = self._job_role_lookup(message, recommender)
        if role_answer:
            return role_answer

        # 2) TF-IDF similarity match against known intent patterns.
        user_vector = self.vectorizer.transform([message.lower()])
        similarities = cosine_similarity(user_vector, self.pattern_matrix).flatten()
        best_idx = similarities.argmax()
        best_score = similarities[best_idx]

        if best_score >= 0.3:
            tag = self.tags[best_idx]
            return random.choice(self.responses_by_tag[tag])

        return random.choice(FALLBACK_RESPONSES)
