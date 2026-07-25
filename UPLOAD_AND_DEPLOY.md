# Upload this project to GitHub

This package is prepared for the empty repository:

`enginyasmun/Coaching`

## Browser upload

1. Open the repository.
2. Click **uploading an existing file** in the blue Quick setup panel.
3. Extract `Coaching_GitHub_Upload.zip` on your computer.
4. Open the extracted `Coaching_GitHub_Upload` folder.
5. Select everything inside the folder, including:
   - `.github`
   - `.gitignore`
   - `templates`
   - `static`
   - `uploads`
   - all root files
6. Drag the selected contents into GitHub.
7. Enter commit message: `Add Salesforce Junior Developer Academy`.
8. Click **Commit changes**.

Do not upload the ZIP itself as the only repository file. GitHub will not extract it.

## Deploy on Render

1. Sign in to Render with GitHub.
2. Select **New +**, then **Blueprint**.
3. Choose `enginyasmun/Coaching`.
4. Render detects `render.yaml`.
5. Approve the service.
6. When deployment finishes, Render provides the live website URL.
7. In the Render service, open **Environment** and copy or replace `ADMIN_PASSWORD`.
8. Sign in using:
   - Email: `admin@example.com`
   - Password: the `ADMIN_PASSWORD` value from Render

The included persistent disk preserves the SQLite database and uploaded student files.
