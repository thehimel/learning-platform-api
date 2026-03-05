# FastAPI Users Setup

> **Maintenance notice:** FastAPI Users is in maintenance mode — no new features, only security and dependency updates. It is stable for production use.

---

## Overview

[fastapi-users](https://github.com/fastapi-users/fastapi-users) provides ready-to-use user registration, login, password reset, and email verification. It integrates natively with async SQLAlchemy and JWT.

### What it provides out of the box

| Feature | Endpoint |
|---|---|
| Register | `POST /auth/register` |
| Login (JWT) | `POST /auth/jwt/login` |
| Logout | `POST /auth/jwt/logout` |
| Forgot password | `POST /auth/forgot-password` |
| Reset password | `POST /auth/reset-password` |
| Request verification | `POST /auth/request-verify-token` |
| Verify email | `POST /auth/verify` |
| Get current user | `GET /users/me` |
| Update current user | `PATCH /users/me` |
| Get user by ID (admin) | `GET /users/{id}` |
| Update user (admin) | `PATCH /users/{id}` |
| Delete user (admin) | `DELETE /users/{id}` |

---

## Step 1 — Install

Add to `requirements.txt`:

```
fastapi-users[sqlalchemy]
```

Install:

```bash
pip install "fastapi-users[sqlalchemy]"
```

> `asyncpg` and `sqlalchemy[asyncio]` are already in `requirements.txt` — no additional driver install needed.

---

## Step 2 — Add Secrets to `app/config.py`

FastAPI Users needs separate secrets for password reset and verification tokens. Add these to `Settings`:

```python
# app/config.py — add inside the Settings class

# FastAPI Users
auth_reset_password_token_secret: str
auth_verification_token_secret: str
```

Add to `.env` and `.env.example`:

```bash
# FastAPI Users — generate each with: openssl rand -hex 32
AUTH_RESET_PASSWORD_TOKEN_SECRET=your-reset-secret-here
AUTH_VERIFICATION_TOKEN_SECRET=your-verification-secret-here
```

---

## Step 3 — Create the User Model

FastAPI Users provides `SQLAlchemyBaseUserTableUUID` which includes all required auth fields. Extend it and register it with the shared `Base` from `app/database.py`.

```python
# app/users/models.py
from fastapi_users.db import SQLAlchemyBaseUserTableUUID

from app.database import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    Inherits from SQLAlchemyBaseUserTableUUID which provides:
    - id (UUID, primary key)
    - email (str, unique, indexed)
    - hashed_password (str)
    - is_active (bool, default True)
    - is_superuser (bool, default False)
    - is_verified (bool, default False)

    Add custom columns below as needed:
    # first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    """
    pass
```

---

## Step 4 — Create Pydantic Schemas

These schemas handle request/response validation for all user endpoints.

```python
# app/users/schemas.py
import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema for reading user data (returned in API responses)."""
    pass


class UserCreate(schemas.BaseUserCreate):
    """Schema for user registration requests."""
    pass


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for user update requests (all fields optional)."""
    pass
```

To expose custom model fields in responses, add them to `UserRead`. To allow users to set them on registration, add to `UserCreate`.

---

## Step 5 — Create the Database Dependency

This bridges FastAPI Users with the existing async session from `app/database.py`.

```python
# app/users/dependencies.py
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.users.models import User


async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)
```

---

## Step 6 — Create the UserManager

`UserManager` is where all user lifecycle logic lives. Secrets are loaded from `settings` — never hardcoded.

> The `on_after_forgot_password` and `on_after_request_verify` hooks below have `print` placeholders. To send real emails, see the [Email Setup guide](email-setup.md).

```python
# app/users/manager.py
import uuid
from typing import Optional

from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase

from app.config import settings
from app.users.dependencies import get_user_db
from app.users.models import User


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.auth_reset_password_token_secret
    verification_token_secret = settings.auth_verification_token_secret

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")
        # TODO: send welcome email

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ):
        print(f"User {user.id} logged in.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} requested password reset. Token: {token}")
        # TODO: send password reset email with token

    async def on_after_reset_password(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has reset their password.")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Token: {token}")
        # TODO: send verification email with token

    async def on_after_verify(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has been verified.")

    async def on_before_delete(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} is about to be deleted.")

    async def on_after_delete(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has been deleted.")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)
```

---

## Step 7 — Configure Authentication Backend

Create a dedicated `app/auth/` directory for the JWT backend and fastapi-users instance — mirroring the `app/auth/` pattern used for custom auth logic.

```python
# app/auth/backend.py
import uuid

from fastapi_users import FastAPIUsers, models
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy

from app.config import settings
from app.users.manager import get_user_manager
from app.users.models import User

bearer_transport = BearerTransport(tokenUrl="api/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(
        secret=settings.jwt_secret_key,
        lifetime_seconds=settings.jwt_access_token_expire_minutes * 60,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
```

---

## Step 8 — Create `app/auth/router.py` and Wire into `app/api/router.py`

### `app/auth/router.py`

All fastapi-users auth routes live here, keeping `app/api/router.py` clean.

```python
# app/auth/router.py
from fastapi import APIRouter

from app.auth.backend import auth_backend, fastapi_users
from app.users.schemas import UserCreate, UserRead

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
    tags=["Auth"],
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    tags=["Auth"],
)
router.include_router(
    fastapi_users.get_reset_password_router(),
    tags=["Auth"],
)
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    tags=["Auth"],
)
```

### `app/users/router.py`

User management routes (me, by ID, update, delete).

```python
# app/users/router.py
from fastapi import APIRouter

from app.auth.backend import fastapi_users
from app.users.schemas import UserRead, UserUpdate

router = APIRouter()

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    tags=["Users"],
)
```

### `app/api/router.py`

Plug both routers into the central aggregator — same pattern as all other modules.

```python
# app/api/router.py
from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.users.router import router as users_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(users_router, prefix="/users", tags=["Users"])
```

The central router is already wired into `main.py` with the `/api` prefix:

```python
# app/main.py (existing line — no change needed)
app.include_router(api_router, prefix="/api", tags=["API"])
```

### Resulting endpoints

| Method | Path |
|---|---|
| `POST` | `/api/auth/jwt/login` |
| `POST` | `/api/auth/jwt/logout` |
| `POST` | `/api/auth/register` |
| `POST` | `/api/auth/forgot-password` |
| `POST` | `/api/auth/reset-password` |
| `POST` | `/api/auth/request-verify-token` |
| `POST` | `/api/auth/verify` |
| `GET` | `/api/users/me` |
| `PATCH` | `/api/users/me` |
| `GET` | `/api/users/{id}` |
| `PATCH` | `/api/users/{id}` |
| `DELETE` | `/api/users/{id}` |

---

## Step 9 — Register User Model in Alembic

Add the import to `alembic/env.py` so autogenerate detects the `user` table:

```python
# alembic/env.py — add after existing model imports
from app.users import models as users_models  # noqa: F401
```

Then generate and apply the migration:

```bash
alembic revision --autogenerate -m "create users table"
alembic upgrade head
```

---

## Step 10 — Protecting Routes

Import `current_active_user` or `current_superuser` from `app.auth.backend`:

```python
from fastapi import Depends
from app.auth.backend import current_active_user, current_superuser
from app.users.models import User


# Requires a valid JWT — returns 401 if not authenticated
@router.get("/me")
async def get_me(user: User = Depends(current_active_user)):
    return {"id": str(user.id), "email": user.email}


# Requires superuser flag — returns 403 if not superuser
@router.delete("/{item_id}")
async def delete_item(item_id: int, user: User = Depends(current_superuser)):
    ...
```

---

## Project File Structure

```
app/
├── auth/
│   ├── __init__.py
│   ├── backend.py   ← auth_backend, fastapi_users, current_active_user, current_superuser
│   └── router.py    ← login, logout, register, password reset, verify routes
├── users/
│   ├── __init__.py
│   ├── models.py        ← User ORM model (SQLAlchemyBaseUserTableUUID + Base)
│   ├── schemas.py       ← UserRead, UserCreate, UserUpdate
│   ├── dependencies.py  ← get_user_db (bridges get_db → SQLAlchemyUserDatabase)
│   ├── manager.py       ← UserManager + get_user_manager dependency
│   └── router.py        ← /me, /{id} user management routes
└── api/
    └── router.py        ← central aggregator (auth + users + future modules)
```

---

## Summary Checklist

- [ ] Add `fastapi-users[sqlalchemy]` to `requirements.txt` and install
- [ ] Add `AUTH_RESET_PASSWORD_TOKEN_SECRET` and `AUTH_VERIFICATION_TOKEN_SECRET` to `.env`, `.env.example`, and `app/config.py`
- [ ] Create `app/users/models.py` with `User` model
- [ ] Create `app/users/schemas.py` with `UserRead`, `UserCreate`, `UserUpdate`
- [ ] Create `app/users/dependencies.py` with `get_user_db`
- [ ] Create `app/users/manager.py` with `UserManager` and `get_user_manager`
- [ ] Create `app/auth/backend.py` with `auth_backend`, `fastapi_users`, `current_active_user`
- [ ] Create `app/auth/router.py` with all auth routes
- [ ] Create `app/users/router.py` with user management routes
- [ ] Wire both routers into `app/api/router.py`
- [ ] Import `users_models` in `alembic/env.py`
- [ ] Run `alembic revision --autogenerate -m "create users table"` and `alembic upgrade head`
- [ ] Set up email sending — see [Email Setup](email-setup.md)

---

## References

- [fastapi-users — GitHub](https://github.com/fastapi-users/fastapi-users)
- [fastapi-users — Documentation](https://fastapi-users.github.io/fastapi-users/latest/)
- [fastapi-users — Full Example (SQLAlchemy)](https://fastapi-users.github.io/fastapi-users/latest/configuration/full-example/)
- [fastapi-users — SQLAlchemy Database](https://fastapi-users.github.io/fastapi-users/latest/configuration/databases/sqlalchemy/)
- [fastapi-users — UserManager](https://fastapi-users.github.io/fastapi-users/latest/configuration/user-manager/)
- [fastapi-users — Authentication](https://fastapi-users.github.io/fastapi-users/latest/configuration/authentication/)
