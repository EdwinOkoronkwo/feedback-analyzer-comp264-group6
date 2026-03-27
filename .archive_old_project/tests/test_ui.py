import sys
import os
# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import streamlit as st

from web.components.results_viewer import ResultsViewer


# 1. Setup the Page
st.set_page_config(page_title="UI Mock Test", layout="wide")
st.title("🧪 ResultsViewer Component Test")

# 2. Define the Mock Data (Matching your DynamoDB Scans exactly)
mock_result = {
    "status": "COMPLETE",
    "ocr": {
        "text_content": [
            "La casa roja relataba la atormentada vida de",
            "n misterioso individuo que asaltaba jugueterías",
            "museos para robar munecos y títeres"
        ],
        "processed_at": "1772065483.5395494"
    },
    "translation": {
        "translated_text": "The red house told the tormented life of a mysterious individual who robbed toy stores...",
        "language": "en"
    },
    "summary": {
        "summary_text": "A dark narrative about a mysterious figure targeting museums and toys.",
        "sentiment": "NEGATIVE"
    },
    "labels": {
        "labels": ["Text", "Paper", "Document"]
    },
    "audio_key": "audio/spanish.jpg.mp3"
}

# 3. Instantiate and Render
st.info("Directly rendering ResultsViewer with Mock Data...")
viewer = ResultsViewer()
viewer.render(mock_result)