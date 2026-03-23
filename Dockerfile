FROM python:3.12-slim

# Install Node for frontend
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g http-server uv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend
COPY backend/ ./backend/
WORKDIR /app/backend
RUN uv sync --frozen

# Frontend
WORKDIR /app/frontend
COPY frontend/ ./frontend/
RUN npm ci --only=production && npm run build

# Root
WORKDIR /app
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8000 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || curl -f http://localhost:3000 || exit 1

CMD ["./start.sh"]
