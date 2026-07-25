# Instructor Ownership and Five Industry Projects

This update adds:

- Student-to-instructor assignment
- Private instructor workspaces
- Administrator oversight
- Five industry applications
- Twenty connected project-build milestones
- Five final-project submissions
- Official LinkedIn-blue assignment labels
- Secure file access based on student ownership

## Access model

### Academy administrators

Academy administrators can:

- See all students
- See all submissions
- Grade any student
- Create instructors
- Assign and reassign students
- Create other academy administrators

The migration automatically makes the oldest active instructor an academy administrator. In a typical one-instructor installation, your current account becomes the administrator.

### Regular instructors

Regular instructors can only:

- See students assigned to them
- See homework submitted by those students
- Download files belonging to those students
- Grade and return work for those students
- Create new students automatically assigned to themselves

Direct URLs are protected. An instructor cannot open another instructor's submission or uploaded file.

## Five industry applications

1. Financial Services: Lending Operations & Underwriting
2. Healthcare: Patient Referral & Care Coordination
3. Nonprofit: Donor & Volunteer Engagement
4. Manufacturing: Order & Inventory Operations
5. Professional Services: AI-Enabled Client Delivery

Each project spans four weeks. Every weekly Hands-On assignment is a project-build milestone. Weeks 4, 8, 12, 16, and 20 also contain a Final Project assignment.

## Install on GitHub

Upload everything from this update package to the root of:

`enginyasmun/Coaching`

Important new files include:

- `curriculum_data.py`
- `migrate_v4.py`

Use commit message:

`Add instructor ownership and five industry projects`

## Update PythonAnywhere

Open a Bash console and run:

```bash
cd ~/Coaching
git pull origin main
workon coaching-env
python migrate_v4.py
```

The migration creates a timestamped backup of `academy.db` before changing anything.

You should see:

- Students assigned to an instructor
- Industry projects: 5
- Final-project assignments: 5

Then:

1. Open the PythonAnywhere **Web** tab.
2. Click **Reload**.
3. Open the website.
4. Press `Ctrl + F5`.

## Assign students

1. Sign in with the academy administrator account.
2. Open **Students**.
3. Use the **Instructor** dropdown beside each student.
4. Click **Assign**.

After assignment, a regular instructor sees only that student and their homework.

## Create regular instructors

1. Open **Instructors**.
2. Enter a name, email, and temporary password.
3. Leave **Academy administrator** unchecked.
4. Create the account.
5. Assign students from the Students page.

## Important

Do not run:

```bash
RESET_DB=1 python seed.py
```

Do not delete `academy.db`.

Use:

```bash
python migrate_v4.py
```

The migration is rerunnable and preserves existing accounts, submissions, scores, feedback, and uploaded-file references.
