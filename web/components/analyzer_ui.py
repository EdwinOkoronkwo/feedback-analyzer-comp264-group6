import streamlit as st
import uuid

import os

class AnalyzerUI:
    def __init__(self):
        self.form = AnalysisForm()
        self.tracker = PipelineTracker()
        self.results = ResultsDisplay()
        self.terminal = LogTerminal()

    
    def render(self, pipeline, user):
        # 1. Determine the current mode
        mode = os.getenv("ENV_MODE", "LOCAL").upper()
        
        # 2. Set dynamic labels
        header_text = "💻 VMware Local Analysis" if mode == "LOCAL" else "☁️ AWS Cloud Analysis"
        spinner_text = "Local Workers are processing..." if mode == "LOCAL" else "AWS Workers are processing..."
        
        # 3. Use the dynamic header
        st.header(header_text)
        
        payload = self.form.render(user)
        
        if payload:
            progress_bar = st.progress(0)
            status_text = st.empty()
            tracker_container = st.empty()
            terminal_container = st.empty()
            
            final_data = None

            # 4. Use the dynamic spinner text
            with st.spinner(spinner_text):
                for progress, info in pipeline.run(payload):
                    # If info is a string, it's a progress update
                    if isinstance(info, str):
                        status_text.markdown(f"**Status:** {info}")
                        progress_bar.progress(progress)
                    # If info is a dict, it's the actual result
                                        # Inside AnalyzerUI.render
                    elif isinstance(info, dict):
                        final_data = info 
                        
                        # 💡 THE UNIVERSAL UNWRAPPER
                        # If AWS gave us a nested 'summary' object, we peek inside it.
                        # If Local gave us a flat dict, we use it as is.
                        display_data = info.get("summary") if isinstance(info.get("summary"), dict) else info
                        
                        with tracker_container.container():
                            self.tracker.render(display_data)
                        with terminal_container.container():
                            self.terminal.render(display_data)
            if final_data and final_data.get("status") == "COMPLETE":
                status_text.success("✅ Analysis Complete!")
                progress_bar.progress(1.0)
                # Render the final results box
                self.results.render(final_data)
            else:
                # This triggers if the loop finishes but status isn't 'COMPLETE'
                st.error(f"❌ Pipeline failed or returned incomplete data.")
                if final_data:
                    st.write("Debug info:", final_data) # See what actually cam

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
    """Handles Text and Image Inputs for both Local and Cloud"""
    def render(self, user):
        # 1. 🎛️ SIDEBAR MODE SWITCH
        with st.sidebar:
            st.header("⚙️ System Settings")
            # This radio button replaces the need for 'export ENV_MODE'
            app_mode = st.radio(
                "Execution Environment",
                options=["LOCAL", "AWS"],
                help="LOCAL: Uses VMware Tesseract/Disk. AWS: Uses S3/Lambda/DynamoDB.",
                index=0 if os.getenv("ENV_MODE", "LOCAL") == "LOCAL" else 1
            )
            # Update the environment variable dynamically for the rest of the session
            os.environ["ENV_MODE"] = app_mode
            
            st.divider()
            if app_mode == "LOCAL":
                st.success("💻 Running on VMware Platform")
            else:
                st.warning("☁️ Running on AWS Cloud Infrastructure")

        with st.container(border=True):
            UPLOAD_DIR = "temp_uploads"
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            
            # 2. Dynamic Info Header
            if app_mode == "LOCAL":
                st.info("📂 Mode: **LOCAL** (Tesseract OCR + Local Storage)")
            else:
                st.info("📡 Mode: **AWS** (S3 Trigger + Lambda Orchestration)")
            
            text_input = st.text_area("Feedback Text", placeholder="Describe the feedback...")
            uploaded_file = st.file_uploader("📸 Image", type=['jpg', 'png', 'jpeg'])
            
            if uploaded_file:
                st.image(uploaded_file, caption=f"File: {uploaded_file.name}", width='stretch')

            if st.button("🚀 Run Analysis Pipeline", width='stretch'):
                if not text_input.strip() and not uploaded_file:
                    st.error("⚠️ Please provide text or an image.")
                    return None

                user_id = getattr(user, 'username', 'anonymous')
                unique_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
                
                payload = {
                    "feedback_id": unique_id,
                    "text": text_input,
                    "user_id": user_id,
                    "source_type": "TEXT",
                    "file_path": None,
                    "image_data": None
                }
                
                if uploaded_file:
                    file_bytes = uploaded_file.getvalue()
                    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                    
                    with open(file_path, "wb") as f:
                        f.write(file_bytes)
                    
                    payload["source_type"] = "IMAGE"
                    payload["file_path"] = os.path.abspath(file_path)
                    payload["image_data"] = {"name": uploaded_file.name, "bytes": file_bytes}
                    
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
    """Handles Final Result Presentation (Local & AWS Compatible)"""
    def render(self, final_results):
        # 1. Determine environment for the success message
        import os
        is_local = os.getenv("ENV_MODE", "LOCAL").upper() == "LOCAL"
        msg = "💻 VMware Local Analysis Complete!" if is_local else "☁️ AWS Cloud Analysis Complete!"
        st.success(msg)

        # 2. THE FLEXIBLE GETTER: Check for nested AWS dict OR flat Local dict
        # This prevents the 'Processing...' hang on both platforms
        db_row = final_results.get("summary") 
        
        # If db_row is None or empty, it means we are likely in 'Local' flat mode
        if not db_row or not isinstance(db_row, dict):
            db_row = final_results 

        col1, col2 = st.columns(2)
        with col1:
            # Metric handles both 'sentiment' objects and strings
            sentiment = db_row.get('sentiment', 'N/A')
            st.metric("Sentiment", str(sentiment).upper())
            
            st.write("**🌐 Input Text:**")
            # Checks AWS key 'translated_text' or Local key 'raw_text'
            input_text = db_row.get('translated_text') or db_row.get('raw_text') or db_row.get('text', 'N/A')
            st.info(input_text)
        
        with col2:
            st.write("**📝 AI Summary (Mistral):**")
            # Checks AWS key 'summary' or Local key 'content'
            summary_text = db_row.get('summary') or db_row.get('content', 'Summary unavailable')
            st.success(summary_text)
            
            if db_row.get('audio_path'):
                st.write("**🎙️ Voice Synthesis:**")
                st.audio(db_row.get('audio_path'))

        with st.expander("🔍 View Technical Logs"):
            st.json(final_results)