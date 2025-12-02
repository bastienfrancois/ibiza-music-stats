import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd

# --- DIAGNOSTIC MODE ---
st.set_page_config(layout="wide")
st.title("🛠️ API Connection Test")

# 1. Check if Secrets exist
try:
    cid = st.secrets["CLIENT_ID"]
    sec = st.secrets["CLIENT_SECRET"]
    st.write(f"✅ Credentials Loaded. ID starts with: `{cid[:4]}...`")
except Exception as e:
    st.error(f"❌ SECRETS MISSING: {e}")
    st.stop()

# 2. Force Authentication
st.write("🔄 Connecting to Spotify API...")
try:
    auth_manager = SpotifyClientCredentials(client_id=cid, client_secret=sec)
    sp = spotipy.Spotify(auth_manager=auth_manager)
except Exception as e:
    st.error(f"❌ AUTH ERROR: {e}")
    st.stop()

# 3. Force Data Fetch (No Try/Except blocks - let it crash if it fails)
st.write("🔍 Searching for playlist...")
# Search
results = sp.search(q="Top Electronic 2025", type="playlist", limit=1)
if not results['playlists']['items']:
    st.error("❌ Search returned no results.")
    st.stop()

playlist = results['playlists']['items'][0]
pid = playlist['id']
st.write(f"✅ Found Playlist: **{playlist['name']}** (ID: `{pid}`)")

st.write("📥 Fetching tracks...")
# Get Tracks
track_results = sp.playlist_items(pid, limit=10) # Just get 10 to test
if not track_results['items']:
    st.error("❌ Playlist is empty.")
    st.stop()

tracks = track_results['items']
st.write(f"✅ Retrieved {len(tracks)} tracks.")

# Get Audio Features (This is usually where it fails)
st.write("🎵 Fetching Audio Features...")
tids = [t['track']['id'] for t in tracks if t['track']]
features = sp.audio_features(tids)

if not features or features[0] is None:
    st.error("❌ Audio Features returned None. (This usually means Keys are valid but lack permissions, or tracks are unplayable)")
    st.stop()

st.success("🎉 SUCCESS! The API is working perfectly.")
st.write("First track feature sample:", features[0])
