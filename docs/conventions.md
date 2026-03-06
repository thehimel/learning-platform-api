# Coding Conventions

Project-wide conventions.

## Module Layout

Each domain module (e.g. `users`, `courses`) follows the same structure:

- `router.py` — HTTP handlers, dependency wiring
- `schemas.py` — Pydantic request/response models
- `models.py` — SQLAlchemy ORM models
- `service.py` — Business logic (or `manager.py` when using fastapi-users)
- `exceptions.py` — Domain-specific exceptions (when needed)
- `tests/` — Tests for the module (colocated with the code)

When using third-party integrations (e.g. fastapi-users), structure may differ: `users` has `manager.py` instead of `service.py`; `auth` has no `schemas.py` or `models.py` (uses users').

## Schema Naming

- `[Resource]Create` — Request body for creation
- `[Resource]Read` — Response model
- `[Resource][SubResource]Read` — Nested response

Align naming across modules (e.g. `UserRead`, `CourseRead`).

## REST

- `POST` for create returns `201 Created`
- `DELETE` for removal returns `204 No Content` when there is no response body
- Use `response_model` on all endpoints
- Collection create path: `"/"` (not `""`)

### Resource Creation

- Return `201 Created` with the **full created resource** in the response body (not `204 No Content`)
- Do not set `Location` header — avoids maintenance burden when resource paths or authorization change
- Define a `[Resource]Read` schema for the created resource (e.g. `EnrollmentRead`, `CourseRead`)
- Service returns the ORM object; FastAPI serializes via `response_model`
- Example: `POST /courses/{id}/enroll` → `201` with `{"id": 42, "course_id": 5, "user_id": "...", "enrolled_at": "..."}`

### Resource Deletion

- Use `DELETE` for removal (e.g. unenroll, remove membership)
- Return `204 No Content` when there is no response body

## Authentication

- `Depends(current_instructor)` for instructor-protected routes
- `Depends(current_active_user)` for authenticated user routes
- `Depends(current_admin)` for admin-only routes

## Database

- `Depends(get_db)` for session injection
- Async SQLAlchemy (`AsyncSession`)

## Error Handling

- Domain exceptions live in `app/<domain>/exceptions.py` (or `app/exceptions.py` for shared)
- Router catches domain exceptions and maps to `HTTPException`
- Structured error responses: use `error_detail(DomainErrorCode.member, "message", **extra)` — error code enums live in each domain (e.g. `app/courses/error_codes.py`), `error_detail` from `app.exceptions`

## Import Order

1. Standard library
2. Third-party
3. Local (`app.*`)

## API Documentation

- `tags=["ResourceName"]` when including routers (e.g. `tags=["Courses"]`)

## Business Logic

- Keep business logic in the `service` layer
- Router handles HTTP concerns only: validation, auth, response shaping, error mapping

## Response Serialization

- Services return ORM objects; do not manually build Pydantic response models in the service layer
- Use `response_model` on endpoints — FastAPI serializes the returned ORM through the schema
- For simple 1:1 mappings, use `model_config = ConfigDict(from_attributes=True)` on the Read schema
- For nested or derived fields (e.g. `enrolled_count`, sorted `instructors`), add a `model_validator(mode="before")` that accepts the ORM and returns a dict for the schema
- Router return type hints should match what the service returns (e.g. `-> list[Course]`, `-> Course`), not the response schema

## Code Formatting

- Blank lines between logical groups (validation → create → assign → return)
- Separate fetch, processing, validation, and return blocks with blank lines
- Use blank lines only; no comments purely for visual separation
- Full words for variables and identifiers (e.g. `customer`, `order_id`), not abbreviations (`c`, `o`, `n`)

## Testing

- Domain tests live in `app/<domain>/tests/` (e.g. `app/courses/tests/`)
- Shared fixtures in project root `conftest.py`
- Use the `routes` fixture from `conftest` — it provides paths via `app.url_path_for(RouteName.*)` so tests stay in sync with the app (e.g. `routes.users_me`, `routes.users_by_id(user_id)`, `routes.courses_create`, `routes.auth_login`) — never hardcode URLs
- Route names live in each domain’s `routes.py` (e.g. `app.auth.routes.RouteName`, `app.users.routes.RouteName`, `app.courses.routes.RouteName`) — routers and tests use these enums
