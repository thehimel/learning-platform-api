# Troubleshoot Database Connection

When a client (IDE, GUI tool, or app) fails to connect to the PostgreSQL instance from [docker-compose.yml](../docker-compose.yml) with a generic error, work through the following.

## Container Not Running

Start the stack and confirm the service is up:

```shell
docker compose up -d
docker compose ps
```

The `postgres` service should show as running.

## Database Missing (Existing Volume)

Postgres creates `POSTGRES_DB` only on first initialization. If the volume was created when `.env` had a different `POSTGRES_DB` (e.g. `fastapi_db`), the current database name (e.g. `learning-platform`) may not exist.

Create the database:

```shell
docker compose exec postgres psql -U postgres -c "CREATE DATABASE \"learning-platform\";"
```

Or reset the data, which removes everything in the volume:

```shell
docker compose down -v
docker compose up -d
```

## Password

Use the same value as `POSTGRES_PASSWORD` in [.env](../.env.example) (e.g. `postgres`). No leading or trailing spaces.

## Port in Use

If another process is using `5432`, either stop it or set `POSTGRES_PORT` in `.env` to a different port and use that port in the client.

## Verify From the Host

Confirm the database accepts connections:

```shell
docker compose exec postgres psql -U postgres -d learning-platform -c "SELECT 1;"
```

If this succeeds, the problem is in the client (password, SSL, or firewall). If it fails, inspect the logs:

```shell
docker compose logs postgres
```

See [commands.md](commands.md) for more Docker Compose commands.

## Can't Locate Revision

`alembic upgrade head` fails with `Can't locate revision identified by '<id>'` when the database's `alembic_version` points to a migration that no longer exists in `alembic/versions/`, usually after migrations were squashed or history was rewritten.

If the schema already matches the current migrations, point the database at the current head (from `alembic heads`):

```sql
UPDATE alembic_version SET version_num = '<head_revision>';
```

Example: production had `b70fd5d8a1a2` from a migration removed in a history rewrite, while the repo's only migration was `12cae6c097b6` with the same tables. The deploy failed with `Can't locate revision identified by 'b70fd5d8a1a2'`, and this fixed it:

```sql
UPDATE alembic_version SET version_num = '12cae6c097b6';
```

If the data is disposable, drop all tables including `alembic_version` and rerun `alembic upgrade head` instead.

To prevent it, never delete or squash a migration already applied to a shared database; add a new revision on top.
