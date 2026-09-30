"""Rebuild data/feedback.db from feedback_seed.sql (full original DB contents)."""
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
SQL = DATA / "feedback_seed.sql"
DB = DATA / "feedback.db"

def ensure_database():
    DATA.mkdir(exist_ok=True)
    if DB.exists() and DB.stat().st_size > 0:
        try:
            con = sqlite3.connect(DB)
            n = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            con.close()
            if n > 0:
                return str(DB)
        except Exception:
            pass
    if not SQL.exists():
        return str(DB)
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(SQL.read_text(encoding="utf-8"))
    con.commit()
    con.close()
    return str(DB)

if __name__ == "__main__":
    print(ensure_database())
