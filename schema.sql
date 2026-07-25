DROP TABLE IF EXISTS submissions;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS project_milestones;
DROP TABLE IF EXISTS weeks;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student','instructor')),
    cohort TEXT,
    assigned_instructor_id INTEGER,
    selected_project_id INTEGER,
    is_admin INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (assigned_instructor_id) REFERENCES users(id),
    FOREIGN KEY (selected_project_id) REFERENCES projects(id)
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_number INTEGER NOT NULL UNIQUE,
    industry TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    entities TEXT NOT NULL,
    personas TEXT NOT NULL,
    process TEXT NOT NULL,
    integration TEXT NOT NULL,
    workspace TEXT NOT NULL,
    agent TEXT NOT NULL,
    accent TEXT NOT NULL
);

CREATE TABLE weeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_number INTEGER NOT NULL UNIQUE,
    stage TEXT NOT NULL,
    title TEXT NOT NULL,
    topics TEXT NOT NULL,
    research_topic TEXT NOT NULL,
    linkedin_topic TEXT NOT NULL
);

CREATE TABLE project_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    instructions TEXT NOT NULL,
    deliverable TEXT NOT NULL,
    is_final INTEGER NOT NULL DEFAULT 0,
    UNIQUE(project_id, week_number),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id INTEGER NOT NULL,
    assignment_key TEXT UNIQUE,
    program_version TEXT NOT NULL DEFAULT 'v5',
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

CREATE INDEX idx_users_assigned_instructor ON users(assigned_instructor_id);
CREATE INDEX idx_users_selected_project ON users(selected_project_id);
CREATE INDEX idx_milestones_project_week ON project_milestones(project_id, week_number);
CREATE INDEX idx_submissions_student ON submissions(student_id);
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_assignments_week ON assignments(week_id);
