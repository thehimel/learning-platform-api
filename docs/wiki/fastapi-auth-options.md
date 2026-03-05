# FastAPI Authentication Options

> Django equivalent: **Django Allauth**

---

## Most Popular Options

### 1. FastAPI Users — closest to Django Allauth

- GitHub: [fastapi-users/fastapi-users](https://github.com/fastapi-users/fastapi-users)
- Handles: registration, login, password reset, email verification
- JWT support built-in
- OAuth2 support via built-in integrations (Google, Facebook, GitHub, etc.)
- Async-native — works with async SQLAlchemy
- Actively maintained, ~4.5k stars

### 2. Authlib — best for SSO/OAuth

- GitHub: [lepture/authlib](https://github.com/lepture/authlib)
- The go-to library for OAuth 1.0, OAuth 2.0, and OpenID Connect (SSO)
- Works with FastAPI via `httpx` integration
- Use when fine-grained control over OAuth flows is needed

### 3. python-jose / PyJWT — JWT only

- For pure JWT without the full auth stack
- Already in use via `python-jose[cryptography]`

---

## Recommended Combination

```
fastapi-users[sqlalchemy]   ← handles auth, JWT, OAuth2 (Google, GitHub, etc.)
authlib                     ← for enterprise SSO / OpenID Connect if needed
httpx                       ← required by authlib for async HTTP
```

### FastAPI Users feature support

| Feature | Support |
|---|---|
| JWT | ✅ built-in |
| OAuth2 (Google, GitHub, Facebook) | ✅ built-in |
| OpenID Connect / SSO | ✅ via Authlib |
| Async SQLAlchemy | ✅ native |
| Password hashing (bcrypt) | ✅ built-in |
| Email verification | ✅ built-in |

---

## Compared to Django Allauth

| Django Allauth | FastAPI equivalent |
|---|---|
| Social account adapters | FastAPI Users OAuth2 clients |
| `allauth.account` | FastAPI Users core |
| Session-based auth | JWT (stateless) or cookie-based |
| Admin UI | No built-in UI (API only) |

> Key difference: FastAPI is API-first — there is no built-in UI like Allauth provides. The frontend handles that separately.

---

## References

- [fastapi-users — GitHub](https://github.com/fastapi-users/fastapi-users)
- [fastapi-users — Documentation](https://fastapi-users.github.io/fastapi-users/latest/)
- [Authlib — GitHub](https://github.com/lepture/authlib)
- [Authlib — Documentation](https://docs.authlib.org/en/latest/)
- [python-jose — GitHub](https://github.com/mpdavis/python-jose)
- [PyJWT — Documentation](https://pyjwt.readthedocs.io/en/stable/)
- [Django Allauth — Documentation](https://docs.allauth.org/en/latest/)
