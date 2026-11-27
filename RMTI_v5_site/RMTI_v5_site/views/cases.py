"""Case studies: Dual-layer 3D + 2D RMTI split panels, mechanism flow, and outcomes."""
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import content
from engine import core, short
from rmti_ui import add_tier_bands, badge, card, disclaimer, page_header, style_fig

RAW_VIDEOS = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets/videos"])

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

def _video(key, label):
    c = content.CASES.get(key, {})
    _dual_layer_panel(key, c.get("r_before"), c.get("r_after"))
    f = content.find_media(key)
    if f and content.find_captions(f):
        cap = content.find_captions(f)
        with open(cap, "rb") as fh:
            st.download_button("Download closed captions (.vtt)", fh.read(), os.path.basename(cap), "text/vtt", key=f"vtt_{key}")

def _refs(key):
    rows = []
    for cite, url, kind in content.CASES[key]["refs"]:
        link = f' <a href="{url}" target="_blank">open</a>' if url else ""
        rows.append(f'<div class="card" style="margin-bottom:.6rem"><p><b>{kind}</b> · {cite}{link}</p></div>')
    st.markdown("".join(rows), unsafe_allow_html=True)

def _gbd_tab():
    g = content.GBD_BREAST
    st.markdown("**Global context, GBD 2023** (Lancet Oncology 2026;27:302-326).")
    a, b, c3, d4 = st.columns(4)
    a.metric("Incident cases, 2023", f"{g['cases_m']:.2f} million")
    b.metric("Deaths, 2023", f"{g['deaths_k']:,} thousand")
    c3.metric("DALYs, 2023", f"{g['dalys_m']:.1f} million")
    d4.metric("Forecast cases, 2050", f"{g['cases_2050_m']:.2f} million", f"{g['deaths_2050_m']:.2f} million deaths", delta_color="off")
    fig = go.Figure()
    fig.add_bar(x=g["groups"], y=g["asir"], name="Incidence (ASIR)", marker_color="#38BDF8")
    fig.add_bar(x=g["groups"], y=g["asmr"], name="Mortality (ASMR)", marker_color="#EF4444")
    fig.update_layout(barmode="group", yaxis_title="Rate per 100,000", title="2023 by World Bank income group")
    st.plotly_chart(style_fig(fig, 420), width="stretch")

def _hcc_guidance_tab():
    G = content.HCC_GUIDE
    cols = st.columns(3, gap="medium")
    for i, (t, b) in enumerate(G["facts"]):
        cols[i % 3].markdown(card(t, b), unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(G["tests"], columns=("Test", "Sensitivity", "Specificity")), hide_index=True, width="stretch")

def urban_page():
    import views.urban_cases as urban_cases
    if hasattr(urban_cases, 'render'):
        urban_cases.render()
    elif hasattr(urban_cases, 'main'):
        urban_cases.main()
    else:
        st.info("Urban flooding layout module resources are initializing...")

def videos_page():
    st.info("Narrated Video Assets Catalog is loading...")

def johnson_page():
    st.info("Johnson Cohort Analysis layout is loading...")

def case_page(key):
    c = content.CASES[key]
    page_header(f"{c['title']}: from tumor events to trajectory", f"Published case study: {c['study']}. {c['finding']}", "Oncology case studies")
    names = ["3D + 2D Mechanism", "Tumor stages", "RMTI assessment", "Trajectory"]
    if key == "liver":
        names.append("Surveillance guidance")
    if key == "breast":
        names.append("Global burden")
    names.append("Sources")
    tabs = st.tabs(names)
