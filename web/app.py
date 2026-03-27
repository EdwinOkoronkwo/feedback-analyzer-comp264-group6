import sys
import os
import streamlit as st

# 1. Path Setup
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from chalicelib.utils.factory_selector import FactorySelector
from web.components.analytics_view import AnalyticsView
from web.components.auth_ui import AuthUI
from web.components.admin_ui import AdminUI
from web.components.analyzer_ui import AnalyzerUI
from web.components.history_ui import HistoryUI

# 2. Strategy Selection
FactoryClass, mode_label = FactorySelector.get_factory()

st.set_page_config(page_title="AI Sentinel", page_icon="🛡️", layout="wide")

# 3. Infrastructure Initialization (Run once)

with st.sidebar:
    st.title("🛡️ AI Sentinel")
    # 1. Get current saved mode or default to LOCAL
    current_env = os.getenv("ENV_MODE", "LOCAL")
    
    # 2. Manual toggle
    new_mode = st.radio(
        "Environment Mode",
        options=["LOCAL", "AWS"],
        index=0 if current_env == "LOCAL" else 1,
        help="Switch between VMware Local and AWS Cloud infrastructure."
    )

    # 3. IF MODE CHANGED: Clear session and rerun to force re-initialization
    if new_mode != current_env:
        os.environ["ENV_MODE"] = new_mode
        st.session_state.clear() # Wipe the old bridge/user_service
        st.rerun()

# 2. Strategy Selection (Now reactive to the Sidebar!)
FactoryClass, mode_label = FactorySelector.get_factory()

st.set_page_config(page_title="AI Sentinel", page_icon="🛡️", layout="wide")

# 3. Infrastructure Initialization
if 'initialized' not in st.session_state:
    try:
        # Rebuilds the logic for the chosen mode (VMware vs AWS)
        bridge, user_service = FactoryClass.create_pipeline_and_auth()
        
        if "LOCAL" in mode_label:
            analytics_provider = FactoryClass._build_analytics(logger=None)
        else:
            analytics_provider, _ = FactoryClass.get_analytics_layer()

        st.session_state.bridge = bridge  
        st.session_state.user_service = user_service 
        st.session_state.analytics_provider = analytics_provider
        st.session_state.initialized = True
        
    except Exception as e:
        st.error(f"🚨 Infrastructure Failure ({mode_label})")
        st.exception(e)
        st.stop()

# 4. Auth Logic (Requires the newly initialized user_service)
auth = AuthUI(st.session_state.user_service)
auth.render()

if st.session_state.get('authenticated'):
    user = st.session_state.user
    
    # Sidebar Navigation
    st.sidebar.title(f"🛡️ AI Sentinel")
    st.sidebar.info(f"Mode: {mode_label}")
    
    nav_options = ["New Analysis", "My History"]
    if getattr(user, 'role', 'user') == "admin":
        nav_options.extend(["Analytics Dashboard", "System Admin"])
        
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    choice = st.sidebar.radio("Navigation", nav_options)

    # 5. Routing
    if choice == "New Analysis":
        AnalyzerUI().render(st.session_state.bridge, user)
        
    elif choice == "My History":
        HistoryUI().render(st.session_state.bridge, user)

    elif choice == "Analytics Dashboard":
        AnalyticsView().render(provider=st.session_state.analytics_provider)
        
    elif choice == "System Admin":
        AdminUI().render(st.session_state.user_service)