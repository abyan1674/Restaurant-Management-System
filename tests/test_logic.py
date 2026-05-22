"""
Unit Tests — logic.py
Target: Pure business logic functions (no database, no Streamlit required).
Run: pytest tests/test_logic.py -v
"""
import pytest
from logic import hash_password, calculate_cart_total, get_loyalty_tier, calculate_order_total


# -------------------------------------------------------
# hash_password(password: str) -> str
# Expected: returns a 32-char MD5 hex digest string
# -------------------------------------------------------
# Write your unit tests for hash_password() here


# -------------------------------------------------------
# calculate_cart_total(cart: dict) -> float
# Cart format: {item_id: {"name": str, "price": float, "qty": int}}
# Expected: returns sum of price * qty across all items
# -------------------------------------------------------
# Write your unit tests for calculate_cart_total() here


# -------------------------------------------------------
# get_loyalty_tier(total_spent: float) -> str
# Expected: "Bronze Foodie" | "Silver Gourmand" | "Gold VIP"
# Boundaries: Silver >= 50, Gold >= 150
# -------------------------------------------------------
# Write your unit tests for get_loyalty_tier() here


# -------------------------------------------------------
# calculate_order_total(items: list[dict]) -> float
# Item format: {"unit_price": float, "quantity": int}
# Expected: returns sum of unit_price * quantity across all items
# -------------------------------------------------------
# Write your unit tests for calculate_order_total() here
