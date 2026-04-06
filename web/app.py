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
# New Import
from web.components.dataset_ui import DatasetUI 

# 2. Page Configuration (Must be the first Streamlit command)
st.set_page_config(page_title="AI Sentinel", page_icon="🛡️", layout="wide")

# 3. Sidebar Infrastructure Toggle
with st.sidebar:
    st.title("🛡️ AI Sentinel")
    current_env = os.getenv("ENV_MODE", "LOCAL")
    
    new_mode = st.radio(
        "Environment Mode",
        options=["LOCAL", "AWS"],
        index=0 if current_env == "LOCAL" else 1,
        help="Switch between VMware Local and AWS Cloud infrastructure."
    )

    if new_mode != current_env:
        os.environ["ENV_MODE"] = new_mode
        st.session_state.clear() 
        st.rerun()

# 4. Strategy Selection
FactoryClass, mode_label = FactorySelector.get_factory()


# 5. Infrastructure Initialization
if 'initialized' not in st.session_state:
    try:
        bridge, user_service = FactoryClass.create_pipeline_and_auth()
        
        # 🎯 NEW: Logic to get both layers depending on Mode
        if "LOCAL" in mode_label:
            analytics_provider = FactoryClass._build_analytics(logger=None)
            # Add local summaries provider if you have one, else None
            summaries_provider = None 
        else:
            # AWS Mode
            analytics_provider, _ = FactoryClass.get_analytics_layer()
            # Fetch the new layer we added to the Factory
            summaries_provider = FactoryClass.get_summaries_layer()

        st.session_state.bridge = bridge  
        st.session_state.user_service = user_service 
        st.session_state.analytics_provider = analytics_provider
        # 🎯 Store the summaries provider
        st.session_state.summaries_provider = summaries_provider
        st.session_state.initialized = True
        
    except Exception as e:
        st.error(f"🚨 Infrastructure Failure ({mode_label})")
        st.exception(e)
        st.stop()

# 6. Auth Logic
auth = AuthUI(st.session_state.user_service)
auth.render()

if st.session_state.get('authenticated'):
    user = st.session_state.user
    
    # Sidebar Navigation
    st.sidebar.info(f"Mode: {mode_label}")
    
    # Add "Dataset Ingestion" to the navigation
    nav_options = ["New Analysis", "Dataset Ingestion", "My History"]
    
    if getattr(user, 'role', 'user') == "admin":
        nav_options.extend(["Analytics Dashboard", "System Admin"])
        
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    choice = st.sidebar.radio("Navigation", nav_options)

    # 7. Routing Logic
    if choice == "New Analysis":
        AnalyzerUI().render(st.session_state.bridge, user)
        
    elif choice == "Dataset Ingestion":
        # Render the new Kaggle/MNIST UI
        DatasetUI().render(st.session_state.bridge, user)
        
    # elif choice == "My History":
    #     HistoryUI().render(st.session_state.bridge, user)

    elif choice == "Analytics Dashboard":
        # Pass BOTH providers to the view
        AnalyticsView().render(
            provider=st.session_state.analytics_provider,
            summaries_provider=st.session_state.summaries_provider
        )
        
    # elif choice == "System Admin":
    #     AdminUI().render(st.session_state.user_service)