# BioWorkspace

BioWorkspace is a FastAPI web app for medical biotechnology learning, study notes, practice questions, and a private laboratory case organizer. PostgreSQL data can live on Neon. Sign-up and login use app-issued JWTs; passwords are hashed before they are saved. The application does not approve or release clinical results.

## Run locally

Python 3.12 or later is recommended.

```bash
cd /home/gamp/kimaya/biotech-platform
python3 -m venv .venv
source .venv/bin/activate                 # Windows: .venv\\Scripts\\activate
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
python3 seed.py
uvicorn app.main:app --reload
```

Open <http://localhost:8000>. The app uses local SQLite by default so it can run before you create a Neon project.

## Connect Neon

1. Create a PostgreSQL project in Neon and copy its connection string from the project dashboard.
2. In `.env`, replace `DATABASE_URL` with that connection string. It should use SSL (`sslmode=require`); Neon provides pooled and direct connection strings in its console. [Neon connection guide](https://neon.com/docs/connect/connect-from-any-app)
3. Stop the local app, run `alembic upgrade head`, then `python3 seed.py`.
4. Start the app again with `uvicorn app.main:app --reload`.

The SQLAlchemy driver accepts Neon `postgresql://` URLs and converts them to Psycopg 3. Keep the connection string private. Neon provides a project connection URI with the database, role, and password. [Neon connection guide](https://neon.com/docs/connect/connect-from-any-app)

## Authentication

- `/signup`: create an account with a name, email, and password.
- `/auth/login`: sign in using email and password.
- `/auth/logout`: clear the JWT cookie.

Passwords are hashed with scrypt. A JWT is stored in an HttpOnly cookie and expires after `JWT_EXPIRY_MINUTES` (12 hours by default). Set `JWT_SECRET` to a unique random value of at least 32 characters in production. Also set a unique `SESSION_SECRET`; it signs the short-lived form session used for CSRF protection. Generate secrets with:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

The JWT cookie is marked Secure in production. If you use the API directly, you can send the token as `Authorization: Bearer <token>`.

## Main areas

- `/dashboard`: account workspace overview.
- `/lessons`: 2026–2027 curriculum grouped by track and year.
- `/courses/{course_code}`: published course packs and progress.
- `/notes`: study notes, learning sources, and file uploads.
- `/practice`: practice questions and progress.
- `/cases`: pseudonymous lab cases and structured results.

Uploaded files are stored in `LOCAL_UPLOAD_DIR` on the application filesystem. Keep backups of that folder. On hosting with ephemeral disks, files can disappear when the app is redeployed; choose a host with persistent storage or add a non-AWS object-storage provider before relying on uploads in production.

Database schema changes use Alembic. For a hosted deployment, set `APP_ENV=production`, `DATABASE_URL`, `JWT_SECRET`, `SESSION_SECRET`, and any AI settings in the host’s environment configuration. Apply migrations with `python -m alembic upgrade head` before starting the app.

## AI and privacy settings

AI is off by default. The adapter accepts an OpenAI-compatible provider after review:

| Variable | Purpose |
|---|---|
| `AI_ENABLED` | Explicit feature switch |
| `AI_BASE_URL` | Approved provider endpoint |
| `AI_API_KEY` | Provider credential; store as a hosting secret |
| `AI_MODEL` | Approved model name |
| `AI_MONTHLY_REQUEST_LIMIT` | Per-user monthly request limit |

Identifiable patient information remains disabled by default. Do not enable it before privacy and security review and key configuration.

## Quality checks

```bash
pytest -q
ruff check app tests worker.py seed.py
```

Browser smoke tests require Playwright Chromium and `RUN_BROWSER_TESTS=1`. Use keyboard-only navigation and a screen reader when reviewing accessibility.
