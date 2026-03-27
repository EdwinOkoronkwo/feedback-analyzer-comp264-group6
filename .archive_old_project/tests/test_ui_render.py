from datetime import datetime
import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from chalicelib.models.models import FeedbackModel
from chalicelib.providers.mistral_provider import MistralAnalyzer
from chalicelib.utils.logger import FileAuditLogger

def run_ui_real_ai_test():
    st.set_page_config(page_title="Real AI Integration Test", layout="wide")
    st.title("🚀 Real Mistral AI + UI Integration")

    # 1. Initialize the REAL Analyzer
    logger = FileAuditLogger(name="UIAITest")
    analyzer = MistralAnalyzer(logger)

    # 2. Input from user
    user_input = st.text_area("Enter Feedback to Analyze:", 
                              "The Edmonton server is lagging, please fix the engineering latency.")

    if st.button("Run Real AI Analysis"):
        with st.spinner("🤖 Mistral is thinking..."):
            real_summary = analyzer.summarize(user_input)
            
            # Create a REAL FeedbackModel object instead of a dict
            mock_result = FeedbackModel(
                feedback_id="real-test-001",
                user_id="tester_727d",
                title="UI Integration Test",
                content=real_summary, # This maps to the 'text' or 'content' attribute
                sentiment="NEUTRAL",
                status="COMPLETED",
                timestamp=datetime.now().isoformat(),
                audio_path=None
            )

            st.divider()
            
            # 4. Render using your component
            from web.components.results_viewer import ResultsViewer
            viewer = ResultsViewer()
            viewer.render(mock_result)

if __name__ == "__main__":
    run_ui_real_ai_test()