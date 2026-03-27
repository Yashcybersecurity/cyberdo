# CyberSentinel

CyberSentinel is a Flask + SQLite cyber operations dashboard with:
- Threat overview dashboard
- Intelligence modules (dark web monitor, AI classifier, threat intel feed, forecasting, forensics, playbooks)
- Citizen complaint intake
- Incident and IOC management APIs

This guide is for Windows users only and is written for VS Code terminal (PowerShell).

## 1. Prerequisites

Install these first:
- Git
- Python 3.10+ (recommended: 3.11+)
- VS Code (optional but recommended)

Check versions:

```bash
git --version
python3 --version
```

## 2. Clone The Repository

```bash
git clone https://github.com/Yashcybersecurity/cyberdo.git
cd cyberdo
```

If your cloned folder name is different, `cd` into the folder containing:
- `server.py`
- `init_db.py`
- `schema.sql`
- `index.html`

## 3. Create And Activate Virtual Environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

After activation, your terminal should show `(.venv)`.

## 4. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Current required package:
- `Flask`

## 5. Initialize Database

Run this once to create/reset `cybersentinel.db`:

```bash
python init_db.py
```

What this does:
- Creates SQLite DB
- Applies `schema.sql`
- Loads `seed.sql` if present (optional)

## 6. Run The Server

```bash
python server.py
```

Expected output includes:
- `API: http://localhost:5050`

Open in browser:
- Dashboard: http://localhost:5050/
- Login: http://localhost:5050/login
- DB Records: http://localhost:5050/db-records

## 7. Quick Health Check (Terminal)

In a new terminal (project root):

```powershell
curl http://localhost:5050/api/health
```

Expected: JSON with `"success": true` and status info.

## 8. Developer Workflow

Each time you come back to the project:

```powershell
cd cyberdo
.\.venv\Scripts\Activate.ps1
python server.py
```

## 9. Common Issues + Fixes

### `flask: command not found` or import errors
You likely did not activate the virtual environment.

Fix:

```powershell
.\.venv\Scripts\Activate.ps1
python server.py
```

### Port 5050 already in use
Another process is already running on that port.

Windows (PowerShell):

```powershell
netstat -ano | findstr :5050
taskkill /PID <PID> /F
```

Then run:

```powershell
python server.py
```

### PEP 668 / externally-managed-environment error
Install packages only inside `.venv` (do not use global pip).

### Database looks stale
Reinitialize:

```powershell
python init_db.py
```

Warning: this resets database state.

## 10. Project Structure

```text
cyberdo/
  index.html          # Main dashboard UI
  LOGIN.html          # Login page
  db_records.html     # Database records UI
  server.py           # Flask API + static file serving
  init_db.py          # Database initializer
  schema.sql          # SQLite schema
  requirements.txt    # Python dependencies
```

## 11. Useful API Endpoints

- `GET /api/health`
- `GET /api/dashboard/kpis`
- `GET /api/intelligence/threat-feed`
- `GET /api/intelligence/dark-web-monitor`
- `GET /api/intelligence/forecast`
- `GET /api/intelligence/forensics`
- `POST /api/intelligence/classify-text`

Example classifier request:

```powershell
curl -X POST http://localhost:5050/api/intelligence/classify-text \
  -H "Content-Type: application/json" \
  -d '{"text":"Received OTP scam call and money got debited"}'
```

PowerShell-friendly alternative:

```powershell
$body = @{ text = "Received OTP scam call and money got debited" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:5050/api/intelligence/classify-text" -Method Post -ContentType "application/json" -Body $body
```

## 12. Stop Server

Press:

```text
Ctrl + C
```

inside the terminal where `python server.py` is running.
