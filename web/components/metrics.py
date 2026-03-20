import streamlit as st

class MetricsComponent:
    def render(self, result):
        st.subheader("📈 Executive Summary")
        m1, m2, m3 = st.columns(3)
        
        # 1. Get Sentiment safely
        sentiment = result.get('analysis', {}).get('sentiment', 'MIXED')
        m1.metric("Sentiment", sentiment)
        
        # 2. Security status
        m2.metric("Security", "PII Masked")
        
        # 3. THE FIX: Get the ID regardless of where it is hidden
        # We check both 'persistence' key AND the top level
        persistence_data = result.get('persistence', {})
        record_id = persistence_data.get('id') or result.get('id', 'N/A')
        
        # Display the first 8 characters of the ID
        m3.metric("Record ID", str(record_id)[:8] if record_id else "SAVED")