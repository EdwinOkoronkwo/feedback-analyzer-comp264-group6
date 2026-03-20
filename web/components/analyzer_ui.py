import streamlit as st
import uuid

class AnalyzerUI:
    def __init__(self):
        self.form = AnalysisForm()
        self.tracker = PipelineTracker()
        self.results = ResultsDisplay()
        self.terminal = LogTerminal() # <--- New Subclass

    def render(self, pipeline, user):
        st.header("☁️ AWS Cloud Analysis")
        payload = self.form.render(user)
        
        if payload:
            progress_bar = st.progress(0)
            status_text = st.empty()
            tracker_container = st.empty()
            terminal_container = st.empty() # <--- Placeholder for the log
            
            final_results = {}

            with st.spinner("AWS Workers are processing..."):
                for progress, info in pipeline.run(payload):
                    if isinstance(info, str):
                        # Update the text above the progress bar
                        status_text.markdown(f"**Status:** {info}")
                        progress_bar.progress(progress)
                    else:
                        # Update Emojis
                        with tracker_container.container():
                            self.tracker.render(info.get("summary", {}))
                        
                        # Update the Log Terminal below
                        with terminal_container.container():
                            self.terminal.render(info.get("summary", {}))
                        
                        final_results = info

            if final_results.get("status") == "COMPLETE":
                self.results.render(final_results)
            else:
                st.error(f"❌ Pipeline timed out (ID: {payload['feedback_id']})")

class LogTerminal:
    """Renders a code-block style terminal showing AWS event timestamps"""
    def render(self, db_row):
        st.write("---")
        st.caption("🖥️ AWS CloudWatch Event Stream")
        
        # Mapping DB keys to human-readable log messages
        log_map = [
            ("timestamp", "INIT", "Pipeline record created in DynamoDB"),
            ("master", "MASTER", "S3 Event triggered Orchestrator"),
            ("text", "INPUT", "Data payload extracted and validated"),
            ("sentiment", "ANALYSIS", "Comprehend/Mistral processing started"),
            ("summary", "AI_GEN", "Summary generated and saved"),
            ("audio_path", "POLY", "Speech synthesis complete")
        ]
        
        terminal_lines = []
        for key, tag, msg in log_map:
            if key in db_row and db_row[key] not in [None, "N/A"]:
                # Use the current time or the DB timestamp if you have it
                ts = db_row.get('timestamp', '00:00:00')[-8:] # Show last few digits of TS
                terminal_lines.append(f"[{ts}] [{tag}] {msg} ... ✅")
        
        # Render as a dark terminal block
        log_content = "\n".join(terminal_lines)
        st.code(log_content or "Waiting for AWS handshake...", language="bash")

class AnalysisForm:
    """Handles Text and Image Inputs"""
    def render(self, user):
        with st.container(border=True):
            st.info("Directly linked to S3 & DynamoDB")
            text_input = st.text_area("Feedback Text", placeholder="Describe the feedback...")
            uploaded_file = st.file_uploader("📸 Image", type=['jpg', 'png', 'jpeg'])
            
            if uploaded_file:
                st.image(uploaded_file, caption=f"File: {uploaded_file.name}", use_container_width=True)

            if st.button("🚀 Run Cloud Pipeline", use_container_width=True):
                user_id = getattr(user, 'username', 'anonymous')
                unique_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
                
                payload = {
                    "feedback_id": unique_id,
                    "text": text_input,
                    "user_id": user_id,
                    "image_data": None
                }
                
                if uploaded_file:
                    payload["image_data"] = {
                        "name": uploaded_file.name,
                        "bytes": uploaded_file.getvalue(),
                        "type": uploaded_file.type
                    }
                return payload
        return None

class PipelineTracker:
    def render(self, db_row):
        st.write("### 📡 Live Pipeline Status")
        
        steps = [
            {"key": "master", "label": "Master", "emoji": "🎮"},
            {"key": "text", "label": "OCR/Text", "emoji": "📸"},
            {"key": "sentiment", "label": "Analysis", "emoji": "🧠"},
            {"key": "summary", "label": "Summary", "emoji": "🤖"},
            {"key": "audio_path", "label": "Speech", "emoji": "🎙️"}
        ]
        
        cols = st.columns(len(steps))
        
        for i, step in enumerate(steps):
            with cols[i]:
                is_done = step['key'] in db_row and db_row[step['key']] not in [None, "N/A"]
                
                if is_done:
                    # ✅ Completed Step
                    st.markdown(f"<h2 style='text-align: center;'>{step['emoji']}</h2>", unsafe_allow_html=True)
                    st.success(step['label'])
                elif i > 0 and steps[i-1]['key'] in db_row:
                    # 🟡 Current Active Step (Pulse)
                    st.markdown(f"<h2 style='text-align: center; opacity: 0.5;'>{step['emoji']}</h2>", unsafe_allow_html=True)
                    st.warning(f"**{step['label']}**")
                    st.caption("⚡ Processing...")
                else:
                    # ⚪ Pending Step
                    st.markdown(f"<h2 style='text-align: center; opacity: 0.2;'>{step['emoji']}</h2>", unsafe_allow_html=True)
                    st.info(step['label'])

class ResultsDisplay:
    """Handles Final Result Presentation"""
    def render(self, final_results):
        st.success("✅ Cloud Analysis Complete!")
        db_row = final_results.get("summary", {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Sentiment", str(db_row.get('sentiment', 'N/A')).upper())
            st.write("**🌐 Translated/Input Text:**")
            st.info(db_row.get('translated_text') or db_row.get('text', 'N/A'))
        
        with col2:
            st.write("**📝 AI Summary (Mistral):**")
            st.success(db_row.get('summary', 'Processing...'))
            
            if db_row.get('audio_path'):
                st.write("**🎙️ Voice Synthesis:**")
                st.audio(db_row.get('audio_path'))

        with st.expander("🔍 View Technical Logs"):
            st.json(final_results)


class LogTerminal:
    """Renders a code-block style terminal showing AWS event timestamps"""
    def render(self, db_row):
        st.write("---")
        st.caption("🖥️ AWS CloudWatch Event Stream")
        
        # Mapping DB keys to human-readable log messages
        log_map = [
            ("timestamp", "INIT", "Pipeline record created in DynamoDB"),
            ("master", "MASTER", "S3 Event triggered Orchestrator"),
            ("text", "INPUT", "Data payload extracted and validated"),
            ("sentiment", "ANALYSIS", "Comprehend/Mistral processing started"),
            ("summary", "AI_GEN", "Summary generated and saved"),
            ("audio_path", "POLY", "Speech synthesis complete")
        ]
        
        terminal_lines = []
        for key, tag, msg in log_map:
            if key in db_row and db_row[key] not in [None, "N/A"]:
                # Use the current time or the DB timestamp if you have it
                ts = db_row.get('timestamp', '00:00:00')[-8:] # Show last few digits of TS
                terminal_lines.append(f"[{ts}] [{tag}] {msg} ... ✅")
        
        # Render as a dark terminal block
        log_content = "\n".join(terminal_lines)
        st.code(log_content or "Waiting for AWS handshake...", language="bash")