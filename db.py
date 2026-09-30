import os
import sqlite3
import pandas as pd
try:
    from flask import g
except ImportError:
    g = None
from werkzeug.security import generate_password_hash

DEMO_LECTURERS = [
    "Dr. Okafor", "Dr. Adeyemi", "Prof. Martins", "Dr. Faith",
    "Dr. Pomele", "Prof. Balogun", "Dr. Chukwu", "Dr. (Mrs) Adeleke",
]

DEMO_USERS = [
    ("admin", "admin123", "administrator", None, "System Administrator"),
    ("okafor", "lecturer123", "lecturer", "Dr. Okafor", "Dr. Okafor"),
    ("adeyemi", "lecturer123", "lecturer", "Dr. Adeyemi", "Dr. Adeyemi"),
    ("martins", "lecturer123", "lecturer", "Prof. Martins", "Prof. Martins"),
    ("faith", "lecturer123", "lecturer", "Dr. Faith", "Dr. Faith"),
    ("pomele", "lecturer123", "lecturer", "Dr. Pomele", "Dr. Pomele"),
    ("balogun", "lecturer123", "lecturer", "Prof. Balogun", "Prof. Balogun"),
    ("chukwu", "lecturer123", "lecturer", "Dr. Chukwu", "Dr. Chukwu"),
    ("adeleke", "lecturer123", "lecturer", "Dr. (Mrs) Adeleke", "Dr. (Mrs) Adeleke"),
]

DATABASE_PATH = "data/feedback.db"

DEFAULT_SETTINGS = {
    "announcement_banner": "2025/2026 Academic Session — Anonymous Student Evaluation of Teaching (SET) Portal Active",
    "show_announcement": "true",
    "landing_title": "Anonymous Lecturer Evaluation",
    "landing_subtitle": "Share numerical ratings and free-text comments. Your name and student identity are never stored.",
    "privacy_notice": "This form does not collect student name, matric number, or login details. Only the lecturer, course, rating, and comment are saved for analysis.",
    "custom_guidelines": "Please evaluate objectively based on course engagement, syllabus delivery, and instructional clarity.",
}

def get_connection(db_path=DATABASE_PATH):
    con = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA synchronous = NORMAL;")
    con.execute("PRAGMA cache_size = -64000;")
    con.execute("PRAGMA temp_store = MEMORY;")
    return con

def get_db():
    if g is None:
        return get_connection(DATABASE_PATH)
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = get_connection(DATABASE_PATH)
    return db

def init_db(db_path=DATABASE_PATH):
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    db = get_connection(db_path)
    db.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT, matric_number TEXT,
        lecturer_name TEXT NOT NULL, course TEXT NOT NULL, course_code TEXT,
        rating INTEGER NOT NULL, comment TEXT NOT NULL,
        document_sentiment TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
        role TEXT NOT NULL, lecturer_name TEXT, full_name TEXT)''')
    for col in ["student_name TEXT", "matric_number TEXT", "document_sentiment TEXT"]:
        try:
            db.execute(f"ALTER TABLE feedback ADD COLUMN {col}")
        except Exception:
            pass
    db.execute("CREATE TABLE IF NOT EXISTS site_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    for key, val in DEFAULT_SETTINGS.items():
        db.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)", (key, val))
    for idx_name, idx_def in [
        ("idx_feedback_lecturer", "feedback(lecturer_name)"),
        ("idx_feedback_course", "feedback(course)"),
        ("idx_users_username", "users(username)"),
    ]:
        try:
            db.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
        except Exception:
            pass
    existing = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing == 0:
        for username, password, role, lecturer_name, full_name in DEMO_USERS:
            db.execute(
                "INSERT INTO users (username, password_hash, role, lecturer_name, full_name) VALUES (?, ?, ?, ?, ?)",
                (username, generate_password_hash(password), role, lecturer_name, full_name),
            )
    db.commit()
    db.close()

def get_lecturer_names():
    names = []
    try:
        db = get_db()
        rows = db.execute("SELECT DISTINCT lecturer_name FROM users WHERE role = 'lecturer' AND lecturer_name IS NOT NULL").fetchall()
        for row in rows:
            if row["lecturer_name"] and row["lecturer_name"] not in names:
                names.append(row["lecturer_name"])
        fb = db.execute("SELECT DISTINCT lecturer_name FROM feedback WHERE lecturer_name IS NOT NULL ORDER BY lecturer_name").fetchall()
        for row in fb:
            if row["lecturer_name"] and row["lecturer_name"] not in names:
                names.append(row["lecturer_name"])
    except Exception:
        pass
    return sorted(names) if names else list(DEMO_LECTURERS)

def get_site_settings():
    settings = dict(DEFAULT_SETTINGS)
    try:
        db = get_db()
        for r in db.execute("SELECT key, value FROM site_settings").fetchall():
            settings[r["key"]] = r["value"]
    except Exception:
        pass
    return settings

def update_site_settings(new_settings):
    db = get_db()
    for key, val in new_settings.items():
        db.execute(
            "INSERT INTO site_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(val)),
        )
    db.commit()
