import os
import sqlite3
from functools import wraps
from datetime import datetime, date, timedelta
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, send_from_directory
)
import hashlib
import secrets
from werkzeug.utils import secure_filename

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
UPLOAD_DIR.mkdir(exist_ok=True)


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


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_user():
    if "user_id" not in session:
        return None
    return query_one("SELECT * FROM users WHERE id = ?", (session["user_id"],))


@app.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "today": date.today().isoformat(),
        "csrf_token": get_csrf_token()
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
        user = query_one("SELECT * FROM users WHERE lower(email) = ?", (email,))
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


@app.route("/curriculum")
@login_required
def curriculum():
    weeks = query_all("SELECT * FROM weeks ORDER BY week_number")
    return render_template("curriculum.html", weeks=weeks)


@app.route("/curriculum/week/<int:week_number>")
@login_required
def curriculum_week(week_number):
    week = query_one("SELECT * FROM weeks WHERE week_number = ?", (week_number,))
    if not week:
        abort(404)
    assignments = query_all(
        "SELECT * FROM assignments WHERE week_id = ? ORDER BY CASE category "
        "WHEN 'Hands-On' THEN 1 WHEN 'Research' THEN 2 WHEN 'LinkedIn' THEN 3 ELSE 4 END",
        (week["id"],)
    )
    return render_template("week_detail.html", week=week, assignments=assignments)


@app.route("/student")
@role_required("student")
def student_dashboard():
    user_id = session["user_id"]
    rows = query_all(
        """
        SELECT a.*, w.week_number, w.title AS week_title,
               s.id AS submission_id, s.status AS submission_status,
               s.score, s.submitted_at, s.updated_at, s.mentor_feedback
        FROM assignments a
        JOIN weeks w ON w.id = a.week_id
        LEFT JOIN submissions s ON s.assignment_id = a.id AND s.student_id = ?
        ORDER BY w.week_number,
                 CASE a.category WHEN 'Hands-On' THEN 1 WHEN 'Research' THEN 2 WHEN 'LinkedIn' THEN 3 ELSE 4 END
        """,
        (user_id,)
    )
    summary = query_one(
        """
        SELECT
            COUNT(a.id) AS total,
            SUM(CASE WHEN s.status IN ('Submitted','Under Review','Revision Required','Approved') THEN 1 ELSE 0 END) AS submitted,
            SUM(CASE WHEN s.status = 'Approved' THEN 1 ELSE 0 END) AS approved,
            COALESCE(ROUND(AVG(CASE WHEN s.score IS NOT NULL THEN s.score END), 1), 0) AS avg_score
        FROM assignments a
        LEFT JOIN submissions s ON s.assignment_id = a.id AND s.student_id = ?
        """,
        (user_id,)
    )
    return render_template("student_dashboard.html", rows=rows, summary=summary)


@app.route("/student/assignment/<int:assignment_id>", methods=["GET", "POST"])
@role_required("student")
def student_assignment(assignment_id):
    assignment = query_one(
        """
        SELECT a.*, w.week_number, w.title AS week_title, w.topics
        FROM assignments a JOIN weeks w ON w.id = a.week_id
        WHERE a.id = ?
        """,
        (assignment_id,)
    )
    if not assignment:
        abort(404)
    submission = query_one(
        "SELECT * FROM submissions WHERE assignment_id = ? AND student_id = ?",
        (assignment_id, session["user_id"])
    )

    if request.method == "POST":
        status = request.form.get("status", "Draft")
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
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{session['user_id']}_{assignment_id}_{timestamp}_{safe}"
            uploaded.save(UPLOAD_DIR / filename)

        now = datetime.utcnow().isoformat(timespec="seconds")
        submitted_at = now if status == "Submitted" else (submission["submitted_at"] if submission else None)

        if submission:
            execute(
                """
                UPDATE submissions
                SET status=?, submission_text=?, submission_url=?, linkedin_url=?,
                    student_note=?, file_name=?, submitted_at=?, updated_at=?,
                    revision_number=revision_number + CASE WHEN status='Revision Required' AND ?='Submitted' THEN 1 ELSE 0 END
                WHERE id=?
                """,
                (
                    status, submission_text, submission_url, linkedin_url,
                    student_note, filename, submitted_at, now, status, submission["id"]
                )
            )
        else:
            execute(
                """
                INSERT INTO submissions
                (assignment_id, student_id, status, submission_text, submission_url,
                 linkedin_url, student_note, file_name, submitted_at, updated_at, revision_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    assignment_id, session["user_id"], status, submission_text,
                    submission_url, linkedin_url, student_note, filename,
                    submitted_at, now
                )
            )
        flash("Your work has been saved.", "success")
        return redirect(url_for("student_assignment", assignment_id=assignment_id))

    return render_template("student_assignment.html", assignment=assignment, submission=submission)


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


@app.route("/instructor")
@role_required("instructor")
def instructor_dashboard():
    stats = query_one(
        """
        SELECT
            (SELECT COUNT(*) FROM users WHERE role='student' AND is_active=1) AS students,
            (SELECT COUNT(*) FROM assignments) AS assignments,
            (SELECT COUNT(*) FROM submissions WHERE status IN ('Submitted','Under Review')) AS awaiting_review,
            (SELECT COUNT(*) FROM submissions WHERE status='Revision Required') AS revisions
        """
    )
    recent = query_all(
        """
        SELECT s.*, u.name AS student_name, a.title AS assignment_title,
               a.category, w.week_number
        FROM submissions s
        JOIN users u ON u.id = s.student_id
        JOIN assignments a ON a.id = s.assignment_id
        JOIN weeks w ON w.id = a.week_id
        ORDER BY COALESCE(s.submitted_at, s.updated_at) DESC
        LIMIT 12
        """
    )
    return render_template("instructor_dashboard.html", stats=stats, recent=recent)


@app.route("/instructor/submissions")
@role_required("instructor")
def submissions_list():
    status = request.args.get("status", "").strip()
    student_id = request.args.get("student_id", "").strip()
    category = request.args.get("category", "").strip()

    sql = """
        SELECT s.*, u.name AS student_name, u.email AS student_email,
               a.title AS assignment_title, a.category, a.max_score,
               w.week_number, w.title AS week_title
        FROM submissions s
        JOIN users u ON u.id = s.student_id
        JOIN assignments a ON a.id = s.assignment_id
        JOIN weeks w ON w.id = a.week_id
        WHERE 1=1
    """
    params = []
    if status:
        sql += " AND s.status = ?"
        params.append(status)
    if student_id:
        sql += " AND s.student_id = ?"
        params.append(student_id)
    if category:
        sql += " AND a.category = ?"
        params.append(category)
    sql += " ORDER BY w.week_number, u.name, a.category"

    rows = query_all(sql, params)
    students = query_all("SELECT id, name FROM users WHERE role='student' ORDER BY name")
    return render_template(
        "submissions_list.html",
        rows=rows, students=students,
        selected_status=status, selected_student=student_id, selected_category=category
    )


@app.route("/instructor/submission/<int:submission_id>", methods=["GET", "POST"])
@role_required("instructor")
def grade_submission(submission_id):
    row = query_one(
        """
        SELECT s.*, u.name AS student_name, u.email AS student_email,
               a.title AS assignment_title, a.category, a.instructions,
               a.deliverable, a.max_score, w.week_number, w.title AS week_title
        FROM submissions s
        JOIN users u ON u.id = s.student_id
        JOIN assignments a ON a.id = s.assignment_id
        JOIN weeks w ON w.id = a.week_id
        WHERE s.id = ?
        """,
        (submission_id,)
    )
    if not row:
        abort(404)

    if request.method == "POST":
        status = request.form.get("status", "Under Review")
        score_raw = request.form.get("score", "").strip()
        score = float(score_raw) if score_raw else None
        if score is not None and (score < 0 or score > row["max_score"]):
            flash(f"Score must be between 0 and {row['max_score']}.", "danger")
            return redirect(request.url)
        feedback = request.form.get("mentor_feedback", "").strip()
        now = datetime.utcnow().isoformat(timespec="seconds")
        execute(
            """
            UPDATE submissions
            SET status=?, score=?, mentor_feedback=?, graded_by=?, graded_at=?, updated_at=?
            WHERE id=?
            """,
            (status, score, feedback, session["user_id"], now, now, submission_id)
        )
        flash("Grade and feedback saved.", "success")
        return redirect(url_for("grade_submission", submission_id=submission_id))

    return render_template("grade_submission.html", row=row)


@app.route("/instructor/students", methods=["GET", "POST"])
@role_required("instructor")
def manage_students():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        cohort = request.form.get("cohort", "").strip()
        if not name or not email or not password:
            flash("Name, email, and temporary password are required.", "danger")
        elif query_one("SELECT id FROM users WHERE lower(email)=?", (email,)):
            flash("A user with this email already exists.", "danger")
        else:
            execute(
                """
                INSERT INTO users (name, email, password_hash, role, cohort, is_active, created_at)
                VALUES (?, ?, ?, 'student', ?, 1, ?)
                """,
                (name, email, generate_password_hash(password), cohort, datetime.utcnow().isoformat(timespec="seconds"))
            )
            flash("Student account created.", "success")
            return redirect(url_for("manage_students"))

    students = query_all(
        """
        SELECT u.*,
               COUNT(s.id) AS submissions,
               SUM(CASE WHEN s.status='Approved' THEN 1 ELSE 0 END) AS approved,
               COALESCE(ROUND(AVG(CASE WHEN s.score IS NOT NULL THEN s.score END), 1), 0) AS avg_score
        FROM users u
        LEFT JOIN submissions s ON s.student_id = u.id
        WHERE u.role='student'
        GROUP BY u.id
        ORDER BY u.name
        """
    )
    return render_template("manage_students.html", students=students)


@app.route("/instructor/student/<int:user_id>/toggle", methods=["POST"])
@role_required("instructor")
def toggle_student(user_id):
    student = query_one("SELECT * FROM users WHERE id=? AND role='student'", (user_id,))
    if not student:
        abort(404)
    execute("UPDATE users SET is_active=? WHERE id=?", (0 if student["is_active"] else 1, user_id))
    flash("Student status updated.", "success")
    return redirect(url_for("manage_students"))


@app.route("/instructor/assignments")
@role_required("instructor")
def manage_assignments():
    rows = query_all(
        """
        SELECT a.*, w.week_number, w.title AS week_title,
               COUNT(s.id) AS submissions
        FROM assignments a
        JOIN weeks w ON w.id = a.week_id
        LEFT JOIN submissions s ON s.assignment_id = a.id
        GROUP BY a.id
        ORDER BY w.week_number,
                 CASE a.category WHEN 'Hands-On' THEN 1 WHEN 'Research' THEN 2 WHEN 'LinkedIn' THEN 3 ELSE 4 END
        """
    )
    return render_template("manage_assignments.html", rows=rows)


@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="You do not have access to this page."), 403


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="The requested page was not found."), 404


if __name__ == "__main__":
    app.run(debug=True)
