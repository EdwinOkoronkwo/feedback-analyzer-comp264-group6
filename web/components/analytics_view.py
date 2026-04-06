import streamlit as st
import pandas as pd
import plotly.express as px

import streamlit as st
import pandas as pd
import plotly.express as px

class AnalyticsView:
    def render(self, provider, summaries_provider=None):
        """
        provider: AthenaAnalyticsProvider (High-level Stats)
        summaries_provider: AWSSummaryProvider (Detailed Row Data)
        """
        st.title("📊 Feedback Analytics Dashboard")
        
        # --- SECTION 1: ATHENA CHARTS (Aggregates) ---
        try:
            st.subheader("Cloud Insights (Athena)")
            summary_data = provider.get_sentiment_summary()
            
            if not summary_data:
                st.info("💡 No aggregate data found in Athena. Ensure Glue Crawler has run.")
            else:
                df = pd.DataFrame(summary_data)
                
                # Data Cleaning for Charts
                df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
                df['sentiment'] = df['sentiment'].astype(str).str.upper()

                col1, col2 = st.columns(2)
                
                with col1:
                    color_map = {
                        'POSITIVE': '#2ecc71', 'NEGATIVE': '#e74c3c', 
                        'NEUTRAL': '#f1c40f', 'UNKNOWN': '#95a5a6'
                    }
                    fig = px.pie(
                        df, values='total', names='sentiment', hole=0.4,
                        color='sentiment', color_discrete_map=color_map
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.bar_chart(df.set_index('sentiment')['total'])
                    total_athena = int(df['total'].sum())
                    st.metric("Total Records Scanned", total_athena)

        except Exception as e:
            st.error(f"Athena Layer Error: {e}")

        st.divider()

        # --- SECTION 2: DYNAMODB DETAILS (The "Tobacco Institute" Records) ---
        if summaries_provider:
            try:
                st.subheader("📑 Detailed Analysis Records (DynamoDB)")
                
                # Fetching the 9 records (and any new ones)
                raw_docs = summaries_provider.get_all_summaries()
                
                if not raw_docs:
                    st.warning("No individual records found in the Analysis_Summaries table.")
                else:
                    df_docs = pd.DataFrame(raw_docs)
                    
                    # Layout for the detailed list
                    st.write(f"Showing last {len(df_docs)} processed documents:")
                    
                    # Display as a searchable dataframe
                    st.dataframe(
                        df_docs[['item_id', 'sentiment', 'summary', 'timestamp']], 
                        use_container_width=True,
                        column_config={
                            "item_id": "Document ID",
                            "sentiment": "AI Sentiment",
                            "summary": "Snippet",
                            "timestamp": "Processed Date"
                        }
                    )

                    # Individual Document Inspector
                    selected_id = st.selectbox("Inspect Document Content", df_docs['item_id'].tolist())
                    if selected_id:
                        doc = next(item for item in raw_docs if item["item_id"] == selected_id)
                        with st.expander("Full Text Content", expanded=True):
                            st.text_area("OCR Result", doc['full_text'], height=300)

            except Exception as e:
                st.error(f"Summaries Layer Error: {e}")
        else:
            st.info("Summaries Provider not initialized for this mode.")