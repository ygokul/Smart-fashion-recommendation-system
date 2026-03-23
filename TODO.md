# Render Deployment Progress

✅ 1. Created render.yaml (Backend Python + Frontend Static + PostgreSQL blueprint)

✅ 2. Updated TODO.md with progress

## Remaining Steps:
- [ ] Push to GitHub: `git add . && git commit -m "Add Render deployment config" && git push`
- [ ] Render Dashboard → New → Blueprint → Connect repo (auto-deploys services)
- [ ] **DB Migration MySQL → PostgreSQL**:
  | Issue | Next Action |
  |-------|-------------|
  | mysql-connector-python | Add `psycopg[binary]>=3.2.0` to pyproject.toml |
  | DB connection/pool | Refactor backend/app/main.py to psycopg |
  | Schema (database.sql) | Create `backend/postgres.sql` with SERIAL/JSONB |
- [ ] Test endpoints: Backend `/health`, `/docs`; Frontend connects to API
- [ ] Update frontend API_URL (in components) to prod backend URL
- [ ] Custom domains (optional)

## Quick Deploy:
```
git add render.yaml TODO.md
git commit -m "feat: Add Render.yaml blueprint"
git push origin main
```
Then Render auto-builds!

## Notes:
- Free PostgreSQL (512MB/90-day limit) - link auto-injects env vars.
- Backend build: `uv sync --frozen` (optimal).
- User manual DB init/migration post-deploy.

