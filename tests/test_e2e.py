"""
System / E2E Tests — Playwright for Python
Target: Full user flows on the Streamlit web interface.
Requires the app to be running first: streamlit run app.py
Run: pytest tests/test_e2e.py -v
     pytest tests/test_e2e.py -v --headed   # watch the browser
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8501"


@pytest.fixture(autouse=True)
def go_to_app(page: Page):
    """Navigate to the app and wait for Streamlit to finish loading before each test."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")


# -------------------------------------------------------
# Test: Login page loads correctly
# Expected: app title and Login button are visible
# Hint: use expect(page.get_by_text("...")).to_be_visible()
# -------------------------------------------------------
# Write your E2E test for the login page here


# -------------------------------------------------------
# Test: Guest login flow
# Steps: click "Continue as Guest / Customer" → verify POS page appears
# Hint: use page.get_by_role("button", name="...").click()
# -------------------------------------------------------
# Write your E2E test for guest login here


# -------------------------------------------------------
# Test: Admin login flow
# Steps: fill Username + Password → click Login → verify "Menu Management" in sidebar
# Credentials: admin_super / password
# -------------------------------------------------------
# Write your E2E test for admin login here


# -------------------------------------------------------
# Test: Add item to cart
# Steps: guest login → click first "Add to Cart" button → verify cart appears
# Hint: use page.get_by_role("button", name="Add to Cart").first.click()
# -------------------------------------------------------
# Write your E2E test for add-to-cart here
