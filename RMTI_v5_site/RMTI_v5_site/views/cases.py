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
    it = iter(tabs)
    with next(it):
        _video(key, c["title"].lower())
    with next(it):
        cols = st.columns(4, gap="medium")
        for col, (name, text) in zip(cols, c["stages"]):
            col.markdown(card(name, text), unsafe_allow_html=True)
    with next(it):
        st.dataframe(pd.DataFrame(c["mapping"], columns=("Lever", "Published data used")), hide_index=True, width="stretch")
        a, b = st.columns(2)
        a.metric("R at first review", f"{c['r_before']:.3f}")
        a.markdown(badge(core.tier(c["r_before"])), unsafe_allow_html=True)
        b.metric("R after improvement", f"{c['r_after']:.3f}", f"{(c['r_after'] / c['r_before'] - 1) * 100:.0f}%", delta_color="inverse")
        b.markdown(badge(core.tier(c["r_after"])), unsafe_allow_html=True)
    with next(it):
        g1, g2 = st.columns((1, 2.2), gap="large")
        with g1:
            L = st.slider("L", 0.0, 1.0, 0.5, 0.01, key=f"{key}L")
            E = st.slider("E", 0.0, 1.0, 0.5, 0.01, key=f"{key}E")
        pts = []
        with g2:
            cols = st.columns(4)
            for i, col in enumerate(cols):
                v = col.slider(f"V cycle {i + 1}", 0.0, 1.0, round(0.60 - 0.04 * i, 2), 0.01, key=f"{key}V{i}")
                r = col.slider(f"ρ cycle {i + 1}", 0.0, 0.95, round(0.20 + 0.12 * i, 2), 0.01, key=f"{key}R{i}")
                pts.append(core.score(L, E, v, r)["R_raw"])
        fig = go.Figure()
        add_tier_bands(fig)
        fig.add_trace(go.Scatter(x=list(range(1, 5)), y=pts, mode="lines+markers", line=dict(color="#0F172A", width=4), marker=dict(size=13)))
        fig.update_layout(xaxis=dict(title="Review cycle", dtick=1), yaxis_title="Residual risk R", yaxis_range=(0, max(0.4, max(pts) * 1.2)), showlegend=False)
        st.plotly_chart(style_fig(fig, 360), width="stretch")       
    if key == "liver":
        with next(it):
            _hcc_guidance_tab()
    if key == "breast":
        with next(it):
            _gbd_tab()
    with next(it):
        _refs(key)
    disclaimer()


def johnson_page():
    J = content.JOHNSON
    page_header("HCC progression: the pathway matters for surveillance", "Johnson et al. (BJC Reports, 2024) followed 2,592 non-cirrhotic chronic liver disease patients.", "Oncology case studies")
    k0, k1, k2, k3 = st.columns(4, gap="medium")
    k0.metric("HCC developed", f"{J['hcc']}", f"{J['hcc'] / J['n']:.0%} of cohort", delta_color="off")
    k1.metric("Never passed through cirrhosis", f"{J['no_cirrhosis']}", "28% of HCC", delta_color="off")
    k2.metric("HBV that skipped cirrhosis", f"{J['hbv_direct']} of {J['hbv_total']}", "69%", delta_color="off")
    k3.metric("HCC per 1,000 patient-years", f"{J['rate_noncirr']} vs {J['rate_cirr']}", "non-cirrhotic vs cirrhotic", delta_color="off")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        fig = go.Figure(go.Bar(x=("Passed through cirrhosis", "Remained non-cirrhotic"), y=(J["via_cirrhosis"], J["no_cirrhosis"]), marker_color=("#0284C7", "#EF4444"), text=(J["via_cirrhosis"], J["no_cirrhosis"]), textposition="outside"))
        fig.update_layout(title="Pathway to HCC (n = 172)", yaxis_title="Patients")
        st.plotly_chart(style_fig(fig, 400), width="stretch")
    with c2:
        fig = go.Figure(go.Bar(x=("Hepatitis B", "Hepatitis C"), y=(J["hbv_direct"] / J["hbv_total"] * 100, J["hcv_noncirr"] / J["hcv_total"] * 100), marker_color=("#EF4444", "#38BDF8"), text=(f"{J['hbv_direct']}/{J['hbv_total']}", f"{J['hcv_noncirr']}/{J['hcv_total']}"), textposition="outside"))
        fig.update_layout(title="HCC without cirrhosis, by aetiology", yaxis_title="% of HCC cases", yaxis_range=(0, 100))
        st.plotly_chart(style_fig(fig, 400), width="stretch")
    with st.container(border=True):
        st.markdown("**RMTI Process & Clinical Outcome**")
        st.write("28% of all HCC cases (and 69% of HBV-related HCC) bypassed cirrhosis entirely. RMTI decouples Exposure (E) and Resilience (ρ) from cirrhosis-only gating.")
    disclaimer()


def urban_page():
    from views import urban_cases
          if hasattr(urban_cases, 'render'):
        urban_cases.render()
    elif hasattr(urban_cases, 'main'):
        urban_cases.main()
    elif hasattr(urban_cases, 'show'):
        urban_cases.show()
    else:
        import streamlit as st
        st.info("Sub-Saharan Urban Flooding module is initializing...")

        st.info("Sub-Saharan Urban Flooding module is initializing...")

BREAST_VTT = """WEBVTT

00:00:00.000 --> 00:00:38.000
[Scene 1 · Opening | Oncoclastics · RMTI]
R = L · E · V · (1 − ρ) — Research prototype; illustrative & published aggregate values only.

00:00:38.000 --> 00:01:16.000
[Scene 2 · Source & Cohort | Moura et al., Curr Oncol 2025;32:143]
Luminal A, Luminal B, HER2+, Triple Negative — ~2.3M diagnoses & >660,000 deaths (2022).

00:01:16.000 --> 00:02:11.000
[Scene 3 · Equation & Four Levers | rmti_core.py v2.2.1]
L = 660,000 ÷ 2,300,000 = 0.287 · E: 8 TME mechanisms · V: 3 features · ρ: 4 therapy features.

00:02:11.000 --> 00:02:58.000
[Scene 4 · Baseline Subtype Scores]
Luminal A 0.002 · Luminal B 0.027 · HER2+ 0.065 · TNBC 0.170 (2.6× HER2+, 99× Luminal A; ρ = 0.175).

00:02:58.000 --> 00:03:31.000
[Scene 5 · Fixed Tiers]
Tier 1 Low (<0.05): Luminal A & B · Tier 2 Moderate (<0.15): HER2+ · Tier 3 High (<0.35): TNBC.

00:03:31.000 --> 00:04:14.000
[Scene 6 · Which Lever to Pull]
TNBC ρ: 0.175 → 0.40 cuts R 27.3% (0.170 → 0.124, Tier 2) · E: 0.80 → 0.70 gives 0.149 (−12.5%).

00:04:14.000 --> 00:04:52.000
[Scene 7 · Rubric Sensitivity | 10,000 Perturbed Runs]
Median rank order holds · TNBC: 83.1% Tier 2, 16.9% Tier 3 · At L = 0.40, TNBC R = 0.238 (Tier 3).

00:04:52.000 --> 00:05:30.000
[Scene 8 · Expected Annual Loss & Close]
EAL = L · C · (1 − ρ) (C = 5): TNBC 0.237 vs. others 0.172 · Hypothesis-generating research prototype.
"""


def videos_page():
    page_header(
        "Video Library — Narrated RMTI Walkthroughs & Case Studies",
        "High-contrast 3D + 2D mechanism walkthroughs synchronized with rmti_core.py calculations and peer-reviewed evidence.",
        "Case studies",
    )

    raw_vid = "".join(["https://raw.", "githubusercontent.", "com/drmarolla/RMTI_API/main/assets/videos"])
    breast_mp4 = f"{raw_vid}/rmti_breast_case_study.mp4"
    fallback_mp4 = f"{raw_vid}/video1_4stages_3d.mp4"

    st.subheader("Case Study 1: Breast Cancer & Tumor Microenvironment (Moura et al., 2025)")
    scen = st.radio(
        "Interactive 2D Telemetry Overlay (rmti_core.py v2.2.1 · Marolla, 2026)",
        [
            "Baseline (L = 0.287 · TNBC ρ = 0.175)",
            "Scenario A: TNBC Resilience Parity (ρ: 0.175 → 0.40, −27.3%)",
            "Scenario B: Optimised TNBC Resilience (ρ → 0.55, −45.5%, IEI 1.01)",
            "Scenario C: TME Exposure Reduction (E: 0.80 → 0.70, −12.5%)",
            "Sensitivity: Higher Global Likelihood (L = 0.40)",
        ],
        horizontal=True,
    )

    presets = {
        "Baseline (L = 0.287 · TNBC ρ = 0.175)": [("Luminal A", 0.002, "Tier 1", "#38BDF8"), ("Luminal B", 0.027, "Tier 1", "#60A5FA"), ("HER2+", 0.065, "Tier 2", "#F59E0B"), ("TNBC", 0.170, "Tier 3", "#F43F5E")],
        "Scenario A: TNBC Resilience Parity (ρ: 0.175 → 0.40, −27.3%)": [("Luminal A", 0.002, "Tier 1", "#38BDF8"), ("Luminal B", 0.027, "Tier 1", "#60A5FA"), ("HER2+", 0.065, "Tier 2", "#F59E0B"), ("TNBC (ρ=0.40)", 0.124, "Tier 2", "#10B981")],
        "Scenario B: Optimised TNBC Resilience (ρ → 0.55, −45.5%, IEI 1.01)": [("Luminal A", 0.002, "Tier 1", "#38BDF8"), ("Luminal B", 0.027, "Tier 1", "#60A5FA"), ("HER2+", 0.065, "Tier 2", "#F59E0B"), ("TNBC (ρ=0.55)", 0.093, "Tier 2", "#10B981")],
        "Scenario C: TME Exposure Reduction (E: 0.80 → 0.70, −12.5%)": [("Luminal A", 0.002, "Tier 1", "#38BDF8"), ("Luminal B", 0.027, "Tier 1", "#60A5FA"), ("HER2+", 0.065, "Tier 2", "#F59E0B"), ("TNBC (E=0.70)", 0.149, "Tier 2*", "#FBBF24")],
        "Sensitivity: Higher Global Likelihood (L = 0.40)": [("Luminal A", 0.002, "Tier 1", "#38BDF8"), ("Luminal B", 0.038, "Tier 1", "#60A5FA"), ("HER2+", 0.091, "Tier 2", "#F59E0B"), ("TNBC (L=0.40)", 0.238, "Tier 3", "#F43F5E")],
    }
    bars = presets[scen]
    bars_html = "".join(
        f'<div style="display:flex;flex-direction:column;align-items:center;gap:4px">'
        f'<span style="font-size:11px;font-weight:800;color:#FFF">{val:.3f}</span>'
        f'<div style="width:36px;height:{max(8, int((val/0.25)*125))}px;background:{clr};border-radius:5px 5px 1px 1px;box-shadow:0 0 12px {clr}66"></div>'
        f'<span style="font-size:10px;font-weight:700;color:#E2E8F0;text-align:center">{lbl}</span>'
        f'<span style="font-size:9.5px;font-weight:800;color:{clr}">{tr}</span></div>'
        for lbl, val, tr, clr in bars
    )

    v_col, hud_col = st.columns((1.25, 1.0), gap="large")
    with v_col:
        st.video(breast_mp4, subtitles=BREAST_VTT)
        st.caption("Running time: 5:30 (760 spoken words at 145 wpm) · File: `assets/videos/rmti_breast_case_study.mp4`")
    with hud_col:
        st.components.v1.html(f"""
        <style>*{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}</style>
        <div style="background:linear-gradient(145deg,#0B1120,#1E293B);border:1px solid #334155;border-radius:16px;padding:16px;color:#F8FAFC;height:345px;display:flex;flex-direction:column;justify-content:space-between">
          <div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
              <span style="background:#F43F5E;color:#FFF;font-size:10px;font-weight:800;padding:3px 8px;border-radius:4px">MAIN 3D + 2D TELEMETRY</span>
              <span style="font-size:11px;font-weight:700;color:#38BDF8">R = L · E · V · (1 − ρ)</span>
            </div>
            <div style="font-size:13px;font-weight:800;color:#FFFFFF">{scen}</div>
            <div style="font-size:11px;color:#94A3B8;margin-top:2px">8 TME Mechanisms (M2 TAM, Treg, MDSC, N2, IL-17, pDC, Exhaustion, Stiff ECM)</div>
          </div>
          <div style="display:grid;grid-template-columns:repeat(4,1fr);align-items:end;height:185px;padding:10px 8px 4px 8px;border-bottom:1.5px solid #475569;background:rgba(15,23,42,0.55);border-radius:10px">
            {bars_html}
          </div>
          <div style="display:flex;justify-content:space-between;font-size:11px;color:#CBD5E1;font-weight:700">
            <span>EAL (C=5): TNBC 0.237 vs. others 0.172</span>
            <span style="color:#38BDF8">10k MC: 83.1% T2 / 16.9% T3</span>
          </div>
        </div>
        """, height=352)

    with st.expander("Full 8-Scene Narration Script & Rubric Reference (Moura et al., 2025 · Marolla, 2026)", expanded=False):
        st.markdown(
            "- **Scene 1 (0:00–0:38) Opening:** *R = L · E · V · (1 − ρ)* applied to breast cancer tumor microenvironment subtypes (research prototype; no patient data).\n"
            "- **Scene 2 (0:38–1:16) Cohort:** Moura et al. (*Curr. Oncol.* 2025;32:143) — Luminal A, Luminal B, HER2+, Triple Negative (~2.3M diagnoses, >660,000 deaths in 2022).\n"
            "- **Scene 3 (1:16–2:11) Four Levers:** `L = 0.287`; `E` from 8 immunosuppressive TME mechanisms; `V` from grade, spread, prognosis; `ρ` from targeted therapy, resistance, toxicity, immune options.\n"
            "- **Scene 4 (2:11–2:58) Scores:** Luminal A `0.002`, Luminal B `0.027`, HER2+ `0.065`, TNBC `0.170` (`2.6×` HER2+, `99×` Luminal A; `ρ = 0.175` vs. `0.40`).\n"
            "- **Scene 5 (2:58–3:31) Fixed Tiers:** Tier 1 Low (`<0.05`: Luminal A & B), Tier 2 Moderate (`<0.15`: HER2+), Tier 3 High (`<0.35`: TNBC).\n"
            "- **Scene 6 (3:31–4:14) Levers:** Raising TNBC `ρ` `0.175 → 0.40` lowers `R` `27.3%` (`0.170 → 0.124`, Tier 2); lowering `E` `0.80 → 0.70` gives `0.149` (`−12.5%`, borderline).\n"
            "- **Scene 7 (4:14–4:52) Sensitivity:** 10,000 one-step rubric perturbations preserve median rank order (TNBC `83.1%` Tier 2, `16.9%` Tier 3); at `L = 0.40`, TNBC `R = 0.238` (Tier 3).\n"
            "- **Scene 8 (4:52–5:30) EAL & Close:** `EAL = L · C · (1 − ρ)` (`C = 5`): TNBC `0.237` vs. `0.172` for other subtypes."
        )
        st.caption(
            "**Sources:** Moura, T., Laranjeira, P., Caramelo, O., Gil, A. M., & Paiva, A. (2025). *Breast Cancer and Tumor Microenvironment: The Crucial Role of Immune Cells.* "
            "*Current Oncology*, 32(3), 143 (`doi:10.3390/curroncol32030143`) · Marolla, C. (2026). *Applying RMTI to a Breast Cancer Cohort* (`rmti_core.py v2.2.1`)."
        )

    st.divider()
    st.subheader("Additional Framework Walkthroughs")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("**Hepatocellular Carcinoma (HCC) 4-Stage Progression & Triage**")
        st.video(f"{raw_vid}/video1_4stages_3d.mp4?v=7")
    with c2:
        st.markdown("**Time-Indexed Trajectory R(t) & Kalman Filtering**")
        st.video(f"{raw_vid}/video2_trajectory_3d.mp4?v=7")

    disclaimer()

