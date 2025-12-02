import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Ibiza 2025 Telemetry", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .block-container {padding-top: 1rem;}</style>""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
try:
    client_id = st.secrets["CLIENT_ID"]
    client_secret = st.secrets["CLIENT_SECRET"]
except:
    st.error("🚨 Secrets missing. Please check Streamlit Settings.")
    st.stop()

# --- MAIN DATA ENGINE ---
def get_data():
    try:
        # 1. Force Fresh Authentication (Disables caching to fix 'NoneType' errors)
        auth_manager = SpotifyClientCredentials(
            client_id=client_id, 
            client_secret=client_secret, 
            cache_handler=None 
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # 2. HARDCODED TARGET (The ID you provided)
        target_id = '6wQJ2kYwH8wGj1z8xX0j2y' 
        
        # 3. Get Playlist Info & Tracks
        try:
            playlist_info = sp.playlist(target_id)
            pname = playlist_info['name']
            
            # Fetch tracks (Limit 80 for speed/relevance)
            track_results = sp.playlist_items(target_id, limit=80)
            tracks = track_results['items']
        except Exception as e:
             # If the ID is wrong or private, this catches it
            return pd.DataFrame(), f"Playlist Error: {e}"

        # 4. Filter & Extract Data
        track_ids = []
        track_info = {}
        for t in tracks:
            # Filter out local files and empty IDs
            if t.get('track') and t['track'].get('id') and not t['track'].get('is_local'):
                tid = t['track']['id']
                track_ids.append(tid)
                track_info[tid] = {
                    'name': t['track']['name'],
                    'artist': t['track']['artists'][0]['name'],
                    'popularity': t['track']['popularity'],
                    'year': t['track']['album']['release_date'][:4] if t['track']['album']['release_date'] else "N/A"
                }

        # 5. Fetch Audio Features (The Stats)
        audio_features = []
        # Batch requests by 50 to avoid API timeouts
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i+50]
            if batch:
                try:
                    features = sp.audio_features(batch)
                    audio_features.extend([f for f in features if f])
                except:
                    continue

        # 6. Build the Database
        df_data = []
        for feature in audio_features:
            tid = feature['id']
            info = track_info.get(tid, {})
            df_data.append({
                'Track': info.get('name'),
                'Artist': info.get('artist'),
                'Popularity': info.get('popularity'),
                'Year': info.get('year'),
                'BPM': round(feature['tempo']),
                'Energy': feature['energy'],
                'Danceability': feature['danceability'],
                'Loudness': feature['loudness'],
                'Valence': feature['valence'], 
                'Acousticness': feature['acousticness']
            })
        
        return pd.DataFrame(df_data), pname

    except Exception as e:
        st.error(f"❌ CRITICAL API FAILURE: {e}")
        return pd.DataFrame(), "Error"

# --- DASHBOARD RENDER ---
df, pname = get_data()

if not df.empty:
    st.title(f"🏝️ Ibiza Clout: {pname}")
    st.markdown("Telemetric analysis of the 'White Isle' cultural sound.")
    
    # ROW 1: 3D HERO
    st.subheader("1. The Balearic Vibe (Mood vs Energy vs Groove)")
    fig_3d = go.Figure(data=[go.Scatter3d(
        x=df['Valence'], y=df['Energy'], z=df['Danceability'],
        mode='markers',
        marker=dict(
