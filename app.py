import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ibiza 2025 Telemetry", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .block-container {padding-top: 1rem;}</style>""", unsafe_allow_html=True)

# --- RESCUE DATASET (Offline Mode) ---
RESCUE_DATA = [
    {"Track": "Cafe Del Mar", "Artist": "Energy 52", "BPM": 134, "Energy": 0.8, "Valence": 0.4, "Danceability": 0.6, "Loudness": -7, "Acousticness": 0.1, "Popularity": 75, "Year": "1998"},
    {"Track": "Saltwater", "Artist": "Chicane", "BPM": 130, "Energy": 0.7, "Valence": 0.3, "Danceability": 0.5, "Loudness": -8, "Acousticness": 0.2, "Popularity": 68, "Year": "1999"},
    {"Track": "Groovejet", "Artist": "Spiller", "BPM": 123, "Energy": 0.9, "Valence": 0.8, "Danceability": 0.8, "Loudness": -6, "Acousticness": 0.05, "Popularity": 72, "Year": "2000"},
    {"Track": "Silence", "Artist": "Delerium", "BPM": 128, "Energy": 0.8, "Valence": 0.2, "Danceability": 0.5, "Loudness": -7, "Acousticness": 0.01, "Popularity": 70, "Year": "1999"},
    {"Track": "Lady", "Artist": "Modjo", "BPM": 126, "Energy": 0.7, "Valence": 0.9, "Danceability": 0.8, "Loudness": -6, "Acousticness": 0.1, "Popularity": 80, "Year": "2000"},
    {"Track": "Children", "Artist": "Robert Miles", "BPM": 138, "Energy": 0.6, "Valence": 0.1, "Danceability": 0.5, "Loudness": -9, "Acousticness": 0.4, "Popularity": 78, "Year": "1995"},
    {"Track": "9 PM (Till I Come)", "Artist": "ATB", "BPM": 130, "Energy": 0.9, "Valence": 0.6, "Danceability": 0.7, "Loudness": -5, "Acousticness": 0.05, "Popularity": 76, "Year": "1998"},
    {"Track": "Man With The Red Face", "Artist": "Laurent Garnier", "BPM": 126, "Energy": 0.8, "Valence": 0.5, "Danceability": 0.7, "Loudness": -7, "Acousticness": 0.1, "Popularity": 65, "Year": "2000"},
    {"Track": "Touch Me", "Artist": "Rui Da Silva", "BPM": 128, "Energy": 0.7, "Valence": 0.4, "Danceability": 0.7, "Loudness": -6, "Acousticness": 0.1, "Popularity": 60, "Year": "2001"},
    {"Track": "Cola", "Artist": "CamelPhat", "BPM": 122, "Energy": 0.9, "Valence": 0.6, "Danceability": 0.8, "Loudness": -5, "Acousticness": 0.01, "Popularity": 85, "Year": "2017"},
]
# Add simulated points for 3D volume
for i in range(20):
    RESCUE_DATA.append({
        "Track": f"Simulated Track {i}", "Artist": "Unknown",
        "BPM": random.randint(118, 132),
        "Energy": random.uniform(0.5, 0.9),
        "Valence": random.uniform(0.2, 0.8),
        "Danceability": random.uniform(0.6, 0.9),
        "Loudness": random.uniform(-10, -5),
        "Acousticness": random.uniform(0.0, 0.3),
        "Popularity": random.randint(40, 60),
        "Year": "2025"
    })

# --- MAIN LOGIC ---
def get_data_safe():
    source = "Unknown"
    
    # 1. Try API Connection
    try:
        if "CLIENT_ID" in st.secrets:
            auth_manager = SpotifyClientCredentials(
                client_id=st.secrets["CLIENT_ID"], 
                client_secret=st.secrets["CLIENT_SECRET"],
                cache_handler=None
            )
            sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=5)
            
            # SEARCH for an Ibiza playlist (Fix
