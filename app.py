import streamlit as st
import pandas as pd
import datetime
import uuid
import altair as alt
import os
from typing import Any, Optional, List, Dict
from db import DB_CONFIG, create_connection, run_query
from logic import hash_password, calculate_cart_total, get_loyalty_tier, calculate_order_total

# ==========================================
# 0. FORCE LIGHT THEME (WHITE BACKGROUND)
# ==========================================
# This automatically creates a Streamlit config file to force a white theme.
# Using absolute paths and a try-except block to avoid Windows FileNotFoundError
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    st_dir = os.path.join(base_dir, ".streamlit")
    if not os.path.exists(st_dir):
        os.makedirs(st_dir, exist_ok=True)
    st_config_path = os.path.join(st_dir, "config.toml")
    if not os.path.exists(st_config_path):
        with open(st_config_path, "w") as f:
            f.write("[theme]\nbase=\"light\"\n")
except Exception:
    pass # Silently fail so the app continues to run even if folder creation is blocked

# ==========================================
# 1. DATABASE CONFIGURATION & HELPERS
# ==========================================
# DB_CONFIG, create_connection, and run_query are imported from db.py

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
if 'current_page' not in st.session_state:
    st.session_state.current_page = "POS System"

# ==========================================
# 3. MODULE A: AUTHENTICATION
# ==========================================
# hash_password is imported from logic.py

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
        guest_num = str(uuid.uuid4().int)[:4]
        unique_name = f"guest_{guest_num}"
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insert_g = "INSERT INTO users (username, password_hash, role, created_at) VALUES (%s, %s, %s, %s)"
        guest_id = run_query(insert_g, (unique_name, hash_password('guest_pass_123'), 'guest', now), fetch=False, commit=True)
        if guest_id:
            st.session_state.logged_in = True
            st.session_state.user_id = guest_id
            st.session_state.username = 'Guest'
            st.session_state.role = 'guest'
            st.rerun()
        else:
            st.error("Failed to create guest session.")

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.cart = {}
    st.session_state.current_page = "POS System"
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
            st.dataframe(df_menu)

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
                                    st.image(img_url, use_column_width=True)
                                    image_rendered = True
                                else:
                                    local_path = f"static{img_url}"
                                    if os.path.exists(local_path):
                                        st.image(local_path, use_column_width=True)
                                        image_rendered = True
                            except Exception:
                                pass # Silently skip if image rendering fails
                        
                        # Fallback image if nothing was rendered
                        if not image_rendered:
                            st.image("https://placehold.co/400x300?text=No+Image+Available", use_column_width=True)
                        
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

        st.divider()
        st.subheader("🧾 Today's Orders")

        # Query orders placed by this user today
        today_q = """
            SELECT order_id, total_amount, status, created_at
            FROM orders
            WHERE user_id = %s AND DATE(created_at) = CURDATE()
            ORDER BY created_at DESC
        """
        today_orders = run_query(today_q, (st.session_state.user_id,))

        if today_orders:
            # Calculate total spent today
            today_total = sum(float(order['total_amount']) for order in today_orders)
            st.markdown(f"**Total Spent Today: ${today_total:.2f}**")

            # Show simple list of today's receipts
            for order in today_orders:
                with st.expander(f"Order #{order['order_id']} | ${order['total_amount']} ({order['status']})"):
                    # Get items inside this specific order
                    items_q = """
                        SELECT m.name, oi.quantity
                        FROM order_items oi
                        JOIN menu_items m ON oi.menu_items_id = m.menu_items_id
                        WHERE oi.order_id = %s
                    """
                    order_items = run_query(items_q, (order['order_id'],))
                    if order_items:
                        for item in order_items:
                            st.write(f"- {item['quantity']}x {item['name']}")
        else:
            st.caption("No orders placed today yet.")

def add_to_cart(item_id, name, price, redirect_to=None):
    """
    Adds an item to cart. If redirect_to is provided, switches page before rerun.
    """
    if item_id in st.session_state.cart:
        st.session_state.cart[item_id]['qty'] += 1
    else:
        st.session_state.cart[item_id] = {'name': name, 'price': float(price), 'qty': 1}
    
    if redirect_to:
        st.session_state.current_page = redirect_to
    
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
                df_top = pd.DataFrame(top_items)
                df_top['total_sold'] = df_top['total_sold'].astype(int)
                chart = alt.Chart(df_top).mark_bar().encode(
                    x=alt.X('total_sold:Q', title='Units Sold'),
                    y=alt.Y('name:N', sort='-x', title=None)
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No completed sales data yet.")
        
        with col_chart2:
            st.subheader("⏰ Peak Hours (Rush Tracker)")
            query_peak = """
                SELECT HOUR(created_at) as hour_of_day, COUNT(order_id) as total_orders 
                FROM orders 
                WHERE status = 'Completed' 
                GROUP BY HOUR(created_at) 
                ORDER BY hour_of_day
            """
            peak_data = run_query(query_peak)
            if peak_data:
                df_peak = pd.DataFrame(peak_data)
                # Format hour to look nice (e.g., "14:00")
                df_peak['Hour'] = df_peak['hour_of_day'].apply(lambda x: f"{x:02d}:00")
                df_peak = df_peak.set_index('Hour')
                # Use Streamlit's built-in bar chart for simplicity
                st.bar_chart(df_peak['total_orders'], color="#FF4B4B")
            else:
                st.info("Not enough data to track peak hours.")
        
        st.divider()
        
        # --- REVENUE TREND & VIP CUSTOMERS ---
        col_bottom1, col_bottom2 = st.columns([7, 3])
        
        with col_bottom1:
            st.subheader("📈 Daily Revenue Trend")
            query_trend = """
                SELECT DATE(created_at) as order_date, SUM(total_amount) as daily_revenue 
                FROM orders 
                WHERE status = 'Completed' 
                GROUP BY DATE(created_at) 
                ORDER BY order_date
            """
            trend_data = run_query(query_trend)
            if trend_data:
                df_trend = pd.DataFrame(trend_data)
                df_trend['order_date'] = pd.to_datetime(df_trend['order_date'])
                df_trend = df_trend.set_index('order_date')
                st.line_chart(df_trend['daily_revenue'], color="#00C853")
            else:
                st.info("Not enough data for a revenue trend.")
                
        with col_bottom2:
            st.subheader("👑 VIP Customers")
            query_vips = """
                SELECT u.username, SUM(o.total_amount) as total_spent 
                FROM orders o 
                JOIN users u ON o.user_id = u.user_id 
                WHERE o.status = 'Completed' AND u.username NOT LIKE 'Guest_%' AND u.username != 'Guest'
                GROUP BY u.user_id 
                ORDER BY total_spent DESC LIMIT 5
            """
            vips_data = run_query(query_vips)
            if vips_data:
                df_vips = pd.DataFrame(vips_data)
                df_vips.rename(columns={'username': 'Customer', 'total_spent': 'Total Spent ($)'}, inplace=True)
                # Convert to float to ensure two decimal places
                df_vips['Total Spent ($)'] = df_vips['Total Spent ($)'].astype(float).map("{:.2f}".format)
                st.dataframe(df_vips, hide_index=True, use_container_width=True)
            else:
                st.info("No VIP data yet.")
    else:
        st.info("No orders found in the database yet.")

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
            st.dataframe(df_users)
            
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
# 9. MODULE G: CUSTOMER DASHBOARD (DINING DIARY)
# ==========================================
def customer_dashboard():
    st.header("📔 Customer Dashboard")
    st.write("Welcome to your personal food journey!")
    
    user_id = st.session_state.user_id
    
    # --- 1. AT A GLANCE STATS & LOYALTY TIER ---
    stats_q = """
        SELECT COUNT(order_id) as total_orders, SUM(total_amount) as lifetime_spent 
        FROM orders WHERE user_id = %s AND status != 'Cancelled'
    """
    stats = run_query(stats_q, (user_id,))
    
    total_orders = stats[0]['total_orders'] if stats and stats[0]['total_orders'] else 0
    lifetime_spent = float(stats[0]['lifetime_spent']) if stats and stats[0]['lifetime_spent'] else 0.0
    
    tier_label = get_loyalty_tier(lifetime_spent)
    tier_icons = {"Gold VIP": ("🥇 Gold VIP", "gold"), "Silver Gourmand": ("🥈 Silver Gourmand", "silver"), "Bronze Foodie": ("🥉 Bronze Foodie", "#cd7f32")}
    tier, color = tier_icons[tier_label]
        
    c1, c2, c3 = st.columns(3)
    c1.metric("Lifetime Spent 💰", f"${lifetime_spent:.2f}")
    c2.metric("Total Visits 🏃", total_orders)
    c3.markdown(f"**Loyalty Tier:**\n### <span style='color:{color}'>{tier}</span>", unsafe_allow_html=True)
    
    st.divider()

    # --- 2. YOUR GO-TO DISH ---
    st.subheader("❤️ Your Go-To Dish")
    fav_q = """
        SELECT m.menu_items_id, m.name, m.price, SUM(oi.quantity) as times_ordered 
        FROM order_items oi 
        JOIN orders o ON oi.order_id = o.order_id 
        JOIN menu_items m ON oi.menu_items_id = m.menu_items_id 
        WHERE o.user_id = %s 
        GROUP BY m.menu_items_id, m.name, m.price 
        ORDER BY times_ordered DESC LIMIT 1
    """
    favorite = run_query(fav_q, (user_id,))
    
    if favorite and favorite[0]['times_ordered'] > 0:
        fav_item = favorite[0]
        col_text, col_btn = st.columns([3, 1])
        with col_text:
            st.success(f"You really love **{fav_item['name']}**! You've ordered it **{int(fav_item['times_ordered'])} times**.")
        with col_btn:
            if st.button(f"Order it again! (${fav_item['price']})", type="primary"):
                # Use the redirect_to parameter to switch page AND add to cart in one go
                add_to_cart(
                    fav_item['menu_items_id'],
                    fav_item['name'],
                    fav_item['price'],
                    redirect_to="POS System"
                )
    else:
        st.info("You haven't ordered enough yet for us to find your favorite dish. Time to explore the menu!")

    st.divider()

    # --- 3. FULL ORDER HISTORY ---
    st.subheader("📜 Full Receipt Book")
    history_q = "SELECT order_id, created_at, total_amount, payment_method, status FROM orders WHERE user_id = %s ORDER BY created_at DESC"
    history = run_query(history_q, (user_id,))
    
    if history:
        df_history = pd.DataFrame(history)
        df_history.rename(columns={
            'order_id': 'Order #', 'created_at': 'Date', 
            'total_amount': 'Total ($)', 'payment_method': 'Payment', 'status': 'Status'
        }, inplace=True)
        # Display as a clean, read-only table
        st.dataframe(df_history, use_container_width=True, hide_index=True)
    else:
        st.write("No past orders found.")


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

            if st.session_state.role in ['customer']:
                nav_options.append("Customer Dashboard") 
            
            if st.session_state.role in ['admin', 'staff']:
                nav_options.append("Order Tracking")
                
            if st.session_state.role == 'admin':
                nav_options.extend(["Admin Menu Management", "Admin Dashboard", "Admin User Management"])
                
            st.subheader("Navigation")
            for option in nav_options:
                btn_type = "primary" if st.session_state.current_page == option else "secondary"
                if st.button(option, use_container_width=True, type=btn_type):
                    st.session_state.current_page = option
            
            st.divider()
            if st.button("Logout", use_container_width=True):
                logout()
                
        page = st.session_state.current_page
        
        if page == "POS System":
            pos_system()
        elif page == "Customer Dashboard" and st.session_state.role in ['customer']:
            customer_dashboard()
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