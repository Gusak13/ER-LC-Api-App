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

On this computer, open `http://127.0.0.1:8000`.

To use the control panel from a phone on the same local network, open
`http://<YOUR-PC-IP>:8000` on the phone. The PC may use Wi-Fi or Ethernet as
long as both devices connect through the same router. Find the address with:

```powershell
Get-NetIPConfiguration |
    Where-Object IPv4DefaultGateway |
    ForEach-Object { $_.IPv4Address.IPAddress }
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.
The development server listens on all local network interfaces. Do not expose
port 8000 through your router or use this unauthenticated app on public Wi-Fi.

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
- `GET /api/players`: current player summaries from the ER:LC v2 `Players` expansion.
- `POST /api/commands`: sends an ER:LC command.

All commands are enabled by default. Use a comma-separated list to restrict the
application to specific commands, or use `*` to keep every command enabled:

```dotenv
COMMAND_ALLOWLIST=*
```

ER:LC can still reject commands that its remote API restricts. Because this
control panel has no user authentication, every device that can reach it can
attempt any enabled command.

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
