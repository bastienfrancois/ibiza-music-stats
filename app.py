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
    st.error("🚨 Secrets missing.")
    st.stop()

def get_data():
    status_log = [] # Keep a log of what happens
    try:
        # 1. Authenticate
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret, cache_handler=None)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        status_log.append("Auth Successful.")
        
        # 2. TARGET: The Known Working Playlist (EDM 2025)
        # We use this one because we confirmed it works.
        target_id = '5PCv6afEatU3z9cq2fBPDs' 
        
        try:
            playlist_info = sp.playlist(target_id)
            pname = playlist_info['name']
            status_log.append(f"Found Playlist: {pname}")
            
            # Fetch tracks
            track_results = sp.playlist_items(target_id, limit=80)
            tracks = track_results['items']
            status_log.append(f"Downloaded {len(tracks)} tracks.")
        except Exception as e:
            return pd.DataFrame(), f"Playlist Error: {e}", status_log

        # 3. Filter Data
        track_ids = []
        track_info = {}
        for t in tracks:
            if t.get('track') and t['track'].get('id') and not t['track'].get('is_local'):
                tid = t['track']['id']
                track_ids.append(tid)
                track_info[tid] = {
                    'name': t['track']['name'],
                    'artist': t['track']['artists'][0]['name'],
                    'popularity': t['track']['popularity'],
                    'year': t['track']['album']['release_date'][:4] if t['track']['album']['release_date'] else "N/A"
                }
        
        if not track_ids:
             return pd.DataFrame(), "Error: No valid track IDs found (all local or empty).", status_log

        # 4. Audio Features
        audio_features = []
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i+50]
            if batch:
                try:
                    features = sp.audio_features(batch)
                    audio_features.extend([f for f in features if f])
                except:
                    continue

        if not audio_features:
            return pd.DataFrame(), "Error: API returned 0 audio features.", status_log

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

# --- DASHBOARD RENDER ---
df, pname_or_error, logs = get_data()

if not df.empty:
    st.title(f"🏝️ Ibiza Clout: {pname_or_error}")
    
    # ROW 1: 3D HERO
    st.subheader("1. The Balearic Vibe (Mood vs Energy vs Groove)")
    fig_3d = go.Figure(data=[go.Scatter3d(
        x=df['Valence'], y=df['Energy'], z=df['Danceability'],
        mode='markers',
        marker=dict(
            size=df['Popularity']/5, 
            color=df['Acousticness'], 
            colorscale='Viridis', 
            opacity=0.8, 
            colorbar=dict(title="Organic vs Digital")
        ),
        text=df['Track'] + " - " + df['Artist'],
        hovertemplate='<b>%{text}</b><br>Mood: %{x}<br>Energy: %{y}<br>Groove: %{z}<extra></extra>'
    )])
    fig_3d.update_layout(height=600, template='plotly_dark', margin=dict(l=0, r=0, b=0, t=0), 
                         scene=dict(xaxis_title='Mood', yaxis_title='Energy', zaxis_title='Groove'))
    st.plotly_chart(fig_3d, use_container_width=True)

    # ROW 2: STATS
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("BPM Distribution")
        fig_bpm = px.histogram(df, x="BPM", nbins=20, color_discrete_sequence=['#00CC96'])
        fig_bpm.update_layout(template='plotly_dark', height=300)
        st.plotly_chart(fig_bpm, use_container_width=True)
    with col2:
        st.subheader("Emotional Range (Valence)")
        fig_mood = px.scatter(df, x="Valence", y="Energy", color="Acousticness", template='plotly_dark')
        fig_mood.update_layout(height=300)
        st.plotly_chart(fig_mood, use_container_width=True)

    # ROW 3: HISTORY
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Key Architects")
        if 'Artist' in df.columns:
            top_art = df['Artist'].value_counts().head(7)
            fig_art = px.bar(x=top_art.index, y=top_art.values, color=top_art.values, color_continuous_scale='Bluered')
            fig_art.update_layout(template='plotly_dark', height=300, showlegend=False)
            st.plotly_chart(fig_art, use_container_width=True)
    with col4:
        st.subheader("Era (Decades)")
        if 'Year' in df.columns:
            df_sorted = df.sort_values('Year')
            fig_year = px.histogram(df_sorted, x="Year", color_discrete_sequence=['#AB63FA'])
            fig_year.update_layout(template='plotly_dark', height=300)
            st.plotly_chart(fig_year, use_container_width=True)

else:
    # THIS IS THE FIX: It now shows you the logs and the specific error
    st.title("⚠️ Data Load Failed")
    st.error(f"Reason: {pname_or_error}")
    with st.expander("See System Logs"):
        for log in logs:
            st.write(f"- {log}")
