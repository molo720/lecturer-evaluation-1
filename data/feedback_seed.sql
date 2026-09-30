BEGIN TRANSACTION;
CREATE TABLE feedback (
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
INSERT INTO feedback VALUES(1,'Anonymous','ANON','Dr. Okafor','Machine Learning','CSC408',5,'Explains complex concepts with clarity and precision. Always available during office hours.','positive','2025-09-15 10:00:00');
INSERT INTO feedback VALUES(2,'Anonymous','ANON','Dr. Adeyemi','Database Design','CSC302',2,'Explanations are confusing and lack structure. Habitually late to lectures.','negative','2025-09-16 11:00:00');
INSERT INTO feedback VALUES(3,'Anonymous','ANON','Prof. Martins','Cloud Computing','CSC406',3,'Lectures follow the textbook explanations adequately.','neutral','2025-09-17 12:00:00');
CREATE TABLE sqlite_sequence(name,seq);
INSERT INTO sqlite_sequence VALUES('feedback',3);
INSERT INTO sqlite_sequence VALUES('users',9);
CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            lecturer_name TEXT,
            full_name TEXT
        );
CREATE TABLE site_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
CREATE INDEX idx_feedback_lecturer ON feedback(lecturer_name);
CREATE INDEX idx_feedback_course ON feedback(course);
CREATE INDEX idx_feedback_submitted_at ON feedback(submitted_at DESC);
CREATE INDEX idx_feedback_rating ON feedback(rating);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_lecturer_name ON users(lecturer_name);
COMMIT;
