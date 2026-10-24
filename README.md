# TrustVault — Secure Document Management

A working Flask web application with registration/login, private uploads, per-document ownership, read/edit sharing, revocation, audit activity, and admin oversight.

## Run on Windows (VS Code PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy `.env.example` to `.env` and replace `SECRET_KEY` with the generated random string. Then:

```powershell
flask --app app init-db
python app.py
```

Open http://127.0.0.1:5000

To create an admin account (run in another terminal):

```powershell
flask --app app create-admin
```

## Permissions

- Registered users can upload documents, and own the files they upload.
- Owners can read, rename, delete, share and revoke their documents.
- A `read` grant allows downloading only.
- An `edit` grant allows downloading and renaming, not deleting or resharing.
- An admin can view all document metadata, logs, and documents; create admins only using trusted server CLI.
- Unrelated users get 403 even when guessing a document ID.

## Tests

```powershell
pytest -q
```

## Deployment

This project is not deployed by merely downloading the ZIP. For public HTTPS hosting, create a Python web service with a persistent PostgreSQL database and persistent private file storage. Configure `DATABASE_URL`, `SECRET_KEY`, `COOKIE_SECURE=1`, and `UPLOAD_DIR` as private server environment variables. Start with `gunicorn app:app`. On hosts with ephemeral disks, local uploads will be lost: configure a persistent disk or migrate file storage to private S3/Supabase storage. Do not publish with Flask debug mode. Do not expose `.env` or upload files in GitHub.

## Scope and limitations

- The app is functional starter implementation, not independently certified production security.
- Admin page is read-only oversight; admin can act on document actions from dashboard.
- No password reset/email confirmation, malware scanning, file preview, rate limiting, or automated database migrations.
- Audit logging captures application actions and denied document actions, not all infrastructure-level requests.
- `edit` currently means editing document **title**, not file content.
- Public HTTPS URL requires deployment into a hosting account.
- Original Snovasys scoring rubric must be cross-checked before submission.
