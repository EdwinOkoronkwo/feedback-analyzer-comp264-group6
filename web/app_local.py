import sys
import os
import streamlit as st
import boto3

# Adds the parent directory (feedback_analyzer) to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chalicelib.local.local_factory import LocalPipelineFactory as PipelineFactory

# Modular UI Components
from web.components.analytics_view import AnalyticsView
from web.session_manager import SessionManager
from web.components.auth_ui import AuthUI
from web.components.admin_ui import AdminUI

# 🎯 POINT TO LOCAL VERSIONS
from web.components.local_analyzer_ui import LocalAnalyzerUI as AnalyzerUI
from web.components.local_history_ui import LocalHistoryUI as HistoryUI

# --- 1. Initialize Local Infrastructure with Debugging ---
if 'initialized' not in st.session_state:
    try:
        # Check if DynamoDB Local is actually up (port 8000)
        test_client = boto3.client(
            'dynamodb', 
            endpoint_url='http://localhost:8000', 
            region_name='us-east-1',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
        test_client.list_tables() 
        
        pipeline, user_manager = PipelineFactory.create_local_stack()
        
        st.session_state.pipeline = pipeline
        st.session_state.user_manager = user_manager
        st.session_state.initialized = True
        st.session_state.authenticated = False
        st.toast("✅ VMware Local Infrastructure Linked")
        
    except Exception as e:
        st.error("🚨 Local DB Failure. Ensure DynamoDB Local is running on port 8000.")
        st.exception(e) 
        st.stop() 

# --- 2. Sidebar Auth & Navigation ---
st.sidebar.title("🛡️ AI Sentinel (LOCAL)")
st.sidebar.info("Running in VMware Local Mode")

if st.session_state.get('authenticated'):
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Render Login
auth = AuthUI(st.session_state.user_manager)
auth.render()

# --- 3. Main Content Router ---
if st.session_state.get('authenticated'):
    user = st.session_state.user
    
    nav_options = ["New Analysis", "My History"]
    if getattr(user, 'role', 'user') == "admin":
        nav_options.extend(["Analytics Dashboard", "System Admin"])
        
    choice = st.sidebar.radio("Navigation", nav_options)

    if choice == "New Analysis":
        # Now uses the synchronous LocalAnalyzerUI
        AnalyzerUI().render(st.session_state.pipeline, user)
        
    elif choice == "My History":
        # Now uses the LocalHistoryUI (file-system based audio)
        HistoryUI().render(st.session_state.pipeline, user)

    elif choice == "Analytics Dashboard":
        analytics_provider = PipelineFactory.get_local_analytics()
        AnalyticsView().render(provider=analytics_provider)
        
    elif choice == "System Admin":
        AdminUI().render(st.session_state.user_manager)