"""
config.py
----------
Central configuration for the AI Personal Career Coach application.
Reads sensitive values from environment variables where possible and
falls back to sane development defaults.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Secret key used to sign session cookies / CSRF tokens.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # SQLite database stored inside the /instance folder.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'career_coach.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload settings (resumes).
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload size
    ALLOWED_EXTENSIONS = {"pdf"}

    # Path to the careers dataset used by the recommendation engine.
    CAREERS_DATASET = os.path.join(BASE_DIR, "datasets", "careers.csv")
    SKILLS_DATASET = os.path.join(BASE_DIR, "datasets", "skills_certifications.csv")

    # Session cookie hardening.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
