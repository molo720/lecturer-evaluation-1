BEGIN TRANSACTION;
CREATE TABLE feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lecturer_name TEXT NOT NULL,
            course TEXT NOT NULL,
            course_code TEXT,
            rating INTEGER NOT NULL,
            comment TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        , document_sentiment TEXT, student_name TEXT, matric_number TEXT);
INSERT INTO "feedback" VALUES(1,'Dr Okafor','Machine Learning','CSC101',3,'Explains clearly but does not encourage participation','2026-09-05 18:34:01',NULL,NULL,NULL);
INSERT INTO "feedback" VALUES(2,'Dr. Okafor','Machine Learning','CSC101',5,'Explains concept clearly','2026-09-16 17:03:16','positive','Anonymous','ANON');
INSERT INTO "feedback" VALUES(3,'Prof. Balogun','Data Science','Csc 406',3,'He teaches well and is organized.','2026-09-16 17:15:31','positive','Anonymous','ANON');
CREATE TABLE site_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
INSERT INTO "site_settings" VALUES('announcement_banner','2025/2026 Academic Session — Anonymous Student Evaluation of Teaching (SET) Portal Active');
INSERT INTO "site_settings" VALUES('show_announcement','true');
INSERT INTO "site_settings" VALUES('landing_title','Anonymous Lecturer Evaluation');
INSERT INTO "site_settings" VALUES('landing_subtitle','Share numerical ratings and free-text comments. Your name and student identity are never stored.');
INSERT INTO "site_settings" VALUES('privacy_notice','This form does not collect student name, matric number, or login details. Only the lecturer, course, rating, and comment are saved for analysis.');
INSERT INTO "site_settings" VALUES('custom_guidelines','Please evaluate objectively based on course engagement, syllabus delivery, and instructional clarity.');
CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            lecturer_name TEXT,
            full_name TEXT
        );
INSERT INTO "users" VALUES(1,'admin','scrypt:32768:8:1$lpaA1AUv2wTB1JTz$2413b8aba4146700c920383c0317fdee99932eec46bf08b950a6509a4c42dd293e68402f64a08745de6a4367260962403f82a117829a787a5173a59f33041eae','administrator',NULL,'System Administrator');
INSERT INTO "users" VALUES(2,'okafor','scrypt:32768:8:1$x78Zeeuu86R9emNW$5d62c5becae89c8aaad36a85d64f33d2650ed729645e2a4a1c70f9dcf126c3318f22f79043c377203eeff6a23bfa1d5fb1a3fead72439e04c54b4f3d356b06e5','lecturer','Dr. Okafor','Dr. Okafor');
INSERT INTO "users" VALUES(3,'adeyemi','scrypt:32768:8:1$zQWM0t94Xu5PYgI1$6abcbacebdb2f6dcc415cac58da476cb9056b3a42f2fc6d9539466dc34afce02fc0cc1b6c73acd837f9cf711bf3fce41c0f428d722224542f05e1dad091a9a11','lecturer','Dr. Adeyemi','Dr. Adeyemi');
INSERT INTO "users" VALUES(4,'martins','scrypt:32768:8:1$G7FE1DMlpCmaTaKR$b46344204c6a1d2f4e79e35cba938f2212b0634273b90f810e664028883310066eeab98007538db52fc3294195dd7ab6abca6174a510ad4ba9ca05c368db1902','lecturer','Prof. Martins','Prof. Martins');
INSERT INTO "users" VALUES(5,'faith','scrypt:32768:8:1$eH5JHTW2AbTAa0N9$417e4a953e109441c8acab59d4bfc7e0e6bf4a5c76f24fb2c0b6e56742fd0d24a23cd91bfe8a1ee95bded9453967ec5777316c8ea8b4b99469b7d3900ba7222b','lecturer','Dr. Faith','Dr. Faith');
INSERT INTO "users" VALUES(6,'pomele','scrypt:32768:8:1$XQPLv5EAhOpzvEDY$5dc1c1056922dd10a76ae4dd681416766f2a3fff36acf1e7d8506d486104dc06ddfc9ca91bc3ab22c1c5ec758d19c6751ffc6c6c88f1ebb74ee7fe1e427fe8bb','lecturer','Dr. Pomele','Dr. Pomele');
INSERT INTO "users" VALUES(7,'balogun','scrypt:32768:8:1$jYZW64JQuIi7TxKW$ddefb6367da7bb3c78046341ff7a91dbff4ae5174a65383b23ff85d790fffdd47945d3c4295a28bb4b98473124931847d5a9f61223e4bd460d34d76d6162a5d8','lecturer','Prof. Balogun','Prof. Balogun');
INSERT INTO "users" VALUES(8,'chukwu','scrypt:32768:8:1$IEiRtNWkty0LecmZ$784d4b41ce6176e38bd1f7a088cf63be4358160ce7f0aed8390b4a7490cdf039c04144ee5f003f43a67f7c4425d78a3c824962231cb7bef638e4ff88f5bc44a2','lecturer','Dr. Chukwu','Dr. Chukwu');
INSERT INTO "users" VALUES(9,'adeleke','scrypt:32768:8:1$4ZChBYRJ2g3egvuk$4e67f7de24cb5a466c5d68d7eb6aae500e6433eb38c60618c773a9e504e89c0f186e3acba302ba3e8e4bab6ab61005e2c2aada4ece0abc6781dac5a8edc43b9a','lecturer','Dr. (Mrs) Adeleke','Dr. (Mrs) Adeleke');
CREATE INDEX idx_feedback_lecturer ON feedback(lecturer_name);
CREATE INDEX idx_feedback_course ON feedback(course);
CREATE INDEX idx_feedback_submitted_at ON feedback(submitted_at DESC);
CREATE INDEX idx_feedback_rating ON feedback(rating);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_lecturer_name ON users(lecturer_name);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('feedback',3);
INSERT INTO "sqlite_sequence" VALUES('users',11);
COMMIT;
