# TrustVault — Secure Document Management System

TrustVault is a web-based document management application developed for the Snovasys Hiring Challenge. It enables registered users to securely upload, manage, share, and download documents through authentication and server-side access controls.

The application is developed using Python Flask, PostgreSQL, SQLAlchemy, HTML, CSS, JavaScript, and Supabase Storage. It is deployed on Render.

## Live Application

**Website:** https://trustvault-s4wn.onrender.com

**GitHub Repository:** https://github.com/KesireddyPadma/TrustVault

**Demo Link:** https://drive.google.com/file/d/1yDitZYqljCZFgmxxP8oMlh2j14Ry_EEH/view?usp=sharing

## Project Overview

TrustVault provides a centralized platform for storing and managing documents with controlled access.

Users can upload documents, manage their own files, grant permissions to other users, revoke previously granted access, and review available activity information.

The application uses server-side authorization to restrict document operations based on ownership, assigned permissions, and administrative privileges.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | PostgreSQL |
| ORM | Flask-SQLAlchemy |
| Document Storage | Supabase Storage |
| Authentication | Flask-based session authentication |
| Version Control | Git and GitHub |
| Deployment | Render |
| Production Server | Gunicorn |

## Implemented Features

### User Authentication

- User registration and login.
- Password hashing before database storage.
- Session-based authentication.
- Logout functionality.
- Authentication checks for protected application routes.

### Role-Based Access Control

TrustVault supports document access based on user roles, ownership, and granted permissions.

- **Admin:** Administrative oversight and access according to backend authorization rules.
- **Owner:** Users who upload documents and manage their own documents.
- **Viewer:** Users with limited document access based on permissions granted by document owners.

Document authorization is enforced by the backend rather than relying only on frontend visibility.

### Document Management

- Upload supported document types.
- View available document information.
- Download authorized documents.
- Rename documents when permitted.
- Delete owned documents.
- Store document metadata in PostgreSQL.
- Store newly uploaded document files in private Supabase Storage.

### Document Sharing and Permissions

- Document owners can grant access to registered users.
- Read permission allows authorized downloading.
- Edit permission allows authorized downloading and document-title modification.
- Owners can revoke previously granted permissions.
- Unauthorized users are restricted from accessing protected documents.

### Upload Validation

The application validates supported file types and enforces upload-size restrictions.

Supported file extensions:

- PDF
- PNG
- JPG
- JPEG
- MP4

Maximum configured upload size: **10 MB**.

Uploaded documents use generated storage identifiers rather than relying directly on user-provided filenames.

### Audit Logging

TrustVault records application activities through its audit system.

Audit records support reviewing document-related actions and identifying denied access attempts handled by the application.

### Administrative Oversight

Administrative functionality provides visibility into application information and activity according to the implemented administrator permissions.

## Application Architecture

TrustVault uses the following architecture:

**Frontend → Flask Backend → PostgreSQL and Supabase Storage**

The frontend provides the user interface for authentication and document operations.

The Flask backend processes requests, validates inputs, verifies authentication and authorization, and performs document operations.

PostgreSQL stores application data, including users, document metadata, permissions, and audit records.

Supabase Storage stores uploaded document files in a private bucket. Storage credentials are used by the backend and are not exposed to browser users.

## Local Setup Instructions

### Prerequisites

Install the following:

- Python 3
- Git
- PostgreSQL, or access to a PostgreSQL database
- Visual Studio Code or another code editor
- A Supabase project with a private Storage bucket

### Clone the Repository

Open a terminal and run:

```powershell
git clone https://github.com/KesireddyPadma/TrustVault.git
cd TrustVault
```

### Create a Virtual Environment

```powershell
py -m venv .venv
```

Activate the environment in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

```powershell
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the project root.

Use the following configuration as a reference:

```dotenv
SECRET_KEY=replace_with_a_secure_random_secret
DATABASE_URL=postgresql://username:password@localhost:5432/trustvault
COOKIE_SECURE=0
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_supabase_secret_key
SUPABASE_BUCKET=trustvault-documents
```

Generate a Flask secret key using:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Replace the example values with credentials from your own database and Supabase project.

The Supabase URL must be the project base URL, without `/rest/v1` or `/storage/v1` appended.

The Supabase bucket must exist and be configured as private.

**Security note:** Never commit `.env`, passwords, database credentials, or Supabase secret keys to GitHub.

### Initialize the Database

Ensure PostgreSQL is running and the configured database exists.

Run:

```powershell
python -m flask --app app init-db
```

### Start the Application

```powershell
python -m flask --app app run --port 5050 --no-reload
```

Open the application at:

http://127.0.0.1:5050

### Create an Administrator Account

If administrator access is required, use the application's administrator creation command:

```powershell
python -m flask --app app create-admin
```

Follow the terminal instructions to create an administrator account.

## Permissions

| Operation | Owner | User with Read Grant | User with Edit Grant |
|---|---|---|---|
| View authorized document information | Yes | Yes | Yes |
| Download document | Yes | Yes | Yes |
| Rename document | Yes | No | Yes |
| Delete document | Yes | No | No |
| Grant permissions | Yes | No | No |
| Revoke permissions | Yes | No | No |

Administrative access is controlled separately by the backend.

A document identifier alone does not provide permission to access a document.

## Security Measures

TrustVault includes security-focused application controls:

- Password hashing.
- Authentication checks on protected routes.
- Server-side document permission verification.
- Document ownership enforcement.
- Read and edit permission separation.
- Permission revocation.
- File extension, size, and content validation.
- Generated storage keys.
- Private Supabase document storage.
- Environment-variable-based secret configuration.
- Audit logging for supported application actions.

The security design and relevant threats are documented in `THREATS.md`.

## Testing

The project includes a testing workflow for validating application behavior.

To run the available Python tests:

```powershell
pytest -q
```

Important security scenarios to verify include:

- Unauthenticated access to protected routes.
- Unauthorized document access.
- Cross-user download attempts.
- Document ownership restrictions.
- Read-only permission enforcement.
- Edit permission enforcement.
- Permission revocation.
- Invalid file uploads.
- Oversized file uploads.
- Audit logging for denied document access.

Test results should be reported based on actual execution. The presence of a test command does not itself establish that all tests pass.

## Deployment

TrustVault is deployed on Render.

**Live URL:** https://trustvault-s4wn.onrender.com

The production application uses:

- Render for hosting the Flask web application.
- Gunicorn as the production application server.
- PostgreSQL for persistent application data.
- Supabase Storage for private document storage.
- GitHub for source code management.

### Production Environment Variables

The Render web service requires the appropriate configuration values:

```text
SECRET_KEY
DATABASE_URL
COOKIE_SECURE
SUPABASE_URL
SUPABASE_SERVICE_KEY
SUPABASE_BUCKET
```

For HTTPS deployment:

```dotenv
COOKIE_SECURE=1
```

### Production Start Command

```bash
gunicorn app:app
```

### Deployment Verification

The application was deployed successfully on Render.

A newly uploaded document was verified through the live application, and the corresponding stored file was observed in the private Supabase Storage bucket.

The updated Flask application was committed and pushed to GitHub before deployment.

## AI-Assisted Development

AI assistance was used during TrustVault development for:

- Understanding and planning project requirements.
- Flask backend development guidance.
- Database configuration.
- Authentication and authorization discussions.
- Document management implementation.
- Supabase Storage integration.
- Debugging configuration and application errors.
- GitHub and Render deployment guidance.
- Technical documentation.

AI suggestions were reviewed against observed application behavior and corrected when necessary.

Development prompts, corrections, and supporting notes are documented in `PROMPTS.md`.

## TrustVault - Demo Video Link
  Link: https://drive.google.com/file/d/1yDitZYqljCZFgmxxP8oMlh2j14Ry_EEH/view?usp=sharing
  
## Project Documentation

The repository includes the following documentation:

- **README.md:** Project overview, functionality, setup, and deployment.
- **THREATS.md:** Threat model, security controls, risks, and verification guidance.
- **PROMPTS.md:** AI-assisted development notes, prompts, corrections, and development history.

## Scope and Limitations

TrustVault is a working document management application developed for the Snovasys hiring challenge.

The application has not undergone an independent production security audit or penetration test.

Advanced functionality such as multi-factor authentication, password recovery, malware scanning, and automated database migrations is outside the currently documented implementation.

Document editing refers to editing document metadata, such as the title, rather than changing the contents of uploaded files.

Audit logging covers application-level events handled by the implemented logging functionality and does not replace infrastructure-wide security monitoring.

Automated security test coverage and results should be verified before final evaluation.

## Final Note

TrustVault demonstrates the implementation of a document management system with user authentication, server-side authorization, controlled document sharing, permission revocation, private file storage, audit logging, and cloud deployment.

The project documentation describes the implemented functionality, development process, security considerations, and setup requirements to support technical evaluation and further development.