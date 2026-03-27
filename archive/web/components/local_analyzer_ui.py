import streamlit as st
import requests, uuid

import streamlit as st
import requests
import uuid

class LocalAnalyzerUI:
    def render(self, pipeline, user):
        st.header("🏠 Local Analysis (Ollama + gTTS)")
        
        with st.container(border=True):
            text_input = st.text_area("Feedback Text", placeholder="Local processing...")
            uploaded_file = st.file_uploader("📸 Image", type=['jpg', 'png', 'jpeg'])
            
            if st.button("🚀 Run Local Pipeline", use_container_width=True):
                # 1. Prepare Local Payload
                user_id = getattr(user, 'username', 'anonymous')
                fid = f"{user_id}_{uuid.uuid4().hex[:8]}"
                
                payload = {"feedback_id": fid, "text": text_input, "user_id": user_id}
                files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)} if uploaded_file else None

                # 2. Direct Bridge Call (Fast & Synchronous)
                with st.spinner("Ollama & Mistral are thinking..."):
                    res = requests.post("http://localhost:5000/process", data=payload, files=files)
                    
                    if res.status_code == 200:
                        analysis = res.json().get("analysis_preview", {})
                        st.success("✅ Local Analysis Complete")
                        # Display results immediately
                        st.json(analysis) 
                    else:
                        st.error("Local Bridge is offline.")
