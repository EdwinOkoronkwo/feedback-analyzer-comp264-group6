import streamlit as st

class SidebarComponent:
    def render(self):
        with st.sidebar:
            st.header("📥 Data Ingestion")
            text = st.text_area("Feedback Text", height=200)
            analyze_btn = st.button("🚀 Process Pipeline", use_container_width=True)
        return text, analyze_btn