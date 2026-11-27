"""Case studies: Dual-layer 3D + 2D RMTI split panels, mechanism flow, and outcomes."""
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# Safe helper path to resolve files relative to app location
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CURRENT_DIR)
MEDIA_DIR = os.path.join(REPO_ROOT, "media")

RAW_VIDEOS = "https://githubusercontent.com"

STUDIO_CLIPS = {
    "liver": (
        "case_liver.mp4",
        "Clinical Oncology · Hepatocellular Carcinoma (HCC)",
        "Main 3D + 2D: BCLC & ALBI Trajectory",
        (
            ("L · Likelihood", "Cirrhosis & etiology incidence rate", "#0284C7"),
            ("E · Exposure", "At-risk cohort reach & staging", "#EF4444"),
            ("V · Vulnerability", "ALBI hepatic reserve & portal invasion", "#F59E0B"),
            ("1 − ρ · Resilience", "Second-line systemic & surveillance delivery", "#10B981"),
        ),
        "Upgrading surveillance and second-line systemic delivery (ρ) intercepts progression before hepatic reserve (V) collapses, cutting residual risk R from 0.258 (Tier 3 High) to 0.107 (Tier 2 Moderate).",
    ),
    "lung": (
        "case_lung.mp4",
        "Clinical Oncology · Non-Small Cell Lung Cancer",
        "Main 3D + 2D: LDCT Screening Interception",
        (
            ("L · Likelihood", "Smoking & occupational carcinogenesis", "#0284C7"),
            ("E · Exposure", "Target screening population coverage", "#EF4444"),
            ("V · Vulnerability", "Late-stage nodal/metastatic burden", "#F59E0B"),
            ("1 − ρ · Resilience", "Low-dose CT screening & rapid resection", "#10B981"),
        ),
        "Structured LDCT screening shifts Stage IV diagnosis from 35–44% down to 13% (Sabakhtarishvili et al., 2025), compressing residual risk R from 0.281 to 0.112.",
    ),
    "breast": (
        "case_breast.mp4",
        "Clinical Oncology · HR-Positive Breast Cancer",
        "Main 3D + 2D: Endocrine & Targeted Trajectory",
        (
            ("L · Likelihood", "HR+/HER2− metastatic progression hazard", "#0284C7"),
            ("E · Exposure", "Post-endocrine treatment cohort", "#EF4444"),
            ("V · Vulnerability", "Visceral crisis & genomic resistance", "#F59E0B"),
            ("1 − ρ · Resilience", "Timely second-line targeted therapy access", "#10B981"),
        ),
        "Closing the 30% pre-second-line attrition gap (O'Shaughnessy et al., 2026) raises system resilience ρ and lowers residual risk R from 0.234 to 0.098.",
    ),
    "urban": (
        "case_african_cities.mp4",
        "Disaster Science · Six Sub-Saharan African Cities",
        "Main 3D + 2D: Urban Flood & Heat Governance",
        (
            ("L · Likelihood", "Extreme rainfall, flood & heatwave frequency", "#0284C7"),
            ("E · Exposure", "Transit corridors, clinics & dense settlements", "#EF4444"),
            ("V · Vulnerability", "Drainage deficit & baseline health fragility", "#F59E0B"),
            ("1 − ρ · Resilience", "$50M green-grey infrastructure & health continuity", "#10B981"),
        ),
        "Allocating targeted resilience upgrades (ρ) across Bamako, Lagos, and Lilongwe cuts composite residual risk R by up to 48% and maximizes Expected Annual Loss (EAL) avoided per million residents.",
    ),
}

def scan_and_resolve(target_filename):
    if not os.path.exists(MEDIA_DIR):
        return os.path.join("media", target_filename)
    def make_key(name):
        return "".join(c for c in name.replace("–", "-").lower() if c.isalnum())
    target_key = make_key(target_filename)
    target_ext = os.path.splitext(target_filename).lower()
    for actual_file in os.listdir(MEDIA_DIR):
        actual_ext = os.path.splitext(actual_file).lower()
        if actual_ext == target_ext and make_key(actual_file) == target_key:
            return os.path.join(MEDIA_DIR, actual_file)
    return os.path.join(MEDIA_DIR, target_filename)

def _dual_layer_panel(key, r_before=None, r_after=None):
    if key not in STUDIO_CLIPS:
        return
    filename, domain_tag, subtitle, steps, outcome_text = STUDIO_CLIPS[key]
    video_url = f"{RAW_VIDEOS}/{filename}"
    accent = "#0284C7" if key == "urban" else "#DC2626"
    col_3d, col_2d = st.columns((1.55, 1.0), gap="medium")
    with col_3d:
        components.html(f"""
        <style>
          *{{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}
          .card{{background:#FFF;border:1px solid #E2E8F0;border-radius:16px;overflow:hidden}}
          .bar{{display:flex;justify-content:space-between;padding:11px 18px;background:#F8FAFC;border-bottom:1px solid #E2E8F0}}
          .tag{{font-size:11px;font-weight:800;text-transform:uppercase;color:{accent}}}
          video{{width:100%;height:420px;object-fit:contain;background:#FFF;display:block}}
        </style>
        <div class="card">
          <div class="bar"><span class="tag">{domain_tag}</span><span style="font-size:12px;color:#475569;font-weight:600">Main 3D + 2D</span></div>
          <video autoplay loop muted playsinline controls><source src="{video_url}" type="video/mp4"></video>
        </div>
        """, height=470)
    with col_2d:
        with st.container(border=True):
            st.markdown(f"**{subtitle}**")
            st.caption("R = L · E · V · (1 − ρ)")
            for title, desc, clr in steps:
                st.markdown(f'<div style="border-left:4px solid {clr};padding:6px 10px;margin-bottom:8px;background:#F8FAFC;border-radius:0 8px 8px 0;"><div style="font-size:12.5px;font-weight:800;color:#0F172A;">{title}</div><div style="font-size:12px;color:#475569;">{desc}</div></div>', unsafe_allow_html=True)
            if r_before is not None and r_after is not None:
                fig = go.Figure(go.Bar(x=("Baseline R", "Post-Resilience R"), y=(r_before, r_after), marker_color=("#EF4444", "#10B981"), text=(f"{r_before:.3f}", f"{r_after:.3f}"), textposition="outside"))
                fig.update_layout(height=150, margin=dict(l=10, r=10, t=10, b=20), yaxis=dict(range=(0, max(r_before, r_after) * 1.35), visible=False), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
    with st.container(border=True):
        st.markdown("**RMTI Process & Quantified Outcome**")
        st.write(outcome_text)

def videos_page():
    st.header("🎬 Narrated 3D Motion Video Library")
    st.write("Explore how the RMTI framework tracks cellular dynamics, tumor-immune barriers, and residual risks.")
    
    st.subheader("1. Ductal Progression & Subtype Divergence")
    st.video(scan_and_resolve("Ductal Progression & Subtype Divergence Scenes 1-3.mp4"))
    st.audio(scan_and_resolve("Ductal Progression & Subtype Divergence Scenes 1-3.mp3"))
    st.divider()
    
    st.subheader("2. Cells Forming Tumor Immune Barrier (Scene 4)")
    st.video(scan_and_resolve("Cells_forming_tumor_immune_barrier_scene 4.mp4"))
    st.audio(scan_and_resolve("Cells Forming Tumor Immune Barrier Scene 4.mp3"))
    st.divider()

    st.subheader("3. Cells Blocking Tumor Infiltration (Scene 5)")
    st.video(scan_and_resolve("Cells_blocking_tumor_infiltration_scene 5.mp4"))
    st.audio(scan_and_resolve("Cells Blocking Tumor Infiltration Scene 5.mp3"))
    st.divider()

    st.subheader("4. Cells Forming Tumor Immune Barrier (Scenes 6-8)")
    st.video(scan_and_resolve("Cells_forming_tumor_immune_barrier_Scenes 6-8.mp4"))
    st.audio(scan_and_resolve("Cells Forming Tumor Immune Barrier Scenes 6-8.mp3"))
    st.divider()

    st.subheader("5. Antibodies Destroying Tumor Cells")
    st.video(scan_and_resolve("Antibodies_destroying_tumor_cells.mp4"))
    st.audio(scan_and_resolve("Antibodies Destroying Tumor Cells.mp3"))
    st.divider()

    st.subheader("6. Tumor Microenvironment Exposure & Resilience Deficit")
    st.video(scan_and_resolve("Tumor Microenvironment Exposure & Resilience Deficit.mp4"))
    st.audio(scan_and_resolve("Tumor Microenvironment Exposure & Resilience Deficit.mp3"))
    st.divider()

    st.subheader("7. Escalating Residual Risk Trajectory")
    st.video(scan_and_resolve("Escalating Residual Risk Trajectory .mp4"))
    st.audio(scan_and_resolve("Escalating Residual Risk Trajectory.mp3"))

def johnson_page():
    st.header("📊 Johnson Cohort Surveillance Analysis")
    st.write("Tracking longitudinal medical and demographic surveillance datasets.")

def urban_page():
    st.header("🏙️ Sub-Saharan Urban Flooding Case Study")
    _dual_layer_panel("urban", 0.420, 0.218)

def case_page(key):
    st.header(f"Clinical Case Profile: {key.upper()}")
    if key == "liver":
        _dual_layer_panel("liver", 0.258, 0.107)
    elif key == "lung":
        _dual_layer_panel("lung", 0.281, 0.112)
    elif key == "breast":
        _dual_layer_panel("breast", 0.234, 0.098)
