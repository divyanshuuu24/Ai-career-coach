"""
routes/resume.py
------------------
Handles resume (PDF) upload and AI-driven analysis: text extraction,
skill detection, scoring, missing-keyword detection, improvement
suggestions, and suitable job-role recommendations.
"""

import os
import uuid
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models.database import db, ResumeReport

resume_bp = Blueprint("resume", __name__)


def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )


@resume_bp.route("/resume-analyzer", methods=["GET", "POST"])
@login_required
def resume_analyzer():
    if request.method == "POST":
        if "resume_file" not in request.files:
            flash("Please choose a PDF resume to upload.", "danger")
            return redirect(url_for("resume.resume_analyzer"))

        file = request.files["resume_file"]
        if file.filename == "":
            flash("No file selected.", "danger")
            return redirect(url_for("resume.resume_analyzer"))

        if not _allowed_file(file.filename):
            flash("Only PDF files are supported. Please upload a .pdf resume.", "danger")
            return redirect(url_for("resume.resume_analyzer"))

        # Save with a randomized, sanitized filename to avoid path traversal / overwrites.
        original_name = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{original_name}"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
        file.save(save_path)

        try:
            analyzer = current_app.config["RESUME_ANALYZER"]
            result = analyzer.analyze(save_path)
        except Exception as exc:  # corrupt / unreadable PDF, etc.
            flash(f"Could not analyze this PDF: {exc}", "danger")
            return redirect(url_for("resume.resume_analyzer"))
        finally:
            # Remove the uploaded file after analysis — we only keep the report data.
            if os.path.exists(save_path):
                os.remove(save_path)

        report = ResumeReport(
            user_id=current_user.id,
            filename=original_name,
            resume_score=result["resume_score"],
            detected_skills=", ".join(result["detected_skills"]),
            missing_keywords=", ".join(result["missing_keywords"]),
            suggestions="\n".join(result["suggestions"]),
            suggested_roles=", ".join(result["suggested_roles"]),
        )
        db.session.add(report)
        db.session.commit()

        return render_template("resume_analyzer.html", result=result, filename=original_name, analyzed=True)

    return render_template("resume_analyzer.html", analyzed=False)
