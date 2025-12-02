import streamlit as st
import sys
import time

# --- 1. IMMEDIATE HEARTBEAT ---
# If this doesn't show, your server is broken (check requirements.txt)
st.set_page_config(page_title="Ibiza Safe Mode")
st.title("🟢 System Online")
st.write("Streamlit is active. Beginning diagnostics...")

# --- 2. LIBRARY CHECK ---
st.write("Testing Libraries...")
try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    st.success("✅ Libraries (Spotipy, Plotly, Pandas) loaded.")
except ImportError as e:
    st.error(f"❌ CRITICAL ERROR: Library missing -> {e}")
    st.info("Check your 'requirements.txt' file on GitHub. It must contain: spotipy, pandas, plotly")
    st.stop()

# --- 3. CREDENTIAL CHECK ---
st.write("Testing Secrets...")
try:
    client_id = st.secrets["CLIENT_ID"]
    client_secret = st.secrets["CLIENT_SECRET"]
    st.success(f"✅ Secrets found. ID ends in ...{client_id[-4:]}")
except Exception as e:
    st.error(f"❌ Secrets missing: {e}")
    st.stop()

# --- 4. CONNECTION TEST ---
st.write("Testing Spotify API Connection...")
try:
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # Simple Target: Ibiza Classics Official
    target = '37i9dQZF1DWVlysXLVxUxE' 
    playlist = sp.playlist(target)
    st.success(f"✅ Connected to Playlist: {playlist['name']}")
except Exception as e:
    st.error(f"❌ API Connection Failed: {e}")
    st.stop()

# --- 5. DATA FETCHING ---
st.write("Downloading Track Data...")
try:
    results = sp.playlist_items(target, limit=30)
    tracks = results['items']
    
    # Filter valid tracks
    valid_ids = []
    for t in tracks:
        if t['track'] and t['track']['id'] and not t['track']['is_local']:
            valid_ids.append(t['track']['id'])
            
    if not valid_ids:
        st.error("❌ No valid tracks found (all local or empty).")
        st.stop()
        
    st.success(f"✅ Found {len(valid_ids)} valid tracks.")
    
    # Fetch Audio Features
    st.write("Fetching Telemetry (BPM/Energy)...")
    audio_features = sp.audio_features(valid_ids)
    
    # Filter Nones
    clean_features = [f for f in audio_features if f]
    
    if not clean_features:
        st.error("❌ API returned 0 features. (Rate Limiting or Permissions Issue)")
        st.stop()
        
    st.success(f"✅ Successfully analyzed {len(clean_features)} tracks!")

    # --- 6. RENDER GRAPH ---
    st.write("Rendering Graph...")
    df = pd.DataFrame(clean_features)
    
    fig = px.scatter_3d(
        df, x='valence', y='energy', z='danceability',
        color='tempo', title="Ibiza Telemetry Test"
    )
    st.plotly_chart(fig)

except Exception as e:
    st.error(f"❌ Data Processing Failed: {e}")
