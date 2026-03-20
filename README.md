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
