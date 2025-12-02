import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Ibiza 2025 Telemetry", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .block-container {padding-top: 1rem;}</style>""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
try:
    client_id = st.secrets["CLIENT_ID"]
    client_secret = st.secrets["CLIENT_SECRET"]
except:
    st.error("🚨 Secrets missing.")
    st.stop()

def get_data():
    status_log = []
    try:
        # 1. Authenticate (Increase timeout to 10s for slow connections)
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret, cache_handler=None)
        sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=10)
        status_log.append("Auth Successful.")
        
        # 2. TARGET: Official 'Ibiza Classics' Playlist (Guaranteed Data)
        target_id = '37i9dQZF1DWVlysXLVxUxE' 
        
        try:
            playlist_info = sp.playlist(target_id)
            pname = playlist_info['name']
            status_log.append(f"Targeting: {pname}")
            
            # Fetch tracks
            track_results = sp.playlist_items(target_id, limit=80)
            tracks = track_results['items']
            status_log.append(f"Downloaded {len(tracks)} raw items.")
        except Exception as e:
            return pd.DataFrame(), f"Playlist Access Failed: {e}", status_log

        # 3. Filter Valid IDs
        track_ids = []
        track_info = {}
        for t in tracks:
            # STRICT FILTER: Must be a valid track, not local, not None
            if t.get('track') and t['track'].get('id') and not t['track'].get('is_local'):
                tid = t['track']['id']
                track_ids.append(tid)
                track_info[tid] = {
                    'name': t['track']['name'],
                    'artist': t['track']['artists'][0]['name'],
                    'popularity': t['track']['popularity'],
                    'year': t['track']['album']['release_date'][:4] if t['track']['album']['release_date'] else "N/A"
                }
        
        status_log.append(f"Valid Tracks after filtering: {len(track_ids)}")
        if not track_ids:
             return pd.DataFrame(), "Error: No valid track IDs found.", status_log

        # 4. Audio Features (With Retry Logic)
        audio_features = []
        batch_size = 20 # Smaller batch to be safe
        
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i+batch_size]
            if batch:
                try:
                    features = sp.audio_features(batch)
                    valid_batch = [f for f in features if f] # Filter Nones immediately
                    audio_features.extend(valid_batch)
                    status_log.append(f"Batch {i//batch_size + 1}: Success ({len(valid_batch)} features)")
                except Exception as e:
                    status_log.append(f"Batch {i//batch_size + 1} Failed: {e}")
                    time.sleep(1) # Wait 1s and continue
                    continue

        if not audio_features:
            return pd.DataFrame(), "Error: API returned 0 features. (Check Logs)", status_log

        # 5. Build DataFrame
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
        
        return pd.DataFrame(df_data), pname, status_log

    except Exception as e:
        return pd.DataFrame(), f"Critical Error: {e}", status_log
