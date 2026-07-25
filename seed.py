from datetime import datetime, date, timedelta, timezone
import sqlite3
import os
import hashlib
import secrets
from pathlib import Path

from curriculum_data import BASE_WEEKS, PROJECTS, PROJECT_MILESTONES, project_for_week

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "academy.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
PASSWORD_ITERATIONS = 260_000


def generate_password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PASSWORD_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


with get_db() as conn:
    existing = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()
    if existing and os.environ.get("RESET_DB") != "1":
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count > 0:
            print(f"Existing database retained at {DB_PATH}")
            raise SystemExit(0)

    conn.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")
    admin_id = conn.execute(
        """
        INSERT INTO users
        (name,email,password_hash,role,cohort,assigned_instructor_id,is_admin,is_active,created_at)
        VALUES (?,?,?,?,?,NULL,1,1,?)
        """,
        (
            os.environ.get("ADMIN_NAME", "Academy Instructor"),
            admin_email,
            generate_password_hash(admin_password),
            "instructor",
            None,
            now,
        ),
    ).lastrowid

    conn.execute(
        """
        INSERT INTO users
        (name,email,password_hash,role,cohort,assigned_instructor_id,is_admin,is_active,created_at)
        VALUES (?,?,?,?,?,?,0,1,?)
        """,
        (
            os.environ.get("DEMO_STUDENT_NAME", "Demo Student"),
            os.environ.get("DEMO_STUDENT_EMAIL", "student@example.com"),
            generate_password_hash(os.environ.get("DEMO_STUDENT_PASSWORD", "Student123!")),
            "student",
            "Class 1",
            admin_id,
            now,
        ),
    )

    project_ids = {}
    for project in PROJECTS:
        project_ids[project["number"]] = conn.execute(
            """
            INSERT INTO projects
            (project_number,industry,title,summary,final_deliverable,week_start,week_end,accent)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                project["number"], project["industry"], project["title"],
                project["summary"], project["final_deliverable"],
                project["week_start"], project["week_end"], project["accent"],
            ),
        ).lastrowid

    start = date.today()
    for item in BASE_WEEKS:
        week_number, stage, title, topics, _old_hands_on, research_topic, linkedin_topic = item
        project = project_for_week(week_number)
        milestone = PROJECT_MILESTONES[week_number]
        week_id = conn.execute(
            """
            INSERT INTO weeks
            (week_number,project_id,stage,title,topics,hands_on,research_topic,linkedin_topic)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                week_number, project_ids[project["number"]], stage, title, topics,
                milestone["instructions"], research_topic, linkedin_topic,
            ),
        ).lastrowid
        due = (start + timedelta(days=week_number * 7)).isoformat()

        conn.execute(
            """
            INSERT INTO assignments
            (week_id,title,category,instructions,deliverable,max_score,due_date,is_published)
            VALUES (?,?,?,?,?,?,?,1)
            """,
            (
                week_id,
                f"Week {week_number} Project Build: {milestone['title']}",
                "Hands-On",
                milestone["instructions"],
                milestone["deliverable"],
                100,
                due,
            ),
        )
        conn.execute(
            """
            INSERT INTO assignments
            (week_id,title,category,instructions,deliverable,max_score,due_date,is_published)
            VALUES (?,?,?,?,?,?,?,1)
            """,
            (
                week_id,
                f"Week {week_number} Research: {research_topic}",
                "Research",
                research_topic,
                "500 to 1,000 words, at least three credible sources including one official Salesforce source, one practical example, and a personal conclusion.",
                100,
                due,
            ),
        )
        conn.execute(
            """
            INSERT INTO assignments
            (week_id,title,category,instructions,deliverable,max_score,due_date,is_published)
            VALUES (?,?,?,?,?,?,?,1)
            """,
            (
                week_id,
                f"Week {week_number} LinkedIn: {linkedin_topic}",
                "LinkedIn",
                linkedin_topic,
                "Submit a mentor-reviewed draft first. After approval, publish it and add the LinkedIn post URL.",
                100,
                due,
            ),
        )

        if week_number == project["week_end"]:
            conn.execute(
                """
                INSERT INTO assignments
                (week_id,title,category,instructions,deliverable,max_score,due_date,is_published)
                VALUES (?,?,?,?,?,?,?,1)
                """,
                (
                    week_id,
                    f"Final Project {project['number']}: {project['title']}",
                    "Capstone",
                    f"Consolidate the four weekly project-build milestones into one complete {project['industry']} application. Demonstrate the business process, architecture, security, automation or code, testing, and deployment readiness.",
                    project["final_deliverable"],
                    150,
                    due,
                ),
            )

    conn.commit()

print(f"Database initialized at {DB_PATH}")
print(f"Instructor email: {admin_email}")
print("The instructor password is the ADMIN_PASSWORD value used during initialization.")
