"""EvalAI Streamlit — DB-linked, landing page, admin retrain (same as Flask)."""
import os, sys, json
from pathlib import Path
import streamlit as st
import pandas as pd
from werkzeug.security import check_password_hash, generate_password_hash

BASE = Path(__file__).resolve().parent
os.chdir(BASE)
sys.path.insert(0, str(BASE))
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

try:
    from db import (
        DATABASE_PATH, DEMO_LECTURERS, DEFAULT_SETTINGS,
        get_connection, init_db, get_site_settings, get_lecturer_names,
    )
except Exception:
    DATABASE_PATH = str(DATA / "feedback.db")
    DEMO_LECTURERS = ["Dr. Okafor", "Dr. Adeyemi", "Prof. Martins", "Dr. Faith", "Prof. Balogun", "Dr. Chukwu"]
    DEFAULT_SETTINGS = {
        "announcement_banner": "2025/2026 Academic Session — Anonymous Student Evaluation of Teaching (SET) Portal Active",
        "show_announcement": "true",
        "landing_title": "Anonymous Lecturer Evaluation",
        "landing_subtitle": "Share numerical ratings and free-text comments. Your name and student identity are never stored.",
        "privacy_notice": "This form does not collect student name, matric number, or login details. Only the lecturer, course, rating, and comment are saved for analysis.",
        "custom_guidelines": "Please evaluate objectively based on course engagement, syllabus delivery, and instructional clarity.",
    }
    import sqlite3
    def get_connection(db_path=DATABASE_PATH):
        con = sqlite3.connect(db_path, check_same_thread=False)
        con.row_factory = sqlite3.Row
        return con
    def init_db(db_path=DATABASE_PATH):
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        db = get_connection(db_path)
        db.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, matric_number TEXT,
            lecturer_name TEXT NOT NULL, course TEXT NOT NULL, course_code TEXT,
            rating INTEGER NOT NULL, comment TEXT NOT NULL, document_sentiment TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, role TEXT NOT NULL, lecturer_name TEXT, full_name TEXT)""")
        db.execute("CREATE TABLE IF NOT EXISTS site_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        for k, v in DEFAULT_SETTINGS.items():
            db.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)", (k, v))
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            for u, p, r, ln, fn in [
                ("admin", "admin123", "administrator", None, "System Administrator"),
                ("okafor", "lecturer123", "lecturer", "Dr. Okafor", "Dr. Okafor"),
                ("adeyemi", "lecturer123", "lecturer", "Dr. Adeyemi", "Dr. Adeyemi"),
            ]:
                db.execute("INSERT INTO users (username, password_hash, role, lecturer_name, full_name) VALUES (?,?,?,?,?)",
                           (u, generate_password_hash(p), r, ln, fn))
        db.commit(); db.close()
    def get_site_settings():
        s = dict(DEFAULT_SETTINGS)
        try:
            db = get_connection(); rows = db.execute("SELECT key, value FROM site_settings").fetchall()
            for r in rows: s[r["key"]] = r["value"]
            db.close()
        except Exception: pass
        return s
    def get_lecturer_names():
        try:
            db = get_connection()
            rows = db.execute("SELECT DISTINCT lecturer_name FROM users WHERE role='lecturer' AND lecturer_name IS NOT NULL").fetchall()
            names = [r["lecturer_name"] for r in rows if r["lecturer_name"]]
            db.close()
            return sorted(names) if names else list(DEMO_LECTURERS)
        except Exception:
            return list(DEMO_LECTURERS)

def analyze_comment(comment, rating=3):
    try:
        from ml_engine import run_analysis
        return run_analysis(comment, rating)
    except Exception:
        return {"document_sentiment": "neutral"}

def save_eval(lecturer, course, code, rating, comment):
    lecturer, course, code, comment = (lecturer or "").strip(), (course or "").strip(), (code or "").strip(), (comment or "").strip()
    if not lecturer or not course or not comment:
        return False, "Please fill in lecturer, course, and comment."
    try: r = int(rating)
    except Exception: r = 3
    ana = analyze_comment(comment, r)
    sent = ana.get("document_sentiment", "neutral") if isinstance(ana, dict) else "neutral"
    db = get_connection(DATABASE_PATH)
    cols = [x[1] for x in db.execute("PRAGMA table_info(feedback)").fetchall()]
    data = {"lecturer_name": lecturer, "course": course, "course_code": code, "rating": r, "comment": comment, "document_sentiment": sent}
    if "student_name" in cols: data["student_name"] = "Anonymous"
    if "matric_number" in cols: data["matric_number"] = "ANON"
    keys = [k for k in data if k in cols]
    db.execute(f"INSERT INTO feedback ({','.join(keys)}) VALUES ({','.join('?'*len(keys))})", [data[k] for k in keys])
    db.commit(); db.close()
    return True, None

def load_feedback():
    db = get_connection(DATABASE_PATH)
    df = pd.read_sql_query("SELECT * FROM feedback ORDER BY submitted_at DESC", db)
    db.close()
    return df

def authenticate(username, password):
    db = get_connection(DATABASE_PATH)
    row = db.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
    db.close()
    if row and check_password_hash(row["password_hash"], password):
        return dict(row)
    return None

def load_metrics():
    for p in [DATA / "model_evaluation_metrics.json", BASE / "model_evaluation_metrics.json"]:
        if p.exists():
            return json.loads(p.read_text())
    return None

def run_retrain():
    """Same as Flask admin_retrain: train_models.main() then reload models."""
    from train_models import main as run_train
    run_train()
    try:
        from ml_engine import load_all_models
        load_all_models()
    except Exception:
        pass

st.set_page_config(page_title="EvalAI — Lecturer Evaluation", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

def page_landing():
    settings = get_site_settings()
    lecturers = get_lecturer_names()
    if settings.get("show_announcement") == "true" and settings.get("announcement_banner"):
        st.info(f"📢 {settings['announcement_banner']}")
    st.markdown(f"### {settings.get('landing_title', 'Anonymous Lecturer Evaluation')}")
    st.caption(settings.get("landing_subtitle", ""))
    st.success(settings.get("privacy_notice", DEFAULT_SETTINGS["privacy_notice"]))
    if settings.get("custom_guidelines"):
        st.info(f"**Evaluation Guidelines:** {settings['custom_guidelines']}")
    with st.form("anon"):
        c1, c2 = st.columns(2)
        with c1:
            lecturer = st.selectbox("Lecturer", [""] + list(lecturers))
            course = st.text_input("Course", placeholder="e.g. Machine Learning")
        with c2:
            code = st.text_input("Course code", placeholder="e.g. CSC401")
            rating = st.selectbox("Rating", [5, 4, 3, 2, 1], index=2)
        comment = st.text_area("Comment", height=130, placeholder="Write honestly about teaching clarity, assessment, availability...")
        if st.form_submit_button("Submit anonymous evaluation", use_container_width=True):
            ok, err = save_eval(lecturer, course, code, rating, comment)
            if ok: st.success("Thank you. Your anonymous evaluation has been submitted.")
            else: st.error(err or "Failed")

def page_login():
    st.header("Staff login")
    with st.form("login"):
        u = st.text_input("Username"); p = st.text_input("Password", type="password")
        if st.form_submit_button("Sign in", use_container_width=True):
            user = authenticate(u, p)
            if user:
                st.session_state.user = user; st.rerun()
            else:
                st.error("Invalid username or password.")
    st.caption("Demo: admin / admin123 · lecturers: okafor / lecturer123")

def page_dashboard():
    st.header("Dashboard")
    df = load_feedback()
    if df.empty:
        st.warning("No feedback in the database yet."); return
    a,b,c,d = st.columns(4)
    a.metric("Total", len(df)); b.metric("Lecturers", df["lecturer_name"].nunique())
    c.metric("Courses", df["course"].nunique()); d.metric("Avg rating", f"{df['rating'].mean():.2f}")
    if "document_sentiment" in df.columns:
        st.bar_chart(df["document_sentiment"].fillna("unknown").value_counts())
    st.bar_chart(df.groupby("lecturer_name")["rating"].mean().sort_values(ascending=False))
    st.dataframe(df.head(50), use_container_width=True)

def page_report():
    st.header("Lecturer report")
    df = load_feedback()
    if df.empty: st.warning("No feedback yet."); return
    names = sorted(df["lecturer_name"].dropna().unique())
    user = st.session_state.get("user")
    if user and user.get("role") == "lecturer" and user.get("lecturer_name") in names:
        chosen = st.selectbox("Lecturer", names, index=names.index(user["lecturer_name"]))
    else:
        chosen = st.selectbox("Lecturer", names)
    sub = df[df["lecturer_name"] == chosen]
    st.metric("Evaluations", len(sub)); st.metric("Avg rating", f"{sub['rating'].mean():.2f}")
    if "document_sentiment" in sub.columns:
        st.bar_chart(sub["document_sentiment"].fillna("unknown").value_counts())
    for _, r in sub.head(25).iterrows():
        st.markdown(f"- **{r.get('document_sentiment','—')}** ({r['rating']}/5): {r['comment'][:280]}")

def page_sentiment():
    st.header("Sentiment / aspect analysis")
    text = st.text_area("Student comment", height=140)
    rating = st.slider("Rating", 1, 5, 3)
    if st.button("Analyse", use_container_width=True) and text.strip():
        st.json(analyze_comment(text, rating))

def page_model():
    st.header("Model evaluation — SVM vs Naive Bayes")
    st.caption("Comparative evaluation (existing training pipeline).")
    user = st.session_state.get("user")
    if user and user.get("role") == "administrator":
        st.subheader("Retrain models")
        st.write("Administrators can retrain SVM and Naive Bayes (same as Flask `/admin/retrain`).")
        if st.button("Retrain classifiers", type="primary":
            with st.spinner("Retraining…"):
                try:
                    run_retrain()
                    st.success("Models retrained successfully! Hyperparameters tuned and evaluation metrics updated.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Retraining error: {e}")
        st.divider()
    metrics = load_metrics()
    if not metrics:
        st.warning("model_evaluation_metrics.json not found. Run retrain to generate metrics.")
        return
    doc = metrics.get("document_level", {})
    svm, nb = doc.get("svm", {}), doc.get("naive_bayes", {})
    st.write(f"Majority baseline: **{doc.get('majority_baseline_accuracy', '—')}**")
    st.dataframe(pd.DataFrame([
        {"Model": "SVM", "Accuracy": svm.get("accuracy"), "Macro F1": svm.get("macro_f1"), "Weighted F1": svm.get("weighted_f1")},
        {"Model": "Naive Bayes", "Accuracy": nb.get("accuracy"), "Macro F1": nb.get("macro_f1"), "Weighted F1": nb.get("weighted_f1")},
    ]), use_container_width=True)
    if metrics.get("aspect_level"):
        st.subheader("Aspect-level"); st.dataframe(pd.DataFrame(metrics["aspect_level"]), use_container_width=True)

def main():
    if "user" not in st.session_state:
        st.session_state.user = None
    init_db(DATABASE_PATH)
    st.sidebar.title("EvalAI")
    user = st.session_state.user
    if user:
        st.sidebar.markdown(f"**{user.get('full_name') or user['username']}** ({user['role']})")
        nav = ["Landing / Student evaluation", "Dashboard", "Lecturer report", "Sentiment analysis", "Model evaluation", "Logout"]
    else:
        nav = ["Landing / Student evaluation", "Staff login"]
    choice = st.sidebar.radio("Navigate", nav)
    if choice == "Landing / Student evaluation": page_landing()
    elif choice == "Staff login": page_login()
    elif choice == "Logout":
        st.session_state.user = None; st.rerun()
    elif choice == "Dashboard": page_dashboard()
    elif choice == "Lecturer report": page_report()
    elif choice == "Sentiment analysis": page_sentiment()
    elif choice == "Model evaluation": page_model()

if __name__ == "__main__":
    main()
