"""Rerunnable migration to the 16-week student-selected project model."""

from datetime import datetime, date, timedelta, timezone
from pathlib import Path
import os
import shutil
import sqlite3

from curriculum_data import PROGRAM_WEEKS, PROJECTS, PROJECT_MILESTONES

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "academy.db"))


def table_exists(conn, table):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def add_column(conn, table, definition):
    name = definition.split()[0]
    if name not in columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


if not DB_PATH.exists():
    raise SystemExit(f"Database not found: {DB_PATH}")

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
backup_path = DB_PATH.with_name(
    f"{DB_PATH.stem}_backup_before_v5_{timestamp}{DB_PATH.suffix}"
)
shutil.copy2(DB_PATH, backup_path)

with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    add_column(conn, "users", "assigned_instructor_id INTEGER")
    add_column(conn, "users", "selected_project_id INTEGER")
    add_column(conn, "users", "is_admin INTEGER NOT NULL DEFAULT 0")

    if not table_exists(conn, "projects"):
        conn.execute(
            """
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_number INTEGER NOT NULL UNIQUE,
                industry TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                entities TEXT NOT NULL DEFAULT '',
                personas TEXT NOT NULL DEFAULT '',
                process TEXT NOT NULL DEFAULT '',
                integration TEXT NOT NULL DEFAULT '',
                workspace TEXT NOT NULL DEFAULT '',
                agent TEXT NOT NULL DEFAULT '',
                accent TEXT NOT NULL
            )
            """
        )
    else:
        for definition in (
            "entities TEXT NOT NULL DEFAULT ''",
            "personas TEXT NOT NULL DEFAULT ''",
            "process TEXT NOT NULL DEFAULT ''",
            "integration TEXT NOT NULL DEFAULT ''",
            "workspace TEXT NOT NULL DEFAULT ''",
            "agent TEXT NOT NULL DEFAULT ''",
        ):
            add_column(conn, "projects", definition)

    if not table_exists(conn, "project_milestones"):
        conn.execute(
            """
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
            )
            """
        )

    add_column(conn, "assignments", "assignment_key TEXT")
    add_column(conn, "assignments", "program_version TEXT NOT NULL DEFAULT 'legacy'")
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_assignments_key_unique
        ON assignments(assignment_key)
        WHERE assignment_key IS NOT NULL
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_users_assigned_instructor
        ON users(assigned_instructor_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_users_selected_project
        ON users(selected_project_id)
        """
    )

    admin = conn.execute(
        """
        SELECT * FROM users
        WHERE role='instructor' AND is_admin=1
        ORDER BY is_active DESC,id
        LIMIT 1
        """
    ).fetchone()
    if admin is None:
        admin = conn.execute(
            """
            SELECT * FROM users
            WHERE role='instructor'
            ORDER BY is_active DESC,id
            LIMIT 1
            """
        ).fetchone()
        if admin is None:
            raise RuntimeError("At least one instructor account is required.")
        conn.execute("UPDATE users SET is_admin=1 WHERE id=?", (admin["id"],))

    conn.execute(
        """
        UPDATE users
        SET assigned_instructor_id=?
        WHERE role='student' AND assigned_instructor_id IS NULL
        """,
        (admin["id"],),
    )
    conn.execute(
        """
        UPDATE users
        SET cohort='Class ' || trim(substr(cohort,7))
        WHERE role='student' AND cohort LIKE 'Cohort %'
        """
    )

    project_ids = {}
    for project in PROJECTS:
        existing = conn.execute(
            "SELECT id FROM projects WHERE project_number=?",
            (project["number"],),
        ).fetchone()
        values = (
            project["industry"], project["title"], project["summary"],
            project["entities"], project["personas"], project["process"],
            project["integration"], project["workspace"], project["agent"],
            project["accent"], project["number"],
        )
        if existing:
            conn.execute(
                """
                UPDATE projects
                SET industry=?,title=?,summary=?,entities=?,personas=?,process=?,
                    integration=?,workspace=?,agent=?,accent=?
                WHERE project_number=?
                """,
                values,
            )
            project_ids[project["number"]] = existing["id"]
        else:
            project_ids[project["number"]] = conn.execute(
                """
                INSERT INTO projects
                (industry,title,summary,entities,personas,process,integration,
                 workspace,agent,accent,project_number)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                values,
            ).lastrowid

    for project in PROJECTS:
        project_id = project_ids[project["number"]]
        for milestone in PROJECT_MILESTONES[project["number"]]:
            existing = conn.execute(
                """
                SELECT id FROM project_milestones
                WHERE project_id=? AND week_number=?
                """,
                (project_id, milestone["week_number"]),
            ).fetchone()
            values = (
                milestone["title"], milestone["instructions"],
                milestone["deliverable"], milestone["is_final"],
                project_id, milestone["week_number"],
            )
            if existing:
                conn.execute(
                    """
                    UPDATE project_milestones
                    SET title=?,instructions=?,deliverable=?,is_final=?
                    WHERE project_id=? AND week_number=?
                    """,
                    values,
                )
            else:
                conn.execute(
                    """
                    INSERT INTO project_milestones
                    (title,instructions,deliverable,is_final,project_id,week_number)
                    VALUES (?,?,?,?,?,?)
                    """,
                    values,
                )

    conn.execute(
        """
        UPDATE assignments
        SET is_published=0
        WHERE COALESCE(program_version,'legacy') <> 'v5'
        """
    )

    start = date.today()
    week_ids = {}
    existing_week_columns = columns(conn, "weeks")
    for item in PROGRAM_WEEKS:
        week_number, stage, title, topics, research_topic, linkedin_topic = item
        existing = conn.execute(
            "SELECT id FROM weeks WHERE week_number=?", (week_number,)
        ).fetchone()
        if existing:
            update_parts = [
                "stage=?", "title=?", "topics=?",
                "research_topic=?", "linkedin_topic=?"
            ]
            params = [stage, title, topics, research_topic, linkedin_topic]
            if "hands_on" in existing_week_columns:
                update_parts.append("hands_on=?")
                params.append("Project-specific milestone selected from project_milestones.")
            params.append(week_number)
            conn.execute(
                f"UPDATE weeks SET {','.join(update_parts)} WHERE week_number=?",
                params,
            )
            week_ids[week_number] = existing["id"]
        else:
            if "hands_on" in existing_week_columns and "project_id" in existing_week_columns:
                week_ids[week_number] = conn.execute(
                    """
                    INSERT INTO weeks
                    (week_number,project_id,stage,title,topics,hands_on,
                     research_topic,linkedin_topic)
                    VALUES (?,NULL,?,?,?,?,?,?)
                    """,
                    (
                        week_number, stage, title, topics,
                        "Project-specific milestone selected from project_milestones.",
                        research_topic, linkedin_topic,
                    ),
                ).lastrowid
            elif "hands_on" in existing_week_columns:
                week_ids[week_number] = conn.execute(
                    """
                    INSERT INTO weeks
                    (week_number,stage,title,topics,hands_on,
                     research_topic,linkedin_topic)
                    VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        week_number, stage, title, topics,
                        "Project-specific milestone selected from project_milestones.",
                        research_topic, linkedin_topic,
                    ),
                ).lastrowid
            else:
                week_ids[week_number] = conn.execute(
                    """
                    INSERT INTO weeks
                    (week_number,stage,title,topics,research_topic,linkedin_topic)
                    VALUES (?,?,?,?,?,?)
                    """,
                    item,
                ).lastrowid

        due = (start + timedelta(days=week_number * 7)).isoformat()
        if week_number < 16:
            build_category = "Hands-On"
            build_key = f"v5:w{week_number:02d}:build"
            build_title = f"Week {week_number} Project Build"
            build_score = 100
            build_instructions = (
                f"Complete Week {week_number} of the student's selected project plan."
            )
            build_deliverable = (
                "The project-specific milestone defines the required deliverable."
            )
        else:
            build_category = "Capstone"
            build_key = "v5:w16:capstone"
            build_title = "Week 16 Final Industry Application"
            build_score = 150
            build_instructions = (
                "Complete, deploy, document, and demonstrate the student's selected "
                "industry application."
            )
            build_deliverable = (
                "A production-style application, source repository, architecture "
                "documentation, tests, release evidence, agent guardrails, and final "
                "stakeholder demonstration."
            )

        assignment_specs = [
            (
                build_key, build_title, build_category, build_instructions,
                build_deliverable, build_score,
            ),
            (
                f"v5:w{week_number:02d}:research",
                f"Week {week_number} Research: {research_topic}",
                "Research", research_topic,
                "500 to 1,000 words, at least three credible sources including "
                "one official Salesforce source, one practical example, and a "
                "personal conclusion.", 100,
            ),
            (
                f"v5:w{week_number:02d}:linkedin",
                f"Week {week_number} LinkedIn: {linkedin_topic}",
                "LinkedIn", linkedin_topic,
                "Submit a mentor-reviewed draft first. After approval, publish it "
                "and add the LinkedIn post URL.", 100,
            ),
        ]

        for key, title, category, instructions, deliverable, max_score in assignment_specs:
            existing_assignment = conn.execute(
                "SELECT id FROM assignments WHERE assignment_key=?", (key,)
            ).fetchone()
            if existing_assignment:
                conn.execute(
                    """
                    UPDATE assignments
                    SET week_id=?,program_version='v5',title=?,category=?,
                        instructions=?,deliverable=?,max_score=?,due_date=?,
                        is_published=1
                    WHERE assignment_key=?
                    """,
                    (
                        week_ids[week_number], title, category, instructions,
                        deliverable, max_score, due, key,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO assignments
                    (week_id,assignment_key,program_version,title,category,
                     instructions,deliverable,max_score,due_date,is_published)
                    VALUES (?,?,'v5',?,?,?,?,?,?,1)
                    """,
                    (
                        week_ids[week_number], key, title, category,
                        instructions, deliverable, max_score, due,
                    ),
                )

    conn.commit()

with sqlite3.connect(DB_PATH) as conn:
    project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    milestone_count = conn.execute(
        "SELECT COUNT(*) FROM project_milestones"
    ).fetchone()[0]
    active_assignments = conn.execute(
        """
        SELECT COUNT(*) FROM assignments
        WHERE program_version='v5' AND is_published=1
        """
    ).fetchone()[0]
    unselected_students = conn.execute(
        """
        SELECT COUNT(*) FROM users
        WHERE role='student' AND selected_project_id IS NULL
        """
    ).fetchone()[0]

print(f"Migration completed: {DB_PATH}")
print(f"Backup created: {backup_path}")
print(f"Project choices: {project_count}")
print(f"Sixteen-week project milestones: {milestone_count}")
print(f"Assignments per student: {active_assignments}")
print(f"Students who still need to select a project: {unselected_students}")
