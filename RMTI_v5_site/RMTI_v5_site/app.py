import streamlit as st

st.title("RMTI Video Library")
st.caption("Narrated walkthroughs of the framework and case studies.")

# Required System Disclaimer Banner
st.warning(
    "⚠️ **Research prototype.** Not validated against outcomes, not a medical device, "
    "and not for patient-care or emergency decisions. Enter synthetic or published aggregate values only."
)

# Structural Navigation Tabs
tab1, tab2 = st.tabs(["🧬 Microenvironment Dynamics", "🏥 Clinical Case Studies"])

with tab1:
    st.header("Resilience Model & Microenvironment Progression")
    st.write("Explore how the RMTI framework tracks cellular dynamics, tumor-immune barriers, and residual risks.")
    
    # 1. Ductal Progression
    st.subheader("1. Ductal Progression & Subtype Divergence")
    st.video("media/Ductal Progression & Subtype Divergence Scenes 1–3.mp4")
    st.audio("media/Ductal Progression & Subtype Divergence Scenes 1–3.mp3")
    st.caption("RMTI metrics: Quantifying initial structural anomalies and baseline divergence parameters.")
    st.divider()
    
    # 2. Immune Barrier 4
    st.subheader("2. Cells Forming Tumor Immune Barrier (Scene 4)")
    st.video("media/Cells_forming_tumor_immune_barrier_scene 4.mp4")
    st.audio("media/Cells_forming_tumor_immune_barrier_scene 4.mp3")
    st.caption("RMTI metrics: Mapping primary localized immune shields and spatial cell aggregation.")
    st.divider()
    
    # 3. Blocking Infiltration
    st.subheader("3. Cells Blocking Tumor Infiltration (Scene 5)")
    st.video("media/Cells_blocking_tumor_infiltration_scene 5.mp4")
    st.audio("media/Cells_blocking_tumor_infiltration_scene 5.mp3")
    st.caption("RMTI metrics: Evaluating barrier impedance and cytotoxic active exclusion zones.")
    st.divider()
    
    # 4. Immune Barrier 6-8
    st.subheader("4. Cells Forming Tumor Immune Barrier (Scenes 6–8)")
    st.video("media/Cells_forming_tumor_immune_barrier_Scenes 6–8.mp4")
    st.audio("media/Cells_forming_tumor_immune_barrier_Scenes 6–8.mp3")
    st.caption("RMTI metrics: Assessing matured defense networks and structural resilience profiles.")
    st.divider()
    
    # 5. Antibodies Destroying Tumor Cells
    st.subheader("5. Antibodies Destroying Tumor Cells")
    st.video("media/Antibodies_destroying_tumor_cells.mp4")
    st.audio("media/Antibodies_destroying_tumor_cells.mp3")
    st.caption("RMTI metrics: Tracking therapeutic clearance velocity and apoptotic cascade initialization.")
    st.divider()
    
    # 6. Exposure & Resilience Deficit
    st.subheader("6. Tumor Microenvironment Exposure & Resilience Deficit")
    st.video("media/Tumor Microenvironment Exposure & Resilience Deficit.mp4")
    st.audio("media/Tumor Microenvironment Exposure & Resilience Deficit.mp3")
    st.caption("RMTI metrics: Calculating systemic programmatic collapse and metabolic depletion rates.")
    st.divider()
    
    # 7. Escalating Residual Risk
    st.subheader("7. Escalating Residual Risk Trajectory")
    st.video("media/Escalating Residual Risk Trajectory .mp4")
    st.audio("media/Escalating Residual Risk Trajectory .mp3")
    st.caption("RMTI metrics: Forecasting long-term recurrence pathways and sub-clinical persistence.")

with tab2:
    st.header("Organ-Specific Framework Applications")
    st.write("See real-time trajectory evaluations mapped directly against localized progression indices across Stages 1 to 4.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Breast Cancer")
        st.video("media/rmti_breast_case_study.mp4")
        st.audio("media/rmti_breast_case_study.mp3")
        st.caption("Staged walkthrough tracking ductal to nodal progression indices across Stages 1–4.")
        
    with col2:
        st.subheader("Liver Cancer")
        st.video("media/rmti_liver_case_study.mp4")
        st.audio("media/rmti_liver_case_study.mp3")
        st.caption("Tracking vascular infiltration and local macrovascular portal vein density parameters across Stages 1–4.")
        
    with col3:
        st.subheader("Lung Cancer")
        st.video("media/rmti_lung_case_study.mp4")
        st.audio("media/rmti_lung_case_study.mp3")
        st.caption("Simulating alveolar structural compromises and distant metastatic vectors across Stages 1–4.")
