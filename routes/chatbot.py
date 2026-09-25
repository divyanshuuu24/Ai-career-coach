"""
routes/chatbot.py
-------------------
Serves the AI Career Chatbot page and a JSON API endpoint the
front-end JavaScript calls (via fetch) to send a message and receive
an AI-generated response, which is also logged to chat history.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from models.database import db, ChatHistory

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/chatbot")
@login_required
def chatbot_page():
    history = ChatHistory.query.filter_by(user_id=current_user.id).order_by(
        ChatHistory.created_at.asc()
    ).limit(20).all()
    return render_template("chatbot.html", history=history)


@chatbot_bp.route("/chatbot/api", methods=["POST"])
@login_required
def chatbot_api():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "Empty message"}), 400
    if len(message) > 500:
        return jsonify({"error": "Message too long (max 500 characters)."}), 400

    bot = current_app.config["CHATBOT"]
    recommender = current_app.config["RECOMMENDER"]
    response_text = bot.get_response(message, recommender=recommender)

    db.session.add(ChatHistory(user_id=current_user.id, message=message, response=response_text))
    db.session.commit()

    return jsonify({"response": response_text})
