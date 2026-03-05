# Commands

## Management

```shell
uv run uvicorn app.main:app --reload
```

### Health Check

```shell
# Verify API is running
curl http://localhost:8000/

# Verify database connectivity
curl http://localhost:8000/health/db
```

## Docker

### Build and Run (Standalone)

```shell
# Build the image with a custom tag
docker build -t learning-platform-api .

# Run the container (interactive, remove on exit)
docker run -it --rm --name learning-platform-api learning-platform-api
```

### Run a Single Python Script

```shell
# Mount current directory and run a script (replace your-demon-script.py with your file)
docker run -it --rm -v "$PWD":/usr/src/app -w /usr/src/app python:3.14 python your-demon-script.py
```

### Inspect Container Filesystem

```shell
# Open a shell in the running API container (use container name from docker compose ps)
docker exec -it learning-platform-api bash

# Verify bind mount: check that local files are available
cat app/main.py
```

## Docker Compose

### PostgreSQL Only

```shell
# Start PostgreSQL in the background (run app.main locally against it)
docker compose up -d postgres

# Check service status
docker compose ps postgres

# View logs (use -f to follow)
docker compose logs postgres
docker compose logs -f postgres

# Stop
docker compose stop postgres

# Stop and remove the database volume (deletes data)
docker compose down -v postgres
```

### API and PostgreSQL (Bind Mount, --reload)

```shell
# Start API and PostgreSQL
docker compose up -d

# Rebuild after Dockerfile changes (--build forces a rebuild so Dockerfile changes are reflected)
docker compose up --build -d

# Check service status
docker compose ps

# View logs (use -f to follow)
docker compose logs api
docker compose logs -f api

# Stop
docker compose down

# Stop and remove the database volume (deletes data)
docker compose down -v

# Create database if missing (e.g. after changing POSTGRES_DB in .env)
docker compose exec postgres psql -U postgres -c "CREATE DATABASE \"learning-platform\";"

# Verify connection from host (replace DB name if different)
docker compose exec postgres psql -U postgres -d learning-platform -c "SELECT 1;"
```

### Compose Logs (All Services)

```shell
# View logs from all services (use -f to follow)
docker compose logs
docker compose logs -f
```

### Docker Hub (Push Image)

```shell
# Build the image first (if not already built)
docker compose build

# Log in to Docker Hub
docker login

# Tag the locally built image (replace username with your Docker Hub username)
# Image name is typically project_service, e.g. learning-platform-api_api
docker image tag learning-platform-api_api username/fastapi

# Verify the tag
docker image ls

# Push the image to Docker Hub
docker push username/fastapi
```

`docker-compose.yml` can reference `image: username/fastapi` instead of `build: .` to use the pushed image.

## Alembic

Run from the project root. See [Alembic Setup](config/sqlalchemy-alembic-async-setup.md) for the full guide.

| Description | Alembic | Django equivalent |
|-------------|---------|-------------------|
| Initialize Alembic (creates `alembic/` and `alembic.ini`) | `alembic init alembic` | none |
| Create migration from model changes | `alembic revision --autogenerate -m "message"` | `python manage.py makemigrations` |
| Create manual migration, no autogenerate | `alembic revision -m "message"` | `python manage.py makemigrations` |
| Apply all pending migrations | `alembic upgrade head` | `python manage.py migrate` |
| Upgrade to a specific revision | `alembic upgrade <revision>` | `python manage.py migrate <app> <revision>` |
| Roll back one revision | `alembic downgrade -1` | `python manage.py migrate <app> <prev_rev>` |
| Roll back to a specific revision | `alembic downgrade <revision>` | `python manage.py migrate <app> <revision>` |
| Show current revision | `alembic current` | `python manage.py showmigrations` |
| Show latest (head) migration | `alembic heads` | `python manage.py showmigrations` |
| List migration history | `alembic history` | `python manage.py showmigrations` |

`alembic downgrade -N` works for any negative N (e.g. `-2`, `-3`) to roll back multiple revisions. For branched migrations, prefer `alembic downgrade <revision>` with a specific revision ID.

Verify applied migrations in PostgreSQL:

```shell
docker compose exec postgres psql -U postgres -d learning-platform -c "SELECT * FROM public.alembic_version ORDER BY version_num ASC;"
```

## Ruff

```shell
# Lint
ruff check .

# Format
ruff format .

# Lint with auto-fix
ruff check . --fix

# Lint and format specific path
ruff check app/
ruff format app/
```

## Pytest

Run from the project root. The test database (`{POSTGRES_DB}_test`, or `POSTGRES_DB_TEST` if set) is created automatically before tests, and migrations run automatically. No manual setup needed.

```shell
# Run all tests (minimal output)
pytest

# List each test function (verbose)
pytest -v

# Show print statements (disable output capture; useful when debugging)
pytest -v -s

# Stop on first failure (useful when debugging)
pytest -x

# Drop the test database after the run (clean teardown)
pytest --drop-test-db

# Show create/teardown log messages
pytest --log-cli-level=INFO

# Suppress warning messages
pytest --disable-warnings

# Explore all available options
pytest --help
```

### Faster Runs

```shell
# Quiet mode (less output, slightly faster)
pytest -q

# Show 10 slowest tests (helps find bottlenecks)
pytest --durations=10

# Parallel execution across CPU cores (pytest-xdist)
# May be faster on large suites; can be slower on small suites due to worker overhead
pytest -n auto

# Combine: quiet + parallel
pytest -q -n auto
```

## Pre-commit

```shell
# Install pre-commit hooks (run once)
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files

# Run pre-commit on staged files only (default when run on commit)
pre-commit run
```

## JWT

```shell
# Generate a secure secret key for JWT (set as JWT_SECRET_KEY in .env)
openssl rand -hex 32
```

## Install Dependencies

```shell
uv sync
```
