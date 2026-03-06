# Coding Conventions

Project-wide conventions.

## Module Layout

Each domain module (e.g. `users`, `courses`) follows the same structure:

- `router.py` — HTTP handlers, dependency wiring
- `schemas.py` — Pydantic request/response models
- `models.py` — SQLAlchemy ORM models
- `service.py` — Business logic
- `exceptions.py` — Domain-specific exceptions (when needed)
- `tests/` — Tests for the module (colocated with the code)

## Schema Naming

- `[Resource]Create` — Request body for creation
- `[Resource]Read` — Response model
- `[Resource][SubResource]Read` — Nested response

Align naming across modules (e.g. `UserRead`, `CourseRead`).

## REST

- `POST` for create returns `201 Created`
- Set `Location` header on create: `{base_path}/{resource_id}` (derive from `request.url.path`, no hardcoded paths)
- Use `response_model` on all endpoints
- Collection create path: `"/"` (not `""`)

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

## Code Formatting

- Blank lines between logical groups (validation → create → assign → return)
- Separate fetch, processing, validation, and return blocks with blank lines
- Use blank lines only; no comments purely for visual separation
- Full words for variables and identifiers (e.g. `customer`, `order_id`), not abbreviations (`c`, `o`, `n`)

## Testing

- Domain tests live in `app/<domain>/tests/` (e.g. `app/courses/tests/`)
- Shared fixtures in project root `conftest.py`
