import os
import streamlit as st

# 1. Define a robust helper function to safely resolve file paths
def get_media_path(filename):
    # Standardize path configurations for Streamlit Cloud environments
    base_paths = ["media", os.path.join("RMTI_v5_site", "media")]
    
    for base in base_paths:
        target_path = os.path.join(base, filename)
        if os.path.exists(target_path):
            return target_path
            
    # Fallback to scanning the directory for structural character mismatches (like hyphens vs dashes)
    for base in base_paths:
        if os.path.exists(base):
            for file in os.listdir(base):
                # Clean strings to identify name matches safely
                if file.replace("–", "-").lower() == filename.replace("–", "-").lower():
                    return os.path.join(base, file)
                    
    # Ultimate fallback string if no file matches are found
    return os.path.join("media", filename)

# --- Update your layout application implementation using the helper function below ---

st.title("RMTI Video Library")
st.caption("Narrated walkthroughs of the framework and case studies.")

st.warning(
    "⚠️ **Research prototype.** Not validated against outcomes, not a medical device, "
    "and not for patient-care or emergency decisions. Enter synthetic or published aggregate values only."
)

tab1, tab2 = st.tabs(["🧬 Microenvironment Dynamics", "🏥 Clinical Case Studies"])

with tab1:
    st.header("Resilience Model & Microenvironment Progression")
    
    # 1. Ductal Progression (Using safe resolution)
    st.subheader("1. Ductal Progression & Subtype Divergence")
    
    video_1 = get_media_path("Ductal Progression & Subtype Divergence Scenes 1-3.mp4")
    audio_1 = get_media_path("Ductal Progression & Subtype Divergence Scenes 1-3.mp3")
    
    st.video(video_1)
    st.audio(audio_1)
    st.caption("RMTI metrics: Quantifying initial structural anomalies and baseline divergence parameters.")
