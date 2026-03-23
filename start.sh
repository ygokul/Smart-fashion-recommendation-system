#!/bin/bash
set -e

echo "🚀 Starting Smart Fashion Recommendation System (Backend + Frontend)"

# Install backend deps
cd backend
echo "📦 Installing Python deps..."
uv sync --frozen

# Backend in background
echo "🐍 Starting FastAPI backend..."
uv run --frozen uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend
sleep 5
curl -f http://localhost:8000/health || (echo "Backend health check failed"; exit 1)

# Frontend
cd ../frontend
echo "📦 Installing Node deps & building..."
npm ci --only=production
npm run build

# Serve frontend static files via backend? Or simple nginx/http-server
# Option 1: http-server (lightweight)
npx http-server dist -p 3000 -c-1 --cors &

FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Health check
sleep 3
curl -f http://localhost:3000 || (echo "Frontend failed"; exit 1)

echo "✅ Both services running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"

# Wait for both
wait $BACKEND_PID $FRONTEND_PID
