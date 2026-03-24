## Prerequisites

- Python 3.10+
- Node.js & npm (for Frontend)
- [Google Cloud Project](https://console.cloud.google.com/) with Vertex AI enabled.

## Installation & Setup

Clone the repository:

```bash
git clone <repository-url>
cd UAI_GPT
```

### 1. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Install dependencies using `uv` (recommended) or `pip`:

```bash
# Using uv
uv sync

# Using pip
pip install -r requirements.txt
```

**Configuration**:
Ensure you have a `.env` file with your Google Cloud credentials (API keys) or set up Application Default Credentials.

Start the Backend Server:

```bash
uv run uvicorn app.main:app --reload
```

The API will run at `http://127.0.0.1:8000`.

### 2. Frontend Setup

Navigate to the frontend directory:

```bash
cd ../frontend
```

Install dependencies:

```bash
npm install
```

Start the Development Server:

```bash
npm run dev
```

The Frontend will run at `http://localhost:5173` (default Vite port).

## Project Structure

- `backend/`
  - `app/`: Core application logic (API, Services, Models).
  - `tests/`: specific test scripts.
  - `requirements.txt`: Python dependencies.
- `frontend/`
  - `src/`: React source code (Components, Pages).
  - `vite.config.ts`: Vite configuration.
  - `package.json`: Node dependencies.

## API Documentation

- **Swagger UI**: Visit `http://127.0.0.1:8000/docs`.

## Render Deployment

This repository is a monorepo with both `frontend/` and `backend/`. For Render, the recommended setup is to deploy from the repository root so changes in either folder trigger a new deploy.

### Render Dashboard Values

- Root Directory: leave blank
- Build Command: `pip install -r backend/requirements-render.txt && cd frontend && npm ci && npm run build && cd .. && mkdir -p backend/generated_images`
- Start Command: `cd backend && python -m uvicorn app.main_render:app --host 0.0.0.0 --port $PORT --workers 1`

### Why Root Directory Should Be Blank

If you set Root Directory to `backend`, Render will ignore changes in `frontend/` for auto-deploys. Since this app builds the React frontend into `backend/static`, deploying from the repo root is the correct setup.

### Required Environment Variables

- `SECRET_KEY`: generate a random secret in Render
- `ACCESS_TOKEN_EXPIRE_MINUTES`: `1440`
- `JSON_STATE_PATH`: `/opt/render/project/src/backend/data/render_state.json`

### Python Version

The repository pins Python with `.python-version` to `3.11.11`. This avoids the Render default Python 3.14 issue from your failed build log.

## JSON Storage On Render

This deployment can run without MySQL. When no DB environment variables are set, the backend stores users, profiles, sessions, and chat history in a JSON file.

Default JSON path:

```text
/opt/render/project/src/backend/data/render_state.json
```

The backend creates this file automatically on first startup.

### Expected JSON Shape

Use a top-level object with these keys:

```json
{
  "users": {
    "demo": {
      "id": 1,
      "username": "demo",
      "email": "demo@example.com",
      "password_hash": "$2b$12$...",
      "subscription_tier": "free",
      "is_active": true,
      "created_at": "2026-03-24T12:00:00+00:00"
    }
  },
  "profiles": {},
  "sessions": {},
  "messages": {},
  "next_user_id": 2
}
```

### Using Your Own JSON Seed

If you already have JSON data, place it at `backend/data/render_state.json` before deploy, or change `JSON_STATE_PATH` in Render to point at a different file inside the project.

The repository still includes `backend/scripts/import_json_to_mysql.py` if you later decide to move to MySQL, but it is not required for this Render setup.

## Notes

- The frontend is built into `backend/static` during the Render build.
- The backend serves the frontend and API from the same Render service.
- If MySQL env vars are not set, the app uses JSON file storage.
- Render web services do not guarantee durable local storage across all redeploy scenarios. If you need durable JSON persistence, attach a persistent disk or move to an external database later.
