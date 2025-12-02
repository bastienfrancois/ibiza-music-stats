import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Ibiza 2025 Telemetry", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .block-container {padding-top: 1rem;}</style>""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    # This looks for the file you just uploaded to GitHub
    return pd.read_csv("ibiza_data2.csv")

try:
    df = load_data()
    
    st.title("🏝️ Ibiza Telemetry Dashboard")
    st.caption(f"Analysis of {len(df):,} Tracks | Source: Offline Dataset")

    # --- ROW 1: THE HERO CUBE ---
    st.subheader("1. The Vibe Cube (Mood vs Energy vs Groove)")
    # We use a predefined color scale to make it look professional
    fig = px.scatter_3d(df, x='Valence', y='Energy', z='Danceability',
                        color='Acousticness', size='Popularity',
                        hover_name='Track', 
                        template='plotly_dark',
                        color_continuous_scale='Viridis',
                        labels={'Valence': 'Mood', 'Energy': 'Intensity', 'Danceability': 'Groove'})
    
    fig.update_layout(height=700, margin=dict(l=0,r=0,b=0,t=0), scene_camera=dict(eye=dict(x=1.5, y=1.5, z=0.5)))
    st.plotly_chart(fig, use_container_width=True)

    # --- ROW 2: CORE STATS ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("BPM (Tempo)")
        # Green histogram for Tempo
        fig_bpm = px.histogram(df, x="BPM", nbins=30, template='plotly_dark', color_discrete_sequence=['#00CC96'])
        fig_bpm.update_layout(bargap=0.1)
        st.plotly_chart(fig_bpm, use_container_width=True)
        
    with c2:
        st.subheader("Evolution (Year)")
        # Purple histogram for Eras
        # We filter out 'N/A' years to prevent errors
        clean_years = df[df['Year'] != 'N/A'].sort_values('Year')
        fig_year = px.histogram(clean_years, x="Year", template='plotly_dark', color_discrete_sequence=['#AB63FA'])
        fig_year.update_layout(bargap=0.1)
        st.plotly_chart(fig_year, use_container_width=True)

    # --- ROW 3: DEEP DIVE ---
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Top Artists")
        # Filter out the "Session" tracks so we only see Real Artists in the chart
        real_artists = df[~df['Track'].str.contains("Session", na=False)]['Artist'].value_counts().head(10)
        fig_art = px.bar(x=real_artists.index, y=real_artists.values, template='plotly_dark', 
                         color=real_artists.values, color_continuous_scale='Bluered')
        fig_art.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Tracks")
        st.plotly_chart(fig_art, use_container_width=True)
        
    with c4:
        st.subheader("Mood Map")
        fig_mood = px.scatter(df, x="Valence", y="Energy", color="Acousticness", 
                              template='plotly_dark', title="Sad/Dark (Left) vs Happy/Energetic (Right)")
        st.plotly_chart(fig_mood, use_container_width=True)

except FileNotFoundError:
    st.error("⚠️ File 'ibiza_data.csv' not found.")
    st.info("Make sure you uploaded the CSV file to the root of your GitHub repository.")
except Exception as e:
    st.error(f"Something went wrong: {e}")
