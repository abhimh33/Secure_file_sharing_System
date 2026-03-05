# Secure File Sharing System — Project Explanation

> A plain-English, end-to-end walkthrough of how every piece of this project works — written like you're explaining it to a friend over coffee.

---

## Table of Contents

1. [What Is This Project?](#1-what-is-this-project)
2. [The Big Picture (System Architecture)](#2-the-big-picture-system-architecture)
3. [Tech Stack — What Tools We Used and Why](#3-tech-stack--what-tools-we-used-and-why)
4. [How the Backend Is Organized](#4-how-the-backend-is-organized)
5. [How the Frontend Is Organized](#5-how-the-frontend-is-organized)
6. [The Database — Where We Store Everything](#6-the-database--where-we-store-everything)
7. [Authentication — How Login / Signup Works](#7-authentication--how-login--signup-works)
8. [Role-Based Access Control (RBAC)](#8-role-based-access-control-rbac)
9. [File Upload & Download — The Core Feature](#9-file-upload--download--the-core-feature)
10. [Share Links — Letting Others Download Your Files](#10-share-links--letting-others-download-your-files)
11. [Redis — The Fast In-Memory Cache](#11-redis--the-fast-in-memory-cache)
12. [Audit Logging — Who Did What, When](#12-audit-logging--who-did-what-when)
13. [Security Measures — How We Keep Things Safe](#13-security-measures--how-we-keep-things-safe)
14. [How Frontend Talks to Backend (API Layer)](#14-how-frontend-talks-to-backend-api-layer)
15. [How to Run the Project](#15-how-to-run-the-project)
16. [Request Lifecycle — A Full Example](#16-request-lifecycle--a-full-example)
17. [Folder Structure Explained](#17-folder-structure-explained)

---

## 1. What Is This Project?

Imagine Google Drive, but built from scratch, with a focus on **security and controlled sharing**.

Users can:

- **Sign up / log in** with email and password.
- **Upload files** (up to 200 MB) which are stored securely in AWS S3 (a cloud storage service).
- **Generate temporary share links** for any file — with options like password protection, download limits, and expiry times.
- **Download files** through those links — even without an account (unless the link creator requires one).
- **Admin users** can manage all users, view every file, and see a full audit trail of everything that happened in the system.

The whole system is built as a **separate frontend + backend** (a "decoupled" architecture), so the React app in your browser talks to the FastAPI server through an API.

---

## 2. The Big Picture (System Architecture)

Here's how all the pieces connect:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER'S BROWSER                                 │
│                                                                         │
│   React + TypeScript Frontend  (runs on http://localhost:3000)          │
│   ┌────────────┐  ┌───────────┐  ┌────────────┐  ┌────────────────┐     │
│   │ Login Page │  │ Files Page│  │ Share Page │  │  Admin Panel   │     │
│   └─────┬──────┘  └─────┬─────┘  └──────┬─────┘  └───────┬────────┘     │
│         │               │               │                │              │
│         └───────────────┼───────────────┼────────────────┘              │
│                         │   Axios HTTP  │                               │
│                         │   Requests    │                               │
└─────────────────────────┼───────────────┼───────────────────────────────┘
                          │               │
                   ┌──────▼───────────────▼──────┐
                   │     Vite Dev Proxy          │
                   │  /api/* → localhost:8000    │
                   └──────────────┬──────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────┐
│                        FASTAPI BACKEND                                  │
│                   (runs on http://localhost:8000)                       │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     API Endpoints Layer                         │   │
│   │  /auth/*   /files/*   /share/*   /users/*   /audit/*  /health   │   │
│   └─────────────────────────┬───────────────────────────────────────┘   │
│                             │                                           │
│   ┌─────────────────────────▼───────────────────────────────────────┐   │
│   │                     Security Layer                              │   │
│   │  JWT Tokens  •  Password Hashing (bcrypt)  •  RBAC Checks       │   │
│   └─────────────────────────┬───────────────────────────────────────┘   │
│                             │                                           │
│   ┌─────────────────────────▼───────────────────────────────────────┐   │
│   │                     Service Layer                               │   │
│   │  AuthService  •  FileService  •  ShareService  •  AuditService  │   │
│   └──────┬──────────────┬──────────────────┬───────────────┬────────┘   │
│          │              │                  │               │            │
└──────────┼──────────────┼──────────────────┼───────────────┼────────────┘
           │              │                  │               │
     ┌─────▼─────┐  ┌────▼─────┐  ┌────────▼───────┐  ┌───▼──────┐
     │ PostgreSQL│  │  AWS S3  │  │     Redis      │  │ Audit DB │
     │  Database │  │ (files)  │  │ (share links,  │  │  (logs)  │
     │ (metadata,│  │          │  │  sessions,TTL) │  │          │
     │  users,   │  │          │  │                │  │          │
     │  roles)   │  │          │  │                │  │          │
     └───────────┘  └──────────┘  └────────────────┘  └──────────┘
```

**In plain English:**

1. You open the React app in your browser.
2. Every time you do something (log in, upload a file, create a share link), the frontend sends an HTTP request to the FastAPI backend.
3. The backend checks your identity (JWT token), checks your permissions (RBAC), does the work (talks to the database, S3, or Redis), and sends back a response.
4. The frontend updates the screen based on that response.

---

## 3. Tech Stack — What Tools We Used and Why

| Layer      | Technology                | Why We Chose It                                                       |
|------------|---------------------------|-----------------------------------------------------------------------|
| Frontend   | **React 19 + TypeScript** | Modern UI library with type safety — catch bugs before runtime        |
| Bundler    | **Vite**                  | Blazing-fast dev server with hot-reload                               |
| Styling    | **Tailwind CSS**          | Utility-first CSS — build UI fast without custom stylesheets          |
| State      | **Zustand**               | Tiny, simple state manager — stores login info across pages           |
| Data fetch | **React Query**           | Smart caching / refetching for API calls                              |
| Backend    | **FastAPI (Python)**      | Async-capable, auto-generates API docs, Pydantic validation built-in  |
| Database   | **PostgreSQL**            | Rock-solid relational DB for users, files, roles, audit logs          |
| ORM        | **SQLAlchemy 2.0**        | Maps Python classes to database tables                                |
| Migrations | **Alembic**               | Handles database schema changes over time                             |
| Cache      | **Redis**                 | In-memory store with built-in expiration — perfect for share links    |
| Storage    | **AWS S3**                | Infinite-scale cloud storage — files never touch our server's disk    |
| Auth       | **JWT (python-jose)**     | Stateless authentication — no server-side session needed              |
| Passwords  | **bcrypt**                | Industry-standard one-way hashing — even we can't see your password   |

---

## 4. How the Backend Is Organized

The backend follows a **layered architecture** — each layer has one job:

```
app/
├── api/v1/endpoints/   ← LAYER 1: Receives HTTP requests, returns responses
├── security/           ← LAYER 2: Auth checks (JWT, passwords, RBAC)
├── services/           ← LAYER 3: Business logic (the "brain")
├── models/             ← LAYER 4: Database table definitions
├── schemas/            ← Pydantic models for request/response validation
├── core/               ← Config, database connection, Redis, S3 client
└── utils/              ← Helpers and logging
```

### How a request flows through these layers:

1. **Endpoint** (e.g., `POST /api/v1/files/upload`) receives the request.
2. **Security dependency** (injected by FastAPI) extracts the JWT token, validates it, and loads the `User` object.
3. **RBAC check** verifies the user's role has permission for this action.
4. **Service** (e.g., `FileService.upload_file()`) contains the actual logic — validate the file, upload it to S3, save metadata to PostgreSQL.
5. **Model** (e.g., `File`) is the SQLAlchemy class that maps to the `files` database table.
6. **Schema** (e.g., `FileResponse`) defines exactly what the API sends back to the frontend.

This separation means you can change the database without touching the API, or redesign the API without changing the business logic. Each layer is independent.

---

## 5. How the Frontend Is Organized

```
frontend/src/
├── api/           ← Functions that call the backend (one file per resource)
├── components/    ← Reusable UI pieces (layout, file uploader, auth guard)
├── pages/         ← Full screens (Login, Dashboard, Files, Shares, Admin...)
├── store/         ← Zustand auth store (keeps tokens & user info in memory)
├── types/         ← TypeScript interfaces (User, File, ShareLink, etc.)
└── App.tsx        ← Route definitions — which URL shows which page
```

### Key patterns:

- **`api/client.ts`** — Creates an Axios instance with a base URL and automatically attaches the JWT token to every request via an interceptor. If a token expires, it tries to refresh it silently.
- **`store/authStore.ts`** — A Zustand store persisted to `localStorage`. When you log in, tokens are saved here. When you refresh the page, you stay logged in.
- **`ProtectedRoute.tsx`** — A wrapper component. If you're not logged in and try to visit `/dashboard`, it redirects you to `/login`.
- **React Query** — Used for data fetching. It caches API responses for 5 minutes, so switching between pages feels instant.

---

## 6. The Database — Where We Store Everything

We use PostgreSQL with 6 main tables:

```
┌─────────────┐       ┌──────────────┐       ┌───────────────────┐
│    roles    │       │    users     │       │      files        │
├─────────────┤       ├──────────────┤       ├───────────────────┤
│ id (PK)     │◄──────│ role_id (FK) │       │ id (PK)           │
│ name        │       │ id (PK)      │◄──────│ owner_id (FK)     │
│ description │       │ email        │       │ filename          │
└─────────────┘       │ hashed_pass  │       │ s3_key            │
                      │ full_name    │       │ size, content_type│
                      │ is_active    │       │ is_deleted        │
                      │ is_verified  │       │ description       │
                      └──────┬───────┘       └────────┬──────────┘
                             │                        │
                    ┌────────▼────────┐      ┌────────▼───────────┐
                    │   audit_logs    │      │ file_permissions   │
                    ├─────────────────┤      ├────────────────────┤
                    │ id (PK)         │      │ id (PK)            │
                    │ user_id (FK)    │      │ file_id (FK)       │
                    │ action          │      │ user_id (FK)       │
                    │ resource_type   │      │ permission_level   │
                    │ ip_address      │      │ can_download       │
                    │ details         │      │ can_share          │
                    └─────────────────┘      │ granted_by_id (FK) │
                                             └────────────────────┘
                    ┌─────────────────┐
                    │  share_links    │
                    ├─────────────────┤
                    │ id (PK)         │
                    │ token (unique)  │
                    │ file_id (FK)    │
                    │ created_by (FK) │
                    │ expires_at      │
                    │ max_downloads   │
                    │ download_count  │
                    │ password_hash   │
                    │ is_active       │
                    └─────────────────┘
```

### What each table does:

| Table               | Purpose                                                                                 |
|---------------------|-----------------------------------------------------------------------------------------|
| **roles**           | Stores 3 roles: `admin`, `user`, `viewer`. Created automatically on first startup.      |
| **users**           | Every registered account. Passwords are stored as bcrypt hashes (not plain text!).       |
| **files**           | Metadata about uploaded files (name, size, S3 location). The actual file is in S3.      |
| **file_permissions**| When you share a file with another user directly, this records who can see/download it.  |
| **share_links**     | Persistent record of share links (expiry, download limits, password protection).         |
| **audit_logs**      | Every important action is logged here: logins, uploads, downloads, shares, deletions.    |

> **Important:** The actual files are NEVER stored in the database. Only metadata (name, size, S3 path) is stored. The file bytes live in AWS S3.

---

## 7. Authentication — How Login / Signup Works

### Registration Flow:

```
User fills out the form  →  Frontend sends POST /api/v1/auth/register
                                       │
                                       ▼
                            Backend checks:
                            1. Is this email already taken? → 400 error
                            2. Hash the password with bcrypt
                            3. Create user with "user" role
                            4. Generate JWT access + refresh tokens
                            5. Log the action in audit_logs
                                       │
                                       ▼
                            Return tokens + user info to frontend
                                       │
                                       ▼
                            Frontend stores tokens in Zustand + localStorage
                            Redirects to /dashboard
```

### Login Flow:

```
User enters email + password  →  POST /api/v1/auth/login
                                          │
                                          ▼
                              1. Find user by email
                              2. Compare password with bcrypt hash
                              3. If wrong → 401 error + audit log "login_failed"
                              4. If right → generate new JWT tokens
                              5. Log "login_success" in audit_logs
                                          │
                                          ▼
                              Return: { access_token, refresh_token, user }
```

### How JWT Tokens Work:

- **Access token** — Short-lived (20 minutes). Sent with every API request in the `Authorization: Bearer <token>` header. Contains: user ID, email, role.
- **Refresh token** — Longer-lived (7 days). Used ONLY to get a new access token when the old one expires.
- When the access token expires, the frontend's Axios interceptor automatically calls `/auth/refresh` with the refresh token to get a new access token — the user never notices.

---

## 8. Role-Based Access Control (RBAC)

There are 3 roles arranged in a hierarchy:

```
   admin
     │
     ▼
    user
     │
     ▼
   viewer
```

**Each higher role inherits all permissions of the roles below it.**

| Permission          | Admin | User | Viewer |
|---------------------|:-----:|:----:|:------:|
| Upload files        |  ✅  |  ✅  |  ❌   |
| Download own files  |  ✅  |  ✅  |  ❌   |
| Delete own files    |  ✅  |  ✅  |  ❌   |
| Create share links  |  ✅  |  ✅  |  ❌   |
| Download shared     |  ✅  |  ✅  |  ✅   |
| Manage all users    |  ✅  |  ❌  |  ❌   |
| View audit logs     |  ✅  |  ❌  |  ❌   |
| Access all files    |  ✅  |  ❌  |  ❌   |

### How it's enforced:

In the backend, endpoints use `require_role()` as a FastAPI dependency:

```python
@router.get("/users/", dependencies=[Depends(require_role([UserRole.ADMIN]))])
def list_users():
    ...
```

If a regular user tries to access an admin endpoint, they get a `403 Forbidden` error before the function even runs.

---

## 9. File Upload & Download — The Core Feature

### Upload (what happens when you drag a file):

```
1. Frontend reads the file and sends it as multipart/form-data
   → POST /api/v1/files/upload

2. Backend receives the file bytes in memory
   → Validates file size (max 200 MB)

3. Generates a unique S3 key:
   "files/{user_id}/{timestamp}_{uuid}_{filename}"

4. Uploads to AWS S3 private bucket
   → ACL set to 'private' (no public URL)

5. Saves metadata to PostgreSQL:
   filename, size, content_type, s3_key, owner_id

6. Logs "file_upload" in audit_logs

7. Returns file metadata to frontend
```

### Download (your own file):

```
1. Frontend sends GET /api/v1/files/{id}/download

2. Backend checks:
   → Are you the owner? Or an admin?
   → Is the file deleted?

3. Downloads file bytes from S3 into a BytesIO buffer

4. Returns the file as a streaming response
   Content-Disposition: attachment; filename="original_name.pdf"

5. Logs "file_download" in audit_logs
```

**Why S3?** Files never touch the server's disk. They're streamed from the user's browser → server memory → S3 (upload) and S3 → server memory → browser (download). This means the server stays lightweight and storage is essentially unlimited.

---

## 10. Share Links — Letting Others Download Your Files

This is the most interesting feature. Here's how it works end-to-end:

### Creating a share link:

```
1. You select a file and click "Create Share Link"

2. You configure options:
   • Expiry time (e.g., 60 minutes)
   • Max downloads (e.g., 5)
   • Password (optional)
   • Require authentication (optional)
   • Restrict to specific email (optional)

3. Frontend sends POST /api/v1/share/create

4. Backend:
   a. Generates a random 32-character token
   b. Hashes the password (if provided) with bcrypt
   c. Stores link data in BOTH:
      → Redis (with TTL = expiry time, for fast lookups)
      → PostgreSQL share_links table (for permanent record)
   d. Logs "share_create" in audit_logs

5. Returns the share URL: /share/{token}
```

### Using a share link (someone clicks it):

```
1. They visit /share/{token}

2. Frontend sends GET /api/v1/share/{token}/info

3. Backend looks up the token in Redis (fast!)
   → If not in Redis, checks PostgreSQL (fallback)
   → If not found anywhere → "Link not found" error

4. Validates the link:
   → Is it expired? → "This share link has expired"
   → Download limit reached? → "Download limit has been reached"
   → Is it active? → Check is_active flag

5. Returns file info (name, size, type) — NOT the file itself yet

6. Frontend shows the download page with file details

7. User clicks "Download":
   → If password-protected: must enter password first
   → Frontend sends POST /api/v1/share/{token}/download

8. Backend:
   a. Re-validates the token
   b. Verifies password (if required)
   c. Increments download_count in both Redis and PostgreSQL
   d. Downloads file from S3
   e. Streams it to the user
   f. Logs "share_access" in audit_logs
```

### Why Redis + PostgreSQL dual storage?

- **Redis:** Super fast (microsecond lookups). Has built-in TTL (time-to-live) — when the expiry time hits, Redis automatically deletes the key. No cleanup needed.
- **PostgreSQL:** Permanent record. Even after the Redis key expires, admins can see the history of all share links ever created.

---

## 11. Redis — The Fast In-Memory Cache

Redis is an in-memory data store. In this project, it's used for:

| Purpose              | How It Works                                                                          |
|----------------------|---------------------------------------------------------------------------------------|
| **Share link data**  | Stored as JSON with a TTL. When TTL expires, the share link is automatically invalid. |
| **Rate limiting**    | Track how many requests a user makes per minute. Block if they exceed 60/min.         |
| **Session cache**    | Quick lookups without hitting the database every time.                                |

### Example of a share link in Redis:

```json
Key:   "share_link:a1b2c3d4e5f6..."
TTL:   3600 seconds (1 hour)
Value: {
  "file_id": 42,
  "filename": "report.pdf",
  "s3_key": "files/1/20250201_abc123_report.pdf",
  "max_downloads": 5,
  "download_count": 2,
  "password_hash": "$2b$12$...",
  "created_by": 1,
  "expires_at": "2025-02-01T15:00:00"
}
```

When the TTL hits zero, Redis silently removes the key. The next time someone tries to use the link, the backend can't find it → "Link expired."

---

## 12. Audit Logging — Who Did What, When

Every sensitive action is recorded in the `audit_logs` table. This is critical for security and compliance.

### What gets logged:

| Category         | Actions Tracked                                                |
|------------------|----------------------------------------------------------------|
| Authentication   | Login success, login failure, logout, token refresh, password change |
| User Management  | User created, updated, deleted, role assigned                  |
| File Operations  | File upload, download, delete, update                          |
| Sharing          | Share link created, accessed, revoked, permissions changed     |

### Each log entry contains:

- **Who:** user ID + email (email is stored separately in case the user is later deleted)
- **What:** action type (e.g., `FILE_UPLOAD`)
- **Which resource:** resource type + ID (e.g., file #42)
- **Where from:** IP address of the request
- **Details:** Human-readable description (e.g., "File uploaded: report.pdf (1.2 MB)")
- **Status:** success or failed
- **When:** timestamp (auto-generated)

Only admins can view audit logs through the admin panel.

---

## 13. Security Measures — How We Keep Things Safe

### 1. Password Security
- Passwords are hashed with **bcrypt** (one-way hash + salt). Not even the system admin can read them.
- The database stores `$2b$12$randomsaltandhashedpassword`, not `MyPassword123`.

### 2. JWT Token Security
- Access tokens expire in **20 minutes**. Even if stolen, the window is small.
- Refresh tokens expire in **7 days** and can only generate new access tokens.
- Tokens are signed with a secret key using **HS256** algorithm. Tampering is detectable.

### 3. S3 Private Buckets
- All files are stored with **ACL: private**. There are zero public URLs.
- Files can ONLY be accessed through the backend API, which enforces authentication and authorization checks.

### 4. Input Validation
- Every request is validated by **Pydantic schemas** before reaching the business logic.
- File size is capped at **200 MB**.
- SQL injection is prevented by **SQLAlchemy's parameterized queries** (never raw SQL).

### 5. CORS (Cross-Origin Resource Security)
- The backend only accepts requests from allowed origins (configured in settings).
- Random websites can't make API calls to your backend.

### 6. Rate Limiting
- Users are limited to **60 requests per minute**.
- Prevents brute-force attacks and abuse.

### 7. Share Link Security
- Optional **password protection** (bcrypt-hashed).
- **Download limits** — link becomes invalid after N downloads.
- **Time-based expiry** — enforced by Redis TTL.
- Optional **email restriction** — only a specific email can use the link.
- Optional **authentication required** — must be logged in to download.

### 8. Audit Trail
- Every action is logged with IP address, user identity, and timestamp.
- Logs can't be edited or deleted through the API.

### 9. Environment Variables
- All secrets (database password, JWT key, AWS credentials) are loaded from `.env` file.
- `.env` is in `.gitignore` — never committed to Git.
- `.env.example` shows the structure without real values.

---

## 14. How Frontend Talks to Backend (API Layer)

The frontend has a dedicated `api/` folder with one file per resource:

| File          | What It Calls                                              |
|---------------|------------------------------------------------------------|
| `auth.ts`     | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me` |
| `files.ts`    | `/files/upload`, `/files/`, `/files/{id}/download`          |
| `share.ts`    | `/share/create`, `/share/{token}/info`, `/share/{token}/download` |
| `users.ts`    | `/users/` (admin), `/users/{id}/role`                       |
| `audit.ts`    | `/audit/logs` (admin)                                       |

### The Axios client (`client.ts`):

```
1. Creates an Axios instance with baseURL = "/api/v1"
2. Request interceptor: Attaches "Authorization: Bearer {token}" to every request
3. Response interceptor: If 401 error → try refreshing the token → retry the request
   If refresh also fails → log the user out
```

### Vite proxy:

During development, the frontend runs on port 3000 and the backend on port 8000. The Vite config proxies all `/api/*` requests from 3000 → 8000, so the browser thinks everything is on the same server (avoids CORS issues).

---

## 15. How to Run the Project

### Prerequisites:
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+ (or Docker)
- AWS account with S3 bucket

### Steps:

```bash
# 1. Clone the repo
git clone https://github.com/abhimh33/Secure_file_sharing_System.git
cd Secure_file_sharing_System

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your actual database, Redis, AWS, and JWT credentials

# 3. Start Redis (using Docker)
docker-compose up -d

# 4. Set up Python backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt

# 5. Run database migrations
alembic upgrade head

# 6. Start the backend
uvicorn app.main:app --reload --port 8000

# 7. In a new terminal, set up and start the frontend
cd frontend
npm install
npm run dev

# 8. Open http://localhost:3000 in your browser
```

On first startup, the backend automatically:
- Creates all database tables
- Creates 3 default roles (admin, user, viewer)
- Creates a default admin account (email and password from `.env`)

---

## 16. Request Lifecycle — A Full Example

Let's trace what happens when a user **uploads a file**, step by step:

```
[Browser]
    │
    │  1. User drags "report.pdf" onto the upload area
    │
    │  2. FileUpload component reads the file,
    │     calls api/files.ts → uploadFile(file, description)
    │
    │  3. Axios sends:
    │     POST /api/v1/files/upload
    │     Headers: { Authorization: "Bearer eyJhbG..." }
    │     Body: multipart/form-data with the file
    │
    ▼
[Vite Proxy]
    │  4. Forwards request from localhost:3000 → localhost:8000
    ▼
[FastAPI Router — files.py]
    │  5. Route matches: @router.post("/upload")
    │  6. FastAPI dependency injection kicks in:
    │     → get_current_user() extracts JWT from header
    │     → Decodes token → gets user_id
    │     → Loads User from database
    │     → Checks: is the user active? → Yes
    ▼
[FileService.upload_file()]
    │  7. Read file bytes into memory
    │  8. Check file size ≤ 200 MB → OK
    │  9. Generate S3 key: "files/1/20250201_abc123_report.pdf"
    │
    ├──→ [AWS S3]
    │    10. Upload file bytes to private bucket
    │    11. S3 returns success
    │
    ├──→ [PostgreSQL]
    │    12. INSERT INTO files (filename, s3_key, size, owner_id, ...)
    │    13. Database returns the new file record with ID
    │
    ├──→ [AuditService]
    │    14. INSERT INTO audit_logs (action="file_upload", user_id=1, ...)
    │
    ▼
[FastAPI Response]
    │  15. Return JSON: { id: 42, filename: "report.pdf", size: 1048576, ... }
    ▼
[Browser]
    16. React Query receives response
    17. Invalidates the file list cache
    18. files page re-fetches and shows the new file
    19. Toast notification: "File uploaded successfully!"
```

---

## 17. Folder Structure Explained

```
Secure_FileSharing_System/
│
├── app/                          # ← All backend Python code
│   ├── main.py                   # App entry point, lifespan events, middleware
│   ├── api/v1/                   # API version 1
│   │   ├── router.py             # Combines all endpoint routers
│   │   └── endpoints/            # One file per resource
│   │       ├── auth.py           # Register, login, refresh, profile
│   │       ├── files.py          # Upload, download, list, delete
│   │       ├── share.py          # Create/use share links
│   │       ├── users.py          # Admin user management
│   │       ├── audit.py          # Admin audit log viewer
│   │       └── health.py         # Health check (is the server alive?)
│   │
│   ├── core/                     # Infrastructure / connections
│   │   ├── config.py             # All settings from .env
│   │   ├── database.py           # PostgreSQL connection + session factory
│   │   ├── redis.py              # Redis client wrapper
│   │   └── s3.py                 # AWS S3 client wrapper
│   │
│   ├── models/                   # SQLAlchemy ORM models (= database tables)
│   │   ├── user.py               # Users table
│   │   ├── role.py               # Roles table
│   │   ├── file.py               # Files metadata table
│   │   ├── file_permission.py    # File sharing permissions table
│   │   ├── share_link.py         # Share links table
│   │   ├── audit_log.py          # Audit logs table
│   │   └── base.py               # Base model with id, created_at, updated_at
│   │
│   ├── schemas/                  # Pydantic models (request/response shapes)
│   │   ├── auth.py               # LoginRequest, RegisterRequest, TokenResponse
│   │   ├── file.py               # FileResponse, FileUpdate
│   │   ├── share.py              # ShareLinkCreate, ShareLinkInfo
│   │   ├── user.py               # UserResponse, UserUpdate
│   │   ├── audit.py              # AuditLogResponse
│   │   └── common.py             # Pagination, generic responses
│   │
│   ├── security/                 # Authentication & authorization
│   │   ├── jwt.py                # Create & verify JWT tokens
│   │   ├── password.py           # bcrypt hash & verify
│   │   ├── rbac.py               # Role hierarchy & permission checks
│   │   └── dependencies.py       # FastAPI deps: get_current_user, require_role
│   │
│   ├── services/                 # Business logic layer
│   │   ├── auth_service.py       # Register, login, refresh logic
│   │   ├── file_service.py       # Upload, download, delete, permissions
│   │   ├── share_service.py      # Create/validate/use share links
│   │   ├── user_service.py       # User CRUD, role assignment
│   │   └── audit_service.py      # Write & query audit logs
│   │
│   └── utils/                    # Helpers
│       ├── helpers.py            # Misc utilities
│       └── logging.py            # Logging configuration
│
├── frontend/                     # ← All frontend code
│   ├── src/
│   │   ├── App.tsx               # Route definitions
│   │   ├── main.tsx              # React entry point
│   │   ├── api/                  # Axios API client + resource-specific calls
│   │   ├── components/           # Reusable UI components
│   │   ├── pages/                # Full-page components (one per route)
│   │   ├── store/                # Zustand auth state
│   │   └── types/                # TypeScript interfaces
│   ├── index.html                # HTML shell (React mounts here)
│   ├── vite.config.ts            # Vite config + API proxy
│   └── package.json              # Frontend dependencies
│
├── migrations/                   # ← Alembic database migrations
│   ├── env.py                    # Migration environment config
│   └── versions/                 # Each migration is a Python file
│       ├── 001_initial_migration.py
│       └── 20260131_..._add_password_hash_to_share_links.py
│
├── tests/                        # ← Pytest test files
│   ├── conftest.py               # Test fixtures and setup
│   ├── test_auth.py              # Auth endpoint tests
│   ├── test_files.py             # File endpoint tests
│   ├── test_share.py             # Share endpoint tests
│   ├── test_users.py             # User endpoint tests
│   ├── test_audit.py             # Audit endpoint tests
│   └── test_health.py            # Health check tests
│
├── docs/                         # ← Documentation
│   └── screenshots/              # Demo screenshots for README
│
├── .env.example                  # Environment variable template (safe to commit)
├── .gitignore                    # Files that should never be in Git
├── alembic.ini                   # Alembic migration configuration
├── docker-compose.yml            # Docker config for Redis
├── requirements.txt              # Python dependencies
└── README.md                     # Project overview with architecture diagrams
```

---

## Summary

This project is a **production-grade secure file sharing platform** that demonstrates:

- **Clean architecture** — separated layers that are easy to understand and maintain
- **Real security** — bcrypt passwords, JWT auth, RBAC, private S3 storage, audit trails
- **Modern frontend** — React + TypeScript with type-safe API calls and global state management
- **Smart caching** — Redis for ephemeral data with automatic expiration
- **Full observability** — every sensitive action logged with who, what, when, and where

It's the kind of system you'd actually deploy in a company where file security matters — think legal documents, medical records, or confidential business reports.

---

*This document is part of the [Secure File Sharing System](https://github.com/abhimh33/Secure_file_sharing_System) project.*
