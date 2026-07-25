from datetime import datetime, date, timedelta
import sqlite3
import os
import hashlib
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "academy.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
PASSWORD_ITERATIONS = 260_000

def generate_password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PASSWORD_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

weeks = [
(1,"Platform Foundation","Salesforce Platform and CRM Fundamentals",
"CRM concepts, Salesforce architecture, multitenancy, metadata versus data, standard and custom objects, org types, Setup, Object Manager, and Schema Builder.",
"Build a customer onboarding or loan application data model using Account, Contact, Application, Document, Review, and Offer.",
"How Salesforce multitenancy affects application design, governor limits, metadata-driven architecture, and shared platform resources.",
"Salesforce is more than a CRM: what metadata-driven development means."),
(2,"Platform Foundation","Data Modeling and Data Quality",
"Lookup and master-detail relationships, junction objects, formulas, roll-up summaries, validation rules, external IDs, record types, Dynamic Forms, duplicate rules, and matching rules.",
"Enhance the Week 1 model with validation, duplicate prevention, formulas, record types, a junction object, and conditional field visibility.",
"Lookup versus master-detail relationships, including ownership, deletion, sharing, roll-ups, and reparenting.",
"One relationship-design decision that can affect an entire Salesforce solution."),
(3,"Platform Foundation","Security and Access Control",
"Profiles, permission sets, permission set groups, OWD, role hierarchy, sharing rules, object permissions, field-level security, record access, least privilege, and audit tools.",
"Create Sales Representative, Underwriter, and Manager personas with documented access boundaries.",
"How Salesforce security layers work together across object, field, and record access.",
"Salesforce security is not controlled by one setting."),
(4,"Platform Foundation","Flow and Declarative Automation",
"Before-save flows, after-save flows, screen flows, scheduled flows, subflows, invocable Apex, fault paths, order of execution, recursion, and automation selection.",
"Build one before-save flow, one after-save flow, one screen flow, and one scheduled flow with fault handling.",
"Flow versus Apex, including formulas, validation rules, record-triggered Flow, scheduled Flow, and invocable Apex.",
"Not every Salesforce automation requires Apex."),
(5,"Core Development","Development Environment and Salesforce DX",
"VS Code, Salesforce Extension Pack, Salesforce CLI, project structure, org authorization, aliases, metadata retrieval, deployments, source tracking, scratch orgs, sandboxes, manifests, and package directories.",
"Create a Salesforce DX project, connect an org, retrieve metadata, deploy a change, and commit it to Git.",
"Source-driven Salesforce development and the differences among scratch orgs, sandboxes, and Developer Edition orgs.",
"Why modern Salesforce developers should learn Salesforce CLI."),
(6,"Core Development","Apex Programming Fundamentals",
"Variables, data types, collections, conditions, loops, methods, classes, constructors, interfaces, inheritance, exceptions, null handling, and object-oriented programming.",
"Build an Apex scoring service that validates inputs and returns a structured result without database access.",
"Object-oriented programming in Apex and why separation of responsibilities matters.",
"Apex is more than syntax."),
(7,"Core Development","SOQL, SOSL, and Data Access",
"SOQL, SOSL, relationship queries, aggregate queries, bind variables, dynamic SOQL, selectivity, query planning, indexes, governor limits, and bulk processing.",
"Write queries for related records, aggregates, missing data, duplicate applicants, and large-volume scenarios.",
"Efficient SOQL design, selective queries, large data volumes, and the Query Plan Tool.",
"Why SOQL inside a loop is a serious Salesforce development mistake."),
(8,"Core Development","Apex Triggers and Service Architecture",
"Trigger contexts, before and after operations, bulkification, recursion, handler classes, service classes, transaction boundaries, savepoints, and rollback.",
"Build a bulk-safe application review automation using one trigger and supporting classes.",
"Trigger architecture patterns, handlers, services, recursion control, and change detection.",
"A trigger should coordinate work instead of containing the entire application."),
(9,"Core Development","Apex Security",
"with sharing, without sharing, inherited sharing, CRUD, FLS, user mode, system mode, secure dynamic SOQL, validation, injection prevention, and sensitive-data handling.",
"Review and rewrite an intentionally insecure Apex class.",
"User mode, system mode, sharing, CRUD, and field-level security in Apex.",
"Why with sharing does not enforce every Salesforce security layer."),
(10,"Core Development","Apex Testing",
"Test isolation, test data factories, @TestSetup, positive and negative tests, bulk tests, permission tests, asynchronous tests, callout mocks, assertions, and meaningful coverage.",
"Write behavior-focused tests for Week 8 automation, including bulk, permissions, duplicate prevention, and exceptions.",
"What makes an Apex test valuable beyond code coverage.",
"Code coverage does not prove that Salesforce code works correctly."),
(11,"Core Development","Asynchronous Apex and Integrations",
"Future, Queueable, Batch, Scheduled Apex, Platform Events, Change Data Capture, REST callouts, JSON, Named Credentials, retry design, idempotency, logging, and recovery.",
"Build a mock external verification process using Queueable Apex, a callout mock, logging, and safe retries.",
"Queueable Apex versus Batch Apex versus Platform Events.",
"Choosing the correct asynchronous tool in Salesforce."),
(12,"Core Development","Lightning Web Components Fundamentals",
"HTML, CSS, modern JavaScript, modules, promises, async and await, LWC structure, reactivity, getters, events, conditional rendering, lists, base components, and SLDS.",
"Build an application summary component with status, risk, and missing-document indicators.",
"How Lightning Web Components use modern web standards.",
"One JavaScript concept that became important while learning LWC."),
(13,"Core Development","LWC Data and Component Communication",
"Lightning Data Service, UI Record API, wire service, imperative Apex, caching, parent-child communication, custom events, Lightning Message Service, navigation, toasts, and loading states.",
"Build a review workbench with multiple communicating components and user-friendly error handling.",
"Lightning Data Service versus custom Apex controllers.",
"Not every LWC requires a custom Apex controller."),
(14,"Core Development","Advanced LWC and User Experience",
"Composition, reusable utilities, custom data tables, forms, validation, file upload, accessibility, responsive design, debouncing, performance, and Jest fundamentals.",
"Create a reusable document-management component with search, categories, upload, permissions, and responsive behavior.",
"LWC performance and accessibility.",
"A component is not complete merely because it works."),
(15,"Engineering Practices","Git and Team Development",
"Repositories, branches, commits, pull requests, merge conflicts, code review, protected branches, reverting, .gitignore, and secrets management.",
"Complete a feature branch workflow with focused commits, a pull request, review feedback, conflict resolution, and merge.",
"Git workflows for Salesforce teams.",
"A good Git commit should tell a story."),
(16,"Engineering Practices","Deployment and DevOps",
"Development lifecycle, source-driven releases, CLI deployments, DevOps Center, continuous integration, validation deployments, dependencies, destructive changes, rollback planning, and post-deployment steps.",
"Prepare and validate a release containing Apex, tests, LWC, fields, permissions, and Flow.",
"Continuous integration and Salesforce deployment reliability.",
"Deployment success does not always mean release success."),
(17,"Engineering Practices","Debugging, Monitoring, and Code Quality",
"Debug logs, Developer Console, Apex Replay Debugger, Flow failures, limits, permissions, integration failures, static analysis, Code Analyzer, technical debt, and root-cause analysis.",
"Diagnose a multi-layer broken feature and produce a root-cause report.",
"Structured root-cause analysis across Apex, Flow, LWC, permissions, and integrations.",
"Debugging should begin with evidence rather than guesses."),
(18,"AI and Agents","AI-Assisted Salesforce Development",
"LLM limitations, prompts, context windows, hallucinations, privacy, secure context, AI-generated code review, deterministic versus probabilistic systems, and verification workflows.",
"Use an AI coding assistant to produce an Apex service, then identify and correct issues involving security, bulkification, null handling, testing, and maintainability.",
"Benefits and risks of AI-generated Salesforce code.",
"AI can generate code, but it cannot own the consequences."),
(19,"AI and Agents","MCP Servers, Tools, CLI, and Agent Skills",
"Model Context Protocol, clients, servers, tools, resources, authentication, Salesforce DX MCP Server, tool discovery, least privilege, context management, MCP versus APIs, MCP versus CLI, skills, project instructions, and scripts.",
"Configure an approved development agent to inspect metadata, query an org, run tests, run code analysis, retrieve metadata, and explain a deployment diff.",
"MCP servers versus APIs versus Salesforce CLI, plus the difference among tools, skills, scripts, and instructions.",
"MCP gives an agent tools, while skills teach it how the team wants work performed."),
(20,"AI and Agents","Agentforce Development",
"Agentforce fundamentals, instructions, actions, Flow actions, Apex actions, prompt templates, Agent Script, Agentforce DX, grounding, guardrails, testing, Agent API, headless agents, deployment, monitoring, and escalation.",
"Build an internal application-review agent that summarizes records, identifies missing documents, triggers approved actions, refuses unauthorized actions, and escalates unsupported requests.",
"Designing secure and reliable Salesforce agents.",
"A Salesforce agent needs clearly defined authorization boundaries.")
]

with get_db() as conn:
    existing = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()
    if existing and os.environ.get("RESET_DB") != "1":
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count > 0:
            print(f"Existing database retained at {DB_PATH}")
            raise SystemExit(0)

    conn.executescript(open(BASE_DIR / "schema.sql", "r", encoding="utf-8").read())
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO users (name,email,password_hash,role,cohort,is_active,created_at) VALUES (?,?,?,?,?,?,?)",
        (os.environ.get("ADMIN_NAME", "Academy Instructor"), os.environ.get("ADMIN_EMAIL", "admin@example.com"), generate_password_hash(os.environ.get("ADMIN_PASSWORD", "Admin123!")), "instructor","",1,now)
    )
    conn.execute(
        "INSERT INTO users (name,email,password_hash,role,cohort,is_active,created_at) VALUES (?,?,?,?,?,?,?)",
        (os.environ.get("DEMO_STUDENT_NAME", "Demo Student"), os.environ.get("DEMO_STUDENT_EMAIL", "student@example.com"), generate_password_hash(os.environ.get("DEMO_STUDENT_PASSWORD", "Student123!")), "student","Cohort 1",1,now)
    )

    start = date.today()
    for item in weeks:
        cur = conn.execute(
            "INSERT INTO weeks (week_number,stage,title,topics,hands_on,research_topic,linkedin_topic) VALUES (?,?,?,?,?,?,?)",
            item
        )
        week_id = cur.lastrowid
        due = (start + timedelta(days=item[0]*7)).isoformat()

        conn.execute(
            "INSERT INTO assignments (week_id,title,category,instructions,deliverable,max_score,due_date,is_published) VALUES (?,?,?,?,?,?,?,1)",
            (week_id, f"Week {item[0]} Hands-On: {item[2]}", "Hands-On", item[4],
             "Submit source code, screenshots or a repository link, testing evidence, and a short explanation of your design decisions.", 100, due)
        )
        conn.execute(
            "INSERT INTO assignments (week_id,title,category,instructions,deliverable,max_score,due_date,is_published) VALUES (?,?,?,?,?,?,?,1)",
            (week_id, f"Week {item[0]} Research: {item[5]}", "Research", item[5],
             "500 to 1,000 words, at least three credible sources including one official Salesforce source, one practical example, and a personal conclusion.", 100, due)
        )
        conn.execute(
            "INSERT INTO assignments (week_id,title,category,instructions,deliverable,max_score,due_date,is_published) VALUES (?,?,?,?,?,?,?,1)",
            (week_id, f"Week {item[0]} LinkedIn: {item[6]}", "LinkedIn", item[6],
             "Submit a mentor-reviewed draft first. After approval, publish it and add the LinkedIn post URL.", 100, due)
        )

    conn.commit()

print(f"Database initialized at {DB_PATH}")
print("Instructor: admin@example.com / Admin123!")
print("Student: student@example.com / Student123!")
