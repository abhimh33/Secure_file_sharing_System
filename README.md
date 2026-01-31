# 🔒 Secure File Sharing System

A production-ready secure file sharing platform built with FastAPI, PostgreSQL, Redis, and AWS S3.

## ✨ Features

- **🔐 JWT Authentication** - Access & refresh tokens with configurable expiry
- **👥 Role-Based Access Control** - Admin, User, and Viewer roles
- **📁 Secure File Storage** - Private AWS S3 bucket storage
- **🔗 Expiring Share Links** - Redis-based TTL share links
- **📝 Complete Audit Logging** - Track all sensitive actions
- **⚡ Rate Limiting** - Redis-based request rate limiting
- **🔒 No Direct S3 Access** - All file downloads through backend

## 🏗️ Architecture

```
Client (Web / API Client)
        |
        v
FastAPI Gateway (JWT + RBAC)
        |
        |-- PostgreSQL (users, files, permissions, audit logs)
        |
        |-- Redis (expiring share links, rate limiting, TTL)
        |
        |-- AWS S3 (private file storage)
```

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL + SQLAlchemy + Alembic
- **Cache**: Redis
- **Storage**: AWS S3
- **Auth**: JWT (python-jose) + bcrypt
- **Testing**: pytest

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- AWS Account with S3 access
- Docker (for Redis)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd Secure_FileSharing_System

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start Redis (Docker)

```bash
docker-compose up -d redis
```

### 3. Create PostgreSQL Database

```sql
-- Connect to PostgreSQL and run:
CREATE DATABASE "SECUREFILE_SHARING_APPLICATION";
```

### 4. Configure Environment

The `.env` file is already configured. Update if needed:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=AbhiMH33
POSTGRES_DB=SECUREFILE_SHARING_APPLICATION

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# AWS S3 (update with your credentials)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-2
S3_BUCKET_NAME=your-bucket-name

# JWT
JWT_SECRET_KEY=AbhiMH33
ACCESS_TOKEN_EXPIRE_MINUTES=20
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 5. Run Application

```bash
# Run with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Access API Documentation

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## 📚 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout user |
| GET | `/api/v1/auth/me` | Get current user |

### Users (Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/` | List all users |
| GET | `/api/v1/users/{id}` | Get user details |
| PUT | `/api/v1/users/me` | Update own profile |
| PUT | `/api/v1/users/{id}/role` | Assign role |
| DELETE | `/api/v1/users/{id}` | Deactivate user |

### Files
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/files/upload` | Upload file |
| GET | `/api/v1/files/` | List my files |
| GET | `/api/v1/files/shared` | List shared files |
| GET | `/api/v1/files/{id}` | Get file details |
| GET | `/api/v1/files/{id}/download` | Download file |
| DELETE | `/api/v1/files/{id}` | Delete file |
| POST | `/api/v1/files/{id}/permissions` | Grant permission |

### Share Links
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/share/` | Create share link |
| GET | `/api/v1/share/` | List my share links |
| GET | `/api/v1/share/{token}/info` | Get link info |
| GET | `/api/v1/share/{token}/download` | Download via link |
| DELETE | `/api/v1/share/{token}` | Revoke link |

### Audit Logs (Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/audit/` | Get all audit logs |
| GET | `/api/v1/audit/my-activity` | Get own activity |
| GET | `/api/v1/audit/file/{id}` | Get file history |

## 👥 User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full system access, user management, view all files |
| **User** | Upload, manage, share own files |
| **Viewer** | Download shared files only |

## 🔐 Security Features

1. **Private S3 Buckets** - No public access to files
2. **Backend-Only Downloads** - All file access through API
3. **JWT Token Security** - Short-lived access tokens, longer refresh tokens
4. **Password Hashing** - bcrypt with salt
5. **Rate Limiting** - 60 requests/minute per IP
6. **Audit Logging** - Complete trail of all actions
7. **RBAC** - Role-based endpoint protection
8. **Input Validation** - Pydantic schemas on all endpoints

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py -v
```

## 📁 Project Structure

```
secure-file-sharing/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   ├── users.py
│   │       │   ├── files.py
│   │       │   ├── share.py
│   │       │   ├── audit.py
│   │       │   └── health.py
│   │       └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── redis.py
│   │   └── s3.py
│   ├── models/
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── file.py
│   │   ├── file_permission.py
│   │   ├── share_link.py
│   │   └── audit_log.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── file.py
│   │   ├── share.py
│   │   └── audit.py
│   ├── security/
│   │   ├── dependencies.py
│   │   ├── jwt.py
│   │   ├── password.py
│   │   └── rbac.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── file_service.py
│   │   ├── share_service.py
│   │   └── audit_service.py
│   └── main.py
├── migrations/
│   ├── versions/
│   │   └── 001_initial_migration.py
│   └── env.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_files.py
│   ├── test_share.py
│   └── test_audit.py
├── .env
├── alembic.ini
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔧 Database Migrations

```bash
# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🐳 Docker (Coming Soon)

```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f app
```

## 📈 Default Admin Account

On first startup, a default admin user is created:

- **Email**: admin@securefile.com
- **Password**: AbhiMH33

⚠️ **Change this password in production!**

## 🚧 Coming Soon

- [ ] Dockerfile for FastAPI app
- [ ] Kubernetes manifests
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Ansible playbooks
- [ ] Email verification
- [ ] Password reset

## 📝 License

MIT License

## 👨‍💻 Author

Secure File Sharing System - Built for enterprise-grade file sharing.
