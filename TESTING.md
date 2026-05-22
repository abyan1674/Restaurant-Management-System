# Testing Guide

This project includes three layers of automated testing, designed and implemented with AI assistance (Claude).

## Architecture Overview

The monolithic `app.py` was refactored to separate concerns:

| File | Role |
|------|------|
| `db.py` | Database layer — `DB_CONFIG`, `create_connection()`, `run_query()` |
| `logic.py` | Pure business logic — `hash_password()`, `calculate_cart_total()`, `get_loyalty_tier()`, `calculate_order_total()` |
| `app.py` | Streamlit UI — imports from `db.py` and `logic.py` |

This separation is what makes each test phase independently runnable.

---

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# .\venv\Scripts\activate       # Windows

# 2. Install all dependencies (equivalent to npm install)
pip install -r requirements.txt

# 3. Install Playwright browsers (one-time)
playwright install
```

---

## Unit Testing — `pytest`

**Target:** Pure business logic functions in `logic.py`.  
**AI Contribution:** AI analyzed functional requirements and generated test cases covering boundary values and edge cases (empty inputs, exact tier boundaries) that humans might overlook.  
**No database or running server required.**

```bash
pytest tests/test_logic.py -v
```

Covered functions and cases:

| Function | Edge Cases Tested |
|----------|-------------------|
| `hash_password()` | Known MD5 value, empty string |
| `calculate_cart_total()` | Empty cart, single item, multiple items |
| `get_loyalty_tier()` | Bronze / Silver / Gold boundaries (exact values 50, 149.99, 150) |
| `calculate_order_total()` | Empty list, single line, multiple lines |

---

## Integration Testing — `pytest` + `pytest-mock`

**Target:** The interaction between the Python application and MySQL (`db.py` CRUD operations).  
**AI Contribution:** AI designed the database mocking strategy using `unittest.mock.patch`, enabling teammates to run integration tests without a local MySQL server installed.  
**No MySQL server required.**

```bash
pytest tests/test_db.py -v
```

Covered scenarios:

| Test | What is verified |
|------|-----------------|
| `test_create_connection_uses_db_config` | `mysql.connector.connect` is called with correct config |
| `test_run_query_select_returns_list_of_dicts` | SELECT path returns mocked row data |
| `test_run_query_insert_returns_lastrowid` | INSERT path returns `lastrowid` and calls `commit()` |
| `test_run_query_returns_none_on_connection_error` | Graceful `None` return when DB is unreachable |

---

## System / E2E Testing — Playwright for Python

**Target:** Complete end-to-end user flows on the Streamlit web interface.  
**AI Contribution:** AI translated natural language user stories into automated browser scripts using robust role-based and text-based locators (`get_by_role`, `get_by_text`) to handle Streamlit's dynamic CSS class names.  
**Requires the Streamlit app to be running.**

```bash
# Terminal 1 — start the app
streamlit run app.py

# Terminal 2 — run E2E tests
pytest tests/test_e2e.py -v

# Optional: watch the browser while tests run
pytest tests/test_e2e.py -v --headed
```

Covered user flows:

| Test | Flow |
|------|------|
| `test_login_page_loads` | App title and Login button are visible |
| `test_guest_login` | Click "Continue as Guest" → POS System page appears |
| `test_admin_login` | Login with admin credentials → Menu Management visible in sidebar |
| `test_add_to_cart` | As guest, click "Add to Cart" → Cart section appears |

---

## Running the Full Test Suite

```bash
# Unit + Integration (no server needed)
pytest tests/test_logic.py tests/test_db.py -v

# All three phases (requires streamlit run app.py in another terminal)
pytest tests/ -v --tb=short
```
