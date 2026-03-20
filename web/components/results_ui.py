import streamlit as st
import streamlit as st

import streamlit as st

class ResultsUI:
    def render(self, result):
        st.subheader("📈 Executive Summary")
        m1, m2, m3 = st.columns(3)
        
        summary_data = result.get('summary', {})
        
        # Use .get() to avoid the dot notation crash
        m1.metric("Sentiment", summary_data.get('sentiment', "MIXED"))
        m2.metric("Security", "PII Masked")
        
        # Pull ID from the OCR data or use a fallback
        record_id = result.get('ocr', {}).get('feedback_id', "SAVED")
        m3.metric("Record ID", str(record_id)[:8])

# class ResultsUI:
#     def render(self, result):
#         # 1. Extract the nested data from the dictionary
#         # The pipeline yields a dict where result['ocr'], result['translation'], etc. exist
#         ocr_data = result.get('ocr', {})
#         trans_data = result.get('translation', {})
#         summary_data = result.get('summary', {})

#         # --- PART 1: EXECUTIVE SUMMARY ---
#         st.subheader("📈 Executive Summary")
#         m1, m2, m3 = st.columns(3)
        
#         # Get sentiment from the summary worker's output
#         sentiment_val = summary_data.get('sentiment', "MIXED")
#         m1.metric("Sentiment", sentiment_val)
#         m2.metric("Security", "PII Masked")
        
#         # Use the feedback_id (filename) as the Record ID
#         # Since 'result' is the dict, we look for the ID inside the sub-results
#         record_id = ocr_data.get('feedback_id', "SAVED")
#         m3.metric("Record ID", str(record_id)[:8])

#         # --- PART 2: DEEP DIVE ---
#         st.subheader("🔍 Deep Dive Analysis")
#         tab1, tab2, tab3 = st.tabs(["📄 Original", "🛡️ Sanitized", "🌍 Translation"])
        
#         with tab1:
#             st.info("Original Input (Extracted via OCR)")
#             # In the cloud model, OCR 'text' is the original source
#             st.write(ocr_data.get('text', "No text detected."))
            
#         with tab2:
#             st.warning("PII Filtered for Security Logs")
#             # If your Sanitizer ran locally before upload, we show that, 
#             # otherwise we show a placeholder
#             st.code(result.get('safe_text', "Secure log generated..."), language=None)
            
#         with tab3:
#             st.success("English Translation")
#             st.write(trans_data.get('translated_text', "No translation available."))