# A&R Portal - AI Coding Instructions

## Architecture Overview

This is a **FastAPI backend + static HTML/JavaScript frontend** portal for A&R (Artists & Repertoire) management. The backend serves static files and provides authentication APIs, while the frontend consists of standalone HTML pages with embedded JavaScript.

- **Backend**: FastAPI app in `app/` with SQLAlchemy ORM
- **Frontend**: Static HTML pages in `static/` served via `StaticFiles` mount
- **Database**: SQLite (`ar_portal.db`) with PostgreSQL support in config but SQLite hardcoded in [app/db/session.py](../app/db/session.py)
- **Auth**: Dual authentication - traditional username/password + Microsoft Azure AD OAuth2

## Project Structure

```
app/
  main.py          # FastAPI app, CORS, static file mounting, route includes
  api/auth.py      # Authentication endpoints (login, Microsoft OAuth flow)
  core/
    config.py      # Pydantic settings from .env (Azure AD, JWT, DB config)
    security.py    # JWT tokens, password hashing, MSAL integration
  db/
    session.py     # SQLAlchemy engine and SessionLocal (SQLite hardcoded)
    base.py        # Declarative base for models
  models/user.py   # User model with dual auth support (nullable hashed_password)
static/
  login.html       # Login page with Microsoft SSO button
  dashboard/       # Dashboard pages (home, discover, outreach, status)
```

## Critical Configuration Discrepancy

**Database URL Mismatch**: [app/core/config.py](../app/core/config.py) defaults to PostgreSQL, but [app/db/session.py](../app/db/session.py) hardcodes SQLite. When updating database settings, modify `session.py` to use `settings.DATABASE_URL` from config.

## Development Workflow

**Initial Setup**:
```bash
# Create .env with Azure AD credentials (see config.py for required vars)
# Install dependencies
pip install -r requirements.txt

# Initialize database tables
python init_db.py

# Run server
uvicorn app.main:app --reload --port 8000
```

**Key Environment Variables** (in `.env`):
- `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` - Required for Microsoft auth
- `AZURE_REDIRECT_URI` - Defaults to `http://localhost:8000/auth/microsoft/callback`
- `SECRET_KEY` - JWT signing (default is insecure, must change in production)
- `DATABASE_URL` - Not currently used due to hardcoded SQLite in session.py

## Authentication Patterns

### Dual Auth Support
The `User` model supports both traditional and Microsoft authentication via **nullable `hashed_password`**:
- Traditional users: email + hashed_password
- Microsoft users: email only, auto-created on first OAuth login with default role "user"

### Microsoft OAuth Flow
1. Frontend calls `/auth/microsoft/login` → returns `auth_url`
2. User redirects to Microsoft, authenticates
3. Microsoft redirects to `/auth/microsoft/callback` with `code` and `state`
4. Backend exchanges code for token, fetches user info from Graph API
5. Auto-creates user if not exists, generates JWT, redirects to `/dashboard` with token in query params

**CSRF Protection**: Uses in-memory `oauth_states` dict (not production-ready - use Redis/DB in prod)

## Frontend Integration Conventions

- **Token Passing**: Dashboard redirect includes JWT and user info as URL query params (see [app/api/auth.py](../app/api/auth.py))
- **Static Routing**: Main routes (`/`, `/dashboard`) serve HTML files via `FileResponse` or `RedirectResponse`
- **Client-Side State**: Frontend JavaScript must extract token from URL and store locally

## Database Patterns

- Use SQLAlchemy ORM exclusively (see [app/models/user.py](../app/models/user.py))
- Import `Base` from `app.db.base` for new models
- Run `init_db.py` to create/update tables (no Alembic migrations currently configured)
- Dependency injection pattern: use `get_db()` dependency in route handlers

## Security Considerations

- **JWT Tokens**: Created with `create_access_token()` in [app/core/security.py](../app/core/security.py), 60-minute expiry
- **Password Hashing**: Uses bcrypt via passlib (see `hash_password`/`verify_password`)
- **Protected Endpoints**: All `/api/discover/*` endpoints require JWT authentication via `get_current_user` dependency
- **Rate Limiting**: SlowAPI configured - 5 requests/minute on `/auth/login`
- **CORS**: Configured for localhost development on ports 3000, 5173, 8000
- **State Management**: OAuth states stored in-memory - **not suitable for production multi-instance deployments**
- **⚠️ CRITICAL**: Default `SECRET_KEY` must be changed in production (see SECURITY.md)

## Adding New Features

**New API Endpoints**: Create router in `app/api/`, import in [app/main.py](../app/main.py)

**New Models**: 
1. Define in `app/models/` inheriting from `Base`
2. Import in [init_db.py](../init_db.py) 
3. Run `python init_db.py` to create tables

**New Dashboard Pages**: Add HTML to `static/dashboard/`, reference in navigation

## Testing & Quality

- `pytest`, `black`, `ruff` in requirements but no test files exist yet
- No CI/CD or linting configuration currently in place
