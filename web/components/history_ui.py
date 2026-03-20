import streamlit as st
import pandas as pd
import os

class HistoryUI:
    def safe_get(self, obj, key, default="N/A"):
        """Extracts data safely from Dicts or Class Objects."""
        if isinstance(obj, dict):
            # Check for common naming aliases
            if key == 'summary': return obj.get('summary') or obj.get('content') or default
            if key == 'text': return obj.get('text') or obj.get('text_content') or default
            return obj.get(key, default)
        return getattr(obj, key, default)

    def render(self, pipeline, user):
        st.header("📜 Analytics History Explorer")

        # 1. SCOPE SELECTION
        is_admin = getattr(user, 'role', 'user') == 'admin'
        scope = st.radio(
            "Select History Scope:",
            ["My History", "System History"] if is_admin else ["My History"],
            horizontal=True
        )

        # 2. DATA FETCHING
        with st.spinner(f"Loading {scope}..."):
            if scope == "System History":
                items = pipeline.get_all_feedback()
            else:
                # Assuming your pipeline has a get_user_feedback method
                items = pipeline.get_user_feedback(user.username)

        if not items:
            st.info(f"No records found for {scope}.")
            return

        # 3. TABLE VIEW (Pandas for scannability)
        # We transform the complex objects into a clean flat list for the table
        table_data = []
        for i in items:
            table_data.append({
                "ID": self.safe_get(i, 'feedback_id'),
                "Timestamp": self.safe_get(i, 'processed_at')[:16],
                "User": self.safe_get(i, 'user_id'),
                "Sentiment": str(self.safe_get(i, 'sentiment')).upper(),
                "Summary": self.safe_get(i, 'summary')[:60] + "...",
                "Object": i # Keep the original object for the deep dive
            })

        df = pd.DataFrame(table_data)

        # Display the table
        st.subheader(f"📊 {scope} Overview")
        # Use column config to hide the 'Object' column from the user but keep it in the DF
        event = st.dataframe(
            df.drop(columns=['Object']), 
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        # 4. ROW SELECTION & DEEP DIVE
        # If a row is clicked, show the details
        selected_rows = event.selection.rows
        if selected_rows:
            selected_index = selected_rows[0]
            selected_item = table_data[selected_index]['Object']
            
            st.divider()
            st.subheader("🔍 Selected Record Deep Dive")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Full Summary:**\n{self.safe_get(selected_item, 'summary')}")
                with st.expander("📄 View Full Source Text"):
                    st.write(self.safe_get(selected_item, 'text'))
            
            with col2:
                sent = self.safe_get(selected_item, 'sentiment')
                st.metric("Sentiment", str(sent).upper())
                st.write(f"**Processed At:** {self.safe_get(selected_item, 'processed_at')}")
                
                # Extract the path (which is now an S3 URL)
                audio_path = self.safe_get(selected_item, 'audio_path')

                if audio_path and audio_path != "N/A":
                    # If it's a URL (starts with http), Streamlit plays it directly
                    if str(audio_path).startswith("http"):
                        st.audio(audio_path)
                    # Fallback: if it's a local file that actually exists (for local testing)
                    elif os.path.exists(str(audio_path)):
                        st.audio(audio_path)
                    else:
                        st.warning("⚠️ Audio source not reachable.")
        else:
            st.caption("💡 Click a row in the table to view the full AI analysis and audio.")