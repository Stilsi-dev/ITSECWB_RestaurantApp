# ITSECWB_CS — Restaurant Web App (ITSECWB Project)

A secure **Restaurant Management System** built with **Django** implementing **Role-Based Access Control (RBAC)**, **audit logging**, **session security**, **account lockout**, **re-authentication for critical actions**, and strict **input validation** — compliant with the ITSECWB Machine Project Specifications and Secure Web Development Checklist.

---

## **Roles & Permissions**

### **Administrator**
- Manage all user accounts & roles (Admin, Manager, Customer)
- Create/assign elevated accounts
- View and filter system audit logs (read-only)
- Full system access

### **Manager**
- Manage menu items (CRUD)
- View and update all customer orders
- Change order statuses following allowed transitions

### **Customer**
- Self-register and log in
- Place, view, and cancel own orders (while pending)
- View available menu items

---

## **Setup Instructions**

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

7. **Access the app**
    - **Web:** `http://127.0.0.1:8000`
    - **Django Admin:** `http://127.0.0.1:8000/admin`

---

## **Main URLs**

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
- `/orders/` — list (managers/admins see all; customers see own)
- `/orders/create/`
- `/orders/<id>/edit/`
- `/orders/<id>/delete/`
- `/orders/<id>/status/<to>/` — restricted status transitions

### Logs (Admin-only)
- `/logs/` — filterable, paginated audit trail

---

## **Security Features**

### Authentication
- All non-public routes require login
- Generic login failure messages
- **Account lockout** after 5 failed attempts (15 min cooldown)
- Passwords stored using salted cryptographic hashes
- **Password policy:**
  - Min length (12 chars policy, 8 chars form enforcement — align as needed)
  - Must contain uppercase, lowercase, number, special char
  - Block common/numeric passwords
- **Password history & age:**
  - Cannot reuse last 5 passwords
  - Must be at least 1 day old before change
- Re-authentication required for critical operations
- Secure password reset with hashed security question answers and no user enumeration

### Authorization & Access Control
- Centralized role checks
- Fail-secure responses (403/404 without revealing details)
- Business logic enforced (customers can only manage their own orders and only while pending)

### Input Validation
- Strict form validation (length, range)
- Database-level `CheckConstraint`s
- All invalid inputs rejected and logged

### Error Handling
- Custom error templates (`400.html`, `403.html`, `404.html`, `500.html`, `csrf.html`)
- No debug or stack traces shown to users in production

### Logging
- All key security events logged (auth attempts, access control failures, validation errors, CRUD actions)
- Logs stored in DB and file (`logs/project.log`)
- Admin-only log viewing with filters and pagination

### Session Security
- Idle timeout: 30 minutes
- Session expires on browser close
- Security headers: `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_REFERRER_POLICY=same-origin`, `X_FRAME_OPTIONS=DENY`

---

## **Compliance Mapping (Checklist → Implementation)**

| Checklist Item | Implemented In |
|----------------|----------------|
| Require auth for non-public pages | `@login_required` on views |
| Fail-secure auth & access | `_deny()`, `_fail_secure_forbidden()`, 403/404 handling |
| Salted password hashes | Django’s default hashers |
| Generic login failure | `accounts/views.py:login_view` |
| Password complexity & length | `accounts/validators.py` + settings |
| Account lockout | `accounts/auth_backends.py` + `signals.py` |
| Password re-use blocked | `PasswordHistory` + validators |
| Min password age | Validators & settings |
| Re-auth before critical ops | `/reauth/` + decorator |
| Access control checks | Centralized role checks in views |
| Enforce business rules | Order/customer ownership checks |
| Data validation | Forms + model constraints |
| No debug in errors | Custom error templates |
| Logging successes & failures | `logs/utils.py:audit_log` |
| Restrict log access | `/logs/` admin-only |

---

## **Production Recommendations**
Before deploying:
- Set `DEBUG = False`
- Replace `SECRET_KEY` with a strong value from environment variables
- Set `ALLOWED_HOSTS`
- Create `logs/` dir with correct permissions
- Consider enabling:
  - `SECURE_SSL_REDIRECT = True`
  - `CSRF_COOKIE_SECURE = True`
  - `SESSION_COOKIE_SECURE = True`
  - `SECURE_HSTS_SECONDS` and related settings

---
