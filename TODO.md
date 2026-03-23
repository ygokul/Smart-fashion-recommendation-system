# Smart Fashion Recommendation System - Deployment TODO

## Render Configuration Plan (Approved)
1. [x] Understand project: Monorepo (backend Python/FastAPI + frontend Vite/React), Docker + start.sh for both services.
2. [x] Plan confirmed: Root Directory: empty | Build: empty | Start: ./start.sh (mandatory fields handled; Docker overrides).
3. [] Update Render dashboard/render.yaml with values.
4. [] Test locally: `docker build -t app . && docker run -p 8000:8000 -p 3000:3000 -e PORT=10000 app` (note: adapt start.sh for $PORT if needed).
5. [] Deploy on Render, verify backend (8000)/frontend (3000).
6. [] Optional: Refactor for single $PORT (backend proxy /api, serve frontend static).
