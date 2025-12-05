import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Ibiza Clout Study", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .block-container {padding-top: 1rem;}</style>""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    # Updated to version 3 as requested
    return pd.read_csv("ibiza_data_electronic.csv")

try:
    raw_df = load_data()
    
    # --- PRE-PROCESSING ---
    # 1. Strict BPM Filter (60 to 160)
    df = raw_df[(raw_df['BPM'] >= 65) & (raw_df['BPM'] <= 160)].copy()
    
    # 2. Create "Display Title" (Artist - Full Track Name)
    df['Artist_Clean'] = df['Artist'].astype(str).str.replace(r"[\[\]']", "", regex=True)
    df['Display_Title'] = df['Artist_Clean'] + " - " + df['Track']

    # --- DASHBOARD HEADER ---
    st.title("🏝️ Ibiza Clout Study - A statistical analysis of 10000 Ibiza Songs")
    st.caption(f"Analyzing {len(df):,} Tracks | BPM Range: 50-200 | Source: Kaggle Research Data fitered for electronic genres")

    # --- ROW 1: THE 3D ANALYSIS ---
    st.subheader("1. The Ibiza Sound Structure")
    st.markdown("X: **Tempo (BPM)** | Y: **Danceability** | Z: **Energy** | Color: **Popularity**")
    
    fig_3d = px.scatter_3d(df, 
                        x='BPM', 
                        y='Danceability', 
                        z='Energy', # Fixed capitalization (was 'energy')
                        color='Popularity', 
                        size='key', 
                        hover_name='Display_Title',
                        hover_data={'BPM': True, 'key': True, 'Display_Title': False},
                        template='plotly_dark',
                        color_continuous_scale='Turbo',
                        title="3D Telemetry: BPM vs Danceability vs Energy")
    
    # Make the graph tall
    fig_3d.update_layout(height=800, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig_3d, use_container_width=True)

    # --- ROW 2: DETAILED STATS ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Tempo Analysis (Strict 2-BPM Granularity)")
        fig_bpm = px.histogram(df, x="BPM", 
                               nbins=75, 
                               template='plotly_dark', 
                               color_discrete_sequence=['#00CC96'])
        
        # Force strict 2-beat intervals
        fig_bpm.update_traces(xbins=dict(start=50, end=200, size=2))
        fig_bpm.update_layout(bargap=0.05, xaxis_title="BPM (Beats Per Minute)")
        st.plotly_chart(fig_bpm, use_container_width=True)
        
    with c2:
        st.subheader("Energy vs Danceability")
        fig_scatter = px.scatter(df, x="Danceability", y="Energy", 
                                 color="Genre" if "Genre" in df.columns else "Popularity",
                                 hover_name="Display_Title",
                                 template='plotly_dark',
                                 title="Club Readiness (Groove vs Intensity)")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- ROW 3: TOP 50 & GENRES ---
    st.subheader("Top 50 Most Popular Tracks")
    
    # Sort by popularity and take top 50
    top_50 = df.sort_values('Popularity', ascending=False).head(50)
    
    # Horizontal Bar Chart, Colored by Loudness
    fig_top = px.bar(top_50, 
                     x='Popularity', 
                     y='Display_Title', 
                     orientation='h', # Horizontal
                     template='plotly_dark',
                     color='Loudness', 
                     color_continuous_scale='Magma', 
                     hover_data=['BPM', 'Genre'])
    
    # Invert Y axis so #1 is at the top
    fig_top.update_layout(yaxis=dict(autorange="reversed"), 
                          height=1000, 
                          xaxis_title="Popularity Score (0-100)", 
                          yaxis_title=None)
    st.plotly_chart(fig_top, use_container_width=True)

except Exception as e:
    st.error(f"Something went wrong: {e}")
    st.info("Tip: Ensure your 'ibiza_data3.csv' is uploaded to GitHub.")




