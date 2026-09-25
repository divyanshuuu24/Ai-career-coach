"""
routes/main.py
----------------
Core application routes: static pages (Home/About/Contact), the
Career Assessment flow (Assessment -> AI Analysis -> Recommendation),
Skill Gap Analysis, Learning Roadmap, and the user Dashboard.
"""

import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user

from models.database import db, Assessment, CareerRecommendation, Skill, Roadmap, ResumeReport, ChatHistory

main_bp = Blueprint("main", __name__)


# ---------------------------------------------------------------------
# Public marketing / informational pages
# ---------------------------------------------------------------------

@main_bp.route("/")
def home():
    return render_template("home.html")


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not name or not email or not message:
            flash("Please fill in all fields before sending your message.", "danger")
        else:
            # In production this would send an email / save to a "messages" table.
            flash("Thanks for reaching out! Our team will get back to you soon.", "success")
            return redirect(url_for("main.contact"))
    return render_template("contact.html")


# ---------------------------------------------------------------------
# Career Assessment -> AI Analysis -> Recommendation flow
# ---------------------------------------------------------------------

@main_bp.route("/assessment", methods=["GET", "POST"])
@login_required
def assessment():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        education = request.form.get("education", "").strip()
        college = request.form.get("college", "").strip()
        current_skills = request.form.get("current_skills", "").strip()
        interests = request.form.get("interests", "").strip()
        preferred_industry = request.form.get("preferred_industry", "").strip()
        career_goal = request.form.get("career_goal", "").strip()
        experience_level = request.form.get("experience_level", "").strip()

        # ---- Server-side validation ----
        errors = []
        if not name:
            errors.append("Name is required.")
        if not age.isdigit() or not (10 <= int(age) <= 100):
            errors.append("Please enter a valid age between 10 and 100.")
        if not current_skills:
            errors.append("Please list at least one current skill.")
        if not education:
            errors.append("Education level is required.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("assessment.html", form=request.form)

        new_assessment = Assessment(
            user_id=current_user.id,
            name=name,
            age=int(age),
            gender=gender,
            education=education,
            college=college,
            current_skills=current_skills,
            interests=interests,
            preferred_industry=preferred_industry,
            career_goal=career_goal,
            experience_level=experience_level,
        )
        db.session.add(new_assessment)
        db.session.commit()

        # Run the AI recommendation engine and persist top-3 results.
        recommender = current_app.config["RECOMMENDER"]
        results = recommender.recommend(
            user_skills=current_skills,
            user_interests=interests,
            preferred_industry=preferred_industry,
            top_n=3,
        )
        for r in results:
            db.session.add(CareerRecommendation(
                assessment_id=new_assessment.id,
                career_name=r["career_name"],
                match_percentage=r["match_percentage"],
                salary_range=r["salary_range"],
                description=r["description"],
                future_demand=r["future_demand"],
                reason=r["reason"],
                rank=r["rank"],
            ))
        db.session.commit()

        return redirect(url_for("main.analysis", assessment_id=new_assessment.id))

    return render_template("assessment.html", form={})


@main_bp.route("/analysis/<int:assessment_id>")
@login_required
def analysis(assessment_id):
    assessment_obj = _get_owned_assessment(assessment_id)
    return render_template("analysis.html", assessment=assessment_obj)


@main_bp.route("/recommendation/<int:assessment_id>")
@login_required
def recommendation(assessment_id):
    assessment_obj = _get_owned_assessment(assessment_id)
    recs = CareerRecommendation.query.filter_by(assessment_id=assessment_obj.id).order_by(
        CareerRecommendation.rank
    ).all()
    return render_template("recommendation.html", assessment=assessment_obj, recommendations=recs)


# ---------------------------------------------------------------------
# Skill Gap Analysis
# ---------------------------------------------------------------------

@main_bp.route("/skill-gap/<int:assessment_id>/<path:career_name>")
@login_required
def skill_gap(assessment_id, career_name):
    assessment_obj = _get_owned_assessment(assessment_id)
    recommender = current_app.config["RECOMMENDER"]
    gap_engine = current_app.config["SKILL_GAP_ANALYZER"]

    career = recommender.get_career_by_name(career_name)
    if not career:
        abort(404)

    result = gap_engine.analyze(assessment_obj.current_skills, career["required_skills"])

    # Persist/refresh Skill rows for this user so the Dashboard can aggregate progress.
    Skill.query.filter_by(user_id=current_user.id).delete()
    for skill_name in result["existing_skills"]:
        db.session.add(Skill(user_id=current_user.id, skill_name=skill_name, status="acquired", priority="Medium"))
    for item in result["missing_skills"]:
        db.session.add(Skill(user_id=current_user.id, skill_name=item["skill"], status="missing", priority=item["priority"]))
    db.session.commit()

    return render_template(
        "skill_gap.html",
        assessment=assessment_obj,
        career=career,
        result=result,
    )


# ---------------------------------------------------------------------
# Personalized Learning Roadmap
# ---------------------------------------------------------------------

@main_bp.route("/roadmap/<int:assessment_id>/<path:career_name>")
@login_required
def roadmap(assessment_id, career_name):
    assessment_obj = _get_owned_assessment(assessment_id)
    recommender = current_app.config["RECOMMENDER"]
    gap_engine = current_app.config["SKILL_GAP_ANALYZER"]
    roadmap_gen = current_app.config["ROADMAP_GENERATOR"]

    career = recommender.get_career_by_name(career_name)
    if not career:
        abort(404)

    gap_result = gap_engine.analyze(assessment_obj.current_skills, career["required_skills"])
    roadmap_data = roadmap_gen.generate(career_name, gap_result["missing_skills"])

    # Save (or update) the roadmap for this user + career combo.
    existing = Roadmap.query.filter_by(user_id=current_user.id, target_career=career_name).first()
    if existing:
        existing.roadmap_json = json.dumps(roadmap_data)
    else:
        db.session.add(Roadmap(
            user_id=current_user.id,
            target_career=career_name,
            roadmap_json=json.dumps(roadmap_data),
            progress_percent=0.0,
        ))
    db.session.commit()

    return render_template("roadmap.html", assessment=assessment_obj, career=career, roadmap=roadmap_data)


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------

@main_bp.route("/dashboard")
@login_required
def dashboard():
    latest_assessment = Assessment.query.filter_by(user_id=current_user.id).order_by(
        Assessment.created_at.desc()
    ).first()

    recommendations = []
    if latest_assessment:
        recommendations = CareerRecommendation.query.filter_by(
            assessment_id=latest_assessment.id
        ).order_by(CareerRecommendation.rank).all()

    all_skills = Skill.query.filter_by(user_id=current_user.id).all()
    acquired_count = sum(1 for s in all_skills if s.status == "acquired")
    missing_count = sum(1 for s in all_skills if s.status == "missing")

    roadmaps = Roadmap.query.filter_by(user_id=current_user.id).all()
    resume_reports = ResumeReport.query.filter_by(user_id=current_user.id).order_by(
        ResumeReport.created_at.desc()
    ).limit(5).all()
    chat_count = ChatHistory.query.filter_by(user_id=current_user.id).count()

    # Simple "activity history" feed built from the most recent records.
    activity = []
    for a in Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.created_at.desc()).limit(3):
        activity.append({"type": "Assessment", "detail": f"Completed career assessment", "date": a.created_at})
    for r in resume_reports[:3]:
        activity.append({"type": "Resume", "detail": f"Analyzed resume: {r.filename} (score {r.resume_score})", "date": r.created_at})
    for rm in roadmaps[:3]:
        activity.append({"type": "Roadmap", "detail": f"Generated roadmap for {rm.target_career}", "date": rm.created_at})
    activity.sort(key=lambda x: x["date"], reverse=True)

    top_match_score = recommendations[0].match_percentage if recommendations else 0

    return render_template(
        "dashboard.html",
        latest_assessment=latest_assessment,
        recommendations=recommendations,
        acquired_count=acquired_count,
        missing_count=missing_count,
        roadmaps=roadmaps,
        resume_reports=resume_reports,
        chat_count=chat_count,
        activity=activity[:6],
        top_match_score=top_match_score,
    )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _get_owned_assessment(assessment_id):
    """Fetch an assessment and ensure it belongs to the currently logged-in user."""
    assessment_obj = Assessment.query.get_or_404(assessment_id)
    if assessment_obj.user_id != current_user.id:
        abort(403)
    return assessment_obj
