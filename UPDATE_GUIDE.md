# Classes and Instructor Management Update

This update:

1. Moves the dark green technology bar below the three white outcome cards.
2. Renames visible **Cohort** terminology to **Class**.
3. Adds instructor account management.

## Add instructors

After installing:

1. Sign in as an instructor.
2. Click **Instructors** in the left navigation.
3. Enter the instructor's name, email, and temporary password.
4. Click **Create instructor account**.
5. Send the credentials privately.

Every active instructor has full academy access.

The website prevents you from deactivating your own account and prevents deactivation of the final active instructor.

## Classes

The database field remains named `cohort` internally so the update is compatible with your existing database. The website displays **Class**.

On the Students page, each student now has an editable Class field. You can change an existing value such as `Cohort 1` to `Class 1` and click **Save**.

## Upload to GitHub

Upload these items to the root of `enginyasmun/Coaching`:

- `app.py`
- `seed.py`
- `templates`
- `static`

Commit message:

`Add classes and instructor management`

## Update PythonAnywhere

```bash
cd ~/Coaching
git pull origin main
```

Then open the PythonAnywhere **Web** tab and click **Reload**.

Press `Ctrl + F5` on the website.

## Important

Do not run `RESET_DB=1 python seed.py`.

Do not delete `academy.db`. Your existing accounts, students, assignments, grades, and submissions remain intact.
