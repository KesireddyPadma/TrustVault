# TrustVault - AI Prompts and Development Notes

**Project:** TrustVault — Secure Document Sharing with an Audit Trail  
**Main AI tool:** ChatGPT   
**Stack:** Python, Flask, SQLAlchemy, PostgreSQL, HTML, CSS, GitHub and Render

## Purpose

This document explains how AI assistance was used during the development of TrustVault, a secure, role-based document management application. It records the main areas where prompts supported planning, implementation, debugging, testing, and deployment. AI-generated suggestions were treated as drafts and checked against the project's actual behavior before adoption.

## Project Context

TrustVault is a Flask-based web application for uploading, organizing, sharing, and managing documents with access controls. It uses Python and Flask for the backend, SQLAlchemy with PostgreSQL for application data, HTML/CSS/JavaScript for the interface, and a private Supabase Storage bucket for uploaded files. The application is deployed on Render and its source code is maintained on GitHub.

The project focuses on document ownership, role-based permissions, controlled downloads, audit records, and safe file handling.


## Dated AI Development Log

The following entries are a **retrospective account** of AI-assisted work discussed during the project. The requested dates reflect the development discussion timeline; they are **not evidence of separate commits on each day**. Prompts are paraphrased unless quoted verbatim. Git history currently shows an initial commit on 24 October and a storage-integration commit on 25 October.

### 1. 19 October 2026 — Project planning

- **What I asked:** How to understand the Snovasys TrustVault requirements and build the project step by step using Python, SQL, HTML, CSS, and JavaScript.
- **What AI produced:** A suggested development plan covering authentication, documents, permissions, database setup, and testing.
- **What was wrong or incomplete:** Planning suggestions did not constitute a working or tested application.
- **What I did instead:** Used the plan to organize the implementation work and selected a Flask-based approach.
- **Commit evidence:** The first repository snapshot was committed later, on 24 October: [Initial TrustVault commit](https://github.com/KesireddyPadma/TrustVault/commit/f9264d0). No 19 October commit is present in the supplied history.

### 2. 21 October 2026 — Authorization and access control

- **What I asked:** How owners, administrators, and explicitly authorized users should access documents without relying on hidden frontend buttons.
- **What AI produced:** Guidance on server-side ownership and document-grant checks.
- **What was wrong or incomplete:** Generic role advice cannot prove that download, edit, delete, and share endpoints all enforce authorization.
- **What I did instead:** Used the application's backend permission-checking approach and treated cross-user attempts as required security tests; full automated-test results have not been confirmed.
- **Commit evidence:** The authorization code was included in the [24 October initial repository snapshot](https://github.com/KesireddyPadma/TrustVault/commit/f9264d0); there is no separate 21 October commit in the supplied history.

### 3.22 October 2026 — Audit trail and denied actions

- **What I asked:** How to record document activity, permission changes, and denied access attempts for security review.
- **What AI produced:** Guidance on audit records and logging around protected operations.
- **What was wrong or incomplete:** Merely having an audit model does not guarantee every allowed or denied action is recorded.
- **What I did instead:** Included audit logging in the Flask design and identified event-by-event checks as necessary before claiming complete audit coverage.
- **Commit evidence:** The audit implementation appears in the [24 October initial repository snapshot](https://github.com/KesireddyPadma/TrustVault/commit/f9264d0); no separate 22 October commit is present.

### 4.23 October 2026 — Interface and application workflow

- **What I asked:** How to make the TrustVault website usable for registration, login, upload, document listing, and sharing.
- **What AI produced:** Frontend and workflow suggestions for a role-based document-management application.
- **What was wrong or incomplete:** A working interface does not by itself prove that backend permissions and error cases work correctly.
- **What I did instead:** Continued with the Flask application and tested key workflows manually; broader user and security tests still need verification.
- **Commit evidence:** The implemented website was recorded in the [24 October initial repository snapshot](https://github.com/KesireddyPadma/TrustVault/commit/f9264d0); no separate 23 October commit is present.

### 5.24 October 2026 — Local configuration and initial repository snapshot

- **What I asked:** How to troubleshoot local setup and prepare the working TrustVault project for GitHub and hosting.
- **What AI produced:** Terminal, environment configuration, and deployment guidance.
- **What was wrong or incomplete:** A successful local run or Git commit alone does not prove the hosted service works or that uploads survive redeployment.
- **What I did instead:** Committed the initial Flask project and continued deployment and storage verification.
- **Commit evidence:** [Initial TrustVault commit — 24 October 2026](https://github.com/KesireddyPadma/TrustVault/commit/f9264d0).

### 6.Subsequent update — 25 October 2026: Supabase storage integration

- **What I asked:** How to store files in a private Supabase bucket and fix an HTTP 404 during upload.
- **What AI produced:** Storage API integration and configuration troubleshooting guidance.
- **What was wrong or incomplete:** `SUPABASE_URL` was configured with `/rest/v1` rather than the project base URL, causing the constructed Storage API request to fail.
- **What I did instead:** Corrected the URL, restarted the Flask app, checked local upload/download, pushed the updated code, and confirmed Render deployment and live Supabase object storage.
- **Commit evidence:** [Supabase integration commit — 25 October 2026](https://github.com/KesireddyPadma/TrustVault/commit/cf2144e).

## Specific AI Mistakes or Corrections

**Supabase URL configuration:** An initial configuration used a Supabase REST API URL ending in `/rest/v1` instead of the project base URL. Storage uploads returned an HTTP 404 error. The URL was corrected to the base project URL, the Flask server was restarted, and upload/download operations were tested again.

**Local development port:** Local testing was confusing when another process appeared to be using the expected port. The application was run explicitly on port `5050` with reload disabled, and the `/health` endpoint was checked.

**Persistent document storage:** Local filesystem storage was not sufficient for reliable persistence on a hosted service. The application was updated to use a private Supabase Storage bucket for newly uploaded files. Local and deployed upload behavior was then checked.

**Documentation accuracy:** Earlier documentation describing permanent storage as unfinished became outdated after Supabase integration. Project documentation was revised to describe the implemented storage approach rather than the earlier limitation.

## Verification and Engineering Practices

Changes were checked through local Flask runs, application health checks, manual upload and download tests, inspection of the private Supabase bucket, Git commit/push confirmation, and successful Render deployment. Security-sensitive changes should also be checked with automated authorization and audit tests before final submission; this document does not claim that unverified tests passed.

Engineering practices included keeping secrets in environment variables, excluding local `.env` files from Git, using a private storage bucket, performing permission checks on the server, validating uploaded files, and maintaining changes in version control.

## Tools Used

- **ChatGPT:** Planning, code explanations, debugging guidance, and documentation drafting.
- **Visual Studio Code:** Editing and running the application locally.
- **Python and Flask:** Backend development.
- **SQLAlchemy and PostgreSQL:** Database models and persistent application data.
- **Supabase Storage:** Private storage for uploaded documents.
- **Git and GitHub:** Version control and repository hosting.
- **Render:** Hosting and deployment.
- **Browser and terminal:** Manual verification and troubleshooting.

## Final Note

This document reflects the observed TrustVault development process, including AI-assisted planning, implementation, debugging, and deployment. Representative prompts are clearly identified, and retrospective dates are not presented as individual Git commits. The links point to the two commits shown in the available Git history. No unexecuted security test is represented as passed.