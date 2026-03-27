import streamlit as st
import pandas as pd
import os


class LocalHistoryUI:
    def render(self, pipeline, user):
        st.header("📜 Local History")
        
        # Pull directly from your LocalPipelineFactory's persistence layer
        items = pipeline.get_user_feedback(user.username)
        
        if not items:
            st.info("No local records found.")
            return

        for item in items:
            with st.expander(f"Record: {item.get('feedback_id')}"):
                st.write(f"**Sentiment:** {item.get('sentiment')}")
                st.write(f"**Summary:** {item.get('summary')}")
                
                # Simple Local Path Audio
                audio_path = item.get('audio_path')
                if audio_path and os.path.exists(audio_path):
                    st.audio(audio_path)