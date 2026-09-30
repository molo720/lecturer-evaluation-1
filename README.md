# EvalAI – Lecturer Evaluation (Streamlit)

Streamlit frontend linked to the existing SQLite database and trained models.

## Deploy (Streamlit Community Cloud)

- **Repository:** molo720/lecturer-evaluation-1
- **Main file path:** `streamlit_app.py`
- **Branch:** `main`

## Features

- Landing page (same settings as Flask landing.html)
- Anonymous student evaluation → feedback table
- Staff login (users table)
- Dashboard & lecturer report
- Sentiment analysis via existing ml_engine
- Model evaluation (SVM vs Naive Bayes)
- **Admin retrain** → train_models.main() (same as Flask /admin/retrain)

## Demo logins

- admin / admin123
- Lecturers: okafor, adeyemi, … / lecturer123
