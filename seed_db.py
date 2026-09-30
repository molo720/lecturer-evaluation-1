"""Ensure data/feedback.db contains original users/settings and evaluation records."""
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DB = DATA / "feedback.db"
CSV = DATA / "synthetic_evaluations.csv"

# Original password hashes from the project database (admin123 / lecturer123)
USERS = [
    (1, "admin", "scrypt:32768:8:1$lpaA1AUv2wTB1JTz$2413b8aba4146700c920383c0317fdee99932eec46bf08b950a6509a4c42dd293e68402f64a08745de6a4367260962403f82a117829a787a5173a59f33041eae", "administrator", None, "System Administrator"),
    (2, "okafor", "scrypt:32768:8:1$x78Zeeuu86R9emNW$5d62c5becae89c8aaad36a85d64f33d2650ed729645e2a4a1c70f9dcf126c3318f22f79043c377203eeff6a23bfa1d5fb1a3fead72439e04c54b4f3d356b06e5", "lecturer", "Dr. Okafor", "Dr. Okafor"),
    (3, "adeyemi", "scrypt:32768:8:1$zQWM0t94Xu5PYgI1$6abcbacebdb2f6dcc415cac58da476cb9056b3a42f2fc6d9539466dc34afce02fc0cc1b6c73acd837f9cf711bf3fce41c0f428d722224542f05e1dad091a9a11", "lecturer", "Dr. Adeyemi", "Dr. Adeyemi"),
    (4, "martins", "scrypt:32768:8:1$G7FE1DMlpCmaTaKR$b46344204c6a1d2f4e79e35cba938f2212b0634273b90f810e664028883310066eeab98007538db52fc3294195dd7ab6abca6174a510ad4ba9ca05c368db1902", "lecturer", "Prof. Martins", "Prof. Martins"),
    (5, "faith", "scrypt:32768:8:1$eH5JHTW2AbTAa0N9$417e4a953e109441c8acab59d4bfc7e0e6bf4a5c76f24fb2c0b6e56742fd0d24a23cd91bfe8a1ee95bded9453967ec5777316c8ea8b4b99469b7d3900ba7222b", "lecturer", "Dr. Faith", "Dr. Faith"),
    (6, "pomele", "scrypt:32768:8:1$XQPLv5EAhOpzvEDY$5dc1c1056922dd10a76ae4dd681416766f2a3fff36acf1e7d8506d486104dc06ddfc9ca91bc3ab22c1c5ec758d19c6751ffc6c6c88f1ebb74ee7fe1e427fe8bb", "lecturer", "Dr. Pomele", "Dr. Pomele"),
    (7, "balogun", "scrypt:32768:8:1$jYZW64JQuIi7TxKW$ddefb6367da7bb3c78046341ff7a91dbff4ae5174a65383b23ff85d790fffdd47945d3c4295a28bb4b98473124931847d5a9f61223e4bd460d34d76d6162a5d8", "lecturer", "Prof. Balogun", "Prof. Balogun"),
    (8, "chukwu", "scrypt:32768:8:1$IEiRtNWkty0LecmZ$784d4b41ce6176e38bd1f7a088cf63be4358160ce7f0aed8390b4a7490cdf039c04144ee5f003f43a67f7c4425d78a3c824962231cb7bef638e4ff88f5bc44a2", "lecturer", "Dr. Chukwu", "Dr. Chukwu"),
    (9, "adeleke", "scrypt:32768:8:1$4ZChBYRJ2g3egvuk$4e67f7de24cb5a466c5d68d7eb6aae500e6433eb38c60618c773a9e504e89c0f186e3acba302ba3e8e4bab6ab61005e2c2aada4ece0abc6781dac5a8edc43b9a", "lecturer", "Dr. (Mrs) Adeleke", "Dr. (Mrs) Adeleke"),
]

SETTINGS = {
    "announcement_banner": "2025/2026 Academic Session — Anonymous Student Evaluation of Teaching (SET) Portal Active",
    "show_announcement": "true",
    "landing_title": "Anonymous Lecturer Evaluation",
    "landing_subtitle": "Share numerical ratings and free-text comments. Your name and student identity are never stored.",
    "privacy_notice": "This form does not collect student name, matric number, or login details. Only the lecturer, course, rating, and comment are saved for analysis.",
    "custom_guidelines": "Please evaluate objectively based on course engagement, syllabus delivery, and instructional clarity.",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    matric_number TEXT,
    lecturer_name TEXT NOT NULL,
    course TEXT NOT NULL,
    course_code TEXT,
    rating INTEGER NOT NULL,
    comment TEXT NOT NULL,
    document_sentiment TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    lecturer_name TEXT,
    full_name TEXT
);
CREATE TABLE IF NOT EXISTS site_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

def _create_schema(con):
    con.executescript(SCHEMA)

def _seed_users_settings(con):
    n = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if n == 0:
        for row in USERS:
            con.execute(
                "INSERT INTO users (id, username, password_hash, role, lecturer_name, full_name) VALUES (?,?,?,?,?,?)",
                row,
            )
    for k, v in SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)", (k, v))

def _seed_feedback(con):
    n = con.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
    if n > 0:
        return
    if CSV.exists():
        try:
            import pandas as pd
            df = pd.read_csv(CSV)
            for _, row in df.iterrows():
                con.execute(
                    """INSERT INTO feedback
                       (lecturer_name, course, course_code, rating, comment, document_sentiment, student_name, matric_number)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        str(row.get("lecturer_name", "Unknown")),
                        str(row.get("course", "Unknown")),
                        str(row.get("course_code", "")),
                        int(row.get("rating", 3)),
                        str(row.get("comment", "")),
                        str(row.get("document_sentiment", "neutral")),
                        "Anonymous",
                        "ANON",
                    ),
                )
            return
        except Exception:
            pass
    try:
        from train_models import generate_synthetic_dataset
        df = generate_synthetic_dataset(1600)
        for _, row in df.iterrows():
            con.execute(
                """INSERT INTO feedback
                   (lecturer_name, course, course_code, rating, comment, document_sentiment, student_name, matric_number)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    str(row.get("lecturer_name", "Unknown")),
                    str(row.get("course", "Unknown")),
                    str(row.get("course_code", "")),
                    int(row.get("rating", 3)),
                    str(row.get("comment", "")),
                    str(row.get("document_sentiment", "neutral")),
                    "Anonymous",
                    "ANON",
                ),
            )
        return
    except Exception:
        pass
    import random
    random.seed(42)
    lecturers = [u[4] for u in USERS if u[4]]
    for i in range(500):
        sent = random.choices(["positive", "negative", "neutral"], weights=[0.42, 0.38, 0.2])[0]
        rating = {"positive": 5, "negative": 2, "neutral": 3}[sent]
        comment = {
            "positive": "Explains concepts clearly and is always available for students.",
            "negative": "Classes are often late and explanations are hard to follow.",
            "neutral": "Course follows the standard syllabus adequately.",
        }[sent]
        con.execute(
            """INSERT INTO feedback
               (lecturer_name, course, course_code, rating, comment, document_sentiment, student_name, matric_number)
               VALUES (?,?,?,?,?,?,?,?)""",
            (random.choice(lecturers), "Machine Learning", "CSC408", rating, comment, sent, "Anonymous", "ANON"),
        )

def ensure_database():
    """Create/repair data/feedback.db with original users and evaluation data."""
    DATA.mkdir(exist_ok=True)
    con = sqlite3.connect(str(DB), check_same_thread=False)
    try:
        _create_schema(con)
        _seed_users_settings(con)
        _seed_feedback(con)
        con.commit()
    finally:
        con.close()
    return str(DB)

if __name__ == "__main__":
    p = ensure_database()
    con = sqlite3.connect(p)
    print("db", p)
    print("users", con.execute("SELECT COUNT(*) FROM users").fetchone()[0])
    print("feedback", con.execute("SELECT COUNT(*) FROM feedback").fetchone()[0])
    print("settings", con.execute("SELECT COUNT(*) FROM site_settings").fetchone()[0])
    con.close()
