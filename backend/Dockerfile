FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Railway (and Render) inject a $PORT env var at runtime and route traffic
# to whatever port the container actually listens on — a hardcoded port
# here would silently mismatch that and make every deployment fail its
# health check even though the build succeeded. Shell form + ${PORT:-8000}
# uses Railway's assigned port when present, and falls back to 8000 for
# plain `docker run` / docker-compose locally where $PORT isn't set.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
