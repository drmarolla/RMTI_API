import os
import streamlit as st

# Step up to the true repository root directory where the 'media' folder sits
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(CURRENT_DIR, "media")

# Explicit dictionary mapping of exact file names found on your server
MEDIA_MAP = {
    # 1. Ductal Progression
    "v1": "Ductal Progression & Subtype Divergence  Scenes 1-3.mp4",
    "a1": "Ductal Progression & Subtype Divergence (Scenes 1-3).mp3",
    
    # 2. Immune Barrier 4
    "v2": "Cells_forming_tumor_immune_barrier_scene 4.mp4",
    "a2": "Cells Forming Tumor Immune Barrier (Scene 4).mp3",
    
    # 3. Blocking Infiltration
    "v3": "Cells_blocking_tumor_infiltration_scene 5.mp4",
    "a3": "Cells Blocking Tumor Infiltration (Scene 5).mp3",
    
    # 4. Immune Barrier 6-8
    "v4": "Cells_forming_tumor_immune_barrier_Scenes 6-8.mp4",
    "a4": "Cells Forming Tumor Immune Barrier (Scenes 6-8).mp3",
    
    # 5. Antibodies Destroying
    "v5": "Antibodies_destroying_tumor_cells.mp4",
    "a5": "Antibodies Destroying Tumor Cells.mp3",
    
    # 6. Exposure & Resilience
    "v6": "Tumor Microenvironment Exposure & Resilience Deficit.mp4",
    "a6": "Tumor Microenvironment Exposure & Resilience Deficit.mp3",
    
    # 7. Escalating Residual Risk
    "v7": "Escalating Residual Risk Trajectory .mp4",
    "a7": "Escalating Residual Risk Trajectory.mp3",
    
    # Organ Case Studies
    "v_breast": "rmti_breast_case_study.mp4",
    "a_breast": "Breast Cancer Case Study (Stages 1-4).mp3",
    
    "v_liver": "rmti_liver_case_study.mp4",
    "a_liver": "Liver Cancer Case Study (Stages 1-4).mp3",
    
    "v_lung": "rmti_lung_case_study.mp4",
    "a_lung": "Lung Cancer Case Study (Stages 1-4).mp3"
}

def get_path(key):
    return os.path.join(MEDIA_DIR, MEDIA_MAP[key])

# --- Streamlit UI Render Configuration ---

st.title("RMTI Video Library")
st.caption("Narrated walkthroughs of the framework and case studies.")

st.warning(
    "⚠️ **Research prototype.** Not validated against outcomes, not a medical device, "
    "and not for patient-care or emergency decisions. Enter synthetic or published aggregate values only."
)

tab1, tab2 = st.tabs(["🧬 Microenvironment Dynamics", "🏥 Clinical Case Studies"])

with tab1:
    st.header("Resilience Model & Microenvironment Progression")
    st.write("Explore how the RMTI framework tracks cellular dynamics, tumor-immune barriers, and residual risks.")
    
    # 1. Ductal Progression
    st.subheader("1. Ductal Progression & Subtype Divergence")
    st.video(get_path("v1"))
    st.audio(get_path("a1"))
    st.caption("RMTI metrics: Quantifying initial structural anomalies and baseline divergence parameters.")
    st.divider()
    
    # 2. Immune Barrier 4
    st.subheader("2. Cells Forming Tumor Immune Barrier (Scene 4)")
    st.video(get_path("v2"))
    st.audio(get_path("a2"))
    st.caption("RMTI metrics: Mapping primary localized immune shields and spatial cell aggregation.")
    st.divider()
    
    # 3. Blocking Infiltration
    st.subheader("3. Cells Blocking Tumor Infiltration (Scene 5)")
    st.video(get_path("v3"))
    st.audio(get_path("a3"))
    st.caption("RMTI metrics: Evaluating barrier impedance and cytotoxic active exclusion zones.")
    st.divider()
    
    # 4. Immune Barrier 6-8
    st.subheader("4. Cells Forming Tumor Immune Barrier (Scenes 6-8)")
    st.video(get_path("v4"))
    st.audio(get_path("a4"))
    st.caption("RMTI metrics: Assessing matured defense networks and structural resilience profiles.")
    st.divider()
    
    # 5. Antibodies Destroying Tumor Cells
    st.subheader("5. Antibodies Destroying Tumor Cells")
    st.video(get_path("v5"))
    st.audio(get_path("a5"))
    st.caption("RMTI metrics: Tracking therapeutic clearance velocity and apoptotic cascade initialization.")
    st.divider()
    
    # 6. Exposure & Resilience Deficit
    st.subheader("6. Tumor Microenvironment Exposure & Resilience Deficit")
    st.video(get_path("v6"))
    st.audio(get_path("a6"))
    st.caption("RMTI metrics: Calculating systemic programmatic collapse and metabolic depletion rates.")
    st.divider()
    
    # 7. Escalating Residual Risk
    st.subheader("7. Escalating Residual Risk Trajectory")
    st.video(get_path("v7"))
    st.audio(get_path("a7"))
    st.caption("RMTI metrics: Forecasting long-term recurrence pathways and sub-clinical disease persistence.")

with tab2:
    st.header("Organ-Specific Framework Applications")
    st.write("See real-time trajectory evaluations mapped directly against localized progression indices across Stages 1 to 4.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Breast Cancer")
        st.video(get_path("v_breast"))
        st.audio(get_path("a_breast"))
        st.caption("Staged walkthrough tracking ductal to nodal progression indices across Stages 1–4.")
        
    with col2:
        st.subheader("Liver Cancer")
        st.video(get_path("v_liver"))
        st.audio(get_path("a_liver"))
        st.caption("Tracking vascular infiltration and local macrovascular portal vein density parameters across Stages 1–4.")
        
    with col3:
        st.subheader("Lung Cancer")
        st.video(get_path("v_lung"))
        st.audio(get_path("a_lung"))
        st.caption("Simulating alveolar structural compromises and distant metastatic vectors across Stages 1–4.")
