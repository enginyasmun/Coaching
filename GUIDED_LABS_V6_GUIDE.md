# Version 6: Trailhead-Style Guided Labs

This update changes the academy from assignment instructions into a complete guided-learning experience.

Every project and every week now includes:

- Learning objectives
- Required tools
- Prerequisites
- Eight ordered hands-on steps
- Exact Salesforce Setup navigation
- Salesforce CLI and Git commands where appropriate
- A checkpoint after every step
- Evidence the student must save
- A final hands-on quality gate
- An eight-step research method
- Suggested research searches
- A source-quality scorecard
- A guided LinkedIn-writing method

There are five projects and sixteen weeks, so the website generates 80 project-specific guided labs.

## Hands-on teaching model

Students are not expected to discover the build path.

The website tells them:

1. What to open
2. What to create
3. What to name it
4. What values to enter
5. What command to run
6. What result they should see
7. What evidence to save
8. What must be true before submission

Project-specific requirements are injected into the lab. For example, the Financial Services track receives lending fields, underwriting automation, lending service rules, queue filters, trigger behavior, integration operation, LWC action, and file ownership. The other industries receive their own exact project requirements.

## Research teaching model

The research lab teaches a repeatable method:

1. Restate the topic as one main question and three subquestions.
2. Define the terms.
3. Start with official Salesforce sources.
4. Add a practical implementation source.
5. Create a claim-evidence-project table.
6. Score source quality.
7. Compare alternatives.
8. Write, cite, and run a final quality check.

Students receive suggested searches, but they must open and evaluate the original sources. The process teaches research rather than asking for an unsupported essay.

## LinkedIn teaching model

Every week includes a guided LinkedIn workflow:

- Write the hook
- Explain the weekly build or research
- Include a concrete technical detail
- Connect it to the selected project
- State a useful takeaway
- Remove confidential information
- Submit for instructor review
- Publish only after approval

LinkedIn labels and fields continue to use LinkedIn blue.

## Interactive progress

Students can mark guided hands-on steps complete.

The progress is stored in the student's browser using local storage. It does not change grades, submissions, or the database. Students can leave and return to the same browser and see their completed steps.

## Instructor-provided setup

Some tools require controlled setup.

### Week 11

The instructor supplies:

- Training endpoint
- Authentication method
- Training credentials
- Allowed test records
- Expected request and response examples

### Week 15

The instructor supplies:

- Approved AI coding tool
- Approved MCP server
- Authentication method
- Repository and org access
- Allowed tools and data scope
- Assigned AI task

### Week 16

The instructor supplies:

- Agentforce-enabled training org
- Permissions
- Approved grounding data
- Allowed actions
- Prohibited actions
- Test users and guardrail scenarios

Students are explicitly told not to select their own endpoint, MCP server, production connection, or credentials.

## Install on the existing Version 5 website

Upload these files and folders to the root of `enginyasmun/Coaching`:

- `app.py`
- `guided_labs.py`
- `templates/`
- `static/`
- `GUIDED_LABS_V6_GUIDE.md`
- `GUIDED_LABS_CATALOG.md`

Use this commit message:

`Add step-by-step guided labs and research training`

Then open a PythonAnywhere Bash console:

```bash
cd ~/Coaching
git pull origin main
workon coaching-env
python -m py_compile app.py guided_labs.py
```

Open the PythonAnywhere **Web** tab and click **Reload**.

Open the website and press:

```text
Ctrl + F5
```

## Database

This Version 6 guided-lab update does not change the database.

Do not run:

```bash
RESET_DB=1 python seed.py
```

Do not delete:

```text
academy.db
```

Do not run `migrate_v5.py` again only for this guided-lab update. Run it only when moving from an older program version to Version 5.

## Full installation

The complete Version 6 package includes the entire application.

For a new installation, follow the existing PythonAnywhere setup and run `seed.py`.

For an installation older than Version 5, install the full package and run:

```bash
python migrate_v5.py
```

before reloading.
