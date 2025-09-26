import streamlit as st
import os
from auth import authenticate_user, create_user, get_user_role
from admin_dashboard import show_admin_dashboard
from user_interface import show_user_interface
from database import init_database

# Page configuration
st.set_page_config(
    page_title="Lung Cancer Detection System",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Initialize database
    init_database()
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'username' not in st.session_state:
        st.session_state.username = None

    # Main header
    st.title("🫁 Lung Cancer Detection System")
    st.markdown("---")

    # Authentication check
    if not st.session_state.authenticated:
        show_login_page()
    else:
        # Show appropriate interface based on user role
        if st.session_state.user_role == 'admin':
            show_admin_dashboard()
        else:
            show_user_interface()

def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.header("Login / Register")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                login_button = st.form_submit_button("Login")
                
                if login_button:
                    user_data = authenticate_user(username, password)
                    if user_data:
                        st.session_state.authenticated = True
                        st.session_state.user_id = user_data['id']
                        st.session_state.user_role = user_data['role']
                        st.session_state.username = user_data['username']
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Username", key="reg_username")
                new_email = st.text_input("Email", key="reg_email")
                new_password = st.text_input("Password", type="password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
                role = st.selectbox("Role", ["user", "admin"], key="reg_role")
                register_button = st.form_submit_button("Register")
                
                if register_button:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long")
                    else:
                        success = create_user(new_username, new_email, new_password, role)
                        if success:
                            st.success("Registration successful! Please login.")
                        else:
                            st.error("Registration failed. Username or email may already exist.")

    # Logout button in sidebar if authenticated
    if st.session_state.authenticated:
        with st.sidebar:
            st.write(f"Welcome, {st.session_state.username}!")
            st.write(f"Role: {st.session_state.user_role}")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.user_id = None
                st.session_state.user_role = None
                st.session_state.username = None
                st.rerun()

if __name__ == "__main__":
    main()
