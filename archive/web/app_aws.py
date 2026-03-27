import sys
import os

# Get the directory that contains the 'web' and 'chalicelib' folders
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add that root to Python's search path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# NOW your existing imports will work
from chalicelib.utils.factory import PipelineFactory

import streamlit as st
import boto3
import os


# Modular UI Components (These should be shared/reusable)
from chalicelib.utils.factory import PipelineFactory
from web.components.analytics_view import AnalyticsView
from web.components.auth_ui import AuthUI
from web.components.analyzer_ui import AnalyzerUI
from web.components.history_ui import HistoryUI
from web.components.admin_ui import AdminUI

# --- 1. Initialize AWS Infrastructure ---
if 'initialized' not in st.session_state:
    try:
        # No endpoint_url here! Boto3 will use IAM Roles in AWS
        pipeline, user_manager = PipelineFactory.create_pipeline_and_auth()
        analytics_provider, _ = PipelineFactory.get_analytics_layer()
        
        st.session_state.pipeline = pipeline
        st.session_state.user_manager = user_manager
        st.session_state.analytics_provider = analytics_provider
        st.session_state.initialized = True
        st.session_state.authenticated = False
        st.toast("☁️ AWS Cloud Infrastructure Linked")
    except Exception as e:
        st.error(f"🚨 Cloud Connection Failure: {str(e)}")
        st.stop() 

# --- 2. Sidebar Auth & Navigation ---
st.sidebar.title("🛡️ AI Sentinel (PROD)")

if not st.session_state.get('authenticated'):
    AuthUI(st.session_state.user_manager).render()
    st.stop() 
else:
    # LOGGED IN logic
    user = st.session_state.user
    st.sidebar.success(f"Connected: {user.username}")

    nav_options = ["New Analysis", "My History"]
    if getattr(user, 'role', 'user') == "admin":
        nav_options.extend(["Analytics Dashboard", "System Admin"])
        
    choice = st.sidebar.radio("Navigation", nav_options)

    # --- 3. Cloud Content Router ---
    if choice == "New Analysis":
        # In AWS, AnalyzerUI uses the S3 + Rekognition/Textract flow
        AnalyzerUI().render(st.session_state.pipeline, user)
        
    elif choice == "My History":
        HistoryUI().render(st.session_state.pipeline, user)

    elif choice == "Analytics Dashboard":
        # Uses the Athena Provider
        AnalyticsView().render(provider=st.session_state.analytics_provider)
        
    elif choice == "System Admin":
        AdminUI().render(st.session_state.user_manager)



