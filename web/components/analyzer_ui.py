import streamlit as st
import uuid
import os

from implementations.shared.pipeline_validator import PipelineValidator

class AnalyzerUI:
    def __init__(self):
        self.form = AnalysisForm()
        self.tracker = PipelineTracker()
        self.results = ResultsDisplay()
        self.terminal = LogTerminal()
        self.validator = PipelineValidator() # Integrated Validator

    def render(self, pipeline, user):
        # 1. Determine the current mode
        mode = os.getenv("ENV_MODE", "LOCAL").upper()
        
        # 2. Set dynamic labels
        header_text = "💻 VMware Local Analysis" if mode == "LOCAL" else "☁️ AWS Cloud Analysis"
        spinner_text = "Local Workers are processing..." if mode == "LOCAL" else "AWS Workers are processing..."
        
        # 3. Use the dynamic header
        st.header(header_text)
        
        # Pass the validator to the form for real-time checks
        payload = self.form.render(user, self.validator)
        
        if payload:
            progress_bar = st.progress(0)
            status_text = st.empty()
            tracker_container = st.empty()
            terminal_container = st.empty()
            
            final_data = None

            with st.spinner(spinner_text):
                for progress, info in pipeline.trigger_pipeline(payload):
                    if isinstance(info, str):
                        status_text.markdown(f"**Status:** {info}")
                        progress_bar.progress(min(progress, 1.0))
                    elif isinstance(info, dict):
                        final_data = info 
                        display_data = info.get("summary") if isinstance(info.get("summary"), dict) else info
                        
                        with tracker_container.container():
                            self.tracker.render(display_data)
                        with terminal_container.container():
                            self.terminal.render(display_data)

            if final_data:
                has_summary = "summary" in final_data or (isinstance(final_data.get("summary"), str))
                is_complete = final_data.get("status") in ["COMPLETE", "SUMMARIZED", "SUCCESS"]
                
                if has_summary or is_complete:
                    status_text.success("✅ Analysis Complete!")
                    progress_bar.progress(1.0)
                    self.results.render(final_data)
                else:
                    st.warning(f"⚠️ Pipeline reached end of loop with status: {final_data.get('status', 'UNKNOWN')}")
                    with st.expander("Inspect Raw Response"):
                        st.json(final_data)

class LogTerminal:
    def render(self, db_row):
        st.write("---")
        st.caption("🖥️ AWS CloudWatch Event Stream")
        log_map = [
            ("feedback_id", "INIT", "Pipeline record created in DynamoDB"),
            ("status", "MASTER", "S3 Event triggered Orchestrator"),
            ("translated_text", "INPUT", "Data payload extracted and validated"),
            ("sentiment", "ANALYSIS", "AI processing started"),
            ("summary", "AI_GEN", "Summary generated and saved"),
            ("audio_path", "POLY", "Speech synthesis complete")
        ]
        terminal_lines = []
        for key, tag, msg in log_map:
            if key in db_row and db_row[key] not in [None, "N/A", ""]:
                raw_ts = str(db_row.get('timestamp', '00:00:00'))
                ts = raw_ts[-8:] 
                terminal_lines.append(f"[{ts}] [{tag}] {msg} ... ✅")
        log_content = "\n".join(terminal_lines)
        st.code(log_content or "Waiting for AWS handshake...", language="bash")

class AnalysisForm:
    def render(self, user, validator):
        with st.sidebar:
            st.header("⚙️ System Settings")
            app_mode = st.radio(
                "Execution Environment",
                options=["LOCAL", "AWS"],
                index=0 if os.getenv("ENV_MODE", "LOCAL") == "LOCAL" else 1
            )
            os.environ["ENV_MODE"] = app_mode
            st.divider()
            
            # Show Constraints in Sidebar for visibility
            st.info(f"📏 **Limits**\n- Text: {validator.LIMITS['max_chars']} chars\n- Image: 10MB")

        with st.container(border=True):
            UPLOAD_DIR = "temp_uploads"
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            
            # Real-time character counter logic
            text_input = st.text_area("Feedback Text", placeholder="Describe the feedback...")
            char_count = len(text_input)
            if char_count > validator.LIMITS['max_chars']:
                st.error(f"⚠️ Text too long: {char_count}/{validator.LIMITS['max_chars']} characters.")
            elif char_count > 0:
                st.caption(f"Characters: {char_count}/{validator.LIMITS['max_chars']}")

            uploaded_file = st.file_uploader("📸 Image", type=['jpg', 'png', 'jpeg', 'pdf', 'tiff'])
            
            if uploaded_file:
                # Immediate File Size Check
                is_valid_img, img_msg = validator.validate_image_spec(uploaded_file)
                if not is_valid_img:
                    st.error(f"❌ {img_msg}")
                else:
                    st.image(uploaded_file, caption=f"Valid File: {uploaded_file.name}", width=300)

            if st.button("🚀 Run Analysis Pipeline", width='stretch'):
                # 1. Validation Logic
                if not text_input.strip() and not uploaded_file:
                    st.error("⚠️ Please provide text or an image.")
                    return None

                # Validate Text
                if text_input.strip():
                    is_valid_txt, txt_msg = validator.validate_text_length(text_input)
                    if not is_valid_txt:
                        st.error(txt_msg)
                        return None
                
                # Validate Image again on button click (Safety)
                if uploaded_file:
                    is_valid_img, img_msg = validator.validate_image_spec(uploaded_file)
                    if not is_valid_img:
                        st.error(img_msg)
                        return None

                # 2. Proceed with Payload Generation
                user_id = getattr(user, 'username', 'anonymous')
                unique_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
                
                payload = {
                    "feedback_id": unique_id,
                    "text": text_input,
                    "user_id": user_id,
                    "status": "PROCESSING",
                    "source_type": "TEXT",
                    "file_path": None,
                    "image_data": None
                }
                
                if uploaded_file:
                    extension = uploaded_file.name.split('.')[-1]
                    consistent_filename = f"{unique_id}.{extension}"
                    file_bytes = uploaded_file.getvalue()
                    file_path = os.path.join(UPLOAD_DIR, consistent_filename)
                    
                    with open(file_path, "wb") as f:
                        f.write(file_bytes)
                    
                    payload["source_type"] = "IMAGE"
                    payload["file_path"] = os.path.abspath(file_path)
                    payload["image_data"] = {
                        "name": consistent_filename,
                        "bytes": file_bytes
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
                    st.markdown(f"<h2 style='text-align: center;'>{step['emoji']}</h2>", unsafe_allow_html=True)
                    st.success(step['label'])
                elif i > 0 and steps[i-1]['key'] in db_row:
                    st.markdown(f"<h2 style='text-align: center; opacity: 0.5;'>{step['emoji']}</h2>", unsafe_allow_html=True)
                    st.warning(f"**{step['label']}**")
                    st.caption("⚡ Processing...")
                else:
                    st.markdown(f"<h2 style='text-align: center; opacity: 0.2;'>{step['emoji']}</h2>", unsafe_allow_html=True)
                    st.info(step['label'])

class ResultsDisplay:
    def render(self, final_results):
        is_local = os.getenv("ENV_MODE", "LOCAL").upper() == "LOCAL"
        msg = "💻 VMware Local Analysis Complete!" if is_local else "☁️ AWS Cloud Analysis Complete!"
        st.success(msg)
        db_row = final_results.get("summary") 
        if not db_row or not isinstance(db_row, dict):
            db_row = final_results 

        col1, col2 = st.columns(2)
        with col1:
            sentiment = db_row.get('sentiment', 'N/A')
            st.metric("Sentiment", str(sentiment).upper())
            st.write("**🌐 Input Text:**")
            input_text = db_row.get('translated_text') or db_row.get('raw_text') or db_row.get('text', 'N/A')
            st.info(input_text)
        
        with col2:
            st.write("**📝 AI Summary (Mistral):**")
            summary_text = db_row.get('summary') or db_row.get('content', 'Summary unavailable')
            st.success(summary_text)
            if db_row.get('audio_path'):
                st.write("**🎙️ Voice Synthesis:**")
                st.audio(db_row.get('audio_path'))

        with st.expander("🔍 View Technical Logs"):
            st.json(final_results)