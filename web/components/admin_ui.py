import streamlit as st

class AdminUI:
    def render(self, user_manager):
        st.header("👥 User Management Dashboard")
        
        # Pull all users via repository
        # This returns a list of UserModel objects
        users = user_manager.get_all_users()
        
        # List View
        st.subheader("Registered Users")
        for u in users:
            # FIX: Access attributes with . instead of ['']
            with st.expander(f"👤 {u.username} - Role: {u.role}"):
                # Detailed View
                col1, col2 = st.columns(2)
                with col1:
                    # Note: If your UserModel uses 'username' as the unique ID:
                    st.write(f"**Username:** `{u.username}`")
                    # Make sure these attributes exist in your UserModel class!
                    if hasattr(u, 'created_at'):
                        st.write(f"**Created:** {u.created_at}")
                with col2:
                    st.write("**Security Hash (Bcrypt):**")
                    # Dot notation for password_hash
                    st.code(u.password_hash, language=None)