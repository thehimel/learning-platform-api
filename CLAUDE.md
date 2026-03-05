# Core

## Module and Service Architecture

- Each service is bundled into its own module with a centralized constants file for all magic strings, numbers, and configuration values.
- Import constants from the module; never hardcode literals anywhere in the codebase.
- Exception: a route path can stay inline where that route itself is declared.
- Tunable values (limits, timeouts, titles, versions, default env values, user-facing messages) stay constants even when used once.
- A module that participates in API versioning owns its version as its own constant, so bumping one module's version never touches or affects another module's.
- Group related constants together in a file, separated by a blank line between groups; no comments labeling the groups.
- Modules must be self-contained and reusable across the application.

## Module Structure

- Constants: magic strings, tokens, config values.
- Router: routes, delegates to service.
- Service: business logic, depends on the repository class, throws domain errors, never HTTP exceptions.
- Repository: owns DB queries via the injected session, returns domain objects, maps DB failures to domain errors.
- Errors: module-owned domain classes extending `DomainError`, defined where thrown.
- Dependencies: wires router, service, and repository via FastAPI's `Depends`.
- Schema: SQLAlchemy models plus Pydantic schemas, the validation layer.

The chain becomes Router → Service → Repository → DB. Transactions are opened by the service, and errors are mapped to HTTP by one generic filter at the edge.

Not every module needs every piece. Some parts of this layering only show up once a module has a use case for them.

## Code Modularity and Reusability

- Functions do one job each; split functions handling multiple concerns.
- Extract common logic into reusable functions to avoid duplication.
- Keep centralization at its core throughout the project, with maximum code reusability and zero redundancy.

## Formatting

- Max line length is 120 characters, code and comments alike.
- A pre-commit hook runs automatically before each commit.

## Writing Style

- Docs: no em dash, headers in title case, no unnecessary line wraps.
- Code comments: no em dash, stay concise, only add one when it is not obvious from the code.
- Comments never name files, classes, or functions, or say where something is used. Describe the behavior itself; the IDE resolves references.
- Delete a comment rather than keep a shortened version of it when it only restates what the code already shows.
- Docstrings follow Google style. Only add Args, Returns, or Raises sections when a docstring needs them, not by default.

## Diagrams

- Draw diagrams with the Excalidraw connector and save the `.excalidraw` source in `docs/assets/excalidraw/`, always matching the rendered diagram.
- Put every piece of text in a box, including titles, footers, and arrow labels, so the diagram works in light and dark mode without a background.
- Use one text color throughout, and style boxes consistently by component role.
- Leave enough gap between boxes, zone borders, and arrow labels.
