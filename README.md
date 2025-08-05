# ITSECWB_CS# Restaurant Web App (ITSECWB Project)

This project is a secure web-based **Restaurant Management System** built with **Django**.  
It implements **role-based access control, audit logging, session security, and input validation**.

---

## **User Roles**

### 1. **Administrator**
- Can manage user accounts (Admin and Manager roles)
- Can view system logs
- Has full system access

### 2. **Manager**
- Can manage menu items (CRUD operations)
- Can view and monitor all customer orders

### 3. **Customer**
- Can place, view, and cancel their own orders
- Can view the available menu items

---

## **Project Setup**

1. **Clone the repository**
    ```bash
    git clone <your-repository-url>
    cd ITSECWB_CS
    ```

2. **Create a virtual environment (recommended)**

    ```bash
    python -m venv venv
    source venv/bin/activate   # For Mac/Linux
    venv\Scripts\activate      # For Windows
    ```

3. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4. **Run initial migrations**

    ```bash
    python manage.py migrate
    ```

5. **Create a superuser (Administrator)**
    ``` bash
    python manage.py createsuperuser
    ```

6. **Start the development server**

    ``` bash
    python manage.py runserver
    ```

7. **Access the application**

- **Web App:** `http://127.0.0.1:8000`  
- **Django Admin (advanced):** `http://127.0.0.1:8000/admin`

---

## Security Features

- **Role-Based Access Control (RBAC):** Users are assigned roles (Admin, Manager, Customer) with different permissions.  
- **Input Validation:** Forms validate user input to avoid invalid data submission.  
- **Audit Logging:** All user actions (login, CRUD operations, order placements, etc.) are stored in the system logs.  
- **Session Management:** Inactive sessions expire after 30 minutes.  
- **Password Security:** Uses Django's password hashing and strong password validators.  

---

## Default Pages

- **Login/Register:** `/login/` and `/register/`  
- **Dashboards:**
  - Administrator: `/dashboard/`
  - Manager: `/dashboard/`
  - Customer: `/dashboard/`
- **Menu Management:** `/menu/`
- **Orders:** `/orders/`
- **System Logs:** `/logs/` (Admins only)
