

from web.components.analyzer_ui import LogTerminal, PipelineTracker, ResultsDisplay

import streamlit as st
import time

import streamlit as st
import time
import pandas as pd
import os
from web.components.analyzer_ui import LogTerminal, PipelineTracker, ResultsDisplay

class DatasetUI:
    def __init__(self):
        self.tracker = PipelineTracker()
        self.results = ResultsDisplay()
        self.terminal = LogTerminal()

    def render(self, bridge, user):
        st.header("🗂️ Dataset Ingestion Hub")
        
        # --- 1. Selection Logic ---
        dataset_type = st.radio(
            "Select Target Dataset", 
            ["Kaggle Tobacco", "MNIST Digits"], 
            horizontal=True,
            key="ds_selector"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if dataset_type == "Kaggle Tobacco":
                category = st.selectbox("Document Category", ["Email", "Memo", "Letter", "Report"])
                base_path = "data/kag_reviews/dataset" 
            else:
                category = st.selectbox("Digit Class (Label)", [str(i) for i in range(10)])
                base_path = None 
        
        with col2:
            limit = st.number_input("Batch Size", 1, 10, 3)

        # --- 2. Trigger Logic (Standard Function Pattern) ---
        if st.button("🚀 Trigger & Monitor Batch", use_container_width=True):
            with st.spinner(f"Initiating {dataset_type} pipeline..."):
                if dataset_type == "Kaggle Tobacco":
                    # 🎯 Expecting a standard dict response
                    response = bridge.trigger_kag_ingestion(
                        base_path=base_path, 
                        folder_name=category, 
                        limit=limit
                    )
                else:
                    response = bridge.trigger_mnist_ingestion(
                        digit=category, 
                        limit=limit
                    )
            
                if response and response.get("status") == "success":
                    st.session_state.current_batch = response.get("sample_ids", [])
                    st.session_state.active_dataset_type = dataset_type
                    st.toast(f"✅ Triggered {len(st.session_state.current_batch)} samples!")
                else:
                    msg = response.get('message', 'Trigger Failed') if response else "No response from Bridge"
                    st.error(f"❌ Error: {msg}")

        # --- 3. Live Results Display (Handled by BatchTracker) ---
        if 'current_batch' in st.session_state:
            st.divider()
            # Initialize the tracker with the bridge and let it handle the loop
            tracker = BatchTracker(bridge)
            tracker.render(st.session_state.current_batch)
            
            # Action bar to reset
            if st.button("🗑️ Clear Batch Results", use_container_width=True):
                del st.session_state.current_batch
                st.rerun()

class BatchResultCard:
    """Renders a single document's analysis result in the batch grid"""
    @staticmethod
    def render(fid, data):
        # Handle different data nesting levels from DynamoDB/Local DB
        db_row = data.get("summary") if isinstance(data.get("summary"), dict) else data
        status = str(db_row.get('status', 'PENDING')).upper()
        ds_type = st.session_state.get('active_dataset_type', 'Dataset')

        sentiment = db_row.get('sentiment')
        summary = db_row.get('summary') or db_row.get('content', 'Processing...')
        
        with st.expander(f"📄 {fid} | {status}", expanded=(status in ["COMPLETE", "COMPLETED", "SUMMARIZED"])):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if sentiment and sentiment != "---":
                    st.metric("Sentiment", str(sentiment).upper())
                else:
                    st.metric("Source", ds_type)
                
                if db_row.get('audio_path'):
                    st.audio(db_row.get('audio_path'))
            
            with col2:
                label = "AI Summary" if ds_type == "Kaggle Tobacco" else "Model Analysis"
                st.markdown(f"**{label}:**")
                st.success(summary)
                
                if st.checkbox("View Raw Data", key=f"raw_{fid}"):
                    raw_text = db_row.get('translated_text') or db_row.get('raw_text') or "No data available."
                    st.caption(raw_text)

class BatchTracker:
    def __init__(self, bridge):
        self.bridge = bridge

    def render(self, sample_ids):
        st.subheader("📡 Live Batch Analysis")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        grid_container = st.container() 
        
        completed_count = 0
        current_results = {}

        # 1. Fetch current status for all IDs
        for fid in sample_ids:
            data = self.bridge._get_table_data("Analysis_Summaries", fid) or {}
            current_results[fid] = data
            
            if str(data.get('status')).upper() in ['COMPLETE', 'COMPLETED', 'SUMMARIZED']:
                completed_count += 1

        # 2. Update Header UI
        prog = completed_count / len(sample_ids) if sample_ids else 0
        progress_bar.progress(prog)
        status_text.markdown(f"**Batch Status:** {completed_count}/{len(sample_ids)} analyzed.")

        # 3. Render Grid
        with grid_container:
            cols = st.columns(2)
            for i, fid in enumerate(sample_ids):
                with cols[i % 2]:
                    BatchResultCard.render(fid, current_results[fid])

        # 4. Polling Logic
        if completed_count < len(sample_ids):
            time.sleep(3) 
            st.rerun()
        else:
            st.balloons()
            st.success("✅ Batch Research Analysis Complete!")