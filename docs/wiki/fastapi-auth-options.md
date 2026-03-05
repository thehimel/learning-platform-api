# FastAPI Authentication Options

Notes from evaluating auth libraries for this project. Django equivalent for context: Django Allauth.

## Options Considered

- [fastapi-users](https://github.com/fastapi-users/fastapi-users): Closest to Django Allauth. Handles registration, login, password reset, and email verification. JWT built in, OAuth2 via built-in integrations (Google, Facebook, GitHub, etc.), async-native with async SQLAlchemy. Actively maintained. This is what the project uses.
- [Authlib](https://github.com/lepture/authlib): Best for SSO/OAuth. The go-to library for OAuth 1.0, OAuth 2.0, and OpenID Connect. Works with FastAPI via an `httpx` integration. Use it when fine-grained control over OAuth flows is needed.
- python-jose / [PyJWT](https://pyjwt.readthedocs.io/en/stable/): For pure JWT without a full auth stack. Already in use here via `python-jose[cryptography]`.

## Recommended Combination

`fastapi-users[sqlalchemy]` handles auth, JWT, and OAuth2. Add `authlib` (with `httpx`) only if enterprise SSO or OpenID Connect is needed later.

## fastapi-users vs Django Allauth

- Social account adapters map to fastapi-users' OAuth2 clients.
- `allauth.account` maps to fastapi-users' core.
- Session-based auth becomes JWT (stateless) or cookie-based.
- There is no built-in admin UI, since FastAPI is API-first; the frontend handles that separately.

## References

- [fastapi-users: GitHub](https://github.com/fastapi-users/fastapi-users)
- [fastapi-users: Documentation](https://fastapi-users.github.io/fastapi-users/latest/)
- [Authlib: GitHub](https://github.com/lepture/authlib)
- [Authlib: Documentation](https://docs.authlib.org/en/latest/)
- [PyJWT: Documentation](https://pyjwt.readthedocs.io/en/stable/)
- [Django Allauth: Documentation](https://docs.allauth.org/en/latest/)
