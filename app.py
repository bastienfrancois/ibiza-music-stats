import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

st.title("🔌 Connection Check")

# 1. Print current keys (masked) to prove the file updated
try:
    cid = st.secrets["CLIENT_ID"]
    st.write(f"Key loaded from Secrets: `{cid[:4]}...`")
except:
    st.error("Secrets not found.")
    st.stop()

# 2. Try the connection
try:
    auth_manager = SpotifyClientCredentials(
        client_id=st.secrets["CLIENT_ID"], 
        client_secret=st.secrets["CLIENT_SECRET"]
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # Try that specific Ibiza playlist
    pl = sp.playlist('6wQJ2kYwH8wGj1z8xX0j2y')
    st.success(f"✅ SUCCESS! Connected to playlist: **{pl['name']}**")
    st.write(f"Total Tracks: {pl['tracks']['total']}")
    
except Exception as e:
    st.error(f"❌ Connection Failed: {e}")
