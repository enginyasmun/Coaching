# Landing and Login Design Refresh

This update changes only the public landing page and login experience. It does not modify the database, curriculum, accounts, submissions, grades, or instructor logic.

## Files included

- `templates/landing.html`
- `templates/login.html`
- `static/styles.css`
- `static/app.js`

## What changed

### Landing page

- Centered maximum-width layout for large monitors
- Stronger headline and content hierarchy
- Cleaner program metrics
- Refined dashboard preview presentation
- New academy outcome band
- More polished program cards
- Improved spacing, visual depth, and responsive behavior

### Login page

- Removed the doubled input borders
- Added dedicated email and password icon areas
- Added clearer labels and helper text
- Added stronger hover and keyboard-focus states
- Added a show/hide password button
- Improved mobile layout and login-card hierarchy
- Added protected-session messaging

## Upload to GitHub

1. Extract `Coaching_Landing_Login_Refresh.zip`.
2. Open `enginyasmun/Coaching` on GitHub.
3. Select **Add file → Upload files**.
4. Drag the `templates` and `static` folders from the extracted update into GitHub.
5. GitHub should show these existing files as modified:
   - `templates/landing.html`
   - `templates/login.html`
   - `static/styles.css`
   - `static/app.js`
6. Use commit message:

   `Improve landing and login design`

7. Commit directly to `main`.

## Update PythonAnywhere

Open a Bash console and run:

```bash
cd ~/Coaching
git pull origin main
```

Then open the PythonAnywhere **Web** tab and click **Reload**.

Open the website and force-refresh the browser:

- Windows: `Ctrl + F5`
- macOS: `Command + Shift + R`

## Important

Do not run `RESET_DB=1 python seed.py` for this design update.
Do not delete `academy.db`.
