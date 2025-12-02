import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random

# --- CONFIG ---
st.set_page_config(page_title="Ibiza 2025", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .block-container {padding-top: 1rem;}</style>""", unsafe_allow_html=True)

# --- DATA ENGINE ---
def get_data_safe():
    # 1. Try Spotify API
    try:
        if "CLIENT_ID" in st.secrets:
            auth_manager = SpotifyClientCredentials(
                client_id=st.secrets["CLIENT_ID"], 
                client_secret=st.secrets["CLIENT_SECRET"],
                cache_handler=None
            )
            sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=5)
            
            # Search for Ibiza Playlist
            results = sp.search(q="Ibiza Classics", type="playlist", limit=1)
            
            if results and results['playlists']['items']:
                playlist = results['playlists']['items'][0]
                pid = playlist['id']
                pname = playlist['name']
                
                # Fetch Tracks
                tracks = sp.playlist_items(pid, limit=50)['items']
                track_ids = [t['track']['id'] for t in tracks if t['track'] and not t['track']['is_local']]
                
                if track_ids:
                    feats = sp.audio_features(track_ids)
                    data = []
                    for i, f in enumerate(feats):
                        if f:
                            t = tracks[i]['track']
                            data.append({
                                "Track": t['name'],
                                "Artist": t['artists'][0]['name'],
                                "BPM": f['tempo'], "Energy": f['energy'], 
                                "Valence": f['valence'], "Danceability": f['danceability'],
                                "Loudness": f['loudness'], "Acousticness": f['acousticness'],
                                "Popularity": t['popularity'], 
                                "Year": t['album']['release_date'][:4] if t['album']['release_date'] else "N/A"
                            })
                    if data:
                        return pd.DataFrame(data), f"Source: Spotify API ({pname})"
    except:
        pass # Silently fail to offline mode

    # 2. OFFLINE GENERATOR (Cannot have syntax errors)
    # Generates 30 clean data points mathematically
    data = []
    for i in range(30):
        data.append({
            "Track": f"Offline Track {i}", 
            "Artist": "Ibiza Resident",
            "BPM": random.randint(118, 132),
            "Energy": random.uniform(0.5, 0.9),
            "Valence": random.uniform(0.3, 0.8),
            "Danceability": random.uniform(0.6, 0.9),
            "Loudness": random.uniform(-10, -5),
            "Acousticness": random.uniform(0.0, 0.4),
            "Popularity": random.randint(50, 90),
            "Year": str(random.randint(1995, 2025))
        })
    return pd.DataFrame(data), "⚠️ Source: Offline Rescue Data"

# --- RENDER ---
df, source = get_data_safe()
st.title("🏝️ Ibiza Telemetry Dashboard")
st.caption(source)

if not df.empty:
    # 3D Plot
    st.subheader("1. The Vibe (Mood vs Energy vs Groove)")
    fig = px.scatter_3d(df, x='Valence', y='Energy', z='Danceability',
                        color='Acousticness', size='Popularity',
                        hover_name='Track', template='plotly_dark')
    fig.update_layout(height=600, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig, use_container_width=True)

    # Charts
    c1, c2 = st.columns(2)
    c1.subheader("BPM Distribution")
    c1.plotly_chart(px.histogram(df, x="BPM", nbins=15, template='plotly_dark'), use_container_width=True)
    
    c2.subheader("Era (Year)")
    c2.plotly_chart(px.histogram(df.sort_values('Year'), x="Year", template='plotly_dark'), use_container_width=True)

    c3, c4 = st.columns(2)
    c3.subheader("Top Artists")
    top_art = df['Artist'].value_counts().head(5)
    c3.plotly_chart(px.bar(x=top_art.index, y=top_art.values, template='plotly_dark'), use_container_width=True)
    
    c4.subheader("Mood Map")
    c4.plotly_chart(px.scatter(df, x="Valence", y="Energy", color="Acousticness", template='plotly_dark'), use_container_width=True)
else:
    st.error("System Failure")
