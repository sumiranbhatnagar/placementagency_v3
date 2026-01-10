import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import hashlib
from datetime import datetime
import pandas as pd
import base64      # ← ADD THIS
import os 

# -------------------------------------------------------
# PAGE CONFIG (top-level)
# -------------------------------------------------------
#st.set_page_config(
   # page_title="Placement Agency - Login",
   # page_icon="🔐",
    #layout="centered",
    #initial_sidebar_state="collapsed"
#)

# =======================================================
# GOOGLE SHEETS CONFIG FOR LOGIN
# =======================================================
SHEET_ID = "1rpuXdpfwjy0BQcaZcn0Acbh-Se6L3PvyNGiNu4NLcPA"


@st.cache_resource
def get_google_sheets_client():
    """Cached Google Sheets client for login - using st.secrets"""
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Use st.secrets instead of credentials.json
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Google Sheets connection error: {str(e)}")
        return None


# =======================================================
# USER AUTHENTICATION FUNCTIONS
# =======================================================
def get_users_from_sheet():
    """Fetch all users from Google Sheets 'Users' tab"""
    try:
        client = get_google_sheets_client()
        if not client:
            return None

        sheet = client.open_by_key(SHEET_ID).worksheet("Users")
        data = sheet.get_all_records()

        if not data:
            return None

        df = pd.DataFrame(data)
        return df

    except Exception as e:
        st.error(f"Error fetching users: {str(e)}")
        return None


def verify_credentials(username, password):
    """Verify username and password against Google Sheets"""
    df = get_users_from_sheet()

    if df is None or df.empty:
        st.error("❌ Unable to fetch user data from Google Sheets")
        return None

    # Filter user
    user = df[df['Username'].str.lower() == username.lower()]

    if user.empty:
        return None

    # Get stored password hash
    stored_hash = user.iloc[0]['Password']

    # Hash input password
    input_hash = hashlib.sha256(password.encode()).hexdigest()

    # Verify password
    if stored_hash == input_hash:
        return {
            'username': user.iloc[0]['Username'],
            'role': user.iloc[0]['Role'],
            'full_name': user.iloc[0].get('Full Name', username),
            'email': user.iloc[0].get('Email', ''),
            'status': user.iloc[0].get('Status', 'Active')
        }

    return None


def log_login_activity(username, status, ip_address="N/A"):
    """Log login attempts to Google Sheets 'Login_Logs' tab"""
    try:
        client = get_google_sheets_client()
        if not client:
            return False

        sheet = client.open_by_key(SHEET_ID).worksheet("Login_Logs")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = [timestamp, username, status, ip_address]
        sheet.append_row(row)

        return True
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
        return False


# =======================================================
# USER MANAGEMENT FUNCTIONS (Admin Only)
# =======================================================
def add_new_user(username, password, role, full_name, email):
    """Add new user to Google Sheets (Admin function)"""
    try:
        client = get_google_sheets_client()
        if not client:
            return False

        sheet = client.open_by_key(SHEET_ID).worksheet("Users")

        # Check if username already exists
        df = get_users_from_sheet()
        if df is not None and username.lower() in df['Username'].str.lower().values:
            st.error(f"❌ Username '{username}' already exists!")
            return False

        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Create user row
        created_date = datetime.now().strftime("%Y-%m-%d")
        row = [username, password_hash, role, full_name, email, "Active", created_date]

        sheet.append_row(row)
        return True

    except Exception as e:
        st.error(f"Error adding user: {str(e)}")
        return False


def change_password(username, new_password):
    """Change user password"""
    try:
        client = get_google_sheets_client()
        if not client:
            return False

        sheet = client.open_by_key(SHEET_ID).worksheet("Users")
        df = pd.DataFrame(sheet.get_all_records())

        # Find user row
        user_idx = df[df['Username'].str.lower() == username.lower()].index

        if user_idx.empty:
            return False

        # Update password (row number = index + 2, because header is row 1)
        row_num = user_idx[0] + 2
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()

        sheet.update_cell(row_num, 2, new_hash)  # Column 2 = Password
        return True

    except Exception as e:
        st.error(f"Error changing password: {str(e)}")
        return False


# =======================================================
# LOGIN UI
# =======================================================
def render_login():
    """Render clean minimal login page"""
    
    bg_url = "https://raw.githubusercontent.com/sumiranbhatnagar/placementagency_v3/main/background.png"
    logo_url = "https://raw.githubusercontent.com/sumiranbhatnagar/placementagency_v3/main/placifylogo.png"
    
    # ===== CSS STYLING =====
    st.markdown(f"""
    <style>
    /* ===== GOOGLE FONTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');
    
    /* ===== HIDE STREAMLIT DEFAULTS ===== */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    [data-testid="stSidebar"] {{display: none !important;}}
    [data-testid="stHeader"] {{display: none !important;}}
    .stDeployButton {{display: none !important;}}
    
    /* ===== BACKGROUND IMAGE ===== */
    .stApp {{
        background-image: url("{bg_url}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        min-height: 100vh;
        font-family: 'Inter', sans-serif;
    }}
    
    /* ===== CENTER CONTENT ===== */
    .main .block-container {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 1rem;
        max-width: 450px !important;
        margin: 0 auto;
    }}
    
    /* ===== WHITE LOGIN CARD ===== */
    [data-testid="stForm"] {{
        background: #ffffff !important;
        border-radius: 16px !important;
        padding: 1.8rem 1.8rem 1.5rem 1.8rem !important;
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.3) !important;
        max-width: 340px !important;
        margin: 0 auto !important;
        border: none !important;
    }}
    
    /* ===== LOGO INSIDE CARD ===== */
    .logo-box {{
        text-align: center;
        margin-bottom: 0.3rem;
    }}
    
    .logo-box img {{
        width: 120px;
        height: auto;
    }}
    
    /* ===== LOGIN TITLE ===== */
    .login-title-box {{
        font-family: 'Montserrat', sans-serif;
        text-align: center;
        color: #333333;
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 1.2rem;
        letter-spacing: 0.5px;
    }}
    
    /* ===== INPUT LABELS ===== */
    .stTextInput > label {{
        font-family: 'Inter', sans-serif !important;
        color: #444444 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }}
    
    /* ===== INPUT FIELDS ===== */
    .stTextInput > div > div > input {{
        font-family: 'Inter', sans-serif !important;
        background: #f9f9f9 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 0.7rem 0.9rem !important;
        font-size: 0.95rem !important;
        color: #333333 !important;
        transition: all 0.2s ease !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{
        color: #aaaaaa !important;
        font-size: 0.9rem !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.1) !important;
        background: #ffffff !important;
    }}
    
    /* ===== CHECKBOX ===== */
    .stCheckbox {{
        margin: 0.3rem 0 !important;
    }}
    
    .stCheckbox label {{
        font-family: 'Inter', sans-serif !important;
        color: #666666 !important;
        font-size: 0.8rem !important;
    }}
    
    /* ===== LOGIN BUTTON ===== */
    .stFormSubmitButton > button {{
        font-family: 'Montserrat', sans-serif !important;
        width: 100% !important;
        background: #4a3470 !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 0.7rem 1.2rem !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.8px !important;
        text-transform: uppercase !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 3px 10px rgba(74, 52, 112, 0.25) !important;
        margin-top: 0.8rem !important;
    }}
    
    .stFormSubmitButton > button:hover {{
        background: #5d4389 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 15px rgba(74, 52, 112, 0.35) !important;
    }}
    
    /* ===== ALERTS ===== */
    .stAlert {{
        font-family: 'Inter', sans-serif !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
    }}
    
    </style>
    """, unsafe_allow_html=True)
    
    # ===== LOGIN FORM =====
    with st.form("login_form", clear_on_submit=False):
        
        # Logo inside card
        st.markdown(f'''
        <div class="logo-box">
            <img src="{logo_url}" alt="Placify">
        </div>
        ''', unsafe_allow_html=True)
        
        # Title inside card
        st.markdown('<div class="login-title-box">Login</div>', unsafe_allow_html=True)
        
        username = st.text_input(
            "Username",
            placeholder="Username",
            key="username_input"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Password",
            key="password_input"
        )
        
        remember_me = st.checkbox("Remember me", value=False)
        
        submitted = st.form_submit_button("LOGIN", use_container_width=True)
        
        if submitted:
            if not username or not password:
                st.error("❌ Please enter both fields")
            else:
                with st.spinner("Verifying..."):
                    user_data = verify_credentials(username, password)
                    
                    if user_data:
                        if user_data.get("status", "Active").lower() != "active":
                            st.error("❌ Account deactivated")
                            log_login_activity(username, "Failed - Deactivated")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.username = user_data["username"]
                            st.session_state.role = user_data["role"]
                            st.session_state.full_name = user_data["full_name"]
                            st.session_state.email = user_data["email"]
                            
                            log_login_activity(username, "Success")
                            st.success(f"✅ Welcome!")
                            st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                        log_login_activity(username, "Failed")


# =======================================================
# CHANGE PASSWORD UI
# =======================================================
def render_change_password():
    """Render change password interface"""
    st.subheader("🔒 Change Password")

    with st.form("change_password_form"):
        st.info(f"Changing password for: **{st.session_state.username}**")

        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        submitted = st.form_submit_button("Update Password")

        if submitted:
            # Verify current password
            user_data = verify_credentials(st.session_state.username, current_password)

            if not user_data:
                st.error("❌ Current password is incorrect")
            elif len(new_password) < 6:
                st.error("❌ New password must be at least 6 characters")
            elif new_password != confirm_password:
                st.error("❌ New passwords do not match")
            else:
                if change_password(st.session_state.username, new_password):
                    st.success("✅ Password changed successfully!")
                    log_login_activity(st.session_state.username, "Password Changed")
                else:
                    st.error("❌ Error changing password")


# =======================================================
# USER MANAGEMENT UI (Admin Only)
# =======================================================
def render_user_management():
    """Render user management interface (Admin only)"""

    if st.session_state.get("role", "").upper() != "ADMIN":
        st.error("❌ Access Denied: Admin privileges required")
        return

    st.subheader("👥 User Management")

    tab1, tab2, tab3 = st.tabs(["View Users", "Add User", "Login Logs"])

    with tab1:
        st.markdown("### 📋 All Users")
        df = get_users_from_sheet()

        if df is not None and not df.empty:
            # Hide password column
            display_df = df.drop(columns=["Password"], errors="ignore")
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No users found")

    with tab2:
        st.markdown("### ➕ Add New User")

        with st.form("add_user_form"):
            col1, col2 = st.columns(2)

            with col1:
                new_username = st.text_input(
                    "Username *", placeholder="e.g., john.doe"
                )
                new_password = st.text_input(
                    "Password *", type="password", placeholder="Min 6 characters"
                )
                role = st.selectbox("Role *", ["ADMIN", "RECRUITER", "VIEWER"])

            with col2:
                full_name = st.text_input(
                    "Full Name *", placeholder="e.g., John Doe"
                )
                email = st.text_input("Email", placeholder="user@example.com")

            submitted = st.form_submit_button("Add User")

            if submitted:
                if not new_username or not new_password or not full_name:
                    st.error("❌ Please fill all required fields")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    if add_new_user(
                        new_username, new_password, role, full_name, email
                    ):
                        st.success(
                            f"✅ User '{new_username}' added successfully!"
                        )
                        log_login_activity(
                            st.session_state.username,
                            f"Added user: {new_username}",
                        )
                        st.rerun()

    with tab3:
        st.markdown("### 📊 Login Activity Logs")
        try:
            client = get_google_sheets_client()
            if client:
                sheet = client.open_by_key(SHEET_ID).worksheet("Login_Logs")
                logs_df = pd.DataFrame(sheet.get_all_records())

                if not logs_df.empty:
                    # Show last 50 logs
                    st.dataframe(
                        logs_df.tail(50).sort_values(
                            "Timestamp", ascending=False
                        ),
                        use_container_width=True,
                    )
                else:
                    st.info("No login logs yet")
        except Exception as e:
            st.error(f"Error loading logs: {str(e)}")


# =======================================================
# LOGOUT FUNCTION
# =======================================================
def logout():
    """Logout user and clear session"""
    username = st.session_state.get("username", "Unknown")
    log_login_activity(username, "Logout")

    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


# =======================================================
# DIRECT RUN (for testing)
# =======================================================
if __name__ == "__main__":
    render_login()




