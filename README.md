# ER:LC Control Panel

A server-side FastAPI foundation for an ER:LC private-server control panel.
The browser talks only to this application; the ER:LC server key remains on the
backend.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Set the real `SERVER_KEY` in `.env`, then start the development server:

```powershell
.\.venv\Scripts\python run.py
```

Open `http://127.0.0.1:8000`. Interactive API documentation is available at
`http://127.0.0.1:8000/docs`.

## Application Layout

- `app/config.py`: environment configuration and command allowlist.
- `app/client.py`: ER:LC HTTP client with no automatic retries.
- `app/schemas.py`: validated public request and response models.
- `app/services/`: application policy, including command authorization.
- `app/routes/`: FastAPI server and command endpoints.
- `app/templates/`: server-rendered HTML.
- `app/static/`: browser CSS and JavaScript.
- `tests/`: client, service, and application tests.

## API

- `GET /health`: local application health.
- `GET /api/server`: safe server summary without the server or join keys.
- `POST /api/commands`: sends an allowlisted ER:LC command.

The default command allowlist is `h,m`. Configure it as a comma-separated list:

```dotenv
COMMAND_ALLOWLIST=h,m
```

## Development Checks

```powershell
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\ruff check .
```

## Security Boundary

Do not expose this application publicly until authentication, role-based access,
CSRF protection, rate limiting, and audit logging are implemented. The backend's
public IP must be authorized in the ER:LC Server Owner Dashboard before command
requests can succeed.
