# 🍽️ Streamlit Restaurant Management System

A lightweight Restaurant Point of Sale (POS) and Management System built with Python, Streamlit, and MySQL.

It provides a responsive interface for staff to process orders and monitor statuses, while admins can manage menu items, view analytics, and control user permissions.

---

## ✨ Features

- 🔐 Role-Based Access Control (RBAC): Admin and Staff dashboards with different privileges.
- 🛒 Interactive POS System: menu browsing, category/price filters, name search, and cart management.
- 📋 Order Tracking: pending, preparing, served, and completed order states.
- 🛠️ Admin Menu Management: add categories, upload item images, update prices, set Out of Stock.
- 📈 Business Dashboard: revenue, top-sellers, and order status distribution charts.
- 👥 User Management: create staff/admin accounts with secure password hashing.

---

## 🚀 Prerequisites

- Python 3.8+
- MySQL Server (local install via XAMPP/WAMP/MAMP, or native MySQL)
- Git (optional)

---

## 🛠️ Local Setup

### 1) Database setup

1. Create database: `restaurant_management`.
2. Import SQL schema + test data from `restaurant_management.sql`.
3. Update DB settings in `app.py` (`DB_CONFIG`) to match your credentials:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",       # MySQL username
    "password": "",       # MySQL password
    "database": "restaurant_management"
}
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Run the app

```bash
streamlit run app.py
```

---

## 🔑 Default test accounts

- Admin: `admin_super`
- Password: `5e884898da28047151d0e56f8dc62927`

- Staff: `staff_sarah`
- Password: `a1d0c6e83f027327d8461063f4ac58a6`

- Customer: `emily_r`
- Password: `8d969eef6ecad3c29a3a629280e686cf`

---

## 🧩 Notes

- Ensure MySQL connection credentials are correct in `app.py`.
- If you have streamlit port conflict, use `streamlit run app.py --server.port 8502`.
- If you need to regenerate the database, drop the `restaurant_management` DB and re-import the `.sql` file.
