import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- 1. SETUP & LOGGING ---
st.set_page_config(page_title="Ibiza Debugger", layout="wide")
st.title("🛠️ Live Diagnostic Mode")

# --- 2. CREDENTIAL CHECK ---
st.write("1️⃣ Checking Credentials...")
try:
    cid = st.secrets["CLIENT_ID"]
    sec = st.secrets["CLIENT_SECRET"]
    
    # Check if they look like valid strings
    if len(cid) != 32 or len(sec) != 32:
        st.warning(f"⚠️ Warning: Keys look the wrong length. ID is {len(cid)} chars. (Should be 32)")
    
    st.success(f"✅ Credentials found. ID: `{cid[:4]}...`")
except Exception as e:
    st.error(f"❌ CRITICAL ERROR: Secrets are missing. {e}")
    st.stop()

# --- 3. API CONNECTION ---
st.write("2️⃣ Connecting to Spotify...")
try:
    auth_manager = SpotifyClientCredentials(client_id=cid, client_secret=sec)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    st.success("✅ Spotify Object Created.")
except Exception as e:
    st.error(f"❌ CONNECTION FAILED: {e}")
    st.stop()

# --- 4. PLAYLIST SEARCH ---
st.write("3️⃣ Searching for 'Ibiza Classics'...")
try:
    # Try a direct search
    results = sp.search(q="Ibiza Classics", type="playlist", limit=1)
    
    if not results['playlists']['items']:
        st.error("❌ Search returned 0 results. The API is working, but found nothing.")
        st.stop()
        
    playlist = results['playlists']['items'][0]
    pid = playlist['id']
    pname = playlist['name']
    st.success(f"✅ Found Playlist: **{pname}** (ID: `{pid}`)")
except Exception as e:
    # This captures the 401/403/404 errors
    st.error(f"❌ SEARCH FAILED. This is the error: {e}")
    st.stop()

# --- 5. FETCH TRACKS ---
st.write(f"4️⃣ Downloading tracks from '{pname}'...")
try:
    track_results = sp.playlist_items(pid, limit=50)
    tracks = track_results['items']
    
    if not tracks:
        st.error("❌ Playlist is empty.")
        st.stop()
        
    st.success(f"✅ Retrieved {len(tracks)} raw items.")
except Exception as e:
    st.error(f"❌ DOWNLOAD FAILED: {e}")
    st.stop()

# --- 6. DATA PROCESSING ---
st.write("5️⃣ Processing Audio Features...")
try:
    track_ids = []
    track_info = {}
    
    # Filter valid tracks
    for t in tracks:
        if t.get('track') and t['track'].get('id'):
            tid = t['track']['id']
            track_ids.append(tid)
            track_info[tid] = {
                'name': t['track']['name'],
                'artist': t['track']['artists'][0]['name'],
                'popularity': t['track']['popularity']
            }
            
    # Batch Fetch
    audio_features = []
    if track_ids:
        # Fetch first 50
        features = sp.audio_features(track_ids[:50])
        audio_features = [f for f in features if f is not None]
        
    if not audio_features:
        st.error("❌ No audio features returned. (Possible permissions issue)")
        st.stop()

    st.success(f"✅ Successfully analyzed {len(audio_features)} tracks.")
    
    # Create simple DF to prove it works
    df = pd.DataFrame(audio_features)
    st.dataframe(df.head())
    
except Exception as e:
    st.error(f"❌ PROCESSING FAILED: {e}")
    st.stop()

st.balloons()
st.success("🎉 SYSTEM IS FULLY OPERATIONAL. You can now revert to the Graph Code.")
