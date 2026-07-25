# Salesforce Junior Developer Academy

A standalone web application for managing a 20-week Salesforce junior developer program.

## Included

- Instructor and student authentication
- Role-based access
- Complete 20-week curriculum
- 60 seeded assignments:
  - 20 hands-on assignments
  - 20 research assignments
  - 20 LinkedIn assignments
- Student submission pages
- File upload, repository links, written work, and LinkedIn links
- Instructor grading, feedback, revision requests, and approval
- Student account management
- Progress dashboard
- SQLite database
- Dockerfile and Render deployment configuration

## Initial accounts

Credentials are read from environment variables:

- `ADMIN_NAME`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `DEMO_STUDENT_NAME`
- `DEMO_STUDENT_EMAIL`
- `DEMO_STUDENT_PASSWORD`

Local defaults exist for development only. Set new values before public deployment.

## Run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Deploy to Render

1. Create a GitHub repository and upload this project.
2. Sign in to Render.
3. Create a new Blueprint and select the repository.
4. Render reads `render.yaml`.
5. The included `render.yaml` provisions a persistent disk for SQLite and uploaded files.

For a production deployment with multiple users, PostgreSQL and cloud object storage are recommended.

## Production checklist

- Replace demo accounts and passwords.
- Set a strong `SECRET_KEY`.
- Disable Flask debug mode.
- Use HTTPS.
- Move from SQLite to PostgreSQL for a larger deployment.
- Store uploads in S3, Cloudinary, or similar object storage.
- Add email-based password reset and invitation flows.
- Configure email-based password reset and invitation flows for a larger public deployment.

## Data safety

`seed.py` creates the database only when it is missing or empty. It does not overwrite an existing populated database unless `RESET_DB=1` is explicitly set.
