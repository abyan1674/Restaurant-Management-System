import mysql.connector
from mysql.connector import Error
from typing import Any, Optional

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "restaurant_management"
}


def create_connection():
    connection = mysql.connector.connect(**DB_CONFIG)
    return connection


def run_query(query: str, params: Optional[tuple] = None, fetch: bool = True, commit: bool = False) -> Any:
    """
    Generic DB executor.
    - commit=True (INSERT/UPDATE/DELETE): returns lastrowid (int) or None on error
    - fetch=True (SELECT): returns list of dicts or None on error
    """
    try:
        conn = create_connection()
    except Error:
        return None

    cursor = conn.cursor(dictionary=True)
    result: Any = None
    try:
        cursor.execute(query, params if params is not None else ())
        if commit:
            conn.commit()
            result = cursor.lastrowid
        elif fetch:
            result = cursor.fetchall()
    except Exception:
        result = None
    finally:
        cursor.close()
        conn.close()
    return result
