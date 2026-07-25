# Guided Labs Version 6.1 Hotfix

This hotfix fixes the Internal Server Error on curriculum week pages.

## Cause

The week route returns `project_title`, `project_number`, and `project_summary`, while the guided-lab builder expected `title`, `number`, and `summary`.

## Install

1. Upload `guided_labs.py` to the root of the GitHub `Coaching` repository and replace the existing file.
2. Commit with: `Fix guided lab project field mapping`
3. On PythonAnywhere run:

```bash
cd ~/Coaching
git pull origin main
workon coaching-env
python -m py_compile guided_labs.py app.py
```

4. Open the PythonAnywhere Web tab and click Reload.
5. Hard-refresh the website with `Ctrl + F5`.

No database migration or reset is required.
