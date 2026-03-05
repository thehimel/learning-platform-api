# Role-Based Access Control (RBAC) Setup

RBAC is implemented using a `UserRole` enum on the `User` model and a `require_role` dependency factory in `app/auth/backend.py`. No third-party library is needed.

---

## Roles

Defined as a `str` enum so values are stored as readable strings in the database.

| Role | Description |
|---|---|
| `student` | Default role on registration. Can access learning content. |
| `instructor` | Can create and manage courses. |
| `admin` | Full platform access. Can manage all users and content. |

```python
# app/users/models.py
class UserRole(str, enum.Enum):
    student = "student"
    instructor = "instructor"
    admin = "admin"
```

Roles are **hierarchical** — a higher role always includes the permissions of lower roles:

```
admin ⊇ instructor ⊇ student
```

---

## User Model

The `role` column is added to the `User` model with `student` as the server-side default so every new registration starts as a student automatically.

```python
# app/users/models.py
role: Mapped[UserRole] = mapped_column(
    SAEnum(UserRole, name="userrole"),
    default=UserRole.student,
    server_default=UserRole.student.value,
    nullable=False,
)
```

---

## Dependency Factory

`require_role` in `app/auth/backend.py` is a factory that returns an async FastAPI dependency. It first verifies the JWT (via `current_active_user`), then checks the role.

```python
# app/auth/backend.py
def require_role(*roles: UserRole):
    """Factory that returns a dependency enforcing one of the given roles."""
    async def checker(user: User = Depends(current_active_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return user
    return checker
```

---

## Ready-to-Use Dependencies

Three pre-built dependencies cover all common access levels. Import directly into route handlers.

```python
# app/auth/backend.py
current_student    = require_role(UserRole.student, UserRole.instructor, UserRole.admin)
current_instructor = require_role(UserRole.instructor, UserRole.admin)
current_admin      = require_role(UserRole.admin)
```

| Dependency | Who can access |
|---|---|
| `current_active_user` | Any authenticated user (no role check) |
| `current_student` | student, instructor, admin |
| `current_instructor` | instructor, admin |
| `current_admin` | admin only |

---

## Usage in Route Handlers

### Per-route dependency

```python
from fastapi import Depends
from app.auth.backend import current_student, current_instructor, current_admin
from app.users.models import User


# Any authenticated user
@router.get("/profile")
async def get_profile(user: User = Depends(current_active_user)):
    ...

# Students and above
@router.get("/courses/{id}/content")
async def get_course_content(user: User = Depends(current_student)):
    ...

# Instructors and above
@router.post("/courses")
async def create_course(user: User = Depends(current_instructor)):
    ...

# Admins only
@router.delete("/courses/{id}")
async def delete_course(user: User = Depends(current_admin)):
    ...
```

### Router-level dependency (applies to all routes in a group)

```python
from fastapi import APIRouter, Depends
from app.auth.backend import current_admin

admin_router = APIRouter(dependencies=[Depends(current_admin)])

@admin_router.get("/{id}")
async def get_user(...):
    ...

@admin_router.patch("/{id}")
async def update_user(...):
    ...
```

---

## HTTP Responses

| Situation | Status code |
|---|---|
| No token / invalid token | `401 Unauthorized` |
| Valid token but insufficient role | `403 Forbidden` |
| Admin attempting to delete own account | `403 Forbidden` |
| Valid token and correct role | `200 OK` (or appropriate 2xx) |

---

## `is_superuser` and `role` — No Separate Column

fastapi-users ships with an `is_superuser` flag on the user table. In this project that column has been **dropped** to eliminate the possibility of it going out of sync with `role`.

Instead, `is_superuser` is defined as a SQLAlchemy `hybrid_property` on the `User` model:

- **Instance access** — returns `True` when `role == admin`, `False` otherwise.
- **SQL expression** — translates to `role = 'admin'` in DB queries, so any fastapi-users internal query that filters by `is_superuser` still works correctly.
- **Setter** — intentionally a no-op. If any code path calls `setattr(user, "is_superuser", value)` (e.g. fastapi-users internals during an update), the value is silently discarded.

This means `is_superuser` never needs to be managed manually. Promoting a user to `admin` via `PATCH /api/users/{id}` is the only action needed — `is_superuser` follows automatically.

`is_superuser` is also hidden from the `PATCH /api/users/{id}` request schema in Swagger UI via `_make_schema_cleaner` in `app/users/schemas.py`.

---

## Changing a User's Role

Role changes are not exposed via the self-update endpoint (`PATCH /api/users/me`). Only admins can change roles via `PATCH /api/users/{id}`:

```json
PATCH /api/users/{id}
Authorization: Bearer <admin-token>

{ "role": "instructor" }
```

---

## Summary Checklist

- [ ] `UserRole` enum defined in `app/users/models.py`
- [ ] `role` column added to `User` model with `server_default=UserRole.student.value`
- [ ] `require_role` factory defined in `app/auth/backend.py`
- [ ] `current_student`, `current_instructor`, `current_admin` exported from `app/auth/backend.py`
- [ ] Use `Depends(current_*)` on individual routes or `dependencies=[Depends(current_*)]` on routers
- [ ] Role changes restricted to `PATCH /api/users/{id}` (admin only)
- [ ] `is_superuser` column dropped — replaced by `hybrid_property` derived from `role`
- [ ] `is_superuser` hidden from `UserAdminUpdate` OpenAPI schema via `_make_schema_cleaner`
