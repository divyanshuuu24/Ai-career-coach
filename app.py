"""
app.py
-------
Application entry point for the AI Personal Career Coach.

Run locally with:
    python app.py

This creates the Flask app, wires up the database, authentication,
AI engines (recommender, skill-gap analyzer, roadmap generator,
resume analyzer, chatbot), and registers all route blueprints.
"""

import os
from flask import Flask, render_template
from config import Config
from models.database import db, login_manager

from ai_modules.recommender import CareerRecommender
from ai_modules.skill_gap import SkillGapAnalyzer
from ai_modules.roadmap import RoadmapGenerator
from ai_modules.resume_analyzer import ResumeAnalyzer
from ai_modules.chatbot_engine import CareerChatbot

from routes.auth import auth_bp
from routes.main import main_bp
from routes.resume import resume_bp
from routes.chatbot import chatbot_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure required folders exist (SQLite instance dir + uploads dir).
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ---- Extensions ----
    db.init_app(app)
    login_manager.init_app(app)

    # ---- AI engines: instantiate once at startup and reuse across requests ----
    recommender = CareerRecommender(app.config["CAREERS_DATASET"])
    skill_gap_analyzer = SkillGapAnalyzer(app.config["SKILLS_DATASET"])
    roadmap_generator = RoadmapGenerator()
    resume_analyzer = ResumeAnalyzer(recommender=recommender)
    chatbot = CareerChatbot()

    app.config["RECOMMENDER"] = recommender
    app.config["SKILL_GAP_ANALYZER"] = skill_gap_analyzer
    app.config["ROADMAP_GENERATOR"] = roadmap_generator
    app.config["RESUME_ANALYZER"] = resume_analyzer
    app.config["CHATBOT"] = chatbot

    # ---- Blueprints (route modules) ----
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(chatbot_bp)

    # ---- Error handlers ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(413)
    def too_large(e):
        return render_template("errors/413.html"), 413

    # ---- Create database tables on first run ----
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
