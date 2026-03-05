# Email Setup with fastapi-mail

Used for sending transactional emails such as email verification and password reset links — triggered via `UserManager` hooks from fastapi-users.

---

## Step 1 — Install

Add to `requirements.txt`:

```
fastapi-mail
jinja2
```

Install:

```bash
pip install fastapi-mail jinja2
```

> `jinja2` is needed for HTML email templates. `fastapi[all]` may already include it — check before adding.

---

## Step 2 — Add Email Settings to `app/config.py`

```python
# app/config.py — add inside the Settings class

# Email
mail_username: str
mail_password: str
mail_from: str
mail_from_name: str = "Learning Platform"
mail_server: str
mail_port: int = 587
mail_starttls: bool = True
mail_ssl_tls: bool = False
```

---

## Step 3 — Add to `.env` and `.env.example`

```bash
# Email (SMTP)
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=your-smtp-password
MAIL_FROM=your@email.com
MAIL_FROM_NAME=Learning Platform
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
```

### Common SMTP providers

| Provider | `MAIL_SERVER` | `MAIL_PORT` | Notes |
|---|---|---|---|
| Gmail | `smtp.gmail.com` | `587` | Use an [App Password](https://myaccount.google.com/apppasswords), not your account password |
| Outlook / Hotmail | `smtp.office365.com` | `587` | |
| SendGrid | `smtp.sendgrid.net` | `587` | `MAIL_USERNAME` is always `apikey` |
| AWS SES | `email-smtp.<region>.amazonaws.com` | `587` | Use SMTP credentials from AWS console |
| Mailgun | `smtp.mailgun.org` | `587` | |

---

## Step 4 — Create `app/email/config.py`

Centralise the `ConnectionConfig` so it's built once and reused everywhere.

```python
# app/email/config.py
from pathlib import Path

from fastapi_mail import ConnectionConfig

from app.config import settings

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=settings.mail_starttls,
    MAIL_SSL_TLS=settings.mail_ssl_tls,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)
```

---

## Step 5 — Create Email Templates

Templates are Jinja2 HTML files placed in `app/email/templates/`.

### `app/email/templates/verification.html`

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
  <h2>Verify your email</h2>
  <p>Hi, thanks for signing up. Click the link below to verify your email address:</p>
  <p><a href="{{ verification_url }}">Verify Email</a></p>
  <p>This link expires in 1 hour.</p>
  <p>If you did not create an account, you can safely ignore this email.</p>
</body>
</html>
```

### `app/email/templates/reset_password.html`

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
  <h2>Reset your password</h2>
  <p>Click the link below to reset your password:</p>
  <p><a href="{{ reset_url }}">Reset Password</a></p>
  <p>This link expires in 1 hour.</p>
  <p>If you did not request a password reset, you can safely ignore this email.</p>
</body>
</html>
```

---

## Step 6 — Create `app/email/service.py`

```python
# app/email/service.py
from fastapi_mail import FastMail, MessageSchema, MessageType

from app.email.config import mail_config

fm = FastMail(mail_config)


async def send_verification_email(email: str, token: str, base_url: str) -> None:
    verification_url = f"{base_url}/api/auth/verify?token={token}"
    message = MessageSchema(
        subject="Verify your email address",
        recipients=[email],
        template_body={"verification_url": verification_url},
        subtype=MessageType.html,
    )
    await fm.send_message(message, template_name="verification.html")


async def send_reset_password_email(email: str, token: str, base_url: str) -> None:
    reset_url = f"{base_url}/reset-password?token={token}"
    message = MessageSchema(
        subject="Reset your password",
        recipients=[email],
        template_body={"reset_url": reset_url},
        subtype=MessageType.html,
    )
    await fm.send_message(message, template_name="reset_password.html")
```

---

## Step 7 — Add `APP_BASE_URL` to Settings

The email links need to know the frontend URL (not the API URL).

```python
# app/config.py — add inside the Settings class
app_base_url: str = "http://localhost:3000"
```

```bash
# .env and .env.example
APP_BASE_URL=http://localhost:3000  # dev
# APP_BASE_URL=https://yourdomain.com  # production
```

---

## Step 8 — Wire into `UserManager`

Update `app/users/manager.py` to call the email service from the relevant hooks:

```python
# app/users/manager.py — updated hooks
from app.config import settings
from app.email.service import send_reset_password_email, send_verification_email


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    # ...

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        await send_reset_password_email(
            email=user.email,
            token=token,
            base_url=settings.app_base_url,
        )

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        await send_verification_email(
            email=user.email,
            token=token,
            base_url=settings.app_base_url,
        )
```

---

## Step 9 — Suppress Emails in Tests

Set `SUPPRESS_SEND=1` in `ConnectionConfig` during testing to prevent real emails from being sent:

```python
# In test setup
from app.email.config import fm

fm.config.SUPPRESS_SEND = 1

with fm.record_messages() as outbox:
    # trigger the action that sends an email
    assert len(outbox) == 1
    assert outbox[0]["To"] == "user@example.com"
```

---

## Project File Structure

```
app/
└── email/
    ├── __init__.py
    ├── config.py          ← ConnectionConfig (built from settings)
    ├── service.py         ← send_verification_email, send_reset_password_email
    └── templates/
        ├── verification.html
        └── reset_password.html
```

---

## Summary Checklist

- [ ] Add `fastapi-mail` and `jinja2` to `requirements.txt` and install
- [ ] Add email settings to `app/config.py` and `Settings`
- [ ] Add `MAIL_*` and `APP_BASE_URL` vars to `.env` and `.env.example`
- [ ] Create `app/email/config.py` with `ConnectionConfig`
- [ ] Create `app/email/templates/verification.html`
- [ ] Create `app/email/templates/reset_password.html`
- [ ] Create `app/email/service.py` with sending functions
- [ ] Update `on_after_forgot_password` and `on_after_request_verify` in `UserManager`
- [ ] Set `SUPPRESS_SEND=1` in test config to avoid sending real emails during tests

---

## References

- [fastapi-mail — GitHub](https://github.com/sabuhish/fastapi-mail)
- [fastapi-mail — Documentation](https://sabuhish.github.io/fastapi-mail/)
- [fastapi-mail — Getting Started](https://sabuhish.github.io/fastapi-mail/getting-started/)
- [fastapi-mail — Examples](https://sabuhish.github.io/fastapi-mail/example/)
- [Gmail App Passwords](https://myaccount.google.com/apppasswords)
- [Jinja2 — Documentation](https://jinja.palletsprojects.com/)
