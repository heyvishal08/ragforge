# ==========================================
# Stage 1: Build the Next.js Frontend
# ==========================================
FROM node:20-bookworm-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm run build

# ==========================================
# Stage 2: Final Runtime (FastAPI + Next.js + Nginx)
# ==========================================
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies, Node.js 20, Nginx, and Supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    build-essential \
    libpq-dev \
    nginx \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU first (saves ~1.5GB of GPU bloat and speeds up build)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install backend Python dependencies
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend application code
COPY backend/ /app/backend/
COPY data/ /app/data/

# Copy built frontend application code and production node_modules from builder
COPY --from=frontend-builder /app/frontend/ /app/frontend/

# Copy reverse proxy and supervisor configurations
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Pre-create upload and demo directories with permissions
RUN mkdir -p /app/data/uploads /app/data/demo /tmp/client_body /tmp/proxy_temp \
    && chmod -R 777 /app/data /tmp

# Hugging Face Spaces standard port
EXPOSE 7860

# Default environment variables for container
ENV PORT=7860
ENV BACKEND_HOST=127.0.0.1
ENV BACKEND_PORT=8000
ENV NODE_ENV=production

# Start supervisord to launch Nginx, FastAPI, and Next.js
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
