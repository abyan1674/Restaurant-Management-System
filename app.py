import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import hashlib
import os
import datetime

# ==========================================
# 1. DATABASE CONFIGURATION & HELPERS
# ==========================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",       # Update with your MySQL username
    "password": "",       # Update with your MySQL password
    "database": "restaurant_management"
}

def create_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        st.error(f"Database connection failed: {e}")
        return None

def run_query(query, params=None, fetch=True, commit=False):
    conn = create_connection()
    if conn is None:
        return None
    
    cursor = conn.cursor(dictionary=True)
    result = None
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
            result = cursor.lastrowid
        if fetch:
            result = cursor.fetchall()
    except Exception as e:
        st.error(f"Database Error: {e}")
    finally:
        cursor.close()
        conn.close()
    return result

# ==========================================
# 2. SESSION STATE INITIALIZATION
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'cart' not in st.session_state:
    st.session_state.cart = {} # Format: {menu_item_id: {'name': str, 'price': float, 'qty': int}}

# ==========================================
# 3. MODULE A: AUTHENTICATION
# ==========================================
def hash_password(password):
    # Standard fallback, though your DB might use a specific hashing algorithm
    return hashlib.md5(password.encode()).hexdigest()

def login_page():
    st.title("🍽️ Restaurant Management System")
    st.subheader("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            query = "SELECT * FROM users WHERE username = %s"
            users = run_query(query, (username,))
            
            if users:
                user = users[0]
                # In production, compare hashed passwords. 
                # Doing a direct check here or a simple hash check depending on your exact DB setup.
                if user['password_hash'] == password or user['password_hash'] == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.user_id = user['user_id']
                    st.session_state.username = user['username']
                    st.session_state.role = user['role']
                    st.success(f"Welcome, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid password")
            else:
                st.error("User not found")
                
    st.divider()
    st.subheader("No Account?")
    if st.button("Continue as Guest / Customer", use_container_width=True):
        query_guest = "SELECT * FROM users WHERE username = 'Guest' LIMIT 1"
        guests = run_query(query_guest)
        
        if guests:
            user = guests[0]
            st.session_state.logged_in = True
            st.session_state.user_id = user['user_id']
            st.session_state.username = user['username']
            st.session_state.role = user['role']
            st.rerun()
        else:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            insert_g = "INSERT INTO users (username, password_hash, role, created_at) VALUES (%s, %s, %s, %s)"
            guest_id = run_query(insert_g, ('Guest', hash_password('guest_pass_123'), 'customer', now), fetch=False, commit=True)
            if guest_id:
                st.session_state.logged_in = True
                st.session_state.user_id = guest_id
                st.session_state.username = 'Guest'
                st.session_state.role = 'customer'
                st.rerun()
            else:
                st.error("Failed to create guest session.")

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.cart = {}
    st.rerun()

# ==========================================
# 4. MODULE B: MENU MANAGEMENT (ADMIN)
# ==========================================
def admin_menu_management():
    st.header("🛠️ Menu & Category Management")
    
    tab1, tab2, tab3 = st.tabs(["Add Menu Items", "Manage Categories", "Update Item Status"])
    
    # --- TAB 1: MENU ITEMS ---
    with tab1:
        st.subheader("Add New Menu Item")
        
        # Note: No indents for SELECT command
        cat_query = "SELECT * FROM categories ORDER BY display_order"
        categories = run_query(cat_query)
        cat_options = {cat['name']: cat['category_id'] for cat in categories} if categories else {}
        
        with st.form("add_item_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Item Name")
                price = st.number_input("Price", min_value=0.0, format="%.2f")
                category_name = st.selectbox("Category", options=list(cat_options.keys()))
            with col2:
                description = st.text_area("Description")
                is_available = st.checkbox("Available", value=True)
                image_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
            
            submit_item = st.form_submit_button("Add Item")
            
            if submit_item and name and price > 0:
                img_path = ""
                if image_file:
                    # Save image locally
                    if not os.path.exists("static/img"):
                        os.makedirs("static/img")
                    img_path = f"/img/{image_file.name}"
                    with open(f"static{img_path}", "wb") as f:
                        f.write(image_file.getbuffer())
                
                cat_id = cat_options[category_name]
                avail_int = 1 if is_available else 0
                
                insert_q = "INSERT INTO menu_items (name, description, price, image_url, is_available, category_id) VALUES (%s, %s, %s, %s, %s, %s)"
                run_query(insert_q, (name, description, price, img_path, avail_int, cat_id), fetch=False, commit=True)
                st.success("Item added successfully!")

        st.divider()
        st.subheader("Current Menu Items")
        # Note: No indents for SELECT command
        menu_query = "SELECT m.menu_items_id, m.name, m.price, c.name as category, m.is_available FROM menu_items m JOIN categories c ON m.category_id = c.category_id"
        menu_items = run_query(menu_query)
        if menu_items:
            df_menu = pd.DataFrame(menu_items)
            st.dataframe(df_menu, use_container_width=True)

    # --- TAB 2: CATEGORIES ---
    with tab2:
        st.subheader("Add New Category")
        with st.form("add_cat_form", clear_on_submit=True):
            cat_name = st.text_input("Category Name")
            display_order = st.number_input("Display Order", min_value=1, step=1)
            submit_cat = st.form_submit_button("Add Category")
            
            if submit_cat and cat_name:
                insert_c = "INSERT INTO categories (name, display_order) VALUES (%s, %s)"
                run_query(insert_c, (cat_name, display_order), fetch=False, commit=True)
                st.success("Category added!")
                st.rerun()

    # --- NEW TAB 3: UPDATE ITEM STATUS ---
    with tab3:
        st.subheader("Update Availability")
        st.write("Mark items as 'Out of Stock' or update their prices.")
        
        menu_query_update = "SELECT menu_items_id, name, price, is_available FROM menu_items"
        items_to_update = run_query(menu_query_update)
        
        if items_to_update:
            item_options = {f"{item['name']} - ${item['price']}": item['menu_items_id'] for item in items_to_update}
            selected_item_label = st.selectbox("Select Item to Update", options=list(item_options.keys()))
            
            if selected_item_label:
                selected_id = item_options[selected_item_label]
                # Find the current status of the selected item
                current_item = next(item for item in items_to_update if item['menu_items_id'] == selected_id)
                current_status = bool(current_item['is_available'])
                
                with st.form("update_item_form"):
                    new_availability = st.checkbox("Item is Available", value=current_status)
                    new_price = st.number_input("Update Price", min_value=0.0, value=float(current_item['price']), format="%.2f")
                    
                    update_btn = st.form_submit_button("Save Changes")
                    
                    if update_btn:
                        avail_int = 1 if new_availability else 0
                        update_q = "UPDATE menu_items SET is_available = %s, price = %s WHERE menu_items_id = %s"
                        run_query(update_q, (avail_int, new_price, selected_id), fetch=False, commit=True)
                        st.success(f"Successfully updated {current_item['name']}!")
                        st.rerun()

# ==========================================
# 5. MODULE C: POINT OF SALE (POS)
# ==========================================
def pos_system():
    st.header("🛒 Point of Sale (POS)")
    
    col_menu, col_cart = st.columns([7, 3])
    
    with col_menu:
        # Note: No indents for SELECT command
        items_q = "SELECT m.*, c.name as category_name, i.image_url as ext_image_url FROM menu_items m JOIN categories c ON m.category_id = c.category_id LEFT JOIN item_images i ON m.menu_items_id = i.menu_items_id AND i.is_primary = 1 WHERE m.is_available = 1"
        items = run_query(items_q)
        
        if items:
            df = pd.DataFrame(items)
            categories = df['category_name'].unique()
            
            st.subheader("Filter Menu")
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                search_text = st.text_input("🔍 Search Food Name", "")
            with col_f2:
                selected_cat = st.selectbox("📂 Category", ["All"] + list(categories))
            with col_f3:
                max_price = float(df['price'].max()) if not df.empty else 100.0
                price_range = st.slider("💲 Price Range", 0.0, max_price, (0.0, max_price))

            # Apply filters to dataframe
            if selected_cat != "All":
                df = df[df['category_name'] == selected_cat]
            if search_text:
                df = df[df['name'].str.contains(search_text, case=False, na=False)]
            df = df[(df['price'] >= price_range[0]) & (df['price'] <= price_range[1])]
            
            st.divider()
            
            # Display Items in a Grid
            cols = st.columns(3)
            for index, row in df.reset_index(drop=True).iterrows():
                with cols[index % 3]:
                    with st.container(border=True):
                        
                        # Render Image if available, otherwise use a fallback
                        img_url = row.get('ext_image_url') if pd.notna(row.get('ext_image_url')) else row.get('image_url')
                        image_rendered = False
                        
                        if pd.notna(img_url) and img_url:
                            try:
                                if str(img_url).startswith('http'):
                                    st.image(img_url, use_container_width=True)
                                    image_rendered = True
                                else:
                                    local_path = f"static{img_url}"
                                    if os.path.exists(local_path):
                                        st.image(local_path, use_container_width=True)
                                        image_rendered = True
                            except Exception:
                                pass # Silently skip if image rendering fails
                        
                        # Fallback image if nothing was rendered
                        if not image_rendered:
                            st.image("https://placehold.co/400x300?text=No+Image+Available", use_container_width=True)
                        
                        st.markdown(f"**{row['name']}**")
                        st.caption(f"${row['price']:.2f}")
                        if st.button(f"Add to Cart", key=f"add_{row['menu_items_id']}"):
                            add_to_cart(row['menu_items_id'], row['name'], row['price'])

    with col_cart:
        st.subheader("Current Order")
        if not st.session_state.cart:
            st.info("Cart is empty.")
        else:
            total_amount = 0.0
            for item_id, item_data in st.session_state.cart.items():
                st.write(f"{item_data['name']} (x{item_data['qty']}) - ${item_data['price'] * item_data['qty']:.2f}")
                total_amount += item_data['price'] * item_data['qty']
                
                # Increment / Decrement buttons
                c1, c2 = st.columns(2)
                if c1.button("➕", key=f"inc_{item_id}"):
                    add_to_cart(item_id, item_data['name'], item_data['price'])
                if c2.button("➖", key=f"dec_{item_id}"):
                    remove_from_cart(item_id)
            
            st.divider()
            st.markdown(f"### Total: **${total_amount:.2f}**")
            
            pay_method = st.selectbox("Payment Method", ["Cash", "Credit Card", "Mobile Pay"])
            
            if st.button("Complete Order 🚀", type="primary", use_container_width=True):
                process_checkout(total_amount, pay_method)

def add_to_cart(item_id, name, price):
    if item_id in st.session_state.cart:
        st.session_state.cart[item_id]['qty'] += 1
    else:
        st.session_state.cart[item_id] = {'name': name, 'price': float(price), 'qty': 1}
    st.rerun()

def remove_from_cart(item_id):
    if item_id in st.session_state.cart:
        st.session_state.cart[item_id]['qty'] -= 1
        if st.session_state.cart[item_id]['qty'] <= 0:
            del st.session_state.cart[item_id]
        st.rerun()

def process_checkout(total_amount, payment_method):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 1. Insert into orders table
    order_q = "INSERT INTO orders (status, total_amount, payment_method, created_at, user_id) VALUES (%s, %s, %s, %s, %s)"
    order_id = run_query(order_q, ("Pending", total_amount, payment_method, now, st.session_state.user_id), fetch=False, commit=True)
    
    if order_id:
        # 2. Insert into order_items table
        for item_id, data in st.session_state.cart.items():
            oi_q = "INSERT INTO order_items (order_id, quantity, unit_price, created_at, menu_items_id) VALUES (%s, %s, %s, %s, %s)"
            run_query(oi_q, (order_id, data['qty'], data['price'], now, item_id), fetch=False, commit=True)
            
        st.session_state.cart = {} # Clear cart
        st.success(f"Order #{order_id} processed successfully!")
        st.rerun()

# ==========================================
# 6. MODULE D: ORDER TRACKING
# ==========================================
def order_tracking():
    st.header("📋 Order Tracking Dashboard")
    
    orders_q = "SELECT * FROM orders ORDER BY created_at DESC LIMIT 50"
    orders = run_query(orders_q)
    
    if orders:
        for order in orders:
            with st.expander(f"Order #{order['order_id']} | Total: ${order['total_amount']} | Status: {order['status']}"):
                st.write(f"**Date:** {order['created_at']}")
                st.write(f"**Payment:** {order['payment_method']}")
                
                # Fetch items for this order
                items_q = "SELECT o.quantity, m.name FROM order_items o JOIN menu_items m ON o.menu_items_id = m.menu_items_id WHERE o.order_id = %s"
                items = run_query(items_q, (order['order_id'],))
                if items:
                    for i in items:
                        st.write(f"- {i['quantity']}x {i['name']}")
                
                # Status Update Toggle
                new_status = st.selectbox("Update Status", ["Pending", "Preparing", "Served", "Completed", "Cancelled"], 
                                          index=["Pending", "Preparing", "Served", "Completed", "Cancelled"].index(order['status']) if order['status'] in ["Pending", "Preparing", "Served", "Completed", "Cancelled"] else 3,
                                          key=f"status_{order['order_id']}")
                if st.button("Save Status", key=f"btn_{order['order_id']}"):
                    update_q = "UPDATE orders SET status = %s WHERE order_id = %s"
                    run_query(update_q, (new_status, order['order_id']), fetch=False, commit=True)
                    st.success("Status Updated!")
                    st.rerun()
    else:
        st.info("No orders found.")

# ==========================================
# 7. MODULE E: ADMIN DASHBOARD
# ==========================================
def admin_dashboard():
    st.header("📈 Business Dashboard")
    
    # Note: No indents for SELECT command
    query_orders = "SELECT status, total_amount FROM orders"
    all_orders = run_query(query_orders)
    
    if all_orders:
        df_orders = pd.DataFrame(all_orders)
        df_orders['total_amount'] = df_orders['total_amount'].astype(float)
        
        completed_orders = df_orders[df_orders['status'] == 'Completed']
        total_revenue = completed_orders['total_amount'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue 💰", f"${total_revenue:.2f}")
        c2.metric("Total Orders 📦", len(all_orders))
        c3.metric("Completed Orders ✅", len(completed_orders))
        
        st.divider()
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Top Selling Items")
            # Note: No indents for SELECT command
            query_top = "SELECT m.name, SUM(o.quantity) as total_sold FROM order_items o JOIN menu_items m ON o.menu_items_id = m.menu_items_id JOIN orders ord ON o.order_id = ord.order_id WHERE ord.status = 'Completed' GROUP BY m.menu_items_id ORDER BY total_sold DESC LIMIT 5"
            top_items = run_query(query_top)
            if top_items:
                import altair as alt
                df_top = pd.DataFrame(top_items)
                df_top['total_sold'] = df_top['total_sold'].astype(int)
                chart = alt.Chart(df_top).mark_bar().encode(
                    x=alt.X('total_sold:Q', title='Units Sold'),
                    y=alt.Y('name:N', sort='-x', title=None)
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No completed sales data yet.")

# ==========================================
# 8. MODULE F: USER MANAGEMENT (ADMIN)
# ==========================================
def admin_user_management():
    st.header("👥 User Management")
    
    tab1, tab2 = st.tabs(["View Users", "Create New User"])
    
    with tab1:
        st.subheader("Current Users")
        # Note: No indents for SELECT command
        query_users = "SELECT user_id, username, role, created_at FROM users"
        users = run_query(query_users)
        
        if users:
            df_users = pd.DataFrame(users)
            st.dataframe(df_users, use_container_width=True)
            
    with tab2:
        st.subheader("Create Staff/Admin Account")
        with st.form("add_user_form", clear_on_submit=True):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["staff", "admin", "customer", "guest"])
            submit_user = st.form_submit_button("Create User")
            
            if submit_user and new_username and new_password:
                hashed_pw = hash_password(new_password)
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                insert_u = "INSERT INTO users (username, password_hash, role, created_at) VALUES (%s, %s, %s, %s)"
                run_query(insert_u, (new_username, hashed_pw, new_role, now), fetch=False, commit=True)
                st.success(f"User '{new_username}' created successfully!")
                st.rerun()

# ==========================================
# MAIN APP ROUTING
# ==========================================
def main():
    st.set_page_config(page_title="Restaurant POS", layout="wide")
    
    if not st.session_state.logged_in:
        login_page()
    else:
        with st.sidebar:
            st.title(f"Hi, {st.session_state.username}")
            st.write(f"Role: **{st.session_state.role.capitalize()}**")
            st.divider()
            
            nav_options = ["POS System"]
            
            if st.session_state.role in ['admin', 'staff']:
                nav_options.append("Order Tracking")
                
            if st.session_state.role == 'admin':
                nav_options.extend(["Admin Menu Management", "Admin Dashboard", "Admin User Management"])
                
            page = st.radio("Navigation", nav_options)
            
            st.divider()
            if st.button("Logout"):
                logout()
                
        if page == "POS System":
            pos_system()
        elif page == "Order Tracking" and st.session_state.role in ['admin', 'staff']:
            order_tracking()
        elif page == "Admin Menu Management" and st.session_state.role == 'admin':
            admin_menu_management()
        elif page == "Admin Dashboard" and st.session_state.role == 'admin':
            admin_dashboard()
        elif page == "Admin User Management" and st.session_state.role == 'admin':
            admin_user_management()

if __name__ == "__main__":
    main()
