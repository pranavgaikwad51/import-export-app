import streamlit as st
import pandas as pd
import hashlib
import os

# ------------- CONFIG ----------------
st.set_page_config(page_title="Import-Export Hub", layout="wide")
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.csv")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.csv")
BUYERS_FILE = os.path.join(DATA_DIR, "buyers.csv")

# ------------- AUTH ------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    return pd.DataFrame(columns=["username", "hashed_password", "role"])

def save_user(username, hashed_password, role):
    users = load_users()
    new_user = pd.DataFrame([[username, hashed_password, role]],
                            columns=["username", "hashed_password", "role"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USERS_FILE, index=False)

def authenticate_user(username, password):
    users = load_users()
    hashed = hash_password(password)
    user_row = users[(users["username"] == username) & 
                     (users["hashed_password"] == hashed)]
    if not user_row.empty:
        return user_row.iloc[0]["role"]
    return None

def user_exists(username):
    users = load_users()
    return username in users["username"].values

# ------------- HELPERS ------------------
def load_products():
    if os.path.exists(PRODUCTS_FILE):
        return pd.read_csv(PRODUCTS_FILE)
    return pd.DataFrame(columns=["product_name", "price", "quantity", "image_path"])

def load_buyers():
    if os.path.exists(BUYERS_FILE):
        return pd.read_csv(BUYERS_FILE)
    return pd.DataFrame(columns=["required_product_name", "quantity"])

def show_confidentiality_checkbox():
    return st.checkbox("✅ I agree not to bypass the middleman. Any violation may result in legal penalties.")

def detect_violation(text):
    forbidden_keywords = ["email", "@", "phone", "contact", "whatsapp", "mobile"]
    for word in forbidden_keywords:
        if word in text.lower():
            return True
    return False

# ------------- UI ------------------
st.title("🌐 Import-Export Middleman Portal")
st.markdown("📝 **NOTE: First sign up, then login.**")

auth_option = st.sidebar.radio("Choose Action", ["Login", "Sign Up"])

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.username = None

# --- SIGN UP ---
if auth_option == "Sign Up":
    st.subheader("🔐 Sign Up")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["Buyer", "Customer", "Middleman"])
    if st.button("Create Account"):
        if user_exists(new_user):
            st.warning("User already exists.")
        elif new_user and new_pass:
            save_user(new_user, hash_password(new_pass), role)
            st.success("Registration successful. Please login.")
        else:
            st.error("Please fill all fields.")

# --- LOGIN ---
elif auth_option == "Login":
    st.subheader("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        role = authenticate_user(username, password)
        if role:
            st.session_state.authenticated = True
            st.session_state.role = role
            st.session_state.username = username
            st.success(f"Welcome {username}!")
        else:
            st.error("Invalid credentials")

# --- MAIN APP AFTER LOGIN ---
if st.session_state.authenticated:
    st.sidebar.success(f"Logged in as: {st.session_state.role}")
    
    if not show_confidentiality_checkbox():
        st.warning("❌ You must agree to the confidentiality policy.")
        st.stop()

    role = st.session_state.role

    # --- Buyer Dashboard ---
    if role == "Buyer":
        st.header("🛒 Buyer Dashboard")
        products = load_products()
        if products.empty:
            st.info("No products available yet.")
        else:
            for _, row in products.iterrows():
                col1, col2 = st.columns([1, 3])
                with col1:
                    if os.path.exists(row["image_path"]):
                        st.image(row["image_path"], width=150)
                    else:
                        st.text("No image")
                with col2:
                    st.markdown(f"**Product**: {row['product_name']}")
                    st.markdown(f"**Price**: ₹{row['price']}")
                    st.markdown(f"**Quantity**: {row['quantity']}")
                    if detect_violation(str(row)):
                        st.error("❗ You violated our confidentiality policy. ₹5,00,000 fine applicable.")
                        st.stop()

    # --- Customer (Seller) Dashboard ---
    elif role == "Customer":
        st.header("🏭 Seller Dashboard")
        buyers = load_buyers()
        if buyers.empty:
            st.info("No buyer requests available.")
        else:
            for _, row in buyers.iterrows():
                st.markdown(f"🔸 **Product Needed**: {row['required_product_name']}")
                st.markdown(f"🔸 **Quantity**: {row['quantity']}")
                if detect_violation(str(row)):
                    st.error("❗ You violated our confidentiality policy. ₹5,00,000 fine applicable.")
                    st.stop()

    # --- Admin Dashboard ---
    elif role == "Middleman":
        st.header("📋 Admin Panel - Full Access")

        st.subheader("👥 Users")
        st.dataframe(load_users())

        st.subheader("📦 Products")
        st.dataframe(load_products())

        st.subheader("🛒 Buyer Requirements")
        st.dataframe(load_buyers())
