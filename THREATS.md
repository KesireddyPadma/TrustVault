# TrustVault Threat Model

## Purpose and Scope

TrustVault is a role-based document management web application developed with Python Flask, Flask-Login, Flask-WTF, Flask-SQLAlchemy, PostgreSQL, HTML, CSS, and JavaScript. It is deployed on Render and uses a private Supabase Storage bucket for newly uploaded documents. This threat model examines the security of user accounts, document access, file uploads, sharing, permission revocation, audit records, and backend storage operations.

This document distinguishes protections observed in the reviewed application code from security tests that still require recorded results. It does not claim that an independent security audit has been performed.

## Assets to Protect

- User identities, email addresses, Argon2 password hashes, and authenticated sessions.
- Private documents stored in Supabase Storage and any legacy files stored locally.
- Document titles, ownership information, file hashes, and metadata in PostgreSQL.
- Per-document read and edit grants and administrative privileges.
- Audit records for user activity and rejected document operations.
- Flask secret key, database connection string, and Supabase service credentials.

## Trust Boundaries

- **Browser to Flask application:** Requests, cookies, document IDs, form fields, and uploaded bytes are untrusted and must be validated by the backend.
- **Flask application to PostgreSQL:** Database records determine account identity, ownership, permissions, and audit history.
- **Flask application to Supabase Storage:** The server uses a secret credential to upload, download, and delete private document objects; the credential must not be exposed to browsers.
- **GitHub to Render:** Source code is deployed from GitHub; production credentials belong in Render environment variables, not tracked source files.

## Threats, Controls, and Tests

| ID | Threat | TrustVault control or required safeguard | Test to run |
|---|---|---|---|
| T1 | Unauthenticated visitor accesses private documents or account pages | Flask-Login protects document routes and private pages. | Open the dashboard and a document download URL in a logged-out browser; verify authentication is required. |
| T2 | User accesses another user's document by guessing its ID | Server-side `require_doc()` checks administrator status, ownership, or a current grant. | Upload as User A, then attempt direct download as unrelated User B; verify HTTP 403 and no file disclosure. |
| T3 | Read-only user edits, deletes, or changes permissions | Read grants allow download; edit grants allow renaming; only owner/admin may manage sharing and deletion. | Share with Read access and attempt rename, delete, share, and revoke operations; confirm denial. |
| T4 | A user retains access after a grant is revoked | Document permissions are looked up from the database for each protected operation. | Grant access, verify download, revoke the grant, then retry the same URL; verify denial. |
| T5 | Unsupported, disguised, or oversized files are uploaded | Allowed PDF, PNG, JPG/JPEG, and TXT types; basic content-signature checks; 10 MB size limit. | Upload an unsupported extension, mismatched file contents, and an oversized file; verify rejection. |
| T6 | Filename collision or path manipulation overwrites or exposes files | `secure_filename()` sanitizes original names and UUID-based storage keys separate stored objects. | Upload two documents with the same filename and a path-like filename; verify independent storage and safe naming. |
| T7 | A private document is exposed directly through Supabase | Private bucket and backend-only service credential; downloads pass through Flask authorization. | Verify anonymous object access is blocked and that the service key is absent from browser responses and Git history. |
| T8 | Unauthorized user shares or revokes someone else's document | Share and revoke routes require owner/admin management permission. | Attempt to grant and revoke permissions using an unrelated account; verify denial. |
| T9 | Denied document actions go unrecorded | `require_doc()` records a `denied` audit event before returning HTTP 403. | Trigger an unauthorized document request and verify the matching event in the audit view or database. |
| T10 | Password theft or session misuse | Argon2 password hashing, Flask-Login, CSRF protection, HttpOnly/SameSite cookies, and configurable Secure cookies. | Inspect a test password hash; submit a POST without a CSRF token; log out and retry a protected route; inspect deployed cookie flags. |
| T11 | Storage failure causes false success or inconsistent document metadata | Upload error handling; metadata is committed after storage succeeds; cleanup is attempted if the database commit fails. | In a local test environment, simulate Supabase upload failure and database failure; check messages, database rows, and orphaned objects. |
| T12 | Automated login guessing or malicious file contents bypass basic safeguards | Password verification and basic file checks exist; rate limiting, account lockout, and malware scanning are not established by the reviewed code. | Test repeated failed logins in a controlled environment and inspect uploaded-file handling; record gaps for remediation. |

## Security Controls Observed in the Reviewed Code

- **Authentication:** Flask-Login restricts protected routes; passwords are hashed using Argon2.
- **Authorization:** The backend evaluates owner, admin, Read, and Edit permissions for document actions. Owner/admin rights are required for sharing, revoking, and deleting documents.
- **CSRF and cookies:** Flask-WTF CSRF protection is initialized. Session cookies are configured with HttpOnly and SameSite=Lax; Secure is controlled by `COOKIE_SECURE` and should be enabled in Render.
- **Upload safety:** File types are allowlisted, content is checked against basic signatures or UTF-8 validation, and uploads are limited to 10 MB. Generated storage keys reduce filename collisions and path manipulation.
- **Private storage:** New documents use Supabase Storage when the required environment variables are configured. PostgreSQL stores document metadata, ownership, permissions, and audit records. Downloaded Supabase files are checked against a stored SHA-256 digest.
- **Auditability:** Upload, download, rename, delete, share, revoke, and rejected document actions are recorded by application logging functions.
- **Error handling:** Access-denied and not-found pages avoid displaying detailed internal exceptions. Storage failures are handled with user-facing errors for relevant operations.

These are code-review observations, not a claim that every control has passed automated or adversarial testing.

## Security Test Evidence Log

| Test area | Current evidence/status | Further verification |
|---|---|---|
| Render deployment | Deployment reported successful | Confirm the live release corresponds to the reviewed commit. |
| Supabase upload and download | Manually confirmed on the live site | Repeat after redeployment; verify anonymous access is blocked. |
| Unauthenticated document access | Not recorded | Test logged-out direct URLs. |
| Cross-user access and Read/Edit restrictions | Not recorded | Test with separate owner, viewer, and editor accounts. |
| Grant and revoke enforcement | Not recorded | Verify access is lost immediately after revocation. |
| Invalid and oversized uploads | Not recorded | Execute negative upload cases. |
| CSRF, logout, and cookie security | Code reviewed; runtime tests not recorded | Test CSRF rejection, session invalidation, and Render cookie configuration. |
| Denied-action audit logging | Code reviewed; runtime test not recorded | Verify a rejected request creates an audit entry. |
| Storage and database failure handling | Code reviewed; fault-injection tests not recorded | Simulate failures locally and check cleanup. |
| Rate limiting and malware scanning | Not verified as implemented | Treat as residual risks, not passed controls. |

## Known Limitations and Residual Risks

- Login rate limiting and temporary account lockout are not established by the reviewed implementation, leaving a password-guessing risk.
- Basic file-signature validation does not replace antivirus or malware scanning.
- Multi-factor authentication, formal backup and disaster-recovery procedures, and an independent penetration test are not established.
- Newly uploaded files use persistent Supabase object storage. Older documents saved to Render's local filesystem may be unavailable after a restart or redeployment unless migrated.
- `COOKIE_SECURE` depends on deployment configuration; it must be set appropriately for the HTTPS production site.
- The application relies on the secrecy of the Supabase service credential and database connection string. Exposed credentials must be rotated promptly.
- Tests without recorded execution evidence must not be represented as passed.

## Responsible Testing

Only test accounts, files, and systems owned by the project team or explicitly authorized for assessment. Use non-sensitive sample documents. Avoid publishing credentials, private documents, or session tokens in screenshots, logs, or the repository. Do not perform disruptive tests against the public deployment.

## Updating This Threat Model

When an issue is found, record the observed behavior and reproduction steps, identify its cause, fix the backend or deployment configuration, add a regression test where possible, and document the actual retest result. Keep this file aligned with the code, configuration, and final demonstration.
