import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Ibiza Cultural Telemetry", layout="wide", initial_sidebar_state="collapsed")
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
        
        # --- CULTURAL SEARCH LOGIC ---
        # We search specifically for the "Sound of Ibiza" rather than generic EDM
        search_queries = [
            "Ibiza Classics",       # The Heritage/Anthems
            "Balearic Beat",        # The original eclectic sound
            "Ibiza Global Radio",   # The modern authentic sound
            "Cafe del Mar"          # The Chillout/Sunset culture
        ]
        
        playlist = None
        for query in search_queries:
            try:
                # Find the most popular playlist for this specific cultural tag
                results = sp.search(q=query, type="playlist", limit=1)
                if results and results['playlists']['items']:
                    playlist = results['playlists']['items'][0]
                    break # Stop if we found a good one
            except:
                continue
        
        if not playlist:
            # Absolute fallback if all searches fail
            playlist = sp.playlist('37i9dQZF1DWVlysXLVxUxE') # "Ibiza Classics" Official by Spotify

        # 2. Get Tracks (Increased limit for better statistical clout)
        track_results = sp.playlist_items(playlist['id'], limit=80)
        tracks = track_results['items']
        
        # 3. Filter Clean IDs & Remove "Filler"
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
                    'release_year': t['track']['album']['release_date'][:4] # Track the era
                }

        # 4. Get Audio Features (Batching)
        audio_features = []
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i+50]
            if batch:
                try:
                    features = sp.audio_features(batch)
                    audio_features.extend([f for f in features if f is not None])
                except:
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
                'Year': info.get('release_year'),
                'BPM': round(feature['tempo']),
                'Energy': feature['energy'],
                'Danceability': feature['danceability'],
                'Loudness': feature['loudness'],
                'Valence': feature['valence'], # Mood/Spirit
                'Acousticness': feature['acousticness'] # High in Balearic, low in EDM
            })
        
        return pd.DataFrame(df_data), playlist['name']

    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame(), "Error"

# --- DASHBOARD RENDER ---
df, pname = get_data()

if not df.empty:
    st.title(f"🏝️ Ibiza Clout: {pname}")
    st.markdown("Analyzing the specific audio signature of the 'White Isle'—distinct from generic commercial EDM.")
    
    # ROW 1: The "Vibe" Cube
    st.subheader("1. The 'Balearic' Spectrum")
    fig_3d = go.Figure(data=[go.Scatter3d(
        x=df['Valence'], y=df['Energy'], z=df['Danceability'],
        mode='markers',
        marker=dict(size=df['Popularity']/6, color=df['Acousticness'], colorscale='Viridis', opacity=0.8, showscale=True, colorbar=dict(title="Organic/Acoustic")),
        text=df['Track'] + " - " + df['Artist'],
        hovertemplate='<b>%{text}</b><br>Mood (Valence): %{x}<br>Energy: %{y}<br>Danceability: %{z}<extra></extra>'
    )])
    fig_3d.update_layout(height=600, template='plotly_dark', margin=dict(l=0, r=0, b=0, t=0),
                         scene=dict(xaxis_title='Mood (Happy/Sad)', yaxis_title='Energy (Chill/Club)', zaxis_title='Groove (Dance)'))
    st.plotly_chart(fig_3d, use_container_width=True)

    # ROW 2: Cultural Indicators
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("BPM: Sunset vs. Club")
        # Ibiza is often slower (90-110 BPM) or House (120-128), unlike Fast EDM (140+)
        fig_bpm = px.histogram(df, x="BPM", nbins=20, color_discrete_sequence=['#00CC96'])
        fig_bpm.update_layout(template='plotly_dark', height=300, margin=dict(l=0, r=0, b=0, t=30))
        st.plotly_chart(fig_bpm, use_container_width=True)
        
    with col2:
        st.subheader("Emotional Range (Valence)")
        # Balearic beat is famous for "Melancholy Euphoria" (High Energy, Mid Valence)
        fig_mood = px.scatter(df, x="Valence", y="Energy", color="Acousticness", template='plotly_dark',
                              labels={"Valence": "Melancholy <---> Euphoric", "Acousticness": "Electronic <---> Organic"})
        fig_mood.update_layout(height=300, margin=dict(l=0, r=0, b=0, t=30))
        st.plotly_chart(fig_mood, use_container_width=True)

    # ROW 3: Legends & Eras
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Key Artists (The Architects)")
        if 'Artist' in df.columns:
            top_art = df['Artist'].value_counts().head(8)
            fig_art = px.bar(x=top_art.index, y=top_art.values, color=top_art.values, color_continuous_scale='Bluered')
            fig_art.update_layout(template='plotly_dark', height=300, showlegend=False)
            st.plotly_chart(fig_art, use_container_width=True)
        
    with col4:
        st.subheader("Era Distribution")
        if 'Year' in df.columns:
            # Sort years to make the chart logical
            df_sorted = df.sort_values('Year')
            fig_year = px.histogram(df_sorted, x="Year", color_discrete_sequence=['#AB63FA'])
            fig_year.update_layout(template='plotly_dark', height=300, title="Decades of Influence")
            st.plotly_chart(fig_year, use_container_width=True)

else:
    st.error("⚠️ Data Loading Failed. Please check your Secrets or try clearing cache.")
