import os
import sqlite3
from functools import wraps
from datetime import datetime, date, timezone
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, send_from_directory
)
import hashlib
import secrets
from werkzeug.utils import secure_filename

from guided_labs import build_guided_lab

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "academy.db"))
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", BASE_DIR / "uploads"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "md", "png", "jpg", "jpeg", "zip"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-in-production")
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

PASSWORD_ITERATIONS = 260_000


def generate_password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PASSWORD_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def check_password_hash(stored, password):
    try:
        algorithm, iterations, salt, expected = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
        ).hex()
        return secrets.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def get_csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


@app.before_request
def protect_csrf():
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        expected = session.get("_csrf_token", "")
        if not expected or not sent or not secrets.compare_digest(sent, expected):
            abort(400)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query_one(sql, params=()):
    with get_db() as conn:
        return conn.execute(sql, params).fetchone()


def query_all(sql, params=()):
    with get_db() as conn:
        return conn.execute(sql, params).fetchall()


def execute(sql, params=()):
    with get_db() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in to continue.", "warning")
                return redirect(url_for("login"))
            if session.get("role") != role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        if user["role"] != "instructor" or not bool(user["is_admin"]):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_user():
    if "user_id" not in session:
        return None
    return query_one("SELECT * FROM users WHERE id=?", (session["user_id"],))


def user_is_admin(user=None):
    user = user or current_user()
    return bool(user and user["role"] == "instructor" and user["is_admin"])


def instructor_can_access_student(student_id, user=None):
    user = user or current_user()
    if not user:
        return False
    if user["role"] == "student":
        return user["id"] == student_id
    if user_is_admin(user):
        return True
    student = query_one(
        "SELECT assigned_instructor_id FROM users WHERE id=? AND role='student'",
        (student_id,),
    )
    return bool(student and student["assigned_instructor_id"] == user["id"])


def student_has_v5_work(student_id):
    row = query_one(
        """
        SELECT COUNT(*) AS total
        FROM submissions s
        JOIN assignments a ON a.id=s.assignment_id
        WHERE s.student_id=? AND a.program_version='v5'
        """,
        (student_id,),
    )
    return bool(row and row["total"])


def project_for_student(student_id):
    row = query_one(
        """
        SELECT p.*
        FROM users u
        LEFT JOIN projects p ON p.id=u.selected_project_id
        WHERE u.id=? AND u.role='student'
        """,
        (student_id,),
    )
    return row if row and row["id"] is not None else None


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@app.context_processor
def inject_globals():
    user = current_user()
    return {
        "current_user": user,
        "is_academy_admin": user_is_admin(user),
        "today": date.today().isoformat(),
        "csrf_token": get_csrf_token(),
    }


@app.route("/")
def home():
    if session.get("role") == "instructor":
        return redirect(url_for("instructor_dashboard"))
    if session.get("role") == "student":
        return redirect(url_for("student_dashboard"))
    return render_template("landing.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query_one("SELECT * FROM users WHERE lower(email)=?", (email,))
        if user and user["is_active"] and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["name"] = user["name"]
            flash(f"Welcome back, {user['name']}.", "success")
            return redirect(url_for("home"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


@app.route("/projects")
@login_required
def projects():
    user = current_user()
    rows = query_all("SELECT * FROM projects ORDER BY project_number")
    milestones = query_all(
        """
        SELECT pm.*,p.project_number,p.title AS project_title
        FROM project_milestones pm
        JOIN projects p ON p.id=pm.project_id
        ORDER BY p.project_number,pm.week_number
        """
    )
    selected_project = None
    locked = False
    if user["role"] == "student":
        selected_project = project_for_student(user["id"])
        locked = student_has_v5_work(user["id"])
    return render_template(
        "projects.html",
        projects=rows,
        milestones=milestones,
        selected_project=selected_project,
        project_locked=locked,
    )


@app.route("/student/select-project", methods=["GET", "POST"])
@role_required("student")
def select_project():
    user = current_user()
    current_project = project_for_student(user["id"])
    locked = student_has_v5_work(user["id"])
    projects = query_all("SELECT * FROM projects ORDER BY project_number")

    if request.method == "POST":
        raw_project = request.form.get("project_id", "").strip()
        try:
            project_id = int(raw_project)
        except ValueError:
            project_id = 0
        project = query_one("SELECT * FROM projects WHERE id=?", (project_id,))
        if not project:
            flash("Select a valid project.", "danger")
        elif locked and current_project and current_project["id"] != project_id:
            flash(
                "Your project is locked because project work has already been submitted. "
                "Contact the academy administrator if this must be changed.",
                "warning",
            )
        else:
            execute(
                "UPDATE users SET selected_project_id=? WHERE id=?",
                (project_id, user["id"]),
            )
            flash(f"{project['title']} is now your 16-week project.", "success")
            return redirect(url_for("student_dashboard"))

    return render_template(
        "project_selection.html",
        projects=projects,
        selected_project=current_project,
        project_locked=locked,
    )


@app.route("/curriculum")
@login_required
def curriculum():
    user = current_user()
    projects = query_all("SELECT * FROM projects ORDER BY project_number")

    if user["role"] == "student":
        if not user["selected_project_id"]:
            return redirect(url_for("select_project"))
        project_id = user["selected_project_id"]
    else:
        raw_project = request.args.get("project", "").strip()
        try:
            project_id = int(raw_project) if raw_project else projects[0]["id"]
        except ValueError:
            project_id = projects[0]["id"]

    selected_project = query_one("SELECT * FROM projects WHERE id=?", (project_id,))
    if not selected_project:
        selected_project = projects[0]
        project_id = selected_project["id"]

    weeks = query_all(
        """
        SELECT w.*,pm.title AS milestone_title,pm.instructions AS milestone_instructions,
               pm.deliverable AS milestone_deliverable,pm.is_final
        FROM weeks w
        JOIN project_milestones pm
          ON pm.week_number=w.week_number AND pm.project_id=?
        WHERE w.week_number BETWEEN 1 AND 16
        ORDER BY w.week_number
        """,
        (project_id,),
    )
    return render_template(
        "curriculum.html",
        projects=projects,
        selected_project=selected_project,
        weeks=weeks,
    )


@app.route("/curriculum/week/<int:week_number>")
@login_required
def curriculum_week(week_number):
    if not 1 <= week_number <= 16:
        abort(404)
    user = current_user()
    if user["role"] == "student":
        if not user["selected_project_id"]:
            return redirect(url_for("select_project"))
        project_id = user["selected_project_id"]
    else:
        raw_project = request.args.get("project", "").strip()
        first_project = query_one(
            "SELECT id FROM projects ORDER BY project_number LIMIT 1"
        )
        default_project_id = first_project["id"] if first_project else 0
        try:
            project_id = int(raw_project) if raw_project else default_project_id
        except ValueError:
            project_id = default_project_id

    week = query_one(
        """
        SELECT w.*,p.id AS project_id,p.project_number,p.industry,
               p.title AS project_title,p.summary AS project_summary,p.accent,
               p.entities,p.personas,p.process,p.integration,p.workspace,p.agent,
               pm.title AS milestone_title,pm.instructions AS milestone_instructions,
               pm.deliverable AS milestone_deliverable,pm.is_final
        FROM weeks w
        JOIN project_milestones pm ON pm.week_number=w.week_number
        JOIN projects p ON p.id=pm.project_id
        WHERE w.week_number=? AND p.id=?
        """,
        (week_number, project_id),
    )
    if not week:
        abort(404)
    assignments = query_all(
        """
        SELECT * FROM assignments
        WHERE week_id=(SELECT id FROM weeks WHERE week_number=?)
          AND program_version='v5' AND is_published=1
        ORDER BY CASE category
          WHEN 'Hands-On' THEN 1 WHEN 'Research' THEN 2
          WHEN 'LinkedIn' THEN 3 WHEN 'Capstone' THEN 4 ELSE 5 END
        """,
        (week_number,),
    )
    guided_lab = build_guided_lab(
        week,
        week_number,
        week["research_topic"],
        week["linkedin_topic"],
    )
    return render_template(
        "week_detail.html",
        week=week,
        assignments=assignments,
        guided_lab=guided_lab,
    )


@app.route("/student")
@role_required("student")
def student_dashboard():
    user = current_user()
    if not user["selected_project_id"]:
        flash("Choose one industry project to begin your 16-week program.", "info")
        return redirect(url_for("select_project"))

    project = project_for_student(user["id"])
    rows = query_all(
        """
        SELECT a.*,w.week_number,w.title AS week_title,
               CASE WHEN a.category IN ('Hands-On','Capstone')
                    THEN pm.title ELSE a.title END AS display_title,
               CASE WHEN a.category IN ('Hands-On','Capstone')
                    THEN pm.instructions ELSE a.instructions END AS display_instructions,
               CASE WHEN a.category IN ('Hands-On','Capstone')
                    THEN pm.deliverable ELSE a.deliverable END AS display_deliverable,
               s.id AS submission_id,s.status AS submission_status,
               s.score,s.submitted_at,s.updated_at,s.mentor_feedback
        FROM assignments a
        JOIN weeks w ON w.id=a.week_id
        LEFT JOIN project_milestones pm
          ON pm.project_id=? AND pm.week_number=w.week_number
        LEFT JOIN submissions s
          ON s.assignment_id=a.id AND s.student_id=?
        WHERE a.program_version='v5' AND a.is_published=1
          AND w.week_number BETWEEN 1 AND 16
        ORDER BY w.week_number,
          CASE a.category WHEN 'Hands-On' THEN 1 WHEN 'Research' THEN 2
          WHEN 'LinkedIn' THEN 3 WHEN 'Capstone' THEN 4 ELSE 5 END
        """,
        (project["id"], user["id"]),
    )
    summary = query_one(
        """
        SELECT COUNT(a.id) AS total,
               SUM(CASE WHEN s.status IN
                 ('Submitted','Under Review','Revision Required','Approved')
                 THEN 1 ELSE 0 END) AS submitted,
               SUM(CASE WHEN s.status='Approved' THEN 1 ELSE 0 END) AS approved,
               COALESCE(ROUND(AVG(CASE WHEN s.score IS NOT NULL THEN s.score END),1),0)
                 AS avg_score
        FROM assignments a
        JOIN weeks w ON w.id=a.week_id
        LEFT JOIN submissions s
          ON s.assignment_id=a.id AND s.student_id=?
        WHERE a.program_version='v5' AND a.is_published=1
          AND w.week_number BETWEEN 1 AND 16
        """,
        (user["id"],),
    )
    project_progress = query_all(
        """
        SELECT w.week_number,pm.title,
               a.id AS assignment_id,a.category,
               s.status,s.score
        FROM weeks w
        JOIN project_milestones pm
          ON pm.week_number=w.week_number AND pm.project_id=?
        JOIN assignments a ON a.week_id=w.id
          AND a.program_version='v5'
          AND a.category IN ('Hands-On','Capstone')
        LEFT JOIN submissions s
          ON s.assignment_id=a.id AND s.student_id=?
        WHERE w.week_number BETWEEN 1 AND 16
        ORDER BY w.week_number
        """,
        (project["id"], user["id"]),
    )
    mentor = query_one(
        """
        SELECT mentor.id,mentor.name,mentor.email
        FROM users student
        LEFT JOIN users mentor ON mentor.id=student.assigned_instructor_id
        WHERE student.id=?
        """,
        (user["id"],),
    )
    return render_template(
        "student_dashboard.html",
        rows=rows,
        summary=summary,
        project=project,
        project_progress=project_progress,
        mentor=mentor,
    )


@app.route("/student/assignment/<int:assignment_id>", methods=["GET", "POST"])
@role_required("student")
def student_assignment(assignment_id):
    user = current_user()
    if not user["selected_project_id"]:
        return redirect(url_for("select_project"))

    assignment = query_one(
        """
        SELECT a.*,w.week_number,w.title AS week_title,w.topics,
               p.id AS project_id,p.project_number,p.industry,p.title AS project_title,
               CASE WHEN a.category IN ('Hands-On','Capstone')
                    THEN pm.title ELSE a.title END AS display_title,
               CASE WHEN a.category IN ('Hands-On','Capstone')
                    THEN pm.instructions ELSE a.instructions END AS display_instructions,
               CASE WHEN a.category IN ('Hands-On','Capstone')
                    THEN pm.deliverable ELSE a.deliverable END AS display_deliverable
        FROM assignments a
        JOIN weeks w ON w.id=a.week_id
        JOIN projects p ON p.id=?
        LEFT JOIN project_milestones pm
          ON pm.project_id=p.id AND pm.week_number=w.week_number
        WHERE a.id=? AND a.program_version='v5' AND a.is_published=1
          AND w.week_number BETWEEN 1 AND 16
        """,
        (user["selected_project_id"], assignment_id),
    )
    if not assignment:
        abort(404)

    submission = query_one(
        "SELECT * FROM submissions WHERE assignment_id=? AND student_id=?",
        (assignment_id, user["id"]),
    )

    if request.method == "POST":
        status = request.form.get("status", "Draft")
        if status not in {"Draft", "Submitted"}:
            status = "Draft"
        submission_text = request.form.get("submission_text", "").strip()
        submission_url = request.form.get("submission_url", "").strip()
        linkedin_url = request.form.get("linkedin_url", "").strip()
        student_note = request.form.get("student_note", "").strip()

        filename = submission["file_name"] if submission else None
        uploaded = request.files.get("file")
        if uploaded and uploaded.filename:
            if not allowed_file(uploaded.filename):
                flash("Unsupported file type.", "danger")
                return redirect(request.url)
            safe = secure_filename(uploaded.filename)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            filename = f"{user['id']}_{assignment_id}_{timestamp}_{safe}"
            uploaded.save(UPLOAD_DIR / filename)

        now = now_iso()
        submitted_at = (
            now if status == "Submitted"
            else (submission["submitted_at"] if submission else None)
        )

        if submission:
            execute(
                """
                UPDATE submissions
                SET status=?,submission_text=?,submission_url=?,linkedin_url=?,
                    student_note=?,file_name=?,submitted_at=?,updated_at=?,
                    revision_number=revision_number +
                      CASE WHEN status='Revision Required' AND ?='Submitted'
                      THEN 1 ELSE 0 END
                WHERE id=? AND student_id=?
                """,
                (
                    status, submission_text, submission_url, linkedin_url,
                    student_note, filename, submitted_at, now, status,
                    submission["id"], user["id"],
                ),
            )
        else:
            execute(
                """
                INSERT INTO submissions
                (assignment_id,student_id,status,submission_text,submission_url,
                 linkedin_url,student_note,file_name,submitted_at,updated_at,revision_number)
                VALUES (?,?,?,?,?,?,?,?,?,?,0)
                """,
                (
                    assignment_id, user["id"], status, submission_text,
                    submission_url, linkedin_url, student_note, filename,
                    submitted_at, now,
                ),
            )
        flash("Your work has been saved.", "success")
        return redirect(url_for("student_assignment", assignment_id=assignment_id))

    return render_template(
        "student_assignment.html", assignment=assignment, submission=submission
    )


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    record = query_one(
        """
        SELECT s.student_id,u.assigned_instructor_id
        FROM submissions s
        JOIN users u ON u.id=s.student_id
        WHERE s.file_name=?
        """,
        (filename,),
    )
    if not record:
        abort(404)
    user = current_user()
    if user["role"] == "student" and record["student_id"] != user["id"]:
        abort(403)
    if (
        user["role"] == "instructor"
        and not user_is_admin(user)
        and record["assigned_instructor_id"] != user["id"]
    ):
        abort(403)
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


@app.route("/instructor")
@role_required("instructor")
def instructor_dashboard():
    user = current_user()
    scope_sql = ""
    params = []
    if not user_is_admin(user):
        scope_sql = " AND u.assigned_instructor_id=?"
        params.append(user["id"])

    students = query_one(
        "SELECT COUNT(*) AS total FROM users u "
        "WHERE u.role='student' AND u.is_active=1" + scope_sql,
        params,
    )["total"]
    awaiting = query_one(
        """
        SELECT COUNT(*) AS total
        FROM submissions s
        JOIN users u ON u.id=s.student_id
        JOIN assignments a ON a.id=s.assignment_id
        WHERE a.program_version='v5'
          AND s.status IN ('Submitted','Under Review')
        """ + scope_sql,
        params,
    )["total"]
    revisions = query_one(
        """
        SELECT COUNT(*) AS total
        FROM submissions s
        JOIN users u ON u.id=s.student_id
        JOIN assignments a ON a.id=s.assignment_id
        WHERE a.program_version='v5'
          AND s.status='Revision Required'
        """ + scope_sql,
        params,
    )["total"]
    assignments = query_one(
        """
        SELECT COUNT(*) AS total
        FROM assignments a JOIN weeks w ON w.id=a.week_id
        WHERE a.program_version='v5' AND a.is_published=1
          AND w.week_number BETWEEN 1 AND 16
        """
    )["total"]

    recent_sql = """
        SELECT s.*,u.name AS student_name,u.email AS student_email,
               p.title AS project_title,p.industry,
               w.week_number,a.category,
               CASE WHEN a.category IN ('Hands-On','Capstone')
                    THEN pm.title ELSE a.title END AS assignment_title
        FROM submissions s
        JOIN users u ON u.id=s.student_id
        JOIN assignments a ON a.id=s.assignment_id
        JOIN weeks w ON w.id=a.week_id
        LEFT JOIN projects p ON p.id=u.selected_project_id
        LEFT JOIN project_milestones pm
          ON pm.project_id=u.selected_project_id
         AND pm.week_number=w.week_number
        WHERE a.program_version='v5'
    """
    recent_params = []
    if not user_is_admin(user):
        recent_sql += " AND u.assigned_instructor_id=?"
        recent_params.append(user["id"])
    recent_sql += " ORDER BY COALESCE(s.submitted_at,s.updated_at) DESC LIMIT 12"
    recent = query_all(recent_sql, recent_params)

    stats = {
        "students": students,
        "assignments": assignments,
        "awaiting_review": awaiting,
        "revisions": revisions,
    }
    return render_template(
        "instructor_dashboard.html",
        stats=stats,
        recent=recent,
        scope_title="Academy overview" if user_is_admin(user) else "My students",
        scope_note=(
            "All students and program activity"
            if user_is_admin(user)
            else "Only students assigned to you"
        ),
    )


@app.route("/instructor/submissions")
@role_required("instructor")
def submissions_list():
    user = current_user()
    status = request.args.get("status", "").strip()
    student_id = request.args.get("student_id", "").strip()
    category = request.args.get("category", "").strip()

    sql = """
        SELECT s.*,u.name AS student_name,u.email AS student_email,
               u.assigned_instructor_id,p.title AS project_title,p.industry,
               a.category,a.max_score,w.week_number,w.title AS week_title,
               CASE WHEN a.category IN ('Hands-On','Capstone')
                    THEN pm.title ELSE a.title END AS assignment_title
        FROM submissions s
        JOIN users u ON u.id=s.student_id
        JOIN assignments a ON a.id=s.assignment_id
        JOIN weeks w ON w.id=a.week_id
        LEFT JOIN projects p ON p.id=u.selected_project_id
        LEFT JOIN project_milestones pm
          ON pm.project_id=u.selected_project_id
         AND pm.week_number=w.week_number
        WHERE a.program_version='v5'
    """
    params = []
    if not user_is_admin(user):
        sql += " AND u.assigned_instructor_id=?"
        params.append(user["id"])
    if status:
        sql += " AND s.status=?"
        params.append(status)
    if student_id:
        sql += " AND s.student_id=?"
        params.append(student_id)
    if category:
        sql += " AND a.category=?"
        params.append(category)
    sql += """
        ORDER BY w.week_number,u.name,
          CASE a.category WHEN 'Hands-On' THEN 1 WHEN 'Research' THEN 2
          WHEN 'LinkedIn' THEN 3 WHEN 'Capstone' THEN 4 ELSE 5 END
    """
    rows = query_all(sql, params)

    if user_is_admin(user):
        students = query_all(
            "SELECT id,name FROM users WHERE role='student' ORDER BY name"
        )
    else:
        students = query_all(
            """
            SELECT id,name FROM users
            WHERE role='student' AND assigned_instructor_id=?
            ORDER BY name
            """,
            (user["id"],),
        )
    return render_template(
        "submissions_list.html",
        rows=rows,
        students=students,
        selected_status=status,
        selected_student=student_id,
        selected_category=category,
    )


@app.route("/instructor/submission/<int:submission_id>", methods=["GET", "POST"])
@role_required("instructor")
def grade_submission(submission_id):
    user = current_user()
    row = query_one(
        """
        SELECT s.*,u.name AS student_name,u.email AS student_email,
               u.assigned_instructor_id,p.title AS project_title,p.industry,
               a.category,a.max_score,w.week_number,w.title AS week_title,
               CASE WHEN a.category IN ('Hands-On','Capstone')
                    THEN pm.title ELSE a.title END AS assignment_title,
               CASE WHEN a.category IN ('Hands-On','Capstone')
                    THEN pm.instructions ELSE a.instructions END AS instructions,
               CASE WHEN a.category IN ('Hands-On','Capstone')
                    THEN pm.deliverable ELSE a.deliverable END AS deliverable
        FROM submissions s
        JOIN users u ON u.id=s.student_id
        JOIN assignments a ON a.id=s.assignment_id
        JOIN weeks w ON w.id=a.week_id
        LEFT JOIN projects p ON p.id=u.selected_project_id
        LEFT JOIN project_milestones pm
          ON pm.project_id=u.selected_project_id
         AND pm.week_number=w.week_number
        WHERE s.id=? AND a.program_version='v5'
        """,
        (submission_id,),
    )
    if not row:
        abort(404)
    if not user_is_admin(user) and row["assigned_instructor_id"] != user["id"]:
        abort(403)

    if request.method == "POST":
        status = request.form.get("status", "Under Review")
        if status not in {"Under Review", "Revision Required", "Approved", "Late"}:
            status = "Under Review"
        score_raw = request.form.get("score", "").strip()
        try:
            score = float(score_raw) if score_raw else None
        except ValueError:
            flash("Enter a valid numeric score.", "danger")
            return redirect(request.url)
        if score is not None and (score < 0 or score > row["max_score"]):
            flash(f"Score must be between 0 and {row['max_score']}.", "danger")
            return redirect(request.url)
        feedback = request.form.get("mentor_feedback", "").strip()
        now = now_iso()
        execute(
            """
            UPDATE submissions
            SET status=?,score=?,mentor_feedback=?,graded_by=?,graded_at=?,updated_at=?
            WHERE id=?
            """,
            (status, score, feedback, user["id"], now, now, submission_id),
        )
        flash("Grade and feedback saved.", "success")
        return redirect(url_for("grade_submission", submission_id=submission_id))

    return render_template("grade_submission.html", row=row)


@app.route("/instructor/students", methods=["GET", "POST"])
@role_required("instructor")
def manage_students():
    user = current_user()
    is_admin = user_is_admin(user)
    instructors = (
        query_all(
            """
            SELECT id,name,email FROM users
            WHERE role='instructor' AND is_active=1
            ORDER BY name
            """
        )
        if is_admin else []
    )
    projects = query_all("SELECT id,industry,title FROM projects ORDER BY project_number")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        class_name = request.form.get("class_name", "").strip()
        assigned_instructor_id = user["id"]

        if is_admin:
            raw_instructor = request.form.get("assigned_instructor_id", "").strip()
            try:
                candidate = int(raw_instructor)
            except ValueError:
                candidate = 0
            valid = query_one(
                """
                SELECT id FROM users
                WHERE id=? AND role='instructor' AND is_active=1
                """,
                (candidate,),
            )
            if not valid:
                flash("Select a valid active instructor.", "danger")
                return redirect(url_for("manage_students"))
            assigned_instructor_id = candidate

        if not name or not email or not password:
            flash("Name, email, and temporary password are required.", "danger")
        elif query_one("SELECT id FROM users WHERE lower(email)=?", (email,)):
            flash("A user with this email already exists.", "danger")
        else:
            execute(
                """
                INSERT INTO users
                (name,email,password_hash,role,cohort,assigned_instructor_id,
                 selected_project_id,is_admin,is_active,created_at)
                VALUES (?,?,?,'student',?,?,NULL,0,1,?)
                """,
                (
                    name, email, generate_password_hash(password),
                    class_name, assigned_instructor_id, now_iso(),
                ),
            )
            flash(
                "Student account created. The student will choose one 16-week project.",
                "success",
            )
            return redirect(url_for("manage_students"))

    sql = """
        SELECT u.*,mentor.name AS instructor_name,
               p.title AS project_title,p.industry,
               COUNT(s.id) AS submissions,
               SUM(CASE WHEN s.status='Approved' THEN 1 ELSE 0 END) AS approved,
               COALESCE(ROUND(AVG(CASE WHEN s.score IS NOT NULL THEN s.score END),1),0)
                 AS avg_score
        FROM users u
        LEFT JOIN users mentor ON mentor.id=u.assigned_instructor_id
        LEFT JOIN projects p ON p.id=u.selected_project_id
        LEFT JOIN submissions s ON s.student_id=u.id
        WHERE u.role='student'
    """
    params = []
    if not is_admin:
        sql += " AND u.assigned_instructor_id=?"
        params.append(user["id"])
    sql += " GROUP BY u.id ORDER BY u.name"
    students = query_all(sql, params)

    return render_template(
        "manage_students.html",
        students=students,
        instructors=instructors,
        projects=projects,
        page_is_admin=is_admin,
    )


@app.route("/instructor/student/<int:user_id>/class", methods=["POST"])
@role_required("instructor")
def update_student_class(user_id):
    user = current_user()
    if not instructor_can_access_student(user_id, user):
        abort(403)
    class_name = request.form.get("class_name", "").strip()
    execute(
        "UPDATE users SET cohort=? WHERE id=? AND role='student'",
        (class_name, user_id),
    )
    flash("Student class updated.", "success")
    return redirect(url_for("manage_students"))


@app.route("/instructor/student/<int:user_id>/assign", methods=["POST"])
@admin_required
def assign_student_instructor(user_id):
    raw = request.form.get("assigned_instructor_id", "").strip()
    try:
        instructor_id = int(raw)
    except ValueError:
        instructor_id = 0
    instructor = query_one(
        """
        SELECT id FROM users
        WHERE id=? AND role='instructor' AND is_active=1
        """,
        (instructor_id,),
    )
    student = query_one("SELECT id FROM users WHERE id=? AND role='student'", (user_id,))
    if not student or not instructor:
        flash("Select a valid active instructor.", "danger")
        return redirect(url_for("manage_students"))
    execute(
        "UPDATE users SET assigned_instructor_id=? WHERE id=?",
        (instructor_id, user_id),
    )
    flash("Student instructor assignment updated.", "success")
    return redirect(url_for("manage_students"))


@app.route("/instructor/student/<int:user_id>/project", methods=["POST"])
@admin_required
def assign_student_project(user_id):
    student = query_one("SELECT * FROM users WHERE id=? AND role='student'", (user_id,))
    if not student:
        abort(404)
    raw = request.form.get("selected_project_id", "").strip()
    try:
        project_id = int(raw)
    except ValueError:
        project_id = 0
    project = query_one("SELECT id,title FROM projects WHERE id=?", (project_id,))
    if not project:
        flash("Select a valid project.", "danger")
        return redirect(url_for("manage_students"))
    if (
        student["selected_project_id"]
        and student["selected_project_id"] != project_id
        and student_has_v5_work(user_id)
    ):
        flash(
            "This student's project is locked because project work has already "
            "been submitted.",
            "warning",
        )
        return redirect(url_for("manage_students"))
    execute(
        "UPDATE users SET selected_project_id=? WHERE id=?",
        (project_id, user_id),
    )
    flash(f"Student project updated to {project['title']}.", "success")
    return redirect(url_for("manage_students"))


@app.route("/instructor/instructors", methods=["GET", "POST"])
@admin_required
def manage_instructors():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        is_admin = 1 if request.form.get("is_admin") == "1" else 0

        if not name or not email or not password:
            flash("Name, email, and temporary password are required.", "danger")
        elif query_one("SELECT id FROM users WHERE lower(email)=?", (email,)):
            flash("A user with this email already exists.", "danger")
        else:
            execute(
                """
                INSERT INTO users
                (name,email,password_hash,role,cohort,assigned_instructor_id,
                 selected_project_id,is_admin,is_active,created_at)
                VALUES (?,?,?,'instructor',NULL,NULL,NULL,?,1,?)
                """,
                (name, email, generate_password_hash(password), is_admin, now_iso()),
            )
            flash("Instructor account created.", "success")
            return redirect(url_for("manage_instructors"))

    instructors = query_all(
        """
        SELECT i.*,
               COUNT(CASE WHEN s.role='student' THEN s.id END) AS assigned_students
        FROM users i
        LEFT JOIN users s ON s.assigned_instructor_id=i.id
        WHERE i.role='instructor'
        GROUP BY i.id
        ORDER BY i.is_active DESC,i.is_admin DESC,i.name
        """
    )
    return render_template("manage_instructors.html", instructors=instructors)


@app.route("/instructor/instructor/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_instructor(user_id):
    instructor = query_one(
        "SELECT * FROM users WHERE id=? AND role='instructor'", (user_id,)
    )
    if not instructor:
        abort(404)
    if user_id == session["user_id"]:
        flash("You cannot deactivate your own instructor account.", "warning")
        return redirect(url_for("manage_instructors"))

    if instructor["is_active"]:
        assigned_count = query_one(
            """
            SELECT COUNT(*) AS total FROM users
            WHERE role='student' AND is_active=1 AND assigned_instructor_id=?
            """,
            (user_id,),
        )["total"]
        if assigned_count:
            flash("Reassign this instructor's active students first.", "warning")
            return redirect(url_for("manage_instructors"))
        if instructor["is_admin"]:
            admin_count = query_one(
                """
                SELECT COUNT(*) AS total FROM users
                WHERE role='instructor' AND is_active=1 AND is_admin=1
                """
            )["total"]
            if admin_count <= 1:
                flash("At least one active academy administrator is required.", "warning")
                return redirect(url_for("manage_instructors"))

    execute(
        "UPDATE users SET is_active=? WHERE id=?",
        (0 if instructor["is_active"] else 1, user_id),
    )
    flash("Instructor status updated.", "success")
    return redirect(url_for("manage_instructors"))


@app.route("/instructor/student/<int:user_id>/toggle", methods=["POST"])
@role_required("instructor")
def toggle_student(user_id):
    user = current_user()
    if not instructor_can_access_student(user_id, user):
        abort(403)
    student = query_one("SELECT * FROM users WHERE id=? AND role='student'", (user_id,))
    if not student:
        abort(404)
    execute(
        "UPDATE users SET is_active=? WHERE id=?",
        (0 if student["is_active"] else 1, user_id),
    )
    flash("Student status updated.", "success")
    return redirect(url_for("manage_students"))


@app.route("/instructor/assignments")
@role_required("instructor")
def manage_assignments():
    user = current_user()
    sql = """
        SELECT a.*,w.week_number,w.title AS week_title,
               COUNT(s.id) AS submissions
        FROM assignments a
        JOIN weeks w ON w.id=a.week_id
        LEFT JOIN submissions s ON s.assignment_id=a.id
        LEFT JOIN users u ON u.id=s.student_id
        WHERE a.program_version='v5' AND a.is_published=1
    """
    params = []
    if not user_is_admin(user):
        sql += " AND (u.assigned_instructor_id=? OR s.id IS NULL)"
        params.append(user["id"])
    sql += """
        GROUP BY a.id
        ORDER BY w.week_number,
          CASE a.category WHEN 'Hands-On' THEN 1 WHEN 'Research' THEN 2
          WHEN 'LinkedIn' THEN 3 WHEN 'Capstone' THEN 4 ELSE 5 END
    """
    rows = query_all(sql, params)
    return render_template("manage_assignments.html", rows=rows)


@app.errorhandler(400)
def bad_request(_):
    return render_template(
        "error.html", code=400, message="The request could not be validated."
    ), 400


@app.errorhandler(403)
def forbidden(_):
    return render_template(
        "error.html", code=403, message="You do not have access to this page."
    ), 403


@app.errorhandler(404)
def not_found(_):
    return render_template(
        "error.html", code=404, message="The requested page was not found."
    ), 404


if __name__ == "__main__":
    app.run(debug=True)
