# Version 5: One Student, One 16-Week Project

This update corrects the project structure.

The five industries are parallel project choices. They are not consecutive four-week projects.

Each student:

1. Selects one industry project.
2. Builds that same application for sixteen weeks.
3. Completes one connected project milestone every week.
4. Completes one research assignment every week.
5. Completes one LinkedIn assignment every week.
6. Delivers the complete application in Week 16.

## Project choices

1. Financial Services: Lending Operations & Underwriting App
2. Healthcare: Patient Referral & Care Coordination App
3. Nonprofit: Donor & Volunteer Engagement App
4. Manufacturing: Order & Inventory Operations App
5. Professional Services: AI-Enabled Client Delivery App

Every project has a complete 16-week plan from discovery through Agentforce and final deployment.

## Student workload

Each student sees:

- 15 weekly project-build assignments
- 1 final application assignment in Week 16
- 16 research assignments
- 16 LinkedIn assignments

Total: 48 assignments.

## Project selection

A student without a selected project is redirected to the project-selection page.

The student may change the selection before submitting any Version 5 work.

After the first new-program submission, the project is locked. An academy administrator can also assign or change the project before work begins from the Students page.

## Instructor privacy

The instructor ownership model remains active.

Regular instructors only see:

- Students assigned to them
- Those students' selected projects
- Those students' submissions
- Those students' files
- Those students' grades and feedback

Academy administrators retain complete oversight.

## LinkedIn design

LinkedIn labels, fields, and review links use LinkedIn blue:

`#0A66C2`

## Upload to GitHub

Upload everything inside this package to the root of:

`enginyasmun/Coaching`

Important files include:

- `app.py`
- `curriculum_data.py`
- `migrate_v5.py`
- `schema.sql`
- `seed.py`
- `templates/`
- `static/`

Use this commit message:

`Change to one selected 16-week project per student`

## Update PythonAnywhere

Open a Bash console and run:

```bash
cd ~/Coaching
git pull origin main
workon coaching-env
python migrate_v5.py
```

The migration creates a timestamped backup of `academy.db`.

Expected output includes:

```text
Project choices: 5
Sixteen-week project milestones: 80
Assignments per student: 48
```

Then:

1. Open the PythonAnywhere **Web** tab.
2. Click **Reload**.
3. Open the website.
4. Press `Ctrl + F5`.

## Existing students

Existing students retain their instructor and class.

They will have no Version 5 project selected immediately after migration. At their next login, the website asks them to choose one of the five projects.

The academy administrator can also select a project from the Students page.

## Existing work

The migration creates a database backup before making changes.

Existing submissions, scores, feedback, accounts, and uploaded-file references are preserved. Previous curriculum assignments are archived from the new active 16-week program.

## Important

Do not run:

```bash
RESET_DB=1 python seed.py
```

Do not delete:

```text
academy.db
```

Use:

```bash
python migrate_v5.py
```
