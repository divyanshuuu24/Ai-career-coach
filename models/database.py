"""
models/database.py
-------------------
Defines all SQLAlchemy ORM models (database tables) used by the
AI Personal Career Coach application, plus the shared `db` and
`login_manager` extension instances.

Tables:
    - User                 : registered accounts (auth)
    - Assessment            : career assessment form submissions
    - CareerRecommendation  : AI-generated career matches per assessment
    - Skill                 : normalized skill records tied to a user
    - Roadmap                : generated 6-month learning roadmap (JSON payload)
    - ResumeReport           : resume analysis results
    - ChatHistory            : AI chatbot conversation log
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"


class User(UserMixin, db.Model):
    """Registered user account."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships (cascade delete keeps the DB consistent).
    assessments = db.relationship("Assessment", backref="user", lazy=True, cascade="all, delete-orphan")
    skills = db.relationship("Skill", backref="user", lazy=True, cascade="all, delete-orphan")
    roadmaps = db.relationship("Roadmap", backref="user", lazy=True, cascade="all, delete-orphan")
    resume_reports = db.relationship("ResumeReport", backref="user", lazy=True, cascade="all, delete-orphan")
    chat_history = db.relationship("ChatHistory", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, raw_password: str) -> None:
        """Hash and store the user's password (never store plain text)."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verify a plain-text password against the stored hash."""
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.email}>"


class Assessment(db.Model):
    """A single career-assessment questionnaire submission."""

    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(120))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(30))
    education = db.Column(db.String(120))
    college = db.Column(db.String(150))
    current_skills = db.Column(db.Text)        # comma-separated
    interests = db.Column(db.Text)
    preferred_industry = db.Column(db.String(120))
    career_goal = db.Column(db.Text)
    experience_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recommendations = db.relationship(
        "CareerRecommendation", backref="assessment", lazy=True, cascade="all, delete-orphan"
    )


class CareerRecommendation(db.Model):
    """One AI-generated career match tied to an assessment."""

    __tablename__ = "career_recommendations"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=False)

    career_name = db.Column(db.String(150))
    match_percentage = db.Column(db.Float)
    salary_range = db.Column(db.String(80))
    description = db.Column(db.Text)
    future_demand = db.Column(db.String(30))
    reason = db.Column(db.Text)
    rank = db.Column(db.Integer)  # 1 = top match
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Skill(db.Model):
    """Normalized skill entries for a user, used for dashboard progress."""

    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_name = db.Column(db.String(120))
    status = db.Column(db.String(20), default="missing")  # 'acquired' or 'missing'
    priority = db.Column(db.String(20), default="Medium")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Roadmap(db.Model):
    """A generated 6-month learning roadmap, stored as JSON text."""

    __tablename__ = "roadmaps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_career = db.Column(db.String(150))
    roadmap_json = db.Column(db.Text)  # serialized list of monthly/weekly milestones
    progress_percent = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ResumeReport(db.Model):
    """Result of an uploaded resume being analyzed."""

    __tablename__ = "resume_reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255))
    resume_score = db.Column(db.Float)
    detected_skills = db.Column(db.Text)     # comma-separated
    missing_keywords = db.Column(db.Text)    # comma-separated
    suggestions = db.Column(db.Text)
    suggested_roles = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatHistory(db.Model):
    """A single message exchange with the AI career chatbot."""

    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text)
    response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login callback used to reload a user object from the session."""
    return User.query.get(int(user_id))
