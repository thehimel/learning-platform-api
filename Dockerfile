# Use the official Python slim image (smaller footprint than the full image)
FROM python:3.14-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set the working directory for subsequent commands
WORKDIR /usr/src/app

# Copy dependency files first to leverage layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy the rest of the application code
COPY . ./

# Start Uvicorn (bind to 0.0.0.0 so the app is reachable from outside the container)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
