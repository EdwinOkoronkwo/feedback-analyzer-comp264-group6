import streamlit as st

class AuthUI:
    def __init__(self, user_manager):
        self.user_manager = user_manager

    def render(self):
        st.sidebar.title("🔐 Authentication")
        mode = st.sidebar.selectbox("Choose Mode", ["Login", "Register"])

        if mode == "Register":
            self._render_registration()
        else:
            self._render_login()

    def _render_login(self):
        with st.sidebar.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In")

            if submit:
                user = self.user_manager.login(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.authenticated = True
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    def _render_registration(self):
        with st.sidebar.form("reg_form"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            role = st.selectbox("Role", ["user", "admin"]) # In prod, this would be restricted
            submit = st.form_submit_button("Create Account")

            if submit:
                if self.user_manager.register(new_user, new_pass, role):
                    st.success("Account created! Please login.")
                else:
                    st.error("Username already exists.")