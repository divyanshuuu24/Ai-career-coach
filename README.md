# AI Personal Career Coach

A full-stack Flask + AI web application that helps students and job seekers discover
the right career path, identify skill gaps, get a personalized learning roadmap,
analyze their resume, and chat with an AI career assistant.

---

## Tech Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login
- **Frontend:** HTML5, CSS3, Bootstrap 5, vanilla JavaScript, Chart.js
- **Database:** SQLite
- **AI/ML:** pandas, NumPy, scikit-learn (TF-IDF + cosine similarity), pdfplumber (resume text extraction)
- **Auth:** Flask-Login + Werkzeug password hashing (PBKDF2)

## Folder Structure

```
ai_career_coach/
├── app.py                     # App factory & entry point
├── config.py                  # Configuration
├── requirements.txt
├── models/
│   └── database.py            # SQLAlchemy models (User, Assessment, etc.)
├── routes/
│   ├── auth.py                # Register / login / logout
│   ├── main.py                # Home, assessment, recommendation, skill gap, roadmap, dashboard
│   ├── resume.py               # Resume upload & analysis
│   └── chatbot.py             # AI chatbot page + API
├── ai_modules/
│   ├── recommender.py         # TF-IDF + cosine similarity career matching
│   ├── skill_gap.py            # Skill gap comparison engine
│   ├── roadmap.py               # 6-month roadmap generator
│   ├── resume_analyzer.py     # PDF text extraction, scoring, keyword detection
│   └── chatbot_engine.py      # Rule-based / TF-IDF intent chatbot (offline, no API key)
├── datasets/
│   ├── careers.csv            # 25 careers with skills, salary, demand, description
│   └── skills_certifications.csv  # Skill -> priority/certification/project mapping
├── templates/                 # Jinja2 HTML templates (13 pages + error pages)
├── static/
│   ├── css/style.css
│   └── js/main.js
├── uploads/                   # Temporary resume upload storage (auto-cleaned)
└── instance/                  # SQLite database file lives here (auto-created)
```

## Setup Instructions

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

The database tables are created automatically on first run (`db.create_all()`
inside the app factory) — no separate migration step is required for this
SQLite-based project.

The app will be available at: **http://localhost:5000**

### 4. Create an account and explore

1. Go to `/register` and create an account.
2. Log in, then complete the **Career Assessment**.
3. View your **AI Analysis** → **Career Recommendations**.
4. Click into **Skill Gap Analysis** and **Learning Roadmap** for any recommended career.
5. Try the **Resume Analyzer** (upload any PDF resume).
6. Chat with the **AI Career Chatbot**.
7. Check your **Dashboard** for progress charts and activity history.

## Security Notes

- Passwords are hashed with Werkzeug's PBKDF2-based `generate_password_hash` — never stored in plain text.
- All database queries go through the SQLAlchemy ORM (parameterized), preventing SQL injection.
- File uploads are restricted to `.pdf`, size-limited to 5MB, and saved with randomized filenames; the file is deleted immediately after analysis.
- Server-side validation backs up all client-side (HTML5 + JS) form validation.
- Session cookies are set `HttpOnly` and `SameSite=Lax`.

## Notes on the AI Engine

- **Career Recommendation** uses TF-IDF vectorization + cosine similarity (scikit-learn) between the user's skills/interests and each career's required-skills text — a fast, dependency-light approximation of semantic similarity that runs fully offline.
- **Skill Gap Analysis** performs a set comparison between user skills and a career's required skills, enriched with priority/certification/project data from `skills_certifications.csv`.
- **Resume Analyzer** extracts text via `pdfplumber`, detects skills via keyword matching against a master skills list, and scores the resume using a weighted heuristic (skills breadth, standard sections present, action-verb usage, length, quantified achievements).
- **AI Chatbot** uses TF-IDF intent matching against a small library of career Q&A patterns — no external API key required, so the whole app runs locally out of the box.

## Extending the Project

- Swap the TF-IDF recommender for `sentence-transformers` embeddings for deeper semantic matching (requires an extra dependency + model download).
- Connect the chatbot to the Anthropic/OpenAI API for open-ended conversation (swap `ai_modules/chatbot_engine.py`).
- Add Flask-WTF `FlaskForm` classes for even stronger CSRF-protected forms (Flask-WTF is already in `requirements.txt`).
- Add an admin panel to manage the careers/skills datasets from the UI instead of editing CSVs directly.
