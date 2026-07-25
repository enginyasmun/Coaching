# Modern Design Update Guide

This package is a complete replacement for the files in your `enginyasmun/Coaching` repository.

## Files that changed

- `templates/base.html`
- `templates/landing.html`
- `templates/login.html`
- `templates/student_dashboard.html`
- `templates/instructor_dashboard.html`
- `templates/curriculum.html`
- `templates/week_detail.html`
- `templates/student_assignment.html`
- `templates/submissions_list.html`
- `templates/grade_submission.html`
- `templates/manage_students.html`
- `templates/manage_assignments.html`
- `templates/error.html`
- `static/styles.css`

## New files

- `static/app.js`
- `static/favicon.svg`

## Safest update method on PythonAnywhere

Your current database is stored in `/home/enginyasmun/Coaching/academy.db`. Do not delete it.

1. In a PythonAnywhere Bash console, run:

```bash
cd ~/Coaching
git status
```

2. Make sure `academy.db` is not tracked by Git. Then pull the new GitHub commit:

```bash
git pull origin main
```

3. Open the PythonAnywhere **Web** tab.
4. Click **Reload enginyasmun.pythonanywhere.com**.
5. Hard-refresh the browser with `Ctrl + F5`.

## Uploading the update to GitHub in the browser

1. Extract `Coaching_Modern_Design.zip`.
2. In GitHub, open `enginyasmun/Coaching`.
3. Choose **Add file → Upload files**.
4. Drag the extracted contents into the upload screen.
5. GitHub will show existing files as replacements and `app.js` / `favicon.svg` as new files.
6. Commit directly to `main` with:

```text
Modernize academy website design
```

The ZIP does not include `academy.db`, so your GitHub upload cannot overwrite your live student database.

## Quick rollback

Every GitHub upload creates a commit. To return to the old design, open the new commit in GitHub and choose **Revert**, then run `git pull origin main` on PythonAnywhere and reload the web app.
