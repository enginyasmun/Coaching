"""Rerunnable migration for instructor ownership and five industry projects."""

from datetime import datetime, timezone
from pathlib import Path
import os
import shutil
import sqlite3

from curriculum_data import PROJECTS, PROJECT_MILESTONES, project_for_week

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "academy.db"))


def column_names(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def table_exists(conn, table):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


if not DB_PATH.exists():
    raise SystemExit(f"Database not found: {DB_PATH}")

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
backup_path = DB_PATH.with_name(f"{DB_PATH.stem}_backup_before_v4_{timestamp}{DB_PATH.suffix}")
shutil.copy2(DB_PATH, backup_path)

with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    users_columns = column_names(conn, "users")
    if "assigned_instructor_id" not in users_columns:
        conn.execute("ALTER TABLE users ADD COLUMN assigned_instructor_id INTEGER")
    if "is_admin" not in users_columns:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")

    if not table_exists(conn, "projects"):
        conn.execute(
            """
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_number INTEGER NOT NULL UNIQUE,
                industry TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                final_deliverable TEXT NOT NULL,
                week_start INTEGER NOT NULL,
                week_end INTEGER NOT NULL,
                accent TEXT NOT NULL
            )
            """
        )

    weeks_columns = column_names(conn, "weeks")
    if "project_id" not in weeks_columns:
        conn.execute("ALTER TABLE weeks ADD COLUMN project_id INTEGER")

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_assigned_instructor ON users(assigned_instructor_id)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_weeks_project ON weeks(project_id)")

    admin = conn.execute(
        """
        SELECT * FROM users
        WHERE role='instructor' AND is_admin=1
        ORDER BY is_active DESC, id
        LIMIT 1
        """
    ).fetchone()
    if admin is None:
        admin = conn.execute(
            """
            SELECT * FROM users
            WHERE role='instructor'
            ORDER BY is_active DESC, id
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
        SET cohort='Class ' || trim(substr(cohort, 7))
        WHERE role='student' AND cohort LIKE 'Cohort %'
        """
    )

    project_ids = {}
    for project in PROJECTS:
        existing = conn.execute(
            "SELECT id FROM projects WHERE project_number=?", (project["number"],)
        ).fetchone()
        values = (
            project["industry"], project["title"], project["summary"],
            project["final_deliverable"], project["week_start"],
            project["week_end"], project["accent"], project["number"],
        )
        if existing:
            conn.execute(
                """
                UPDATE projects
                SET industry=?,title=?,summary=?,final_deliverable=?,
                    week_start=?,week_end=?,accent=?
                WHERE project_number=?
                """,
                values,
            )
            project_ids[project["number"]] = existing["id"]
        else:
            project_ids[project["number"]] = conn.execute(
                """
                INSERT INTO projects
                (industry,title,summary,final_deliverable,week_start,week_end,accent,project_number)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                values,
            ).lastrowid

    week_rows = conn.execute("SELECT id, week_number FROM weeks ORDER BY week_number").fetchall()
    for week in week_rows:
        number = week["week_number"]
        project = project_for_week(number)
        milestone = PROJECT_MILESTONES[number]
        conn.execute(
            "UPDATE weeks SET project_id=?, hands_on=? WHERE id=?",
            (project_ids[project["number"]], milestone["instructions"], week["id"]),
        )
        conn.execute(
            """
            UPDATE assignments
            SET title=?, instructions=?, deliverable=?
            WHERE week_id=? AND category='Hands-On'
            """,
            (
                f"Week {number} Project Build: {milestone['title']}",
                milestone["instructions"],
                milestone["deliverable"],
                week["id"],
            ),
        )

        if number == project["week_end"]:
            capstone = conn.execute(
                """
                SELECT id FROM assignments
                WHERE week_id=? AND category='Capstone'
                """,
                (week["id"],),
            ).fetchone()
            due_row = conn.execute(
                "SELECT due_date FROM assignments WHERE week_id=? ORDER BY id LIMIT 1",
                (week["id"],),
            ).fetchone()
            due_date = due_row["due_date"] if due_row else None
            title = f"Final Project {project['number']}: {project['title']}"
            instructions = (
                f"Consolidate the four weekly project-build milestones into one complete "
                f"{project['industry']} application. Demonstrate the business process, "
                "architecture, security, automation or code, testing, and deployment readiness."
            )
            if capstone:
                conn.execute(
                    """
                    UPDATE assignments
                    SET title=?, instructions=?, deliverable=?, max_score=150
                    WHERE id=?
                    """,
                    (title, instructions, project["final_deliverable"], capstone["id"]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO assignments
                    (week_id,title,category,instructions,deliverable,max_score,due_date,is_published)
                    VALUES (?,?,?,?,?,150,?,1)
                    """,
                    (
                        week["id"], title, "Capstone", instructions,
                        project["final_deliverable"], due_date,
                    ),
                )

    conn.commit()

with sqlite3.connect(DB_PATH) as conn:
    instructor_count = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='instructor'"
    ).fetchone()[0]
    assigned_students = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='student' AND assigned_instructor_id IS NOT NULL"
    ).fetchone()[0]
    project_count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    capstone_count = conn.execute(
        "SELECT COUNT(*) FROM assignments WHERE category='Capstone'"
    ).fetchone()[0]

print(f"Migration completed: {DB_PATH}")
print(f"Backup created: {backup_path}")
print(f"Instructors: {instructor_count}")
print(f"Students assigned to an instructor: {assigned_students}")
print(f"Industry projects: {project_count}")
print(f"Final-project assignments: {capstone_count}")
