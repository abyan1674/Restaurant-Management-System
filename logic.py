import hashlib


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()


def calculate_cart_total(cart: dict) -> float:
    """Sum price * qty for all items in the session cart dict."""
    return sum(item["price"] * item["qty"] for item in cart.values())


def get_loyalty_tier(total_spent: float) -> str:
    """Return loyalty tier label based on lifetime spending."""
    if total_spent >= 150:
        return "Gold VIP"
    elif total_spent >= 50:
        return "Silver Gourmand"
    else:
        return "Bronze Foodie"


def calculate_order_total(items: list) -> float:
    """Sum unit_price * quantity for a list of order-item dicts."""
    return sum(row["unit_price"] * row["quantity"] for row in items)
