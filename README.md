# Salesforce Junior Developer Academy

## Modern interface update

This version includes a complete responsive redesign with a dashboard-style sidebar, modern landing and login pages, improved forms and tables, program progress visuals, mobile navigation, and accessible focus states. Application routes, authentication, submissions, grades, and database logic are unchanged.

A standalone web application for managing a 16-week Salesforce junior developer project program.

## Included

- Instructor and student authentication
- Role-based access
- Five complete 16-week project plans
- 48 active assignments per student:
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


## Version 5 program model

Each student selects one of five industry projects and builds that same application for sixteen weeks. See `PROJECT_CHOICE_V5_GUIDE.md` for migration and deployment steps.

## Version 6 guided learning

Every project-week page now includes a Trailhead-style guided lab with exact build steps, checkpoints, evidence requirements, a structured research method, and a guided LinkedIn workflow. See `GUIDED_LABS_V6_GUIDE.md`.
