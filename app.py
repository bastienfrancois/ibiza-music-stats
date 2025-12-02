import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Ibiza 2025 Telemetry", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .block-container {padding-top: 1rem;}</style>""", unsafe_allow_html=True)

# --- AUTHENTICATION ---
try:
    client_id = st.secrets["CLIENT_ID"]
    client_secret = st.secrets["CLIENT_SECRET"]
except FileNotFoundError:
    st.error("🚨 Secrets missing! Please add CLIENT_ID and CLIENT_SECRET to Streamlit settings.")
    st.stop()

@st.cache_data(ttl=600)
def get_data():
    try:
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # 1. Search for a playlist (Fall back to Global Top 50 if search breaks)
        try:
            results = sp.search(q="Top Electronic 2025", type="playlist", limit=1)
            if results and results['playlists']['items']:
                playlist = results['playlists']['items'][0]
            else:
                raise Exception("Search failed")
        except:
            playlist = sp.playlist('37i9dQZEVXbMDoHDwVN2tF') # Fallback ID

        # 2. Get Tracks (Robust)
        # We increase limit to 50 to get a good sample size
        track_results = sp.playlist_items(playlist['id'], limit=50)
        tracks = track_results['items']
        
        # 3. Filter Clean IDs (The Crash Fix)
        track_ids = []
        track_info = {}
        for t in tracks:
            # CHECK: Ensure track exists AND is not a local file
            if t.get('track') and t['track'].get('id') and not t['track'].get('is_local'):
                tid = t['track']['id']
                track_ids.append(tid)
                track_info[tid] = {
                    'name': t['track']['name'],
                    'artist': t['track']['artists'][0]['name'],
                    'popularity': t['track']['popularity']
                }

        # 4. Get Audio Features (with Error Skipping)
        audio_features = []
        # Batch by 50 to be safe
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i+50]
            if batch:
                try:
                    features = sp.audio_features(batch)
                    # Filter out any Nones that slip through
                    valid_features = [f for f in features if f is not None]
                    audio_features.extend(valid_features)
                except Exception as e:
                    print(f"Skipped bad batch: {e}")
                    continue

        # 5. Build DataFrame
        df_data = []
        for feature in audio_features:
            tid = feature['id']
            info = track_info.get(tid, {})
            df_data.append({
                'Track': info.get('name'),
                'Artist': info.get('artist'),
                'Popularity': info.get('popularity'),
                'BPM': round(feature['tempo']),
                'Energy': feature['energy'],
                'Danceability': feature['danceability'],
                'Loudness': feature['loudness'],
                'Valence': feature['valence']
            })
        
        return pd.DataFrame(df_data), playlist['name']

    except Exception as e:
        # If everything fails, return empty so app doesn't crash
        print(f"Critical Data Error: {e}")
        return pd.DataFrame(), "Error"

# --- DASHBOARD RENDER ---
df, pname = get_data()

if not df.empty:
    st.title(f"🎛️ Analysis: {pname}")
    
    # ROW 1: 3D HERO
    st.subheader("1. The Ibiza Cube (Energy vs Dance vs Loudness)")
    fig_3d = go.Figure(data=[go.Scatter3d(
        x=df['Danceability'], y=df['Energy'], z=df['Loudness'],
        mode='markers',
        marker=dict(size=df['Popularity']/6, color=df['BPM'], colorscale='Turbo', opacity=0.8),
        text=df['Track'] + " - " + df['Artist'],
        hovertemplate='<b>%{text}</b><br>BPM: %{marker.color}<br>Dance: %{x}<br>Energy: %{y}<extra></extra>'
    )])
    fig_3d.update_layout(height=600, template='plotly_dark', margin=dict(l=0, r=0, b=0, t=0),
                         scene=dict(xaxis_title='Danceability', yaxis_title='Energy', zaxis_title='Loudness'))
    st.plotly_chart(fig_3d, use_container_width=True)

    # ROW 2: STATS
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tempo Distribution")
        fig_bpm = px.histogram(df, x="BPM", nbins=15, color_discrete_sequence=['#00CC96'])
        fig_bpm.update_layout(template='plotly_dark', height=300, margin=dict(l=0, r=0, b=0, t=30))
        st.plotly_chart(fig_bpm, use_container_width=True)
        
    with col2:
        st.subheader("Mood vs Intensity")
        fig_mood = px.scatter(df, x="Valence", y="Energy", color="Loudness", template='plotly_dark',
                              labels={"Valence": "Sad (0) <--> Happy (1)"})
        fig_mood.update_layout(height=300, margin=dict(l=0, r=0, b=0, t=30))
        st.plotly_chart(fig_mood, use_container_width=True)

    # ROW 3: ARTISTS & GAUGE
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Top Artists")
        if 'Artist' in df.columns:
            top_art = df['Artist'].value_counts().head(5)
            fig_art = px.bar(x=top_art.index, y=top_art.values, color=top_art.values, color_continuous_scale='Bluered')
            fig_art.update_layout(template='plotly_dark', height=300, showlegend=False)
            st.plotly_chart(fig_art, use_container_width=True)
        
    with col4:
        st.subheader("Playability Score")
        fig_g = go.Figure(go.Indicator(mode="gauge+number", value=df['Danceability'].mean(), 
                                       title={'text': "Avg Danceability"}, gauge={'axis': {'range': [0, 1]}}))
        fig_g.update_layout(template='plotly_dark', height=300)
        st.plotly_chart(fig_g, use_container_width=True)

else:
    # Error Display (Only shows if something is TRULY broken)
    st.error("⚠️ Data Loading Failed.")
    st.info("Troubleshooting: 1. Clear Cache (Press 'C'). 2. Check Streamlit Secrets are saved.")
