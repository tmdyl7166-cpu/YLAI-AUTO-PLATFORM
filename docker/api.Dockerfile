# syntax=docker/dockerfile:1
FROM python:3.12-slim AS api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (if needed for build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt /app/backend/requirements.txt
# Copy the whole project (make optional root requirements available if present)
COPY . /app

RUN python -m pip install -U pip wheel setuptools && \
    ( [ -f /app/requirements.txt ] && python -m pip install -r /app/requirements.txt || true ) && \
    python -m pip install -r /app/backend/requirements.txt

EXPOSE 8001
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8001"]
