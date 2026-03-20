import streamlit as st
import pandas as pd
import plotly.express as px

class AnalyticsView:
    def render(self, provider):
        st.title("📊 Feedback Analytics Dashboard")
        
        try:
            # 1. Fetch data from the local orchestrator/provider
            summary_data = provider.get_sentiment_summary()
            
            if not summary_data or len(summary_data) == 0:
                st.info("💡 No local data found in 'Summaries' table. Run a pipeline analysis first!")
                return

            # 2. DATA CLEANING (Critical for Local Mode)
            # Ensure we have a DataFrame even if some sentiments are missing
            df = pd.DataFrame(summary_data)
            
            # Convert 'total' to numeric safely
            df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
            df['sentiment'] = df['sentiment'].astype(str).str.upper()

            # 3. UI LAYOUT
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Sentiment Proportions")
                # Custom colors to match the app theme
                color_map = {
                    'POSITIVE': '#2ecc71', # Green
                    'NEGATIVE': '#e74c3c', # Red
                    'NEUTRAL': '#f1c40f',  # Yellow
                    'UNKNOWN': '#95a5a6'   # Gray
                }
                
                fig = px.pie(
                    df, 
                    values='total', 
                    names='sentiment', 
                    hole=0.4,
                    color='sentiment',
                    color_discrete_map=color_map
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Volume by Category")
                # Sorting to keep chart consistent
                df_sorted = df.sort_values(by='total', ascending=False)
                st.bar_chart(df_sorted.set_index('sentiment')['total'])
                
                total_records = int(df['total'].sum())
                st.metric("Total Local Records", total_records)

        except Exception as e:
            st.error(f"Failed to build analytics: {e}")
            st.exception(e) # Provides the traceback for debugging