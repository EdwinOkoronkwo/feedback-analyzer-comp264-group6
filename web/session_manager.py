import streamlit as st

from chalicelib.local.local_factory import LocalPipelineFactory
# 1. Update the import to match your factory file

class SessionManager:
    @staticmethod
    def initialize():
        # Core Auth States
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "user" not in st.session_state:
            st.session_state.user = None
            
        # Infrastructure Initialization
        if "pipeline" not in st.session_state or "user_manager" not in st.session_state:
            # 2. CHANGE THIS LINE to use your real method
            pipeline, user_service = LocalPipelineFactory.create_local_stack()
            
            # Store them in session state
            st.session_state.pipeline = pipeline
            # Note: We store user_service as user_manager to keep your UI logic working
            st.session_state.user_manager = user_service
    @staticmethod
    def login_user(user_model):
        st.session_state.authenticated = True
        st.session_state.user = user_model

    @staticmethod
    def logout_user():
        # Clear sensitive state
        st.session_state.authenticated = False
        st.session_state.user = None
        # Use rerun to clear the UI immediately
        st.rerun()