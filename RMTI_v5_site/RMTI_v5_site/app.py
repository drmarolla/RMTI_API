import os
import streamlit as st

st.title("RMTI Video Library")

# 🔍 DIAGNOSTIC EXPLORER: This will show us exactly where files are located
st.header("📂 Debugging Workspace File Path Tracker")
CURRENT_FILE_PATH = os.path.abspath(__file__)
CURRENT_DIR = os.path.dirname(CURRENT_FILE_PATH)
REPO_ROOT = os.path.dirname(CURRENT_DIR)

st.write(f"**App script location:** `{CURRENT_FILE_PATH}`")

# Check nested media directory
nested_media = os.path.join(CURRENT_DIR, "media")
root_media = os.path.join(REPO_ROOT, "media")

st.markdown("### Checking Media Folders:")
if os.path.exists(nested_media):
    st.success(f"Found `media` folder inside subfolder: `{nested_media}`")
    st.write("**Files found:**", os.listdir(nested_media))
    MEDIA_DIR = nested_media
elif os.path.exists(root_media):
    st.success(f"Found `media` folder at repository root: `{root_media}`")
    st.write("**Files found:**", os.listdir(root_media))
    MEDIA_DIR = root_media
else:
    st.error("❌ Could not find a folder named 'media' anywhere near app.py.")
    # Search around for directories
    st.write("Available folders in app directory:", os.listdir(CURRENT_DIR))
    MEDIA_DIR = None

# Helper function to find files dynamically
def safe_resolve(filename):
    if not MEDIA_DIR or not os.path.exists(MEDIA_DIR):
        return filename
    
    target_clean = filename.replace("–", "-").replace(" ", "").strip().lower()
    
    for actual_file in os.listdir(MEDIA_DIR):
        actual_clean = actual_file.replace("–", "-").replace(" ", "").strip().lower()
        if actual_clean == target_clean:
            return os.path.join(MEDIA_DIR, actual_file)
            
    return os.path.join(MEDIA_DIR, filename)

# --- Streamlit UI Render Configuration ---
st.divider()
st.caption("Narrated walkthroughs of the framework and case studies.")

st.warning(
    "⚠️ **Research prototype.** Not validated against outcomes, not a medical device, "
    "and not for patient-care or emergency decisions. Enter synthetic or published aggregate values only."
)

tab1, tab2 = st.tabs(["🧬 Microenvironment Dynamics", "🏥 Clinical Case Studies"])

with tab1:
    st.header("Resilience Model & Microenvironment Progression")
    
    st.subheader("1. Ductal Progression & Subtype Divergence")
    try:
        resolved_video = safe_resolve("Ductal Progression & Subtype Divergence Scenes 1-3.mp4")
        st.video(resolved_video)
        resolved_audio = safe_resolve("Ductal Progression & Subtype Divergence Scenes 1-3.mp3")
        st.audio(resolved_audio)
    except Exception as e:
        st.exception(e)
        
    st.divider()
    
    st.subheader("2. Cells Forming Tumor Immune Barrier (Scene 4)")
    try:
        st.video(safe_resolve("Cells_forming_tumor_immune_barrier_scene 4.mp4"))
        st.audio(safe_resolve("Cells_forming_tumor_immune_barrier_scene 4.mp3"))
    except Exception as e:
        st.exception(e)
