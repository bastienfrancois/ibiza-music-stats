import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ibiza 2025 Telemetry",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS STYLING (Hides the Streamlit Header/Footer for a clean iframe look) ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {padding-top: 1rem; padding-bottom: 1rem;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- CONFIGURATION ---
# Default to Spotify's 'Mint' (Top Electronic) if no ID is provided
PLAYLIST_ID = '37i9dQZF1DX4dyzvuaRJ0n' 

# --- AUTHENTICATION & DATA FETCHING ---
@st.cache_data(ttl=600)
def get_spotify_data(playlist_id):
    # Retrieve secrets safely from Streamlit Cloud
    try:
        client_id = st.secrets["CLIENT_ID"]
        client_secret = st.secrets["CLIENT_SECRET"]
    except FileNotFoundError:
        st.error("Secrets not found. Please set CLIENT_ID and CLIENT_SECRET in Streamlit Cloud settings.")
        return pd.DataFrame()

    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # 1. Get Tracks
    try:
        results = sp.playlist_tracks(playlist_id)
    except Exception as e:
        st.error(f"Error fetching playlist: {e}")
        return pd.DataFrame()
        
    tracks = results['items']
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

    # 2. Get Audio Features (Batching 100 at a time)
    audio_features = []
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        if batch:
            features = sp.audio_features(batch)
            audio_features.extend([f for f in features if f])

    # 3. Build DataFrame
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
    
    return pd.DataFrame(df_data)

# --- DASHBOARD RENDER ---
try:
    df = get_spotify_data(PLAYLIST_ID)

    if not df.empty:
        st.title("🎛️ Ibiza 2025: Audio Telemetry")
        
        # --- ROW 1: THE HERO 3D PLOT ---
        st.subheader("1. Multi-Dimensional Audio Space")
        fig_3d = go.Figure(data=[go.Scatter3d(
            x=df['Danceability'], 
            y=df['Energy'], 
            z=df['Loudness'],
            mode='markers',
            marker=dict(
                size=df['Popularity'] / 6, 
                color=df['BPM'], 
                colorscale='Turbo', 
                opacity=0.8,
                showscale=True,
                colorbar=dict(title='BPM', thickness=15)
            ),
            text=df['Track'] + " - " + df['Artist'],
            hovertemplate='<b>%{text}</b><br>Dance: %{x}<br>Energy: %{y}<br>Loudness: %{z} dB<extra></extra>'
        )])
        
        fig_3d.update_layout(
            height=600, 
            template='plotly_dark', 
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(
                xaxis=dict(title='Danceability', backgroundcolor="#0e1117", gridcolor="#333"),
                yaxis=dict(title='Energy', backgroundcolor="#0e1117", gridcolor="#333"),
                zaxis=dict(title='Loudness', backgroundcolor="#0e1117", gridcolor="#333"),
            )
        )
        st.plotly_chart(fig_3d, use_container_width=True)

        # --- ROW 2: ANALYSIS GRID ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("2. Tempo Distribution (BPM)")
            fig_bpm = px.histogram(df, x="BPM", nbins=20, color_discrete_sequence=['#00CC96'])
            fig_bpm.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', height=350)
            st.plotly_chart(fig_bpm, use_container_width=True)

        with col2:
            st.subheader("3. Mood vs. Intensity")
            fig_mood = px.scatter(df, x="Valence", y="Energy", color="Loudness", 
                                  hover_name="Track", template='plotly_dark',
                                  labels={"Valence": "Sad (0) <--> Happy (1)"})
            fig_mood.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=350)
            st.plotly_chart(fig_mood, use_container_width=True)

        # --- ROW 3: DEEP DIVE ---
        col3, col4, col5 = st.columns(3)

        with col3:
            st.subheader("4. Top Artists")
            top_artists = df['Artist'].value_counts().head(5)
            fig_art = px.bar(x=top_artists.index, y=top_artists.values, color=top_artists.values, color_continuous_scale='Bluered')
            fig_art.update_layout(template='plotly_dark', showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=300, 
                                  xaxis_title=None, yaxis_title="Tracks")
            st.plotly_chart(fig_art, use_container_width=True)

        with col4:
            st.subheader("5. Dynamic Range")
            fig_loud = px.box(df, y="Loudness", points="all", color_discrete_sequence=['#EF553B'])
            fig_loud.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', height=300)
            st.plotly_chart(fig_loud, use_container_width=True)

        with col5:
            st.subheader("6. Playability Score")
            avg_dance = df['Danceability'].mean()
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = avg_dance,
                title = {'text': "Avg Danceability"},
                gauge = {'axis': {'range': [0, 1]}, 'bar': {'color': "#AB63FA"}}
            ))
            fig_gauge.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=30, l=10, r=10, b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)

except Exception as e:
    st.error(f"System Error: {e}")