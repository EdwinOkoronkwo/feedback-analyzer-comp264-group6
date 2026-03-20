import os
import streamlit as st

class ResultsViewer:
    """
    The 'Deep Dive' component. 
    Handles variable alignment between Mistral (Local) and the UI.
    """
    def render(self, result):
        st.subheader("🔍 Deep Dive Analysis")
        
        # 🎯 UNIVERSAL ALIGNMENT: Check every possible name for the data
        # Handles both result.summary and result['summary']
        def get_val(obj, attr_list, default="N/A"):
            for attr in attr_list:
                val = getattr(obj, attr, None) if not isinstance(obj, dict) else obj.get(attr)
                if val: return val
            return default

        summary_txt = get_val(result, ['summary', 'content', 'ai_summary'])
        sentiment = str(get_val(result, ['sentiment', 'label'], 'NEUTRAL')).upper()
        raw_text = get_val(result, ['text', 'raw_text', 'text_content'])
        translated = get_val(result, ['translated_text', 'en_text'], "Translation matches source.")

        # UI LAYOUT
        tab1, tab2, tab3 = st.tabs(["📄 Source Text", "🌍 Translation", "🤖 AI Insights"])

        with tab1:
            st.info("Raw text extracted via Tesseract/Local OCR")
            st.write(raw_text)

        with tab2:
            st.success("English Translation")
            st.write(translated)

        with tab3:
            # Visual Sentiment Indicator
            if sentiment == "POSITIVE":
                st.success(f"😊 Sentiment: {sentiment}")
            elif sentiment == "NEGATIVE":
                st.error(f"😡 Sentiment: {sentiment}")
            else:
                st.info(f"😐 Sentiment: {sentiment}")

            st.markdown("### 🤖 AI Summary")
            st.write(summary_txt)
            st.caption("Powered by Mistral-Medium via Local Flask Bridge")

        # Audio Section
        audio_path = get_val(result, ['audio_path', 'local_audio'], None)
        if audio_path and audio_path != "N/A":
            st.divider()
            st.subheader("🔊 Audio Summary")
            if os.path.exists(str(audio_path)):
                st.audio(str(audio_path))
            else:
                st.warning("Audio file generated but not found on local disk.")