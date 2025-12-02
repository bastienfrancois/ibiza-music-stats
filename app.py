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
# Try to get secrets, otherwise show a helpful error
try:
    client_id = st.secrets["CLIENT_ID"]
    client_secret = st.secrets["CLIENT_SECRET"]
except FileNotFoundError:
    st.error("🚨 Secrets missing! Please add CLIENT_ID and CLIENT_SECRET to Streamlit settings.")
    st.stop()

@st.cache_data(ttl=600)
def get_data():
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # --- ROBUST PLAYLIST FETCHING ---
    # 1. Try a search instead of a hardcoded ID (Much safer)
    try:
        # Search for a popular electronic playlist
        results = sp.search(q="Top Electronic 2025", type="playlist", limit=1)
        if results['playlists']['items']:
            target_id = results['playlists']['items'][0]['id']
            playlist_name = results['playlists']['items'][0]['name']
        else:
            # Fallback to Global Top 50 if search fails
            target_id = '37i9dQZEVXbMDoHDwVN2tF'
            playlist_name = "Global Top 50 (Fallback)"
            
        # 2. Get Tracks using the new 'playlist_items' (Not playlist_tracks)
        results = sp.playlist_items(target_id)
        tracks = results['items']
        
    except Exception as e:
        st.error(f"Spotify API Error: {e}")
        return pd.DataFrame(), "Error"

    # --- PROCESS DATA ---
    track_ids = []
    track_info = {}
    for t in tracks:
        if t['track'] and t['track']['id']:
            tid = t['track']['id']
            track_ids.append(tid)
            track_info[tid] = {
                'name': t['track']['name'],
                'artist': t['track']['artists'][0]['name'],
                'popularity': t['track']['popularity']
            }

    # Batch fetch features
    audio_features = []
    if track_ids:
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            if batch:
                try:
                    features = sp.audio_features(batch)
                    audio_features.extend([f for f in features if f])
                except:
                    pass

    # Build DataFrame
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
    
    return pd.DataFrame(df_data), playlist_name

# --- DASHBOARD ---
df, pname = get_data()

if not df.empty:
    st.title(f"🎛️ Analysis: {pname}")
    
    # 1. 3D Plot
    st.subheader("1. The Ibiza Cube (Energy vs Dance vs Loudness)")
    fig_3d = go.Figure(data=[go.Scatter3d(
        x=df['Danceability'], y=df['Energy'], z=df['Loudness'],
        mode='markers',
        marker=dict(size=df['Popularity']/6, color=df['BPM'], colorscale='Turbo', opacity=0.8),
        text=df['Track'] + " - " + df['Artist'],
        hovertemplate='<b>%{text}</b><br>BPM: %{marker.color}<br>Dance: %{x}<br>Energy: %{y}<extra></extra>'
    )])
    fig_3d.update_layout(height=500, template='plotly_dark', margin=dict(l=0, r=0, b=0, t=0),
                         scene=dict(xaxis_title='Danceability', yaxis_title='Energy', zaxis_title='Loudness'))
    st.plotly_chart(fig_3d, use_container_width=True)

    # 2. Grid Stats
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tempo (BPM)")
        fig_bpm = px.histogram(df, x="BPM", nbins=15, color_discrete_sequence=['#00CC96'])
        fig_bpm.update_layout(template='plotly_dark', height=300)
        st.plotly_chart(fig_bpm, use_container_width=True)
        
    with col2:
        st.subheader("Mood (Valence)")
        fig_mood = px.scatter(df, x="Valence", y="Energy", color="Loudness", template='plotly_dark')
        fig_mood.update_layout(height=300)
        st.plotly_chart(fig_mood, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Top Artists")
        top_art = df['Artist'].value_counts().head(5)
        fig_art = px.bar(x=top_art.index, y=top_art.values, color=top_art.values)
        fig_art.update_layout(template='plotly_dark', height=300, showlegend=False)
        st.plotly_chart(fig_art, use_container_width=True)
        
    with col4:
        st.subheader("Playability Gauge")
        fig_g = go.Figure(go.Indicator(mode="gauge+number", value=df['Danceability'].mean(), 
                                       title={'text': "Avg Danceability"}, gauge={'axis': {'range': [0, 1]}}))
        fig_g.update_layout(template='plotly_dark', height=300)
        st.plotly_chart(fig_g, use_container_width=True)

else:
    st.write("No data found. Check API quotas or Secrets.")
