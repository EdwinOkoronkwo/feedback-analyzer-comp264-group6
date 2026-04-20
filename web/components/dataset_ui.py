import streamlit as st
import time
import pandas as pd
import os
from web.components.analyzer_ui import LogTerminal, PipelineTracker, ResultsDisplay

class BatchResultCard:
    """Renders a single document's analysis result in the batch grid with Speech & OCR support"""
    @staticmethod
    def render(fid, data):
        # 1. THE FLEXIBLE GETTER (Matching ResultsDisplay logic)
        # Handles nested AWS response or flat Local response
        db_row = data.get("summary") if isinstance(data.get("summary"), dict) else data
        
        # 2. Normalize status
        raw_status = str(db_row.get('status', 'PENDING')).upper()
        status = "COMPLETED" if raw_status in ["COMPLETE", "COMPLETED", "SUMMARIZED", "SUCCESS"] else raw_status
        
        # 3. Extract Fields
        ds_type = st.session_state.get('active_dataset_type', 'Kaggle Tobacco')
        sentiment = db_row.get('sentiment')
        summary = db_row.get('summary') or db_row.get('content') or db_row.get('translated_text', 'Processing...')
        
        # 🎯 Metadata Fields (OCR and Audio)
        audio_path = db_row.get('audio_path') or data.get('audio_path')
        raw_ocr = db_row.get('text') or db_row.get('text_content') or db_row.get('translated_text')

        with st.expander(f"📄 {fid} | {status}", expanded=(status == "COMPLETED")):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if sentiment and sentiment not in ["---", "UNKNOWN"]:
                    st.metric("Sentiment", str(sentiment).upper())
                else:
                    st.metric("Source", ds_type)
                
                # 🎙️ CLEAN AUDIO PLAYER LOGIC
                if audio_path:
                    # Case A: Remote URL (S3 Presigned/HTTP)
                    if str(audio_path).startswith(("http://", "https://")):
                        st.audio(audio_path)
                    
                    # Case B: Local file path (VMware/Local mode)
                    elif os.path.exists(str(audio_path)):
                        try:
                            with open(audio_path, "rb") as audio_file:
                                st.audio(audio_file.read(), format="audio/mp3")
                        except Exception as e:
                            st.error("Audio Read Error")
                    
                    # Case C: Processing state
                    else:
                        if status == "COMPLETED":
                            st.warning("🎙️ Audio unreachable")
                        else:
                            st.info("🎙️ Finalizing audio...")
                elif status == "COMPLETED":
                    st.caption("No audio generated.")
                else:
                    st.caption("🎙️ Waiting for pipeline...")
            
            with col2:
                label = "AI Summary" if ds_type == "Kaggle Tobacco" else "Model Analysis"
                st.markdown(f"**{label}:**")
                
                if status == "COMPLETED":
                    st.success(summary)
                else:
                    st.info("⌛ Analysis in progress...")
                
                # Secondary content (OCR)
                if st.checkbox("View Raw OCR Text", key=f"raw_check_{fid}"):
                    st.text_area("Extracted Text", raw_ocr or "No text found", height=150, key=f"txt_area_{fid}")

class BatchTracker:
    def __init__(self, bridge):
        self.bridge = bridge
        # Define our two local tables
        self.summary_table = "Summaries"
        self.metadata_table = "Metadata"

    def render(self, sample_ids):
        st.subheader("📡 Live Batch Analysis")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        grid_container = st.container() 
        
        completed_count = 0
        current_results = {}

        # 1. Fetch and Merge Data from BOTH tables
        for fid in sample_ids:
            # Get the AI Summary part
            summary_data = self.bridge._get_table_data(self.summary_table, fid) or {}
            # Get the OCR & Audio part
            metadata_data = self.bridge._get_table_data(self.metadata_table, fid) or {}
            
            # 🎯 MERGE: combine summary + audio_path + raw_text
            merged_data = {**summary_data, **metadata_data}
            current_results[fid] = merged_data
            
            if str(merged_data.get('status', '')).upper() in ['COMPLETE', 'COMPLETED', 'SUMMARIZED']:
                completed_count += 1

        # 2. UI Updates
        total = len(sample_ids)
        prog = completed_count / total if total > 0 else 0
        progress_bar.progress(prog)
        status_text.markdown(f"**Batch Status:** {completed_count}/{total} analyzed.")

        # 3. Render Grid
        with grid_container:
            cols = st.columns(2)
            for i, fid in enumerate(sample_ids):
                with cols[i % 2]:
                    BatchResultCard.render(fid, current_results[fid])

        # 4. Polling
        if completed_count < total:
            time.sleep(3) 
            st.rerun()
        else:
            st.success("✅ Batch Research Analysis Complete!")
            
class DatasetUI:
    def __init__(self):
        # Note: LogTerminal assumed to be available in runtime
        pass

    def render(self, bridge, user):
        st.header("🗂️ Kaggle Tobacco Dataset Ingestion")
        
        # --- 1. Selection UI ---
        dataset_type = "Kaggle Tobacco"
        st.info(f"Active Dataset: **{dataset_type}**")
        
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Document Category", ["Email", "Memo", "Letter", "Report"])
            base_path = "data/kag_reviews/dataset" 
        
        with col2:
            # Enforcing min 1 and max 10 directly in the widget.
            # This prevents the internal state from ever exceeding 10.
            limit = st.number_input(
                "Batch Size", 
                min_value=1, 
                max_value=10,
                value=3,
                help="Limits the concurrent documents processed to prevent local resource exhaustion (Max 10)."
            )
            
            # Since the widget stops at 10, we show a hint when it reaches that peak
            # to explain why they cannot go further.
            if limit >= 10:
                st.info("💡 Maximum batch size of 10 reached.")
            
            # Final safety enforcement
            limit = max(1, min(limit, 10))


        # --- 2. Trigger Logic ---
        if st.button("🚀 Trigger & Monitor Batch", use_container_width=True):
            with st.spinner("Executing Local Pipeline & Polling Workers..."):
                try:
                    # 🎯 Match Bridge response keys: "status" and "ids"
                    response = bridge.trigger_kag_ingestion(
                        base_path=base_path, 
                        folder_name=category, 
                        limit=limit
                    )

                    # Normalize status string
                    status = str(response.get("status", "")).upper()
                    
                    # 🎯 Fix: Include "DISPATCHED" as a valid success state
                    if status in ["SUCCESS", "COMPLETE", "COMPLETED", "DISPATCHED"]:
                        # 🎯 Fix: Use "ids" to match Bridge return: {"ids": [...]}
                        st.session_state.current_batch = response.get("ids", [])
                        st.session_state.active_dataset_type = dataset_type
                        st.rerun() 
                    else:
                        # Fallback for None values
                        msg = response.get('message') or "No message returned from Bridge"
                        st.error(f"❌ Pipeline Error: {msg}")

                except Exception as e:
                    st.error(f"Bridge Communication Failed: {str(e)}")

        # --- 3. Live Results Display ---
        if 'current_batch' in st.session_state:
            st.divider()
            tracker = BatchTracker(bridge)
            tracker.render(st.session_state.current_batch)
            
            if st.button("🗑️ Clear Batch Results", use_container_width=True):
                del st.session_state.current_batch
                st.rerun()


# import streamlit as st
# import time
# import pandas as pd
# import os
# from web.components.analyzer_ui import LogTerminal, PipelineTracker, ResultsDisplay

# class BatchResultCard:
#     """Renders a single document's analysis result in the batch grid"""
#     @staticmethod
#     def render(fid, data):
#         # Handle different data nesting levels from DynamoDB/Local DB
#         db_row = data.get("summary") if isinstance(data.get("summary"), dict) else data
#         status = str(db_row.get('status', 'PENDING')).upper()
#         ds_type = st.session_state.get('active_dataset_type', 'Dataset')

#         sentiment = db_row.get('sentiment')
#         summary = db_row.get('summary') or db_row.get('content', 'Processing...')
        
#         with st.expander(f"📄 {fid} | {status}", expanded=(status in ["COMPLETE", "COMPLETED", "SUMMARIZED"])):
#             col1, col2 = st.columns([1, 2])
            
#             with col1:
#                 if sentiment and sentiment != "---":
#                     st.metric("Sentiment", str(sentiment).upper())
#                 else:
#                     st.metric("Source", ds_type)
                
#                 if db_row.get('audio_path'):
#                     st.audio(db_row.get('audio_path'))
            
#             with col2:
#                 label = "AI Summary" if ds_type == "Kaggle Tobacco" else "Model Analysis"
#                 st.markdown(f"**{label}:**")
#                 st.success(summary)
                
#                 if st.checkbox("View Raw Data", key=f"raw_{fid}"):
#                     raw_text = db_row.get('translated_text') or db_row.get('raw_text') or "No data available."
#                     st.caption(raw_text)

# class BatchTracker:
#     def __init__(self, bridge):
#         self.bridge = bridge
#         mode = os.getenv("ENV_MODE", "LOCAL").upper()
#         self.target_table = "Analysis_Summaries" if mode == "AWS" else "Summaries"

#     def render(self, sample_ids):
#         st.subheader("📡 Live Batch Analysis")
        
#         progress_bar = st.progress(0)
#         status_text = st.empty()
#         grid_container = st.container() 
        
#         completed_count = 0
#         current_results = {}

#         # 1. Fetch current status for all IDs
#         for fid in sample_ids:
#             if hasattr(self.bridge, 'get_record'):
#                 # Some bridges have a helper that already knows the table
#                 data = self.bridge.get_record(fid) or {}
#             else:
#                 # 🎯 Step 2: Use the dynamic table name here!
#                 data = self.bridge._get_table_data(self.target_table, fid) or {}
                
#             current_results[fid] = data
            
#             if str(data.get('status')).upper() in ['COMPLETE', 'COMPLETED', 'SUMMARIZED']:
#                 completed_count += 1

#         # 2. Update Header UI
#         prog = completed_count / len(sample_ids) if sample_ids else 0
#         progress_bar.progress(prog)
#         status_text.markdown(f"**Batch Status:** {completed_count}/{len(sample_ids)} analyzed.")

#         # 3. Render Grid
#         with grid_container:
#             cols = st.columns(2)
#             for i, fid in enumerate(sample_ids):
#                 with cols[i % 2]:
#                     BatchResultCard.render(fid, current_results[fid])

#         # 4. Polling Logic
#         if completed_count < len(sample_ids):
#             time.sleep(3) 
#             st.rerun()
#         else:
#             st.balloons()
#             st.success("✅ Batch Research Analysis Complete!")

# class DatasetUI:
#     def __init__(self):
#         # These are used for UI consistency but tracker handles the batch loop
#         self.terminal = LogTerminal()

#     def render(self, bridge, user):
#         st.header("🗂️ Dataset Ingestion Hub")
        
#         # --- 1. Selection Logic ---
#         dataset_type = st.radio(
#             "Select Target Dataset", 
#             ["Kaggle Tobacco", "MNIST Digits"], 
#             horizontal=True,
#             key="ds_selector"
#         )
        
#         col1, col2 = st.columns(2)
#         with col1:
#             if dataset_type == "Kaggle Tobacco":
#                 category = st.selectbox("Document Category", ["Email", "Memo", "Letter", "Report"])
#                 base_path = "data/kag_reviews/dataset" 
#             else:
#                 category = st.selectbox("Digit Class (Label)", [str(i) for i in range(10)])
#                 base_path = None 
        
#         with col2:
#             limit = st.number_input("Batch Size", 1, 10, 3)

#         # --- 2. Trigger Logic ---
#         if st.button("🚀 Trigger & Monitor Batch", use_container_width=True):
#             print("\n🔘 [UI DEBUG] Button Clicked!") # 🎯 ADD THIS
#             with st.spinner(f"Initiating {dataset_type} pipeline..."):
#                 try:
#                     print(f"🔘 [UI DEBUG] Calling bridge.trigger_kag_ingestion with type: {dataset_type}") # 🎯 ADD THIS
#                     if dataset_type == "Kaggle Tobacco":
#                         response = bridge.trigger_kag_ingestion(
#                             base_path=base_path, 
#                             folder_name=category, 
#                             limit=limit
#                         )
#                     else:
#                         response = bridge.trigger_mnist_ingestion(
#                             digit=category, 
#                             limit=limit
#                         )

                    
#                     status = str(response.get("status", "")).upper()
#                     if response and status in ["SUCCESS", "COMPLETE", "COMPLETED"]:
#                         st.session_state.current_batch = response.get("sample_ids", [])
#                         st.session_state.active_dataset_type = dataset_type
#                         print(f"🔘 [UI DEBUG] Bridge Response Received: {type(response)}") # 🎯 ADD THIS
#                         st.toast(f"✅ Triggered {len(st.session_state.current_batch)} samples!")
#                     else:
#                         msg = response.get('message', 'Trigger Failed') if response else "No response from Bridge"
#                         st.error(f"❌ Error: {msg}")
#                         print(f"🔘 [UI DEBUG] Bridge Response Received: {type(response)}") # 🎯 ADD THIS
#                 except Exception as e:
#                     st.error(f"Failed to communicate with Bridge: {str(e)}")

#         # --- 3. Live Results Display ---
#         if 'current_batch' in st.session_state:
#             st.divider()
#             tracker = BatchTracker(bridge)
#             tracker.render(st.session_state.current_batch)
            
#             if st.button("🗑️ Clear Batch Results", use_container_width=True):
#                 del st.session_state.current_batch
#                 st.rerun()