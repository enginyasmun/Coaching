DROP TABLE IF EXISTS submissions;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS weeks;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student','instructor')),
    cohort TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE weeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_number INTEGER NOT NULL UNIQUE,
    stage TEXT NOT NULL,
    title TEXT NOT NULL,
    topics TEXT NOT NULL,
    hands_on TEXT NOT NULL,
    research_topic TEXT NOT NULL,
    linkedin_topic TEXT NOT NULL
);

CREATE TABLE assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('Hands-On','Research','LinkedIn','Reflection','Capstone')),
    instructions TEXT NOT NULL,
    deliverable TEXT NOT NULL,
    max_score REAL NOT NULL DEFAULT 100,
    due_date TEXT,
    is_published INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (week_id) REFERENCES weeks(id) ON DELETE CASCADE
);

CREATE TABLE submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Draft'
        CHECK(status IN ('Draft','Submitted','Under Review','Revision Required','Approved','Late')),
    submission_text TEXT,
    submission_url TEXT,
    linkedin_url TEXT,
    student_note TEXT,
    file_name TEXT,
    score REAL,
    mentor_feedback TEXT,
    submitted_at TEXT,
    graded_at TEXT,
    graded_by INTEGER,
    updated_at TEXT NOT NULL,
    revision_number INTEGER NOT NULL DEFAULT 0,
    UNIQUE(assignment_id, student_id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (graded_by) REFERENCES users(id)
);

CREATE INDEX idx_submissions_student ON submissions(student_id);
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_assignments_week ON assignments(week_id);
