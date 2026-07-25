from datetime import datetime, date, timedelta, timezone
import sqlite3
import os
import hashlib
import secrets
from pathlib import Path

from curriculum_data import PROGRAM_WEEKS, PROJECTS, PROJECT_MILESTONES

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
        (name,email,password_hash,role,cohort,assigned_instructor_id,
         selected_project_id,is_admin,is_active,created_at)
        VALUES (?,?,?,?,?,NULL,NULL,1,1,?)
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

    project_ids = {}
    for project in PROJECTS:
        project_ids[project["number"]] = conn.execute(
            """
            INSERT INTO projects
            (project_number,industry,title,summary,entities,personas,process,
             integration,workspace,agent,accent)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                project["number"], project["industry"], project["title"],
                project["summary"], project["entities"], project["personas"],
                project["process"], project["integration"], project["workspace"],
                project["agent"], project["accent"],
            ),
        ).lastrowid

    demo_project_number = int(os.environ.get("DEMO_STUDENT_PROJECT", "1"))
    demo_project_id = project_ids.get(demo_project_number, project_ids[1])
    conn.execute(
        """
        INSERT INTO users
        (name,email,password_hash,role,cohort,assigned_instructor_id,
         selected_project_id,is_admin,is_active,created_at)
        VALUES (?,?,?,?,?,?,?,0,1,?)
        """,
        (
            os.environ.get("DEMO_STUDENT_NAME", "Demo Student"),
            os.environ.get("DEMO_STUDENT_EMAIL", "student@example.com"),
            generate_password_hash(
                os.environ.get("DEMO_STUDENT_PASSWORD", "Student123!")
            ),
            "student",
            "Class 1",
            admin_id,
            demo_project_id,
            now,
        ),
    )

    for project in PROJECTS:
        project_id = project_ids[project["number"]]
        for milestone in PROJECT_MILESTONES[project["number"]]:
            conn.execute(
                """
                INSERT INTO project_milestones
                (project_id,week_number,title,instructions,deliverable,is_final)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    project_id, milestone["week_number"], milestone["title"],
                    milestone["instructions"], milestone["deliverable"],
                    milestone["is_final"],
                ),
            )

    start = date.today()
    for item in PROGRAM_WEEKS:
        week_number, stage, title, topics, research_topic, linkedin_topic = item
        week_id = conn.execute(
            """
            INSERT INTO weeks
            (week_number,stage,title,topics,research_topic,linkedin_topic)
            VALUES (?,?,?,?,?,?)
            """,
            item,
        ).lastrowid
        due = (start + timedelta(days=week_number * 7)).isoformat()

        if week_number < 16:
            category = "Hands-On"
            assignment_title = f"Week {week_number} Project Build"
            assignment_key = f"v5:w{week_number:02d}:build"
            max_score = 100
            instructions = (
                "Complete the Week "
                f"{week_number} milestone for your selected industry application."
            )
            deliverable = (
                "The required deliverable is defined by the project plan selected "
                "for your student account."
            )
        else:
            category = "Capstone"
            assignment_title = "Week 16 Final Industry Application"
            assignment_key = "v5:w16:capstone"
            max_score = 150
            instructions = (
                "Complete, deploy, document, and demonstrate the full application "
                "for your selected industry project."
            )
            deliverable = (
                "A production-style Salesforce application, source repository, "
                "architecture documentation, tests, release evidence, agent "
                "guardrails, and final stakeholder demonstration."
            )

        conn.execute(
            """
            INSERT INTO assignments
            (week_id,assignment_key,program_version,title,category,instructions,
             deliverable,max_score,due_date,is_published)
            VALUES (?,?, 'v5',?,?,?,?,?,?,1)
            """,
            (
                week_id, assignment_key, assignment_title, category,
                instructions, deliverable, max_score, due,
            ),
        )
        conn.execute(
            """
            INSERT INTO assignments
            (week_id,assignment_key,program_version,title,category,instructions,
             deliverable,max_score,due_date,is_published)
            VALUES (?,?, 'v5',?,?,?,?,100,?,1)
            """,
            (
                week_id, f"v5:w{week_number:02d}:research",
                f"Week {week_number} Research: {research_topic}", "Research",
                research_topic,
                "500 to 1,000 words, at least three credible sources including "
                "one official Salesforce source, one practical example, and a "
                "personal conclusion.",
                due,
            ),
        )
        conn.execute(
            """
            INSERT INTO assignments
            (week_id,assignment_key,program_version,title,category,instructions,
             deliverable,max_score,due_date,is_published)
            VALUES (?,?, 'v5',?,?,?,?,100,?,1)
            """,
            (
                week_id, f"v5:w{week_number:02d}:linkedin",
                f"Week {week_number} LinkedIn: {linkedin_topic}", "LinkedIn",
                linkedin_topic,
                "Submit a mentor-reviewed draft first. After approval, publish it "
                "and add the LinkedIn post URL.",
                due,
            ),
        )

    conn.commit()

print(f"Database initialized at {DB_PATH}")
print(f"Instructor email: {admin_email}")
print("Program: 16 weeks, 5 project choices, 48 assignments per student.")
