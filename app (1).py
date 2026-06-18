import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from loguru import logger

# Creates a diary file that rotates if it gets too large
logger.add("melodymatch.log", rotation="1 MB")
logger.info("🎵 MelodyMatch App Initialized.")

st.set_page_config(page_title="MelodyMatch", page_icon="website-logo1.png", layout="centered")

st.markdown("""       
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    [data-testid="stHeader"], [data-testid="stBottom"] { display: none; }
    
    /* Spotify Green Button */
    div.stButton > button:first-child {
        background-color: #1DB954; color: white; border-radius: 50px;
        border: none; padding: 12px 24px; font-weight: 700;
        transition: all 0.3s ease 0s; box-shadow: 0 4px 14px 0 rgba(29, 185, 84, 0.39);
    }
    div.stButton > button:hover { background-color: #1ed760; transform: scale(1.02); }
    
    /* Unified Song Cards with Brand Pink Hover Glow */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #181818;
        border: 1px solid #282828 !important;
        border-radius: 12px;
        padding: 5px; 
        transition: all 0.3s ease; /* Smooth animation */
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #D42068 !important; /* NEW Dark Pink border */
        box-shadow: 0 4px 15px 0 rgba(212, 32, 104, 0.25); /* NEW Dark Pink shadow */
    }
    
    /* Removes accidental backgrounds from inner columns */
    div[data-testid="stVerticalBlock"] {
        background-color: transparent !important;
        border: none !important;
    }
    
    /* The Song Mood Progress Bar (Dark Pink) */
    .stProgress > div > div > div > div { background-color: #D42068 !important; }
    
    /* The Vibe Match Metric (Spotify Green) */
    label[data-testid="stMetricLabel"] { color: #B3B3B3; }
    div[data-testid="stMetricValue"] { color: #1DB954 !important; }

    /* Dropdown Menu Hover & Selected Colors */
    li[role="option"]:hover {
        background-color: rgba(212, 32, 104, 0.2) !important; /* Faded Pink Hover */
    }
    li[role="option"][aria-selected="true"] {
        background-color: rgba(212, 32, 104, 0.4) !important; /* Slightly darker pink for the active selection */
    }
    /* Pulls the whole app closer to the top corner */
    div[data-testid="block-container"] { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

load_dotenv()

@st.cache_resource
def get_engine():
    logger.info("Initializing database connection engine...")
    raw_password = os.getenv("POSTGRES_PASSWORD")
    encoded_password = quote_plus(raw_password)
    
    # --- NEW FIX: Use DB_HOST from Docker, or default to localhost ---
    db_host = os.getenv("DB_HOST", "localhost")
    db_url = f"postgresql://postgres:{encoded_password}@{db_host}:5432/spotify_db"
    # -----------------------------------------------------------------
    
    logger.success("Database engine created successfully.")
    return create_engine(db_url)


@st.cache_data
def load_data():
    logger.info("Loading track data from database...")
    engine = get_engine()
    df = pd.read_sql_table('enriched_tracks', con=engine)
    df['display_name'] = df['track_name'] + " • " + df['artist']
    feature_cols = ['danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness', 
                    'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
    
    scaler = MinMaxScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])
    
    logger.info("Running K-Means clustering algorithm...")
    features_matrix = df[feature_cols].values
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(features_matrix)
    
    vibe_mapping = {
        0: "Balanced / Pop",
        1: "Mellow / Chill",
        2: "Acoustic / Melancholy",
        3: "Party / Upbeat",
        4: "Intense / High Energy"
    }
    df['vibe_cluster'] = [vibe_mapping[label] for label in cluster_labels]
    
    logger.success(f"Successfully loaded and processed {len(df)} tracks.")
    return df, feature_cols

@st.cache_resource
def train_model(_df, feature_cols):
    logger.info("Training NearestNeighbors AI model...")
    features_matrix = _df[feature_cols].values
    
    knn = NearestNeighbors(n_neighbors=20, metric='cosine', algorithm='brute')
    knn.fit(features_matrix)
    logger.success("KNN Model trained successfully.")
    return knn

def trigger_pink_hearts():
    """Custom CSS animation for floating pink hearts (Instant Burst)"""
    hearts_css = """
    <style>
    .heart-floating {
        position: fixed;
        bottom: -15vh; 
        z-index: 999999;
        pointer-events: none; 
    }
    
    /* Changed to reach full opacity faster (5%) so they don't fade in too slowly */
    @keyframes floatUp {
        0% { transform: translateY(0) scale(0.5) rotate(-10deg); opacity: 0; }
        5% { opacity: 1; }
        100% { transform: translateY(-130vh) scale(1.5) rotate(15deg); opacity: 0; }
    }
    </style>
    
    <div class="heart-floating" style="left: 5%; animation: floatUp 1.8s ease-out forwards 0.0s; font-size: 4rem;">💖</div>
    <div class="heart-floating" style="left: 15%; animation: floatUp 2.2s ease-out forwards 0.05s; font-size: 5.5rem;">💗</div>
    <div class="heart-floating" style="left: 25%; animation: floatUp 1.6s ease-out forwards 0.02s; font-size: 3rem;">💕</div>
    <div class="heart-floating" style="left: 35%; animation: floatUp 2.0s ease-out forwards 0.08s; font-size: 6rem;">💖</div>
    <div class="heart-floating" style="left: 45%; animation: floatUp 2.5s ease-out forwards 0.01s; font-size: 4.5rem;">💗</div>
    <div class="heart-floating" style="left: 55%; animation: floatUp 1.9s ease-out forwards 0.04s; font-size: 5rem;">💕</div>
    <div class="heart-floating" style="left: 65%; animation: floatUp 1.7s ease-out forwards 0.0s; font-size: 3.5rem;">💖</div>
    <div class="heart-floating" style="left: 75%; animation: floatUp 2.3s ease-out forwards 0.07s; font-size: 6.5rem;">💗</div>
    <div class="heart-floating" style="left: 85%; animation: floatUp 1.8s ease-out forwards 0.03s; font-size: 4rem;">💕</div>
    <div class="heart-floating" style="left: 95%; animation: floatUp 2.1s ease-out forwards 0.09s; font-size: 5rem;">💖</div>
    
    <div class="heart-floating" style="left: 10%; animation: floatUp 2.4s ease-out forwards 0.1s; font-size: 4.2rem;">💗</div>
    <div class="heart-floating" style="left: 30%; animation: floatUp 1.5s ease-out forwards 0.06s; font-size: 3.8rem;">💕</div>
    <div class="heart-floating" style="left: 50%; animation: floatUp 2.2s ease-out forwards 0.02s; font-size: 5.2rem;">💖</div>
    <div class="heart-floating" style="left: 70%; animation: floatUp 2.3s ease-out forwards 0.05s; font-size: 4.8rem;">💗</div>
    <div class="heart-floating" style="left: 90%; animation: floatUp 1.7s ease-out forwards 0.04s; font-size: 6rem;">💕</div>
    <div class="heart-floating" style="left: 20%; animation: floatUp 1.9s ease-out forwards 0.08s; font-size: 4.5rem;">💖</div>
    <div class="heart-floating" style="left: 40%; animation: floatUp 2.5s ease-out forwards 0.01s; font-size: 3.2rem;">💗</div>
    <div class="heart-floating" style="left: 60%; animation: floatUp 1.8s ease-out forwards 0.06s; font-size: 5.5rem;">💕</div>
    <div class="heart-floating" style="left: 80%; animation: floatUp 2.1s ease-out forwards 0.03s; font-size: 4rem;">💖</div>
    <div class="heart-floating" style="left: 8%; animation: floatUp 2.0s ease-out forwards 0.05s; font-size: 6.2rem;">💗</div>
    """
    st.markdown(hearts_css, unsafe_allow_html=True)

# 1. Create an empty container
loader_placeholder = st.empty()

# 2. Fill it with your logo and a loading message
with loader_placeholder.container():
    st.write("<br><br>", unsafe_allow_html=True) # Adds some top spacing
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col2:
        st.image("website-logo1.png", width=120)

# 3. Run the heavy data loading in the background
df, feature_cols = load_data()
knn_model = train_model(df, feature_cols)

# 4. Instantly destroy the loading screen once the data is ready!
loader_placeholder.empty()

# --- FRONTEND UI (FORMAL CENTERED HEADER) ---
# Adjusted column ratios to fit a much larger logo and text securely
spacer_left, col_logo, col_title, spacer_right = st.columns([0.8, 0.4, 2.2, 0.8], vertical_alignment="center")

with col_logo:
    # Increased the logo size significantly
    st.image("website-logo1.png", width=95) 

with col_title:
    # 1. Used a <div> instead of <h1> to kill the annoying Streamlit anchor link
    # 2. Forced a massive font-size (3.5rem) and heavy font-weight
    # 3. Kept white-space: nowrap so it never breaks to a second line
    st.markdown(
        "<div style='font-size: 3.5rem; font-weight: 800; margin: 0; padding: 0; text-align: left; white-space: nowrap;'>MelodyMatch</div>", 
        unsafe_allow_html=True
    )

# Subtle dividing line that spans the whole page
st.markdown("<hr style='margin-top: 15px; margin-bottom: 20px; border-color: #282828;'>", unsafe_allow_html=True)

# Main instruction text (Centered and slightly larger to balance the massive new header)
st.markdown("<p style='text-align: left; color: #B3B3B3; font-size: 1.1rem;'>Search for a song you love to find new tracks with the same vibe.</p>", unsafe_allow_html=True)
st.write("")

song_list = sorted(df['display_name'].unique().tolist())

selected_display = st.selectbox(
    "🔍 Search your library:", 
    options=song_list,
    index=None, 
    placeholder="Start typing a song or artist... (e.g., Better - Khalid)"
)

num_recs = st.slider("Playlist Size:", 1, 10, 5)

if st.button("Discover New Music", use_container_width=True):
    if not selected_display:
        logger.warning("User clicked search without selecting a track.")
        st.warning("🎵 Please search and select a track first!")
    else:
        logger.info(f"Generating {num_recs} recommendations based on: {selected_display}")
        target_song = df[df['display_name'] == selected_display].iloc[0]
        song_idx = target_song.name
        
        st.success(f"Listening to the vibe of **{target_song['track_name']}**...")
        
        distances, indices = knn_model.kneighbors(df.iloc[song_idx][feature_cols].values.reshape(1, -1), n_neighbors=num_recs + 10)
        
        logger.success("Recommendations successfully generated. Triggering UI animations.")
        trigger_pink_hearts() 
        st.write("---")
        st.markdown("### 🎧 Your Custom Playlist")
        
        displayed_count = 1
        for i in range(1, len(distances[0])):
            if displayed_count > num_recs: break
                
            match_row = df.iloc[indices[0][i]]
            
            if match_row['track_name'].lower() == target_song['track_name'].lower():
                continue
            
            similarity = (1 - distances[0][i]) * 100
            embed_url = f"https://open.spotify.com/embed/track/{match_row['track_id']}?utm_source=generator&theme=0"
            
            with st.container(border=True):
                col_info, col_player = st.columns([1, 1.2], vertical_alignment="center")
                
                with col_info:
                    st.markdown(f"#### {displayed_count}. {match_row['track_name']}")
                    st.markdown(f"**{match_row['artist']}**")
                    
                    # --- THE FIX: Pink UI Badge ---
                    vibe_badge_html = f"""
                        <div style='background-color: rgba(29, 185, 84, 0.15); 
                                    color: #1DB954; 
                                    padding: 4px 12px; 
                                    border-radius: 20px; 
                                    display: inline-block; 
                                    font-size: 12px; 
                                    font-weight: 600; 
                                    margin-bottom: 10px; 
                                    border: 1px solid rgba(29, 185, 84, 0.3);'>
                            🍃 Vibe: {match_row['vibe_cluster']}
                        </div>
                    """
                    st.markdown(vibe_badge_html, unsafe_allow_html=True)
                    # ---------------------------------------------------
                    
                    st.metric("Vibe Match", f"{similarity:.1f}%")
                
                with col_player:
                    st.components.v1.iframe(src=embed_url, height=152)
                
                #st.write("") 
                st.caption("🌷 **Track Energy** (Lowkey → High Voltage)")
                st.progress(float(match_row['valence']))
                
            displayed_count += 1