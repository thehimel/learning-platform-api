# Password Validation Setup

Enforces a configurable password policy on registration and password reset using the
[`password-strength`](https://pypi.org/project/password-strength/) library, hooked into
fastapi-users via `UserManager.validate_password`.

---

## Why `password-strength`

- Declarative, rule-based policy — easy to read and adjust
- Returns a list of *failed* rules, allowing precise error messages per violation
- Lightweight; no external service or heavy dependency

---

## Installation

```bash
pip install password-strength
```

Already included in `requirements.txt`.

---

## How It Works

fastapi-users calls `UserManager.validate_password(password, user)` automatically on:

- `POST /api/auth/register` — before the user is created
- `POST /api/auth/reset-password` — before the new password is saved

If the method raises `InvalidPasswordException`, fastapi-users returns a `400` response with
the reason string included in the body.

---

## Current Policy

Defined in `app/users/manager.py` via `PasswordPolicy.from_names`:

| Rule         | Requirement                              |
|--------------|------------------------------------------|
| `length`     | Minimum 8 characters                     |
| `uppercase`  | At least 1 uppercase letter              |
| `numbers`    | At least 1 digit                         |
| `special`    | At least 1 special character             |
| `nonletters` | At least 1 non-letter (digit or special) |

An additional check rejects passwords that contain the user's email local-part
(e.g. `john` appearing in `john@example.com`).

Multiple failed rules are joined with `; ` in the response so the client can display them all at once.

### Error response example

```json
{
  "detail": "UPDATE_USER_INVALID_PASSWORD",
  "reason": "Password must be at least 8 characters.; Password must contain at least 1 uppercase letter."
}
```

---

## Adjusting the Policy

To tighten or relax the rules, edit `_password_policy` in `app/users/manager.py`.
All available `PasswordPolicy.from_names` parameters:

| Parameter    | Description                                                    |
|--------------|----------------------------------------------------------------|
| `length`     | Minimum total character count                                  |
| `uppercase`  | Minimum uppercase letters required                             |
| `numbers`    | Minimum digits required                                        |
| `special`    | Minimum special characters required                            |
| `nonletters` | Minimum non-letter characters (digits + special combined)      |
| `strength`   | Minimum entropy score (`0.0`–`1.0`) — catches weak patterns like `Aaaaaaaa1!` that technically pass rule checks but have low entropy |

---

## References

- [`password-strength` on PyPI](https://pypi.org/project/password-strength/)
- [fastapi-users — Password validation](https://fastapi-users.github.io/fastapi-users/latest/configuration/user-manager/#validate_password)
- [`InvalidPasswordException` source](https://github.com/fastapi-users/fastapi-users/blob/master/fastapi_users/exceptions.py)
