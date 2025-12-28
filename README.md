# ITSECWB_CS — Restaurant Web App (ITSECWB Project)

A secure **Restaurant Management System** built with **Django**. The app implements **Role-Based Access Control (RBAC)**, **audit logging**, **session security**, **account lockout**, **last login/attempt reporting**, **re-authentication for critical actions**, and strict **input validation** — aligned with the ITSECWB Machine Project Specifications and Secure Web Development Checklist.

---

## Sample test accounts

> ⚠️ Security notice: these accounts are for **testing/demo purposes only**.
> If you publish this repository, do not include real credentials or a real database.
> Do **NOT** use them in production — change or remove them before deployment.

**Manager**
- **Username:** `manager1`  
- **Password:** `M@nager!2024`

**Customer**
- **Username:** `customer1`  
- **Password:** `Cust0mer!2024`

**Administrator**
- **Username:** `admin`  
- **Password:** `admin1234!`

---

## Roles & permissions

### Administrator
- Manage all user accounts & roles (Admin, Manager, Customer)
- Create and assign elevated accounts
- View and filter system audit logs (read-only)
- Full system access

### Manager
- Manage menu items (CRUD)
- View and update all customer orders
- Change order statuses following allowed transitions

### Customer
- Self-register and log in
- Place, view, and cancel their own orders (while pending)
- View available menu items

---

## Setup instructions

Prerequisites:

- Python 3.10+ recommended
- pip

1. **Clone the repository**
    ```bash
    git clone <your-repository-url>
    cd ITSECWB_CS
    ```

2. **Create & activate a virtual environment**
    ```bash
    python -m venv venv
    # Mac/Linux
    source venv/bin/activate
    # Windows
    venv\Scripts\activate
    ```

3. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

  If you see an error about `django_extensions`, it means the dependency is missing from `requirements.txt`.

4. **Run migrations**
    ```bash
    python manage.py migrate
    ```

5. **Create a superuser (Administrator)**
    ```bash
    python manage.py createsuperuser
    ```

6. **Start the development server**
    ```bash
    python manage.py runserver
    ```

7. **Access the application**
    - **Web:** `http://127.0.0.1:8000`
    - **Django Admin:** `http://127.0.0.1:8000/admin`

Optional (start from a clean database):

```bash
# WARNING: deletes local dev database
rm -f db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

---

## Main URLs

### Accounts
- `/login/`, `/logout/`, `/register/`
- `/dashboard/` — role-aware dashboards
- `/manage-users/` — admin-only role management
- `/setup-security-question/`
- `/reauth/` — re-authentication for sensitive actions
- `/change-password/`
- `/reset/` → `/reset/question/` → `/reset/new/` — secure password reset flow

### Menu (Manager/Admin)
- `/menu/` — list
- `/menu/new/` — create
- `/menu/<id>/edit/` — update
- `/menu/<id>/delete/` — delete

### Orders
- `/orders/` — list (managers/admins see all; customers see only their own)
- `/orders/create/`
- `/orders/<id>/edit/`
- `/orders/<id>/delete/`
- `/orders/<id>/status/<to>/` — restricted status transitions

### Logs (Admin-only)
- `/logs/` — filterable, paginated audit trail

---

## Security features

### Authentication
- All non-public routes require login  
- Generic login failure messages (no credential enumeration)  
- **Account lockout** after 5 failed attempts (15 min cooldown)  
- **Last login & last failed attempt reporting** on successful login  
- Passwords stored using salted cryptographic hashes  
- **Password policy:**
  - Minimum length: **8 characters**
  - Must contain at least one uppercase letter, one lowercase letter, one number, and one special character
  - Block common/numeric passwords  
- **Password history & age:**
  - Cannot reuse last **5 passwords**
  - Must be at least **1 day** old before change  
- **Re-authentication** required for critical operations  
- **Secure password reset** with:
  - Hashed security question answers
  - No user enumeration

### Authorization & Access Control
- Centralized role checks
- Fail-secure responses (403/404 without revealing details)
- Business logic enforced (customers can only manage their own orders and only while pending)

### Input Validation
- Strict form validation (length, range, type)
- Database-level `CheckConstraint`s
- All invalid inputs rejected and logged

### Error Handling
- Custom error templates (`400.html`, `403.html`, `404.html`, `500.html`, `csrf.html`)
- No debug or stack traces shown to users in production

### Logging & Auditing
- Logs both **successes and failures**
- Captures:
  - Action description
  - User (if authenticated)
  - Timestamp
  - IP address
  - User-Agent
- Admin-only log viewing with filters and pagination

### Session Security
- Idle timeout: **30 minutes**
- Session expires on browser close
- Secure headers:
  - `SECURE_CONTENT_TYPE_NOSNIFF`
  - `SECURE_REFERRER_POLICY = "same-origin"`
  - `X_FRAME_OPTIONS = "DENY"`

---

## Compliance mapping (Checklist → Implementation)

| Checklist Item | Status | Implemented In |
|----------------|--------|----------------|
| Require auth for non-public pages | ✅ | `@login_required` decorators |
| Fail-secure auth & access | ✅ | `_fail_secure_forbidden()` + error views |
| Salted password hashes | ✅ | Django’s default hashers |
| Generic login failure | ✅ | `login_view` |
| Password complexity & length (8 chars min) | ✅ | `accounts/validators.py` + settings |
| Account lockout | ✅ | `accounts/auth_backends.py` + `signals.py` |
| Password re-use blocked | ✅ | `PasswordHistory` + validators |
| Min password age | ✅ | Validators & settings |
| Re-auth before critical ops | ✅ | `/reauth/` + `require_recent_reauth` decorator |
| Last use reporting | ✅ | `accounts/signals.py` & login message |
| Access control checks | ✅ | Role checks in views |
| Enforce business rules | ✅ | Orders/Menu CRUD restrictions |
| Data validation | ✅ | Forms + model constraints |
| Password fields masked | ✅ | `<input type="password">` in templates |
| Security question randomness & hashing | ✅ | `setup_security_question_view` + `_hash_answer` |
| No debug in errors | ✅ | Custom error templates |
| Logging successes & failures | ✅ | `logs/utils.py:audit_log` |
| Restrict log access | ✅ | `/logs/` admin-only role check |

---

## Production recommendations

Before deployment:
- Set `DEBUG = False`
- Use a strong `SECRET_KEY` from environment variables
- Set `ALLOWED_HOSTS`
- Ensure `logs/` directory exists with proper permissions
- Enable:
  - `SECURE_SSL_REDIRECT = True`
  - `CSRF_COOKIE_SECURE = True`
  - `SESSION_COOKIE_SECURE = True`
  - `SECURE_HSTS_SECONDS` and related headers

---

## License

MIT
