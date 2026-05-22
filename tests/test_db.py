"""
Integration Tests — db.py
Target: Database layer (create_connection, run_query) with MySQL mocked via pytest-mock.
No real MySQL server required — all DB calls are intercepted by mocks.
Run: pytest tests/test_db.py -v
"""
import pytest
from unittest.mock import MagicMock, patch
from db import create_connection, run_query, DB_CONFIG


# -------------------------------------------------------
# create_connection()
# Expected: calls mysql.connector.connect() with DB_CONFIG values
# Hint: use patch("db.mysql.connector.connect") to mock the connector
# -------------------------------------------------------
# Write your integration tests for create_connection() here


# -------------------------------------------------------
# run_query() — SELECT path (fetch=True)
# Expected: executes the query and returns a list of dicts
# Hint: mock create_connection() to return a fake connection object
# -------------------------------------------------------
# Write your integration tests for run_query() SELECT path here


# -------------------------------------------------------
# run_query() — INSERT/UPDATE/DELETE path (commit=True)
# Expected: calls conn.commit() and returns cursor.lastrowid
# -------------------------------------------------------
# Write your integration tests for run_query() commit path here


# -------------------------------------------------------
# run_query() — connection failure
# Expected: returns None gracefully when the DB is unreachable
# Hint: make create_connection() raise an Exception
# -------------------------------------------------------
# Write your integration tests for connection error handling here
